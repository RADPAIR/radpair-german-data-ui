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

3. **Deploy Frontend** (Root Directory = `frontend`)
   - In Vercel Dashboard, import the GitHub repo
   - Set "Root Directory" to `frontend`
   - Set Environment Variable: `NEXT_PUBLIC_WS_URL` = your Cloud Run WS URL (e.g., `wss://<service>-<hash>-<region>.a.run.app/ws`)
   - Deploy

## 🖥️ Backend Deployment (Cloud Run)

The backend is containerized with `backend/Dockerfile` and listens on `$PORT`.

### Option A: Cloud Run GitHub Integration (recommended)

1. Push this repo to GitHub.
2. In Google Cloud Console → Cloud Run → Create Service → Deploy from source.
3. Connect your GitHub repo and pick the branch.
4. Repository root: use this repo; Source directory: `backend/`.
5. Build: Dockerfile (auto-detected).
6. Service settings:
   - Allow unauthenticated invocations.
   - Min instances: 0 or 1 as preferred.
7. Environment variables:
   - `GEMINI_API_KEY` (or `GOOGLE_API_KEY`)
   - Optional: `ALLOWED_ORIGINS` (comma-separated, e.g. `https://your-frontend.vercel.app`)
8. Complete setup to enable automatic deploys on push.

After deploy, note the URL: `https://<service>-<hash>-<region>.a.run.app`. Your WebSocket URL is `wss://<...>/ws`.

### Option B: gcloud (manual)

```bash
gcloud run deploy radpair-german-backend \
  --source backend \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your_key
```

Or, using Docker:

```bash
cd backend
docker build -t gcr.io/$GOOGLE_CLOUD_PROJECT/radpair-german-backend:latest .
docker push gcr.io/$GOOGLE_CLOUD_PROJECT/radpair-german-backend:latest
gcloud run deploy radpair-german-backend \
  --image gcr.io/$GOOGLE_CLOUD_PROJECT/radpair-german-backend:latest \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your_key
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

The frontend is a static site in `frontend/` with a serverless function at `frontend/api/config.js`.

- Set in Vercel Project Settings → Environment Variables (for the `frontend` project):
  - `NEXT_PUBLIC_WS_URL` = your Cloud Run WebSocket URL, e.g. `wss://<service>-<hash>-<region>.a.run.app/ws`

The app reads the value at runtime via `/api/config`.

### Backend Configuration

FastAPI includes permissive CORS by default. To restrict, set:

```env
ALLOWED_ORIGINS=https://your-frontend.vercel.app
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
      - name: Deploy to Cloud Run from source
        run: |
          gcloud run deploy radpair-german-backend \
            --source backend \
            --region us-central1 \
            --allow-unauthenticated \
            --set-env-vars GEMINI_API_KEY=${{ secrets.GEMINI_API_KEY }}
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
