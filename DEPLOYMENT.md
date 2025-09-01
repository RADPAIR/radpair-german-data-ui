# RADPAIR German UI - Deployment Guide

## 🚀 Quick Deploy to Vercel

### One-Click Deploy
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/RADPAIR/radpair-german-data-ui)

### Manual Deploy Steps

1. **Fork/Clone Repository**
   ```bash
   git clone https://github.com/RADPAIR/radpair-german-data-ui.git
   cd radpair-german-data-ui
   ```

2. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

3. **Deploy Frontend**
   ```bash
   vercel
   ```

4. **Set Environment Variables in Vercel Dashboard**
   - `NEXT_PUBLIC_WS_URL`: Your backend WebSocket URL (e.g., `wss://radpair-backend.herokuapp.com/ws`)

## 🖥️ Backend Deployment

### Option 1: Heroku

1. **Create Heroku App**
   ```bash
   cd backend
   heroku create radpair-backend-german
   ```

2. **Create Procfile**
   ```bash
   echo "web: uvicorn server_radpair:app --host 0.0.0.0 --port \$PORT" > Procfile
   ```

3. **Set Environment Variables**
   ```bash
   heroku config:set GEMINI_API_KEY=your_key_here
   ```

4. **Deploy**
   ```bash
   git add .
   git commit -m "Deploy RADPAIR backend"
   git push heroku main
   ```

### Option 2: Railway.app

1. **Create railway.json**
   ```json
   {
     "build": {
       "builder": "NIXPACKS"
     },
     "deploy": {
       "startCommand": "cd backend && uvicorn server_radpair:app --host 0.0.0.0 --port $PORT"
     }
   }
   ```

2. **Deploy via Railway CLI**
   ```bash
   railway login
   railway init
   railway up
   railway env set GEMINI_API_KEY=your_key_here
   ```

### Option 3: Docker

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   
   COPY backend/requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY backend/ .
   COPY data/ ./data/
   
   EXPOSE 8768
   
   CMD ["uvicorn", "server_radpair:app", "--host", "0.0.0.0", "--port", "8768"]
   ```

2. **Build and Run**
   ```bash
   docker build -t radpair-german .
   docker run -p 8768:8768 -e GEMINI_API_KEY=your_key radpair-german
   ```

## 📝 GitHub Setup

### Create Repository

1. **Initialize Local Repo**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: RADPAIR German Medical Transcription UI"
   ```

2. **Create GitHub Repository**
   - Go to https://github.com/RADPAIR
   - Click "New repository"
   - Name: `radpair-german-data-ui`
   - Private/Public as needed

3. **Push to GitHub**
   ```bash
   git remote add origin https://github.com/RADPAIR/radpair-german-data-ui.git
   git branch -M main
   git push -u origin main
   ```

### Branch Structure

```bash
# Main branch (production)
main

# Development branch
git checkout -b develop

# Feature branches
git checkout -b feature/german-macros
git checkout -b feature/radpair-api-integration
```

## 🔧 Configuration

### Frontend Configuration

Update `frontend/app.js`:
```javascript
// For production
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'wss://radpair-backend.herokuapp.com/ws';
```

### Backend Configuration

Update WebSocket CORS in `backend/server_radpair.py`:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://radpair-german.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🔄 CI/CD with GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy RADPAIR German UI

on:
  push:
    branches: [main]

jobs:
  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}

  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: akhileshns/heroku-deploy@v3.12.12
        with:
          heroku_api_key: ${{ secrets.HEROKU_API_KEY }}
          heroku_app_name: "radpair-backend-german"
          heroku_email: ${{ secrets.HEROKU_EMAIL }}
          appdir: "backend"
```

## 🔐 Security Setup

### Required Secrets

**GitHub Secrets:**
- `VERCEL_TOKEN`
- `VERCEL_PROJECT_ID`
- `VERCEL_ORG_ID`
- `HEROKU_API_KEY`
- `HEROKU_EMAIL`

**Production Environment:**
- `GEMINI_API_KEY`
- `RADPAIR_API_KEY` (future)

### SSL/TLS

- Frontend: Automatic via Vercel
- Backend: Use Heroku SSL or Cloudflare

## 📊 Monitoring

### Vercel Analytics
- Enable in Vercel dashboard
- Track page views and performance

### Backend Logging
- Heroku: `heroku logs --tail`
- Railway: `railway logs`

## 🚨 Troubleshooting

### WebSocket Connection Issues
- Check CORS settings
- Verify WSS certificate
- Test with: `wscat -c wss://your-backend/ws`

### Audio Not Working
- Check browser permissions
- Verify HTTPS/WSS (required for getUserMedia)

### German Text Issues
- Verify model: `gemini-2.5-flash-lite`
- Check language parameter: `de-DE`

## 📱 Mobile Support

The UI is responsive and works on mobile devices with:
- Chrome for Android
- Safari for iOS (15+)

## 🔄 Updates

### Deploy Updates
```bash
# Frontend
vercel --prod

# Backend (Heroku)
git push heroku main
```

### Rollback
```bash
# Vercel
vercel rollback

# Heroku
heroku rollback
```

## 📞 Support

Issues: https://github.com/RADPAIR/radpair-german-data-ui/issues
Email: support@radpair.com

---

**IMPORTANT**: Remember to update placeholder APIs with actual RADPAIR endpoints when available!