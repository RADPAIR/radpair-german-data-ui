// Vercel Serverless Function to expose runtime WebSocket URL to static frontend

function canonicalize(url) {
  if (!url) return null;
  try {
    const u = new URL(url);
    if (u.protocol !== 'ws:' && u.protocol !== 'wss:') {
      // Default to wss for production
      u.protocol = 'wss:';
    }
    if (!u.pathname || u.pathname === '/' || u.pathname === '') {
      u.pathname = '/ws';
    }
    return u.toString();
  } catch {
    const base = String(url).replace(/\/$/, '');
    return base.endsWith('/ws') ? base : `${base}/ws`;
  }
}

module.exports = async function handler(req, res) {
  if (req.method === 'OPTIONS') {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    return res.status(204).end();
  }

  const raw = process.env.NEXT_PUBLIC_WS_URL || process.env.radpair_ws_url || 'ws://localhost:8768/ws';
  const wsUrl = canonicalize(raw);

  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Content-Type', 'application/json');
  return res.status(200).json({ wsUrl });
}
