# Web Interface Quick Start Guide

This guide will help you get the AI Day Trading web interface up and running.

## Prerequisites

1. Python 3.9+ installed
2. Node.js 18+ installed
3. Valid Alpaca API keys in `.env` file
4. All Python dependencies installed

## Quick Start (Development Mode)

### Step 1: Start the Backend API

From the project root directory:

```bash
# Make sure dependencies are installed
pip install -r requirements.txt

# Start the FastAPI backend
uvicorn web.backend.app.main:app --reload
```

The backend will be available at `http://localhost:8000`

Verify it's running:
```bash
curl http://localhost:8000/api/health
```

You should see:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T...",
  "bot_running": false
}
```

### Step 2: Start the Frontend Development Server

In a new terminal, from the project root:

```bash
cd web/frontend

# Install dependencies (first time only)
npm install

# Start the development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Step 3: Access the Dashboard

Open your browser and go to: `http://localhost:3000`

You should see:
- Portfolio value and stats
- Open positions (if any)
- Bot control panel
- Real-time connection status

## Testing the Interface

### 1. Check API Connection

The dashboard should load and display your account information. If you see errors:
- Verify backend is running on port 8000
- Check browser console for errors
- Verify your `.env` file has valid Alpaca API keys

### 2. Test Bot Controls

Click "Start Bot" to start the trading bot. The status indicator should turn green.
Click "Stop Bot" to stop it. The status indicator should turn red.

### 3. Test Real-Time Updates

The WebSocket connection status should show "Connected" (blue indicator).
Positions and account values should update automatically every 10 seconds.

### 4. View Positions

If you have open positions, they'll appear in the positions table with:
- Symbol
- Side (LONG/SHORT)
- Quantity
- Entry price
- Current price
- P&L (profit/loss) in dollars and percentage

## Production Deployment with Docker

### Option 1: Docker Compose (Recommended)

From the project root:

```bash
# Build and start all containers
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all containers
docker-compose down
```

Access the application:
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`

### Option 2: Build Individual Containers

Backend:
```bash
docker build -f Dockerfile.backend -t ai-trading-backend .
docker run -p 8000:8000 --env-file .env ai-trading-backend
```

Frontend:
```bash
cd web/frontend
docker build -t ai-trading-frontend .
docker run -p 3000:80 ai-trading-frontend
```

## Synology NAS Deployment (Portainer)

See `DEPLOYMENT.md` for complete instructions on deploying to Synology NAS using Portainer.

Quick steps:
1. Open Portainer on your Synology NAS
2. Go to Stacks > Add stack
3. Paste the contents of `docker-compose.yml`
4. Add environment variables from `.env`
5. Deploy the stack

## Troubleshooting

### Backend won't start

**Error**: `Trading system not initialized`
- **Fix**: Check your `.env` file has valid `ALPACA_API_KEY` and `ALPACA_SECRET_KEY`

**Error**: `AlpacaBroker.__init__() got an unexpected keyword argument`
- **Fix**: Make sure you have the latest version of the code

### Frontend won't connect to backend

**Error**: Network errors in browser console
- **Fix**: Verify backend is running: `curl http://localhost:8000/api/health`
- **Fix**: Check VITE_API_URL in `web/frontend/.env`

**Error**: CORS errors
- **Fix**: Backend already has CORS configured for localhost:3000

### WebSocket disconnects

**Error**: WebSocket connection failed
- **Fix**: Verify backend WebSocket endpoint: `ws://localhost:8000/ws`
- **Fix**: Check browser console for specific error messages

### Positions not showing

**Issue**: Dashboard shows "No open positions" but you have positions
- **Fix**: Check backend logs for errors
- **Fix**: Test the API directly: `curl http://localhost:8000/api/positions`
- **Fix**: Verify your Alpaca account actually has positions

### Docker build fails

**Error**: `Cannot install alpaca-py and websockets`
- **Fix**: Already resolved - make sure you're using the latest `requirements.txt`

## File Structure

```
ai_daytrading/
├── web/
│   ├── backend/
│   │   └── app/
│   │       └── main.py          # FastAPI application
│   └── frontend/
│       ├── src/
│       │   ├── components/      # React components
│       │   ├── hooks/           # Custom hooks
│       │   └── utils/           # API client, formatters
│       ├── package.json
│       ├── vite.config.js
│       └── Dockerfile
├── docker-compose.yml           # Multi-container setup
├── Dockerfile.backend           # Backend container
└── requirements.txt             # Python dependencies
```

## API Endpoints Reference

### Status & Monitoring
- `GET /api/health` - Health check
- `GET /api/status` - Account status and portfolio overview
- `GET /api/positions` - All open positions with P&L

### Bot Control
- `POST /api/bot/start` - Start the trading bot
- `POST /api/bot/stop` - Stop the trading bot

### Configuration
- `GET /api/settings` - Get current settings
- `PUT /api/settings` - Update settings (future feature)

### Real-Time
- `WS /ws` - WebSocket for real-time updates

## Next Steps

1. **Test in development mode** first to ensure everything works
2. **Build Docker containers** for production deployment
3. **Deploy to Synology NAS** using Portainer (see DEPLOYMENT.md)
4. **Monitor logs** to ensure the bot is working correctly
5. **Set up alerts** for important events (future feature)

## Support

For issues or questions:
1. Check the logs: `docker-compose logs` or browser console
2. Verify API keys are valid
3. Test API endpoints directly with curl
4. Review `DEPLOYMENT.md` for deployment-specific issues

## Safety Reminders

- Always use paper trading (`ALPACA_PAPER_TRADING=true`) for testing
- Set appropriate risk limits in `.env`
- Monitor the bot regularly
- Never share your API keys
- Keep your `.env` file secure and never commit it to git
