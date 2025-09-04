// RADPAIR German Medical Transcription - Frontend Logic (v2 No Polish)
// Resolves WebSocket URL at runtime via /api/config or window var

let ws = null;
let audioContext = null;
let source = null;
let processor = null;
let isRecording = false;
let stream = null;

// Resolve WebSocket URL via API (runtime)
let WS_URL = null;

async function resolveWsUrl() {
  try {
    const resp = await fetch('/api/config');
    if (resp.ok) {
      const data = await resp.json();
      if (data && data.wsUrl) {
        WS_URL = data.wsUrl;
      }
    }
  } catch (e) {
    console.warn('Could not resolve /api/config, will use fallback');
  }
  if (!WS_URL && typeof window !== 'undefined' && window.location) {
    const isHttps = window.location.protocol === 'https:';
    WS_URL = `${isHttps ? 'wss' : 'ws'}://${window.location.host}/ws`;
  }
}

// DOM elements
const recordBtn = document.getElementById('recordBtn');
const clearBtn = document.getElementById('clearBtn');
const copyTranscriptBtn = document.getElementById('copyTranscriptBtn');
const copyIcon = document.getElementById('copyIcon');
const copyText = document.getElementById('copyText');
const transcript = document.getElementById('transcript');
const status = document.getElementById('status');
const studyTypeSelect = document.getElementById('studyType');
const connectionDot = document.getElementById('connectionDot');
const connectionStatus = document.getElementById('connectionStatus');
const transcriptStatus = document.getElementById('transcriptStatus');
const recordText = document.getElementById('recordText');
const recordIcon = document.getElementById('recordIcon');
const timestamp = document.getElementById('timestamp');

// Update timestamp
function updateTimestamp() {
  const now = new Date();
  timestamp.textContent = now.toLocaleTimeString('de-DE');
}
setInterval(updateTimestamp, 1000);
updateTimestamp();

// Copy transcript function
async function copyTranscript() {
  const text = transcript.textContent;

  // Don't copy if empty
  if (text === 'Noch kein Transkript vorhanden...' || !text) {
    return;
  }

  try {
    await navigator.clipboard.writeText(text);

    // Visual feedback
    copyTranscriptBtn.classList.add('copied');
    copyIcon.textContent = '✅';
    copyText.textContent = 'Kopiert!';

    // Reset after 2 seconds
    setTimeout(() => {
      copyTranscriptBtn.classList.remove('copied');
      copyIcon.textContent = '📋';
      copyText.textContent = 'Kopieren';
    }, 2000);
  } catch (err) {
    console.error('Failed to copy:', err);
    copyIcon.textContent = '❌';
    copyText.textContent = 'Fehler';
    setTimeout(() => {
      copyIcon.textContent = '📋';
      copyText.textContent = 'Kopieren';
    }, 2000);
  }
}

// WebSocket connection
function connectWebSocket() {
  const envWsUrl = (typeof window !== 'undefined' && window.NEXT_PUBLIC_WS_URL)
    || (typeof process !== 'undefined' && process.env && process.env.NEXT_PUBLIC_WS_URL);
  const wsUrl = envWsUrl || WS_URL || 'ws://localhost:8768/ws';
  try {
    ws = new WebSocket(wsUrl);
  } catch (e) {
    console.error('Failed to create WebSocket with URL:', wsUrl, e);
    throw e;
  }

  ws.onopen = () => {
    console.log('WebSocket connected');
    connectionDot.classList.add('connected');
    connectionStatus.textContent = 'Verbunden';
    status.textContent = 'Verbunden mit Server';
    status.className = 'ready';
    recordBtn.disabled = false;

    // Request study types
    ws.send(JSON.stringify({ type: 'get_study_types' }));
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received message:', data);

    switch (data.type) {
      case 'study_types':
        populateStudyTypes(data.study_types);
        break;

      case 'partial_transcript':
        // Show live transcript (partial during speech)
        if (data.text) {
          transcript.textContent = data.text;
          transcript.className = '';
        }
        transcriptStatus.textContent = 'Live-Transkription';
        break;

      case 'final_transcript':
        // Show final transcript for this turn (with macros expanded)
        if (data.text) {
          transcript.textContent = data.text;
          transcript.className = '';
        }
        break;

      case 'accumulative_transcript':
        // Show the accumulative transcript (all turns combined)
        if (data.text) {
          transcript.textContent = data.text;
          transcript.className = '';
        } else {
          transcript.textContent = 'Noch kein Transkript vorhanden...';
          transcript.className = 'empty';
        }
        transcriptStatus.textContent = 'Transkript aktualisiert';
        break;

      case 'transcript_cleared':
        transcript.textContent = 'Noch kein Transkript vorhanden...';
        transcript.className = 'empty';
        transcriptStatus.textContent = 'Gelöscht';
        break;

      case 'status':
        status.textContent = data.message;
        if (data.message.includes('Aufnahme läuft')) {
          status.className = 'recording';
        } else if (data.message.includes('beendet')) {
          status.className = 'ready';
          transcriptStatus.textContent = 'Bereit';
        } else {
          status.className = 'ready';
        }
        break;

      case 'error':
        console.error('Server error:', data.message);
        status.textContent = `Fehler: ${data.message}`;
        status.className = 'ready';
        break;
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    connectionDot.classList.remove('connected');
    connectionStatus.textContent = 'Fehler';
    status.textContent = 'Verbindungsfehler';
    status.className = 'ready';
  };

  ws.onclose = () => {
    console.log('WebSocket disconnected');
    connectionDot.classList.remove('connected');
    connectionStatus.textContent = 'Getrennt';
    status.textContent = 'Verbindung getrennt - Neuverbindung in 3 Sekunden...';
    status.className = 'ready';
    recordBtn.disabled = true;

    // Reconnect after 3 seconds
    setTimeout(connectWebSocket, 3000);
  };
}

function populateStudyTypes(studyTypes) {
  studyTypeSelect.innerHTML = '<option value="">Studientyp auswählen...</option>';
  studyTypes.forEach(type => {
    const option = document.createElement('option');
    option.value = type;
    option.textContent = type;
    studyTypeSelect.appendChild(option);
  });

  // Set default if available
  if (studyTypes.includes('CT Thorax')) {
    studyTypeSelect.value = 'CT Thorax';
  } else if (studyTypes.length > 0) {
    studyTypeSelect.value = studyTypes[0];
  }
}

// Audio recording functions
async function startRecording() {
  try {
    const studyType = studyTypeSelect.value || 'CT Thorax';

    // Send start message
    ws.send(JSON.stringify({
      type: 'start_recording',
      study_type: studyType
    }));

    // Get user media
    stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        sampleRate: 16000,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      }
    });

    // Create audio context with 16kHz sample rate
    audioContext = new AudioContext({ sampleRate: 16000 });
    source = audioContext.createMediaStreamSource(stream);
    processor = audioContext.createScriptProcessor(4096, 1, 1);

    processor.onaudioprocess = (e) => {
      if (!isRecording) return;

      const inputData = e.inputBuffer.getChannelData(0);

      // Convert Float32 to Int16
      const pcm16 = new Int16Array(inputData.length);
      for (let i = 0; i < inputData.length; i++) {
        const s = Math.max(-1, Math.min(1, inputData[i]));
        pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
      }

      // Send as binary
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(pcm16.buffer);
      }
    };

    source.connect(processor);
    processor.connect(audioContext.destination);

    isRecording = true;
    recordBtn.classList.add('recording');
    recordText.textContent = 'Aufnahme stoppen';
    recordIcon.textContent = '⏹️';
    status.textContent = `Aufnahme läuft für ${studyType}...`;
    status.className = 'recording';
    transcriptStatus.textContent = 'Aufnahme...';

    // Don't clear transcript in v2 - keep accumulative

  } catch (error) {
    console.error('Error starting recording:', error);
    status.textContent = `Fehler: ${error.message}`;
    status.className = 'ready';
  }
}

function stopRecording() {
  isRecording = false;
  recordBtn.classList.remove('recording');
  recordText.textContent = 'Aufnahme starten';
  recordIcon.textContent = '🎤';
  status.textContent = 'Aufnahme beendet';
  status.className = 'ready';

  // Stop audio processing
  if (processor) {
    processor.disconnect();
    processor = null;
  }
  if (source) {
    source.disconnect();
    source = null;
  }
  if (audioContext) {
    audioContext.close();
    audioContext = null;
  }
  if (stream) {
    stream.getTracks().forEach(track => track.stop());
    stream = null;
  }

  // Send stop message
  ws.send(JSON.stringify({ type: 'stop_recording' }));
}

// Event listeners
recordBtn.addEventListener('click', () => {
  if (isRecording) {
    stopRecording();
  } else {
    startRecording();
  }
});

clearBtn.addEventListener('click', () => {
  // Send clear message to server
  ws.send(JSON.stringify({ type: 'clear_transcript' }));
  status.textContent = 'Transkript gelöscht';
  status.className = 'ready';

  setTimeout(() => {
    status.textContent = 'System bereit';
  }, 2000);
});

copyTranscriptBtn.addEventListener('click', copyTranscript);

// Initialize after resolving WS URL
(async () => {
  await resolveWsUrl();
  connectWebSocket();
})();

