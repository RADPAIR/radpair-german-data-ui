#!/bin/bash
# RADPAIR German UI - Deployment Script

echo "🚀 RADPAIR German Medical Transcription UI - Deployment Script"
echo "============================================================"

# Check if git is initialized
if [ ! -d .git ]; then
    echo "📦 Initializing git repository..."
    git init
fi

# Add all files
echo "📝 Adding files to git..."
git add .

# Commit
echo "💾 Creating commit..."
git commit -m "feat: RADPAIR German Medical Transcription UI - Production Ready

- Real-time German transcription with Gemini Live
- Polish processing with Gemini Flash Lite
- 287 German medical study types (placeholder)
- Dark mode UI with RADPAIR branding
- WebSocket communication
- Audio archival (WAV format)
- Vercel-ready frontend
- FastAPI backend

TODO: Integrate with RADPAIR backend APIs for study types and macros"

# Check if remote exists
if ! git remote | grep -q origin; then
    echo "🔗 Adding GitHub remote..."
    echo "Please enter the GitHub repository URL:"
    echo "Example: https://github.com/RADPAIR/radpair-german-data-ui.git"
    read -r REPO_URL
    git remote add origin "$REPO_URL"
fi

# Create main branch
git branch -M main

# Push to GitHub
echo "📤 Pushing to GitHub..."
echo "This will push to the 'main' branch."
echo "Press Enter to continue or Ctrl+C to cancel..."
read -r

git push -u origin main

echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Go to Vercel: https://vercel.com/new"
echo "2. Import your GitHub repository"
echo "3. Set environment variable: NEXT_PUBLIC_WS_URL"
echo "4. Deploy!"
echo ""
echo "For backend deployment, see DEPLOYMENT.md"