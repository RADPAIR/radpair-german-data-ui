# RADPAIR German Medical Transcription UI

Real-time German medical transcription with AI-powered polish processing.

![RADPAIR Logo](public/RADPAIR-LOGO-WHITE.png)

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ (for Vercel deployment)
- Python 3.8+ (for backend server)
- Gemini API key

### Frontend Deployment (Vercel)

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/RADPAIR/radpair-german-data-ui)

Monorepo-friendly via `vercel.json` at repo root.

1. Import the repo into Vercel.
2. In Project Settings → Environment Variables, set `radpair_ws_url` to your Cloud Run WS URL (e.g., `wss://<service>-<hash>-<region>.a.run.app/ws`).
3. Deploy. The static site uses `/api/config` to read the URL at runtime.

### Backend Setup

```bash
# Clone repository
git clone https://github.com/RADPAIR/radpair-german-data-ui.git
cd radpair-german-data-ui/backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Run server
python server_radpair.py
```

## 🎯 Features

- ✅ **Real-time German transcription** with Gemini Live
- ✅ **Intelligent polish processing** with Gemini Flash Lite
- ✅ **287 German medical study types** (placeholder - integrate with RADPAIR API)
- ✅ **Medical macro expansion** (placeholder - awaiting German macros)
- ✅ **Audio archival** - WAV format per turn
- ✅ **Dark mode UI** with RADPAIR branding
- ✅ **WebSocket communication** for low latency

## 📁 Project Structure

```
radpair-german-data-ui/
├── frontend/                # Vercel-deployable frontend
│   ├── index.html          # Main UI (dark mode)
│   ├── app.js             # Frontend logic
│   └── styles.css         # Styles with Comfortaa font
├── backend/               # Python backend server
│   ├── server_radpair.py  # FastAPI WebSocket server
│   ├── requirements.txt   # Python dependencies
│   └── src/              # Core components
│       └── core_components_audio_german.py
├── public/               # Static assets
│   └── RADPAIR-LOGO-WHITE.png
├── data/                 # Placeholder data
│   ├── German_studies.text  # 287 study types (PLACEHOLDER)
│   ├── macros.csv          # English macros (PLACEHOLDER)
│   └── macros_german.csv   # German macros (TODO)
├── vercel.json          # Vercel configuration
├── package.json         # Node dependencies
└── .env.example        # Environment template
```

## 🔌 Integration Points

### Study Types API (PLACEHOLDER)
Currently loads from `German_studies.text`. Replace with RADPAIR API:

```python
# backend/server_radpair.py - Line 67-76
def load_study_types(self):
    # TODO: Replace with RADPAIR API
    # response = requests.get('https://api.radpair.com/v1/study-types/de')
    # return response.json()['study_types']
```

### German Macros (PLACEHOLDER)
Currently uses English macros. Add German medical macros:

```csv
# data/macros_german.csv (TODO: Create this file)
phrase,expanded_text
appendix,Die Appendix zeigt keine Entzündungszeichen.
nieren,Die Nieren sind normal groß und zeigen normale Echogenität.
```

## 🚀 Deployment

### Frontend (Vercel)

1. Fork this repository
2. Import to Vercel
3. Set environment variables:
   ```
   NEXT_PUBLIC_WS_URL=wss://your-backend.herokuapp.com/ws
   ```
4. Deploy!

### Backend (Cloud Run)

The backend has a Dockerfile at `backend/Dockerfile` and serves on `$PORT`.

Quick deploy with gcloud:

```bash
gcloud run deploy radpair-german-backend \
  --source backend \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your_key
```

## 🔧 Configuration

### Environment Variables

**Frontend (.env.local)**:
```env
# Not used at build; set in Vercel Project settings as radpair_ws_url
```

**Backend (.env)**:
```env
GEMINI_API_KEY=your_gemini_api_key_here
# Optional
SERVER_PORT=8080
ALLOWED_ORIGINS=https://your-frontend.vercel.app
```

## 🧪 Testing

### Local Development
```bash
# Terminal 1: Backend
cd backend
python server_radpair.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

Visit: http://localhost:3000

### Test Checklist
- [ ] WebSocket connects
- [ ] Study types load
- [ ] German transcription works
- [ ] Polish completes < 2 seconds
- [ ] Audio files saved
- [ ] UI responsive

## 📊 Performance

- **Transcription**: Real-time with Gemini Live
- **Polish**: < 2 seconds with Gemini Flash Lite
- **Audio**: 16kHz, 16-bit, mono PCM
- **WebSocket**: Low latency communication

## 🔒 Security

- API keys stored in environment variables
- WebSocket authentication (TODO)
- HTTPS/WSS in production
- No sensitive data in repository

## 📝 License

Proprietary - RADPAIR © 2025

## 🤝 Contributing

Please contact the RADPAIR team before contributing.

## 📧 Support

For issues or questions: support@radpair.com

---

**Note**: This is a beta version. Study types and macros are placeholders pending integration with RADPAIR backend services.
