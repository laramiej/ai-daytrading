# AI Day Trading Dashboard - Frontend

A modern React-based web interface for monitoring and controlling the AI day trading bot.

## Features

- Real-time portfolio monitoring
- Live position tracking with P&L
- Bot start/stop controls
- WebSocket-based real-time updates
- Responsive design with TailwindCSS
- Dark mode interface optimized for trading

## Technology Stack

- **React 18.2** - UI framework
- **Vite** - Build tool and dev server
- **TailwindCSS** - Utility-first CSS framework
- **Axios** - HTTP client for API calls
- **Recharts** - Charting library (ready for future analytics)
- **Hero Icons** - Icon library
- **WebSocket** - Real-time data updates

## Getting Started

### Prerequisites

- Node.js 18 or higher
- npm or yarn
- Backend API running on port 8000

### Installation

1. Install dependencies:
```bash
cd web/frontend
npm install
```

2. Create environment file:
```bash
cp .env.example .env
```

3. Configure environment variables in `.env`:
```
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### Development

Run the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000`

### Building for Production

Build the optimized production bundle:
```bash
npm run build
```

Preview the production build:
```bash
npm run preview
```

## Project Structure

```
src/
├── components/          # React components
│   ├── Dashboard.jsx    # Main dashboard view
│   ├── StatusCard.jsx   # Account status cards
│   ├── PositionsTable.jsx  # Positions table
│   └── ControlPanel.jsx    # Bot control panel
├── hooks/              # Custom React hooks
│   └── useWebSocket.js # WebSocket connection hook
├── utils/              # Utility functions
│   ├── api.js          # API client
│   └── formatters.js   # Data formatting utilities
├── App.jsx             # Root component
├── main.jsx            # Application entry point
└── index.css           # Global styles
```

## Components

### Dashboard
Main view that orchestrates all other components and manages state.

### StatusCard
Displays key metrics like portfolio value, equity, buying power, and open positions.

### PositionsTable
Shows all open positions with entry price, current price, and P&L in both dollars and percentage.

### ControlPanel
Provides bot start/stop controls and displays connection status.

## API Integration

The frontend communicates with the backend via:
- **REST API** - For fetching data and executing commands
- **WebSocket** - For real-time updates (positions, status, events)

### API Endpoints Used

- `GET /api/health` - Health check
- `GET /api/status` - Account status and portfolio overview
- `GET /api/positions` - Open positions
- `GET /api/settings` - Trading configuration
- `POST /api/bot/start` - Start the trading bot
- `POST /api/bot/stop` - Stop the trading bot
- `WS /ws` - WebSocket for real-time updates

## Docker Deployment

The frontend is containerized and deployed with Nginx:

```bash
# Build the Docker image
docker build -t ai-trading-frontend .

# Run the container
docker run -p 3000:80 ai-trading-frontend
```

Or use docker-compose from the root directory:
```bash
docker-compose up -d
```

## Customization

### Styling
TailwindCSS is configured in `tailwind.config.js`. Custom colors for trading:
- `trading-green`: #10b981 (for profits)
- `trading-red`: #ef4444 (for losses)

### Adding Features
1. Create new components in `src/components/`
2. Add API endpoints in `src/utils/api.js`
3. Use formatters from `src/utils/formatters.js` for consistent data display

## Troubleshooting

### Frontend won't connect to backend
- Verify backend is running: `curl http://localhost:8000/api/health`
- Check VITE_API_URL in `.env`
- Check browser console for CORS errors

### WebSocket disconnects
- Check VITE_WS_URL in `.env`
- Verify WebSocket endpoint: `ws://localhost:8000/ws`
- Check browser console for connection errors

### Build errors
- Clear node_modules: `rm -rf node_modules && npm install`
- Clear Vite cache: `rm -rf node_modules/.vite`

## License

Part of the AI Day Trading System
