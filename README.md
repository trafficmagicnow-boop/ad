# Adw/Skro Integration

Backend for creating Adw tracking links with Skro S2S integration.

## Features
- Automated link creation with Skro postback
- Auto-sync stats from Adw to Skro every 5 minutes  
- Web dashboard for buyers
- No external dependencies (Python stdlib only)

## Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template)

Or manually:
1. Fork this repo
2. Connect to Railway
3. Deploy automatically

## Local Development

```bash
python server.py
# Visit http://localhost:8000
```

## Configuration

API tokens are hardcoded in `server.py`:
- Adw token: Line 15
- Skro endpoint: Line 163

Replace these with your credentials before deploying.
