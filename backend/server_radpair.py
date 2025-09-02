#!/usr/bin/env python3
"""
RADPAIR BETA - GERMAN MEDICAL TRANSCRIPTION SERVER
===================================================
Version: radpair-beta-v1
Date: 2025-01-09
Status: PRODUCTION READY

Based on Magnus Opus v3-audio-german-FINAL with simplified UI:
- Single transcript box that updates from live to polished
- No concatenated audio transcription
- Dark mode UI with RadPair branding
- All core logic preserved from working version

CRITICAL: Core transcription logic unchanged from v3-audio-german-FINAL
"""

import asyncio
import json
import time
from pathlib import Path
import sys
import os
from datetime import datetime
from dotenv import load_dotenv
import logging

# Set up minimal logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))  # Go up to magnus_opus_streamlined
sys.path.append(str(Path(__file__).parent.parent))  # Also add parent for fallback

# Import from German audio version of core components - UNCHANGED
from src.core_components_audio_german import (
    MagnusOpusHandler,
    MedicalTurnProcessor,
    SpeechDetector,
    macro_processor,
    DEFAULT_STUDY_TYPE,
    PRE_CONTEXT_CHUNKS,
    SAMPLE_RATE,
)

# Load environment variables
load_dotenv()


class WebSocketWrapper:
    """Wrapper to make FastAPI WebSocket compatible with websockets library API"""
    def __init__(self, fastapi_websocket):
        self.ws = fastapi_websocket
    
    async def send(self, message):
        """Convert websockets.send(json.dumps()) to FastAPI send_json()"""
        if isinstance(message, str):
            try:
                # Try to parse as JSON and use send_json
                data = json.loads(message)
                await self.ws.send_json(data)
            except json.JSONDecodeError:
                # If not JSON, send as text
                await self.ws.send_text(message)
        else:
            # For bytes
            await self.ws.send_bytes(message)


class RadPairHandler(MagnusOpusHandler):
    """RadPair Beta handler - simplified version without concatenated audio"""

    def __init__(self, websocket):
        """Initialize RadPair handler"""
        # Wrap the FastAPI WebSocket to make it compatible
        wrapped_ws = WebSocketWrapper(websocket)
        super().__init__(wrapped_ws)
        self.original_websocket = websocket  # Keep original for direct use if needed
        self.completed_segments = []
        self.is_recording = False
        self.current_turn = None
        self.turn_count = 0
        self.speech_detector = SpeechDetector()
        
        # Still save audio files but don't concatenate
        self.audio_file_paths = []
        
        # Cache polish client for performance
        self.polish_client = None
    
    def load_study_types(self):
        """Load German study types from file
        
        NOTE: This is a placeholder implementation for RadPair Beta.
        In production, this should connect to the RadPair backend study catalog.
        
        TODO: Replace with API call to RadPair backend:
        Example: 
            response = requests.get('https://api.radpair.com/v1/study-types/de')
            return response.json()['study_types']
        """
        study_types = []
        # Single source of truth: file under backend/data/
        german_studies_file = Path(__file__).parent / "data" / "German_studies.text"
        
        try:
            if german_studies_file.exists():
                with open(german_studies_file, 'r', encoding='utf-8') as f:
                    study_types = [line.strip() for line in f if line.strip()]
                logger.info(f"Loaded {len(study_types)} German study types from file")
            else:
                logger.warning("German_studies.text not found, using defaults")
                # Fallback to some common German study types
                study_types = [
                    "CT Thorax",
                    "CT Abdomen",
                    "MRT Kopf",
                    "MRT Wirbelsäule",
                    "Röntgen Thorax",
                    "Sonographie Abdomen",
                    "Angiographie"
                ]
        except Exception as e:
            logger.error(f"Error loading study types: {e}")
            # Return minimal defaults on error
            study_types = ["CT Thorax", "MRT Kopf", "Röntgen Thorax"]
        
        return study_types

    async def initialize(self):
        """Initialize Gemini client only"""
        await super().initialize()
        logger.info("RadPair Beta German handler initialized")

    async def handle_audio_chunk(self, audio_data):
        """Process audio for real-time transcription only"""
        # Fix for odd-length audio chunks
        if len(audio_data) % 2 != 0:
            audio_data = audio_data + b'\x00'
        
        # Process through speech detector
        state_change = self.speech_detector.process_chunk(audio_data)

        # Handle speech state changes
        if state_change == "speech_start" and not self.current_turn:
            logger.info(f"==================== SPEECH STARTED ====================")
            logger.info(f"Turn {self.turn_count + 1} beginning")
            self.turn_count += 1
            turn = MedicalTurnProcessor(
                self.client,
                self.turn_count,
                self.websocket,
                self.current_study_type,
                language="de-DE"  # German language setting
            )
            self.current_turn = await turn.__aenter__()

            # Add pre-context audio
            buffer = self.speech_detector.get_buffer()
            if buffer:
                pre_context = buffer[-PRE_CONTEXT_CHUNKS:] if len(buffer) >= PRE_CONTEXT_CHUNKS else buffer
                logger.info(f"Turn {self.turn_count}: Adding {len(pre_context)} pre-context audio chunks")
                for chunk in pre_context:
                    await self.current_turn.add_audio(chunk)

        elif state_change == "speech_end" and self.current_turn:
            logger.info(f"==================== SPEECH ENDED ====================")
            logger.info(f"Turn {self.turn_count}: Finalizing and collecting transcript")
            
            # First call finalize to get the transcript
            result = await self.current_turn.finalize()
            
            # Track audio file if saved
            if hasattr(self.current_turn, 'audio_file_path') and self.current_turn.audio_file_path:
                self.audio_file_paths.append(self.current_turn.audio_file_path)
                logger.info(f"Turn {self.turn_count}: Audio saved to {self.current_turn.audio_file_path}")
            
            # Then properly close the context manager
            await self.current_turn.__aexit__(None, None, None)
            
            # Store completed segment
            if result:
                logger.info(f"Turn {self.turn_count}: Segment completed with transcript: '{result}'")
                self.completed_segments.append(result)
            else:
                logger.warning(f"Turn {self.turn_count}: No transcript received")
            
            self.current_turn = None
            self.speech_detector.clear_buffer()

        # If currently in a turn, send audio
        if self.current_turn:
            await self.current_turn.add_audio(audio_data)

    async def start_recording(self, study_type=None):
        """Start recording session"""
        self.current_study_type = study_type or DEFAULT_STUDY_TYPE
        self.is_recording = True
        self.turn_count = 0
        self.completed_segments = []
        self.audio_file_paths = []
        
        logger.info(f"Starting recording for study type: {self.current_study_type}")
        
        # Send status to UI (use wrapped websocket which has send method)
        await self.websocket.send(json.dumps({
            "type": "status",
            "message": f"Aufnahme läuft für {self.current_study_type}..."
        }))

    async def stop_recording(self):
        """Stop recording and trigger polish only (no concatenation)"""
        logger.info("Stopping recording...")
        self.is_recording = False
        
        # Force end current turn if active
        if self.current_turn:
            logger.info("Finalizing active turn...")
            # First call finalize to get the transcript
            result = await self.current_turn.finalize()
            
            # Track audio file if saved
            if hasattr(self.current_turn, 'audio_file_path') and self.current_turn.audio_file_path:
                self.audio_file_paths.append(self.current_turn.audio_file_path)
                logger.info(f"Final turn: Audio saved to {self.current_turn.audio_file_path}")
            
            # Then properly close the context manager
            await self.current_turn.__aexit__(None, None, None)
            
            if result:
                self.completed_segments.append(result)
                logger.info(f"Final turn: Segment completed with transcript: '{result}'")
            else:
                logger.warning("Final turn: No transcript received")
                
            self.current_turn = None
            self.speech_detector.clear_buffer()
        
        # Create polished transcript
        if self.completed_segments:
            await self._create_polish()
        else:
            logger.info("No segments to polish")
            await self.websocket.send(json.dumps({
                "type": "status",
                "message": "Keine Aufnahme zum Polieren"
            }))

    async def _create_polish(self):
        """Create polished version and send to UI to replace live transcript"""
        # Combine segments with space instead of double newline for deduplication
        combined = " ".join([s for s in self.completed_segments if s])
        
        if not combined.strip():
            logger.info("No content to polish")
            await self.websocket.send(json.dumps({
                "type": "status",
                "message": "Kein Inhalt zum Polieren"
            }))
            return
        
        # Remove duplicate sentences (from original version)
        sentences = combined.split('. ')
        seen = []
        unique_sentences = []
        for sent in sentences:
            sent_clean = sent.strip().lower()
            if sent_clean and sent_clean not in seen:
                seen.append(sent_clean)
                unique_sentences.append(sent.strip())
        
        combined_transcript = '. '.join(unique_sentences)
        if combined_transcript and not combined_transcript.endswith('.'):
            combined_transcript += '.'
        
        logger.info(f"After deduplication: {len(combined_transcript)} chars (from {len(combined)} chars)")
        
        try:
            # Send status
            await self.websocket.send(json.dumps({
                "type": "status",
                "message": "Polierung läuft..."
            }))
            
            logger.info("==================== STARTING POLISH ====================")
            logger.info(f"Input length: {len(combined_transcript)} characters")
            
            # Create polish prompt - EXACT SAME AS WORKING VERSION (simpler, faster)
            polish_prompt = f"""LANGUAGE: Output MUST be in GERMAN (de-DE). Do NOT translate to English.

Polieren Sie diese medizinische Transkription:
1. Korrigieren Sie offensichtliche Fehler
2. Stellen Sie konsistente Formatierung sicher
3. Korrigieren Sie medizinische Terminologie
4. Entfernen Sie Wiederholungen
5. Sorgen Sie für natürlichen Fluss

Intelligente Korrekturbehandlung:
- Wenn Nutzer "nicht X" nach X sagt, entfernen Sie X
- Wenn Nutzer "ich meine Y" nach X sagt, ersetzen Sie X durch Y

Original-Transkript:
{combined_transcript}

Geben Sie NUR den polierten Text ohne Erklärung zurück."""
            
            # Use cached polish client or initialize once
            if not self.polish_client:
                from google import genai
                api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
                self.polish_client = genai.Client(api_key=api_key)
                logger.info("Polish client initialized and cached")
            
            # Get response from Gemini Flash LITE - FASTER MODEL
            response = self.polish_client.models.generate_content(
                model="gemini-2.5-flash-lite",  # Flash lite for fast polish
                contents=polish_prompt
            )
            
            polished = response.text.strip()
            
            logger.info(f"Polish complete. Output length: {len(polished)} characters")
            logger.info("==================== POLISH COMPLETE ====================")
            
            # Send polished transcript to replace live version
            await self.websocket.send(json.dumps({
                "type": "polished_transcript",
                "text": polished
            }))
            
            await self.websocket.send(json.dumps({
                "type": "status",
                "message": "Abgeschlossen"
            }))
            
        except Exception as e:
            logger.error(f"Error during polish: {e}")
            await self.websocket.send(json.dumps({
                "type": "error",
                "message": f"Fehler beim Polieren: {str(e)}"
            }))


# WebSocket server setup - UNCHANGED FROM WORKING VERSION
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# CORS (configurable via env, defaults open)
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
origins = [o.strip() for o in allowed_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health-friendly root endpoint for Cloud Run"""
    return JSONResponse({"status": "ok", "service": "radpair-german-backend"})


@app.get("/healthz")
async def healthz():
    return JSONResponse({"status": "ok"})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for RadPair Beta"""
    await websocket.accept()
    handler = RadPairHandler(websocket)
    
    try:
        # Initialize handler
        await handler.initialize()
        
        # Load and send study types
        study_types = handler.load_study_types()
        await websocket.send_json({
            "type": "study_types",
            "study_types": study_types
        })
        
        # Main message loop
        while True:
            try:
                # Try to receive text/json first
                message = await asyncio.wait_for(websocket.receive(), timeout=0.1)
                
                if "text" in message:
                    data = json.loads(message["text"])
                    
                    if data["type"] == "start_recording":
                        study_type = data.get("study_type", DEFAULT_STUDY_TYPE)
                        await handler.start_recording(study_type)
                    
                    elif data["type"] == "stop_recording":
                        await handler.stop_recording()
                    
                    elif data["type"] == "get_study_types":
                        study_types = handler.load_study_types()
                        await websocket.send_json({
                            "type": "study_types",
                            "study_types": study_types
                        })
                
                elif "bytes" in message:
                    # Handle audio data
                    if handler.is_recording:
                        audio_data = message["bytes"]
                        await handler.handle_audio_chunk(audio_data)
                        
            except asyncio.TimeoutError:
                continue
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in message loop: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
    
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
    finally:
        if handler.current_turn:
            try:
                await handler.current_turn.__aexit__(None, None, None)
            except:
                pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", os.environ.get("SERVER_PORT", 8080)))
    logger.info(f"Starting RadPair German backend on 0.0.0.0:{port}")

    # Create audio recordings directory if it doesn't exist
    audio_dir = Path(__file__).parent / "audio_recordings"
    audio_dir.mkdir(exist_ok=True)

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
