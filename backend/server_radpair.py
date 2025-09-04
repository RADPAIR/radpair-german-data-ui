#!/usr/bin/env python3
"""
RADPAIR BETA - GERMAN MEDICAL TRANSCRIPTION SERVER (NO POLISH VERSION)
=======================================================================
Version: radpair-beta-v2-no-polish
Date: 2025-01-09
Status: PRODUCTION READY

Changes from v1:
- NO POLISH STEP - Direct transcription only
- ACCUMULATIVE TRANSCRIPT - Each pause adds to previous content
- Voice commands for punctuation handled in prompts

Based on Magnus Opus v3-audio-german-FINAL with modifications
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
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent))

# Import from German audio version of core components - UNCHANGED
from src.core_components_audio_german import (
    MagnusOpusHandler,
    MedicalTurnProcessor as OriginalMedicalTurnProcessor,
    SpeechDetector,
    macro_processor,
    DEFAULT_STUDY_TYPE,
    PRE_CONTEXT_CHUNKS,
    SAMPLE_RATE,
)

# Import the new prompt with punctuation commands
from src.core_components_radpair_v2 import create_german_medical_prompt_v2

# Load environment variables
load_dotenv()


class MedicalTurnProcessor(OriginalMedicalTurnProcessor):
    """Override to use new prompt with punctuation commands"""
    
    async def __aenter__(self):
        """Start the medical turn with custom prompt"""
        self.turn_start_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        logger.info(f"Turn {self.turn_number}: Starting medical transcription turn for {self.study_type} at {self.turn_start_time}")
        
        try:
            from google import genai
            from google.genai import types
            from google.genai.types import LiveConnectConfig, Modality
            
            # Use the NEW prompt with punctuation commands
            prompt = create_german_medical_prompt_v2(self.study_type, self.language)
            logger.info(f"Turn {self.turn_number}: System instruction prepared ({len(prompt)} chars)")
            
            # Rest is same as original
            config = LiveConnectConfig(
                response_modalities=[Modality.TEXT],
                realtime_input_config={
                    "automatic_activity_detection": {"disabled": True}
                },
                system_instruction=prompt,
                temperature=0.0,
                top_p=0.1,
                top_k=1,
                max_output_tokens=200
            )
            
            self.context_manager = self.client.aio.live.connect(
                model="models/gemini-live-2.5-flash-preview",
                config=config
            )
            self.session = await self.context_manager.__aenter__()
            
            await self.session.send_realtime_input(
                activity_start=types.ActivityStart()
            )
            
            logger.info(f"Turn {self.turn_number}: Gemini Live session started with punctuation commands")
            return self
            
        except Exception as e:
            logger.error(f"Turn {self.turn_number}: Failed to start session: {e}")
            raise


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


class RadPairHandlerNoPolish(MagnusOpusHandler):
    """RadPair Beta handler - No polish, accumulative transcript"""

    def __init__(self, websocket):
        """Initialize RadPair handler"""
        # Wrap the FastAPI WebSocket to make it compatible
        wrapped_ws = WebSocketWrapper(websocket)
        super().__init__(wrapped_ws)
        self.original_websocket = websocket
        self.accumulative_transcript = ""  # Store ALL transcripts
        self.is_recording = False
        self.current_turn = None
        self.turn_count = 0
        self.speech_detector = SpeechDetector()
        
        # Still save audio files
        self.audio_file_paths = []
    
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
        german_studies_file = Path(__file__).parent / "German_studies.text"
        
        try:
            if german_studies_file.exists():
                with open(german_studies_file, 'r', encoding='utf-8') as f:
                    study_types = [line.strip() for line in f if line.strip()]
                logger.info(f"Loaded {len(study_types)} German study types from file (placeholder)")
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
        logger.info("RadPair Beta German handler initialized (NO POLISH)")

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
            
            # ADD to accumulative transcript instead of replacing
            if result:
                logger.info(f"Turn {self.turn_count}: Segment completed with transcript: '{result}'")
                # Add a space or newline between segments
                if self.accumulative_transcript:
                    self.accumulative_transcript += " "  # Add space between segments
                self.accumulative_transcript += result
                
                # Send the FULL accumulative transcript to UI
                await self.websocket.send(json.dumps({
                    "type": "accumulative_transcript",
                    "text": self.accumulative_transcript
                }))
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
        # Don't clear accumulative transcript on new recording session
        # User can manually clear if needed
        
        logger.info(f"Starting recording for study type: {self.current_study_type}")
        
        # Send status to UI
        await self.websocket.send(json.dumps({
            "type": "status",
            "message": f"Aufnahme läuft für {self.current_study_type}..."
        }))

    async def stop_recording(self):
        """Stop recording - NO POLISH"""
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
                # Add final segment to accumulative transcript
                if self.accumulative_transcript:
                    self.accumulative_transcript += " "
                self.accumulative_transcript += result
                logger.info(f"Final turn: Segment completed with transcript: '{result}'")
                
                # Send final accumulative transcript
                await self.websocket.send(json.dumps({
                    "type": "accumulative_transcript",
                    "text": self.accumulative_transcript
                }))
            else:
                logger.warning("Final turn: No transcript received")
                
            self.current_turn = None
            self.speech_detector.clear_buffer()
        
        # NO POLISH - Just send completion status
        await self.websocket.send(json.dumps({
            "type": "status",
            "message": "Aufnahme beendet"
        }))
    
    async def clear_transcript(self):
        """Clear the accumulative transcript"""
        self.accumulative_transcript = ""
        logger.info("Accumulative transcript cleared")
        await self.websocket.send(json.dumps({
            "type": "transcript_cleared",
            "text": ""
        }))


# WebSocket server setup - UNCHANGED FROM WORKING VERSION
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI()

# Serve static files
static_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root():
    """Serve the RadPair Beta HTML page"""
    return FileResponse(str(static_dir / "index_radpair_noPolish.html"))


@app.get("/index_radpair_noPolish.html")
async def index():
    """Serve the RadPair Beta HTML page"""
    return FileResponse(str(static_dir / "index_radpair_noPolish.html"))


@app.get("/RADPAIR-LOGO-WHITE.png")
async def logo():
    """Serve the RadPair logo"""
    return FileResponse(str(static_dir / "RADPAIR-LOGO-WHITE.png"))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for RadPair Beta"""
    await websocket.accept()
    handler = RadPairHandlerNoPolish(websocket)
    
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
                    
                    elif data["type"] == "clear_transcript":
                        await handler.clear_transcript()
                    
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
    logger.info("Starting RadPair Beta server (NO POLISH) on http://localhost:8768")
    logger.info("UI available at http://localhost:8768/index_radpair_noPolish.html")
    
    # Create audio recordings directory if it doesn't exist
    audio_dir = Path(__file__).parent / "audio_recordings"
    audio_dir.mkdir(exist_ok=True)
    
    uvicorn.run(app, host="0.0.0.0", port=8768, log_level="info")