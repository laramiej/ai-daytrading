"""
FastAPI Web Application for AI Day Trading System
Provides REST API and WebSocket endpoints for the web interface
"""
import sys
import os
from pathlib import Path

# Add parent directory to path to import trading system modules
project_root = str(Path(__file__).parent.parent.parent.parent)
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

from src.utils import load_settings
from src.broker import AlpacaBroker

# Import DayTradingBot components
from llm import LLMFactory
from strategy import MarketAnalyzer, TradingStrategy
from strategy.portfolio_context import PortfolioContext
from risk import RiskManager, RiskLimits

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Day Trading System",
    description="Real-time dashboard and control panel for AI-powered day trading",
    version="1.0.0"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
class TradingState:
    """Manages the trading bot state"""
    def __init__(self):
        self.bot_running = False
        self.bot_task = None
        self.settings = None
        self.broker = None
        self.trading_bot = None
        self.websocket_clients: List[WebSocket] = []

    async def initialize(self):
        """Initialize trading system components"""
        try:
            self.settings = load_settings()
            self.broker = AlpacaBroker(
                api_key=self.settings.alpaca_api_key,
                secret_key=self.settings.alpaca_secret_key,
                paper_trading=self.settings.alpaca_paper_trading
            )

            # Initialize the full trading bot components
            self._initialize_trading_bot()

            logger.info("Trading system initialized")
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            raise

    def _initialize_trading_bot(self):
        """Initialize the trading bot with all components"""
        logger.info("Initializing AI Day Trading Bot...")

        # Initialize LLM provider
        provider_name = self.settings.default_llm_provider
        is_valid, error_msg = self.settings.validate_llm_config(provider_name)
        if not is_valid:
            raise Exception(f"LLM configuration error: {error_msg}")

        api_key = self.settings.get_llm_api_key(provider_name)
        llm_provider = LLMFactory.create_provider(provider_name, api_key)
        logger.info(f"Using LLM provider: {provider_name}")

        # Initialize market analyzer
        market_analyzer = MarketAnalyzer(
            self.broker,
            include_sentiment=True,
            enable_google_trends=self.settings.enable_google_trends,
            finnhub_api_key=self.settings.finnhub_api_key,
            enable_finnhub=self.settings.enable_finnhub
        )

        # Initialize risk manager
        risk_manager = RiskManager(
            broker=self.broker,
            limits=RiskLimits(
                max_position_size=self.settings.max_position_size,
                max_daily_loss=self.settings.max_daily_loss,
                max_total_exposure=self.settings.max_total_exposure,
                stop_loss_percentage=self.settings.stop_loss_percentage,
                take_profit_percentage=self.settings.take_profit_percentage,
                max_open_positions=self.settings.max_open_positions,
                enable_short_selling=self.settings.enable_short_selling
            )
        )

        # Initialize portfolio context
        portfolio = PortfolioContext(self.broker, risk_manager)

        # Initialize trading strategy
        strategy = TradingStrategy(llm_provider, market_analyzer, portfolio)

        # Store components in a simple object
        class SimpleTradingBot:
            def __init__(self, broker, strategy, risk_manager, settings):
                self.broker = broker
                self.strategy = strategy
                self.risk_manager = risk_manager
                self.settings = settings
                self.portfolio = portfolio

            def scan_opportunities(self, min_confidence=70.0):
                """Scan watchlist for trading opportunities"""
                if not self.broker.is_market_open():
                    logger.warning("Market is closed - skipping scan")
                    return []

                watchlist = self.settings.get_watchlist()
                logger.info(f"Analyzing {len(watchlist)} symbols...")

                signals = self.strategy.analyze_watchlist(
                    symbols=watchlist,
                    min_confidence=min_confidence
                )

                if signals:
                    logger.info(f"Found {len(signals)} trading signals")
                else:
                    logger.info("No high-confidence signals found")

                return signals

            def execute_signal(self, signal):
                """Execute a trading signal"""
                logger.info(f"Processing signal: {signal.signal} {signal.symbol}")

                try:
                    quote = self.broker.get_latest_quote(signal.symbol)
                    current_price = (quote["bid_price"] + quote["ask_price"]) / 2

                    # Calculate position size
                    if signal.entry_price and signal.stop_loss:
                        quantity, sizing_explanation = self.risk_manager.calculate_position_size(
                            symbol=signal.symbol,
                            entry_price=signal.entry_price,
                            stop_loss_price=signal.stop_loss
                        )
                    else:
                        quantity = self.settings.max_position_size / current_price
                        quantity = round(quantity, 0)

                    if quantity == 0:
                        logger.warning("Calculated quantity is 0 - skipping trade")
                        return False

                    # Evaluate risk
                    side = "buy" if signal.signal == "BUY" else "sell"
                    risk_decision = self.risk_manager.evaluate_trade(
                        symbol=signal.symbol,
                        side=side,
                        quantity=quantity,
                        estimated_price=current_price
                    )

                    if not risk_decision.approved:
                        logger.warning(f"Trade blocked by risk manager: {risk_decision.reason}")
                        return False

                    final_quantity = risk_decision.recommended_quantity or quantity

                    # Place order
                    order = self.broker.place_market_order(
                        symbol=signal.symbol,
                        quantity=final_quantity,
                        side=side
                    )

                    # Record trade
                    self.portfolio.record_trade(
                        symbol=signal.symbol,
                        side=side,
                        quantity=final_quantity,
                        price=current_price,
                        signal_confidence=signal.confidence,
                        llm_provider=signal.llm_provider
                    )

                    logger.info(f"Order placed successfully! Order ID: {order.order_id}")
                    return True

                except Exception as e:
                    logger.error(f"Error executing signal: {e}")
                    return False

        self.trading_bot = SimpleTradingBot(self.broker, strategy, risk_manager, self.settings)

state = TradingState()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)

manager = ConnectionManager()

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the trading system on startup"""
    try:
        await state.initialize()
        logger.info("FastAPI application started")
    except Exception as e:
        logger.error(f"Startup failed: {e}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if state.bot_task and not state.bot_task.done():
        state.bot_task.cancel()
    logger.info("FastAPI application shutdown")

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "bot_running": state.bot_running
    }

# Get trading status
@app.get("/api/status")
async def get_status():
    """Get current trading system status"""
    if state.broker is None:
        raise HTTPException(status_code=503, detail="Trading system not initialized. Check your .env file for valid Alpaca API keys.")

    try:
        account = state.broker.get_account_info()
        positions = state.broker.get_positions()

        return {
            "bot_running": state.bot_running,
            "account": {
                "equity": account["equity"],
                "cash": account["cash"],
                "buying_power": account["buying_power"],
                "portfolio_value": account["portfolio_value"],
                "day_profit_loss": account["equity"] - account["last_equity"],
                "day_profit_loss_percent": ((account["equity"] - account["last_equity"]) / account["last_equity"] * 100) if account["last_equity"] > 0 else 0
            },
            "positions_count": len(positions),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get positions
@app.get("/api/positions")
async def get_positions():
    """Get all current positions"""
    if state.broker is None:
        raise HTTPException(status_code=503, detail="Trading system not initialized. Check your .env file for valid Alpaca API keys.")

    try:
        positions = state.broker.get_positions()
        return {
            "positions": [
                {
                    "symbol": pos.symbol,
                    "quantity": pos.quantity,
                    "side": pos.side,
                    "entry_price": pos.entry_price,
                    "current_price": pos.current_price,
                    "pnl": pos.pnl,
                    "pnl_percent": pos.pnl_percent
                }
                for pos in positions
            ],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get settings
@app.get("/api/settings")
async def get_settings():
    """Get current trading settings"""
    return {
        "max_position_size": state.settings.max_position_size,
        "max_daily_loss": state.settings.max_daily_loss,
        "max_total_exposure": state.settings.max_total_exposure,
        "stop_loss_percentage": state.settings.stop_loss_percentage,
        "take_profit_percentage": state.settings.take_profit_percentage,
        "max_open_positions": state.settings.max_open_positions,
        "enable_short_selling": state.settings.enable_short_selling,
        "enable_auto_trading": state.settings.enable_auto_trading,
        "default_llm_provider": state.settings.default_llm_provider,
        "watchlist": state.settings.get_watchlist(),
        # Include API keys (masked for security)
        "alpaca_api_key": "***" + state.settings.alpaca_api_key[-4:] if state.settings.alpaca_api_key else "",
        "alpaca_secret_key": "***" + state.settings.alpaca_secret_key[-4:] if state.settings.alpaca_secret_key else "",
        "anthropic_api_key": "***" + state.settings.anthropic_api_key[-4:] if state.settings.anthropic_api_key else "",
        "openai_api_key": "***" + state.settings.openai_api_key[-4:] if state.settings.openai_api_key else "",
        "finnhub_api_key": "***" + state.settings.finnhub_api_key[-4:] if state.settings.finnhub_api_key else "",
    }

# Update settings
@app.put("/api/settings")
async def update_settings(updated_settings: dict):
    """Update trading settings and save to .env file"""
    try:
        import os
        from pathlib import Path

        # Path to .env file
        env_path = Path(__file__).parent.parent.parent.parent / '.env'

        if not env_path.exists():
            raise HTTPException(status_code=404, detail=".env file not found")

        # Read current .env file
        with open(env_path, 'r') as f:
            lines = f.readlines()

        # Update values
        updated_lines = []
        keys_updated = set()

        for line in lines:
            if '=' in line and not line.strip().startswith('#'):
                key = line.split('=')[0].strip()

                # Map frontend keys to env keys
                env_key_map = {
                    'max_position_size': 'MAX_POSITION_SIZE',
                    'max_daily_loss': 'MAX_DAILY_LOSS',
                    'max_total_exposure': 'MAX_TOTAL_EXPOSURE',
                    'stop_loss_percentage': 'STOP_LOSS_PERCENTAGE',
                    'take_profit_percentage': 'TAKE_PROFIT_PERCENTAGE',
                    'max_open_positions': 'MAX_OPEN_POSITIONS',
                    'enable_short_selling': 'ENABLE_SHORT_SELLING',
                    'enable_auto_trading': 'ENABLE_AUTO_TRADING',
                    'default_llm_provider': 'DEFAULT_LLM_PROVIDER',
                    'alpaca_api_key': 'ALPACA_API_KEY',
                    'alpaca_secret_key': 'ALPACA_SECRET_KEY',
                    'anthropic_api_key': 'ANTHROPIC_API_KEY',
                    'openai_api_key': 'OPENAI_API_KEY',
                    'finnhub_api_key': 'FINNHUB_API_KEY',
                    'watchlist': 'WATCHLIST',
                }

                # Check if this key should be updated
                for frontend_key, env_key in env_key_map.items():
                    if key == env_key and frontend_key in updated_settings:
                        value = updated_settings[frontend_key]

                        # Skip if value is masked (unchanged API keys)
                        if isinstance(value, str) and value.startswith('***'):
                            updated_lines.append(line)
                            keys_updated.add(frontend_key)
                            break

                        # Handle different value types
                        if isinstance(value, bool):
                            updated_lines.append(f"{key}={str(value).lower()}\n")
                        elif isinstance(value, list):
                            updated_lines.append(f"{key}={','.join(value)}\n")
                        else:
                            updated_lines.append(f"{key}={value}\n")

                        keys_updated.add(frontend_key)
                        break
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)

        # Write updated .env file
        with open(env_path, 'w') as f:
            f.writelines(updated_lines)

        logger.info(f"Settings updated: {', '.join(keys_updated)}")

        # Reload settings (note: bot needs restart for full effect)
        state.settings = load_settings()

        return {
            "status": "success",
            "message": "Settings saved successfully. Restart the bot for changes to take full effect.",
            "updated_keys": list(keys_updated)
        }

    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task for running the trading bot
async def run_trading_bot_loop(scan_interval: int = 300, min_confidence: float = 70.0):
    """
    Run the trading bot in a background loop

    Args:
        scan_interval: Seconds between scans (default 300 = 5 minutes)
        min_confidence: Minimum confidence threshold
    """
    logger.info(f"Starting trading bot loop (scan interval: {scan_interval}s, min confidence: {min_confidence}%)")

    try:
        while state.bot_running:
            # Check if market is open
            if not state.trading_bot.broker.is_market_open():
                logger.info("Market is closed - waiting 60 seconds before checking again")
                await manager.broadcast({
                    "type": "market_closed",
                    "message": "Market is closed - waiting for market to open",
                    "timestamp": datetime.now().isoformat()
                })
                await asyncio.sleep(60)
                continue

            # Run a single scan
            logger.info("Running market scan...")
            await manager.broadcast({
                "type": "scan_started",
                "message": f"Scanning {len(state.settings.get_watchlist())} symbols for opportunities",
                "timestamp": datetime.now().isoformat()
            })

            try:
                # Scan for opportunities
                signals = state.trading_bot.scan_opportunities(min_confidence)

                # Broadcast signals to WebSocket clients
                if signals:
                    await manager.broadcast({
                        "type": "trading_signals",
                        "count": len(signals),
                        "signals": [
                            {
                                "symbol": s.symbol,
                                "signal": s.signal,
                                "confidence": s.confidence,
                                "reasoning": s.reasoning[:200] + "..." if len(s.reasoning) > 200 else s.reasoning
                            }
                            for s in signals
                        ],
                        "timestamp": datetime.now().isoformat()
                    })

                    # If auto-trading is enabled, execute the highest confidence signal
                    if state.settings.enable_auto_trading and signals:
                        logger.info(f"Auto-trading enabled - executing top signal: {signals[0].symbol}")
                        success = state.trading_bot.execute_signal(signals[0])

                        # Broadcast trade execution result
                        await manager.broadcast({
                            "type": "trade_executed",
                            "success": success,
                            "symbol": signals[0].symbol,
                            "signal": signals[0].signal,
                            "timestamp": datetime.now().isoformat()
                        })
                else:
                    logger.info("No trading signals found in this scan")
                    await manager.broadcast({
                        "type": "scan_complete",
                        "message": "Scan complete - no high-confidence signals found",
                        "timestamp": datetime.now().isoformat()
                    })

            except Exception as e:
                logger.error(f"Error during market scan: {e}")
                await manager.broadcast({
                    "type": "error",
                    "message": f"Scan error: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                })

            # Wait for next scan
            logger.info(f"Waiting {scan_interval} seconds until next scan...")
            await asyncio.sleep(scan_interval)

    except asyncio.CancelledError:
        logger.info("Trading bot loop cancelled")
    except Exception as e:
        logger.error(f"Fatal error in trading bot loop: {e}")
        state.bot_running = False

# Bot control endpoints
@app.post("/api/bot/start")
async def start_bot():
    """Start the trading bot"""
    if state.bot_running:
        raise HTTPException(status_code=400, detail="Bot is already running")

    if state.trading_bot is None:
        raise HTTPException(status_code=503, detail="Trading bot not initialized")

    try:
        state.bot_running = True

        # Start the bot loop as a background task
        state.bot_task = asyncio.create_task(
            run_trading_bot_loop(
                scan_interval=300,  # 5 minutes
                min_confidence=70.0
            )
        )

        logger.info("Trading bot started via API")

        # Broadcast status update to WebSocket clients
        await manager.broadcast({
            "type": "bot_status",
            "running": True,
            "message": "Trading bot started - scanning every 5 minutes",
            "timestamp": datetime.now().isoformat()
        })

        return {
            "status": "success",
            "message": "Bot started successfully - scanning every 5 minutes",
            "bot_running": True,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        state.bot_running = False
        logger.error(f"Error starting bot: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start bot: {str(e)}")

@app.post("/api/bot/stop")
async def stop_bot():
    """Stop the trading bot"""
    if not state.bot_running:
        raise HTTPException(status_code=400, detail="Bot is not running")

    try:
        state.bot_running = False

        # Cancel the bot task if it exists
        if state.bot_task and not state.bot_task.done():
            state.bot_task.cancel()
            try:
                await state.bot_task
            except asyncio.CancelledError:
                pass

        logger.info("Trading bot stopped via API")

        # Broadcast status update to WebSocket clients
        await manager.broadcast({
            "type": "bot_status",
            "running": False,
            "message": "Trading bot stopped",
            "timestamp": datetime.now().isoformat()
        })

        return {
            "status": "success",
            "message": "Bot stopped successfully",
            "bot_running": False,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop bot: {str(e)}")

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and receive messages
            data = await websocket.receive_text()
            logger.debug(f"Received WebSocket message: {data}")
            
            # Echo back for now (can be expanded for client commands)
            await websocket.send_json({
                "type": "ack",
                "message": "Message received",
                "timestamp": datetime.now().isoformat()
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Root endpoint - serve React app
@app.get("/")
async def read_root():
    """Serve the React frontend"""
    return {"message": "AI Day Trading System API", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
