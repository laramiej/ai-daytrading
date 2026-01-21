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
from fastapi.responses import FileResponse, StreamingResponse
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

from src.utils import load_settings
from src.broker import AlpacaBroker
from src.reports import DailyReportManager

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
        self.initialized = False  # Track if trading components are ready
        self.pending_trades: Dict[str, dict] = {}  # trade_id -> signal data for approval
        self._trade_counter = 0  # For generating unique trade IDs
        self.report_manager = DailyReportManager()  # Daily report manager
        self._previous_market_open = None  # Track market state for snapshots

    def add_pending_trade(self, signal) -> str:
        """Add a signal to pending trades for approval"""
        self._trade_counter += 1
        trade_id = f"trade_{self._trade_counter}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.pending_trades[trade_id] = {
            "trade_id": trade_id,
            "symbol": signal.symbol,
            "signal": signal.signal,
            "confidence": signal.confidence,
            "reasoning": signal.reasoning,
            "entry_price": signal.entry_price,
            "stop_loss": signal.stop_loss,
            "take_profit": signal.take_profit,
            "position_size": signal.position_size_recommendation,
            "risk_factors": signal.risk_factors,
            "time_horizon": signal.time_horizon,
            "llm_provider": signal.llm_provider,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        }
        # Store the actual signal object for execution
        self.pending_trades[trade_id]["_signal_obj"] = signal
        return trade_id

    def get_pending_trade(self, trade_id: str) -> Optional[dict]:
        """Get a pending trade by ID"""
        return self.pending_trades.get(trade_id)

    def remove_pending_trade(self, trade_id: str):
        """Remove a pending trade"""
        if trade_id in self.pending_trades:
            del self.pending_trades[trade_id]

    def get_all_pending_trades(self) -> List[dict]:
        """Get all pending trades (without internal signal objects)"""
        trades = []
        for trade_id, trade in self.pending_trades.items():
            trade_copy = {k: v for k, v in trade.items() if not k.startswith('_')}
            trades.append(trade_copy)
        return trades

    async def initialize(self):
        """Initialize settings - broker and bot are initialized lazily when keys are configured"""
        try:
            self.settings = load_settings()
            logger.info("Settings loaded successfully")

            # Check if we can initialize the full trading system
            is_configured, missing = self.settings.is_fully_configured()
            if is_configured:
                self._initialize_broker()
                self._initialize_trading_bot()
                self.initialized = True
                logger.info("Trading system fully initialized")
            else:
                logger.info(f"Trading system not fully configured. Missing: {', '.join(missing)}")
                logger.info("Configure API keys in Settings to enable trading")

        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            # Still allow the app to start so user can configure via UI
            self.settings = load_settings()

    def _initialize_broker(self):
        """Initialize the Alpaca broker"""
        self.broker = AlpacaBroker(
            api_key=self.settings.alpaca_api_key,
            secret_key=self.settings.alpaca_secret_key,
            paper_trading=self.settings.alpaca_paper_trading
        )
        logger.info("Alpaca broker initialized")

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
                enable_short_selling=self.settings.enable_short_selling,
                max_position_exposure_percent=self.settings.max_position_exposure_percent
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

            def analyze_symbol(self, symbol):
                """Analyze a single symbol and return the signal (even HOLD)"""
                try:
                    signal = self.strategy.analyze_symbol(symbol)
                    return signal
                except Exception as e:
                    logger.error(f"Error analyzing {symbol}: {e}")
                    return None

            def get_market_sentiment(self):
                """Get overall market sentiment"""
                try:
                    if self.strategy.market_analyzer.sentiment_analyzer:
                        return self.strategy.market_analyzer._get_cached_market_sentiment()
                    return None
                except Exception as e:
                    logger.error(f"Error getting market sentiment: {e}")
                    return None

            def get_stock_sentiment(self, symbol):
                """Get sentiment for a specific stock"""
                try:
                    if self.strategy.market_analyzer.sentiment_analyzer:
                        return self.strategy.market_analyzer.sentiment_analyzer.get_stock_sentiment(symbol)
                    return None
                except Exception as e:
                    logger.error(f"Error getting stock sentiment for {symbol}: {e}")
                    return None

            def get_watchlist(self):
                """Get the watchlist"""
                return self.settings.get_watchlist()

            def execute_signal(self, signal):
                """
                Execute a trading signal

                Returns:
                    Tuple of (success: bool, reason: str, quantity: float, price: float, realized_pnl: float or None)
                    - quantity and price are 0 if trade failed/blocked
                    - realized_pnl is set when closing a position, None otherwise
                """
                logger.info(f"Processing signal: {signal.signal} {signal.symbol}")

                try:
                    quote = self.broker.get_latest_quote(signal.symbol)
                    current_price = (quote["bid_price"] + quote["ask_price"]) / 2
                    side = "buy" if signal.signal == "BUY" else "sell"

                    # Check if we have an existing position
                    positions = self.broker.get_positions()
                    existing_position = next((p for p in positions if p.symbol == signal.symbol), None)

                    # Track realized P&L when closing positions
                    realized_pnl = None

                    # Determine quantity based on signal type and existing position
                    # Get position side if we have a position (handle both string and enum)
                    position_side = None
                    if existing_position:
                        raw_side = existing_position.side
                        # Handle enum values (e.g., PositionSide.SHORT) vs string values
                        if hasattr(raw_side, 'value'):
                            position_side = raw_side.value.lower()
                        else:
                            position_side = str(raw_side).lower()
                        logger.info(f"Existing position for {signal.symbol}: side={position_side}, quantity={existing_position.quantity}")

                    if side == "sell" and existing_position and position_side == "long":
                        # SELL with existing LONG position: close the entire long position
                        # This REDUCES exposure - we're liquidating an asset, not opening a new position
                        quantity = abs(existing_position.quantity)  # Ensure positive quantity for order
                        logger.info(f"📉 SELL+LONG BRANCH: Closing LONG position for {signal.symbol}")
                        logger.info(f"   Selling {quantity} shares (reduces exposure, skipping dynamic sizing)")
                    elif side == "sell" and existing_position and position_side == "short":
                        # SELL with existing SHORT position: add to short (increase short exposure)
                        logger.info(f"📉 Adding to existing SHORT position for {signal.symbol}")
                        if signal.entry_price and signal.stop_loss:
                            base_quantity, sizing_explanation = self.risk_manager.calculate_position_size(
                                symbol=signal.symbol,
                                entry_price=signal.entry_price,
                                stop_loss_price=signal.stop_loss
                            )
                        else:
                            base_quantity = self.settings.max_position_size / current_price
                            base_quantity = round(base_quantity, 0)
                        quantity, position_value, dynamic_explanation = self.risk_manager.calculate_dynamic_position_size(
                            symbol=signal.symbol,
                            price=current_price,
                            base_quantity=base_quantity
                        )
                        logger.info(f"Additional short size: {quantity} shares ({dynamic_explanation})")
                    elif side == "sell" and not existing_position:
                        # SELL with no position: this is a new short sale
                        logger.info(f"📉 SHORT SELL signal for {signal.symbol} - opening new short position")
                        if not self.risk_manager.limits.enable_short_selling:
                            reason = f"Short selling is DISABLED in settings - cannot short {signal.symbol}"
                            logger.warning(f"⚠️ BLOCKED: {reason}")
                            return False, reason, 0, current_price, None
                        # Calculate short position size with dynamic sizing
                        if signal.entry_price and signal.stop_loss:
                            base_quantity, sizing_explanation = self.risk_manager.calculate_position_size(
                                symbol=signal.symbol,
                                entry_price=signal.entry_price,
                                stop_loss_price=signal.stop_loss
                            )
                        else:
                            base_quantity = self.settings.max_position_size / current_price
                            base_quantity = round(base_quantity, 0)
                        # Apply dynamic position sizing limits
                        quantity, position_value, dynamic_explanation = self.risk_manager.calculate_dynamic_position_size(
                            symbol=signal.symbol,
                            price=current_price,
                            base_quantity=base_quantity
                        )
                        logger.info(f"Short position size: {quantity} shares ({dynamic_explanation})")
                    elif side == "buy" and existing_position and position_side == "short":
                        # BUY with existing SHORT position: close the short (buy to cover)
                        # This REDUCES exposure - we're closing a liability, not opening a new position
                        quantity = abs(existing_position.quantity)  # Ensure positive quantity for order
                        logger.info(f"📈 BUY+SHORT BRANCH: Closing SHORT position for {signal.symbol}")
                        logger.info(f"   Buying to cover {quantity} shares (reduces exposure, skipping dynamic sizing)")
                    elif side == "buy" and existing_position and position_side == "long":
                        # BUY with existing LONG position: add to long (increase long exposure)
                        logger.info(f"📈 Adding to existing LONG position for {signal.symbol}")
                        if signal.entry_price and signal.stop_loss:
                            base_quantity, sizing_explanation = self.risk_manager.calculate_position_size(
                                symbol=signal.symbol,
                                entry_price=signal.entry_price,
                                stop_loss_price=signal.stop_loss
                            )
                        else:
                            base_quantity = self.settings.max_position_size / current_price
                            base_quantity = round(base_quantity, 0)
                        quantity, position_value, dynamic_explanation = self.risk_manager.calculate_dynamic_position_size(
                            symbol=signal.symbol,
                            price=current_price,
                            base_quantity=base_quantity
                        )
                        logger.info(f"Additional long size: {quantity} shares ({dynamic_explanation})")
                    else:
                        # BUY with no position: open new long position
                        # Debug: log what we're seeing
                        logger.info(f"📈 ELSE BRANCH for {signal.symbol}: side={side}, existing_position={existing_position is not None}, position_side={position_side}")
                        if existing_position and position_side not in ["long", "short"]:
                            logger.warning(f"⚠️ UNEXPECTED position_side value: '{position_side}' (type: {type(position_side)})")
                        logger.info(f"📈 BUY signal for {signal.symbol} - opening new long position")
                        if signal.entry_price and signal.stop_loss:
                            base_quantity, sizing_explanation = self.risk_manager.calculate_position_size(
                                symbol=signal.symbol,
                                entry_price=signal.entry_price,
                                stop_loss_price=signal.stop_loss
                            )
                        else:
                            base_quantity = self.settings.max_position_size / current_price
                            base_quantity = round(base_quantity, 0)
                        # Apply dynamic position sizing limits
                        quantity, position_value, dynamic_explanation = self.risk_manager.calculate_dynamic_position_size(
                            symbol=signal.symbol,
                            price=current_price,
                            base_quantity=base_quantity
                        )
                        logger.info(f"Buy position size: {quantity} shares ({dynamic_explanation})")

                    if quantity <= 0:
                        reason = "Insufficient exposure budget remaining - position would be 0 shares"
                        logger.warning(f"TRADE BLOCKED [{signal.symbol}]: {reason}")
                        return False, reason, 0, current_price, None

                    # Evaluate risk
                    risk_decision = self.risk_manager.evaluate_trade(
                        symbol=signal.symbol,
                        side=side,
                        quantity=quantity,
                        estimated_price=current_price
                    )

                    if not risk_decision.approved:
                        reason = f"Risk manager: {risk_decision.reason}"
                        logger.warning(f"Trade blocked - {reason}")
                        return False, reason, 0, current_price, None

                    final_quantity = risk_decision.recommended_quantity or quantity

                    # Final safety check - ensure we're not trying to place a 0-quantity order
                    if final_quantity <= 0:
                        reason = "Final quantity is 0 or negative - cannot execute trade"
                        logger.warning(f"TRADE BLOCKED [{signal.symbol}]: {reason}")
                        return False, reason, 0, current_price, None

                    # Check if we're closing a position
                    is_closing_position = (
                        (side == "buy" and position_side == "short") or
                        (side == "sell" and position_side == "long")
                    )

                    # When closing a position, capture the realized P&L
                    if is_closing_position and existing_position:
                        # Capture realized P&L from the position we're about to close
                        realized_pnl = existing_position.pnl
                        logger.info(f"Closing position for {signal.symbol} - Realized P&L: ${realized_pnl:.2f}")

                    # Always use simple market orders (no stop-loss or take-profit)
                    order = self.broker.place_market_order(
                        symbol=signal.symbol,
                        quantity=final_quantity,
                        side=side
                    )
                    order_desc = f"{side.upper()} {final_quantity} shares @ ${current_price:.2f}"

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
                    return True, f"Order placed: {order_desc}", final_quantity, current_price, realized_pnl

                except Exception as e:
                    reason = f"Error executing signal: {str(e)}"
                    logger.error(reason)
                    return False, reason, 0, 0, None

        self.trading_bot = SimpleTradingBot(self.broker, strategy, risk_manager, self.settings)

        # Connect report manager with trading components
        self.report_manager.set_trading_components(self.broker, risk_manager, portfolio)

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
    is_configured, missing = state.settings.is_fully_configured() if state.settings else (False, ["Settings not loaded"])
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "bot_running": state.bot_running,
        "configured": is_configured,
        "initialized": state.initialized
    }

# Configuration status endpoint
@app.get("/api/config/status")
async def get_config_status():
    """Check if the system is fully configured and ready to run"""
    if state.settings is None:
        return {
            "configured": False,
            "initialized": False,
            "missing": ["Settings not loaded"],
            "message": "Please refresh the page"
        }

    is_configured, missing = state.settings.is_fully_configured()

    return {
        "configured": is_configured,
        "initialized": state.initialized,
        "missing": missing,
        "message": "Ready to start trading" if is_configured else f"Please configure: {', '.join(missing)}"
    }

# Initialize/reinitialize trading system after config changes
@app.post("/api/config/initialize")
async def initialize_trading_system():
    """Initialize or reinitialize the trading system after configuration changes"""
    if state.settings is None:
        raise HTTPException(status_code=500, detail="Settings not loaded")

    # Reload settings from .env
    state.settings = load_settings(reload_env=True)

    is_configured, missing = state.settings.is_fully_configured()

    if not is_configured:
        return {
            "status": "not_configured",
            "initialized": False,
            "missing": missing,
            "message": f"Cannot initialize: {', '.join(missing)}"
        }

    try:
        # Stop the bot if running
        if state.bot_running:
            state.bot_running = False
            if state.bot_task and not state.bot_task.done():
                state.bot_task.cancel()

        # Reinitialize broker and trading bot
        state._initialize_broker()
        state._initialize_trading_bot()
        state.initialized = True

        logger.info("Trading system reinitialized successfully")

        return {
            "status": "success",
            "initialized": True,
            "missing": [],
            "message": "Trading system initialized successfully"
        }
    except Exception as e:
        logger.error(f"Failed to initialize trading system: {e}")
        state.initialized = False
        raise HTTPException(status_code=500, detail=f"Initialization failed: {str(e)}")

# Get trading status
@app.get("/api/status")
async def get_status():
    """Get current trading system status"""
    # Return limited status if not fully configured
    if not state.initialized or state.broker is None:
        is_configured, missing = state.settings.is_fully_configured() if state.settings else (False, ["Settings not loaded"])
        return {
            "bot_running": False,
            "configured": is_configured,
            "initialized": False,
            "missing": missing,
            "account": None,
            "positions_count": 0,
            "timestamp": datetime.now().isoformat()
        }

    try:
        account = state.broker.get_account_info()
        positions = state.broker.get_positions()

        return {
            "bot_running": state.bot_running,
            "configured": True,
            "initialized": state.initialized,
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
    """Get all current positions with associated open orders (stop-loss/take-profit)"""
    if state.broker is None:
        return {
            "positions": [],
            "configured": False,
            "timestamp": datetime.now().isoformat()
        }

    try:
        positions = state.broker.get_positions()
        open_orders = state.broker.get_open_orders()

        # Build a map of open orders by symbol for quick lookup
        # Stop-loss orders (type 'stop' or 'stop_limit') and limit orders (take-profit)
        orders_by_symbol = {}
        for order in open_orders:
            if order.symbol not in orders_by_symbol:
                orders_by_symbol[order.symbol] = {"stop_loss": None, "take_profit": None}

            # Stop orders are stop-loss
            if order.order_type in ["stop", "stop_limit"] and order.stop_price:
                orders_by_symbol[order.symbol]["stop_loss"] = order.stop_price
            # Limit orders on opposite side are take-profit
            elif order.order_type == "limit" and order.limit_price:
                orders_by_symbol[order.symbol]["take_profit"] = order.limit_price

        return {
            "positions": [
                {
                    "symbol": pos.symbol,
                    "quantity": pos.quantity,
                    "side": pos.side,
                    "entry_price": pos.entry_price,
                    "current_price": pos.current_price,
                    "pnl": pos.pnl,
                    "pnl_percent": pos.pnl_percent,
                    "stop_loss": orders_by_symbol.get(pos.symbol, {}).get("stop_loss"),
                    "take_profit": orders_by_symbol.get(pos.symbol, {}).get("take_profit")
                }
                for pos in positions
            ],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _mask_api_key(key: Optional[str]) -> str:
    """Mask an API key for display, showing only last 4 characters"""
    if not key or key.startswith("your_"):
        return ""  # Not configured
    if len(key) <= 4:
        return "***"
    return "***" + key[-4:]

# Get settings
@app.get("/api/settings")
async def get_settings():
    """Get current trading settings"""
    is_configured, missing = state.settings.is_fully_configured() if state.settings else (False, [])

    return {
        "configured": is_configured,
        "initialized": state.initialized,
        "missing": missing,
        "max_position_size": state.settings.max_position_size,
        "max_daily_loss": state.settings.max_daily_loss,
        "max_total_exposure": state.settings.max_total_exposure,
        "stop_loss_percentage": state.settings.stop_loss_percentage,
        "take_profit_percentage": state.settings.take_profit_percentage,
        "max_open_positions": state.settings.max_open_positions,
        "enable_short_selling": state.settings.enable_short_selling,
        "max_position_exposure_percent": state.settings.max_position_exposure_percent,
        "enable_auto_trading": state.settings.enable_auto_trading,
        "enable_finnhub": state.settings.enable_finnhub,
        "default_llm_provider": state.settings.default_llm_provider,
        "watchlist": state.settings.get_watchlist(),
        # Bot scheduling
        "scan_interval_minutes": state.settings.scan_interval_minutes,
        "min_confidence_threshold": state.settings.min_confidence_threshold,
        "close_positions_at_session_end": state.settings.close_positions_at_session_end,
        # Include API keys (masked for security, empty string means not configured)
        "alpaca_api_key": _mask_api_key(state.settings.alpaca_api_key),
        "alpaca_secret_key": _mask_api_key(state.settings.alpaca_secret_key),
        "anthropic_api_key": _mask_api_key(state.settings.anthropic_api_key),
        "openai_api_key": _mask_api_key(state.settings.openai_api_key),
        "finnhub_api_key": _mask_api_key(state.settings.finnhub_api_key),
        "google_api_key": _mask_api_key(state.settings.google_api_key),
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
                    'max_position_exposure_percent': 'MAX_POSITION_EXPOSURE_PERCENT',
                    'enable_auto_trading': 'ENABLE_AUTO_TRADING',
                    'enable_finnhub': 'ENABLE_FINNHUB',
                    'default_llm_provider': 'DEFAULT_LLM_PROVIDER',
                    'scan_interval_minutes': 'SCAN_INTERVAL_MINUTES',
                    'min_confidence_threshold': 'MIN_CONFIDENCE_THRESHOLD',
                    'close_positions_at_session_end': 'CLOSE_POSITIONS_AT_SESSION_END',
                    'alpaca_api_key': 'ALPACA_API_KEY',
                    'alpaca_secret_key': 'ALPACA_SECRET_KEY',
                    'anthropic_api_key': 'ANTHROPIC_API_KEY',
                    'openai_api_key': 'OPENAI_API_KEY',
                    'finnhub_api_key': 'FINNHUB_API_KEY',
                    'google_api_key': 'GOOGLE_API_KEY',
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

        # Add any new keys that weren't found in the file (e.g., commented out or missing)
        env_key_map = {
            'max_position_size': 'MAX_POSITION_SIZE',
            'max_daily_loss': 'MAX_DAILY_LOSS',
            'max_total_exposure': 'MAX_TOTAL_EXPOSURE',
            'stop_loss_percentage': 'STOP_LOSS_PERCENTAGE',
            'take_profit_percentage': 'TAKE_PROFIT_PERCENTAGE',
            'max_open_positions': 'MAX_OPEN_POSITIONS',
            'enable_short_selling': 'ENABLE_SHORT_SELLING',
            'max_position_exposure_percent': 'MAX_POSITION_EXPOSURE_PERCENT',
            'enable_auto_trading': 'ENABLE_AUTO_TRADING',
            'enable_finnhub': 'ENABLE_FINNHUB',
            'default_llm_provider': 'DEFAULT_LLM_PROVIDER',
            'scan_interval_minutes': 'SCAN_INTERVAL_MINUTES',
            'min_confidence_threshold': 'MIN_CONFIDENCE_THRESHOLD',
            'close_positions_at_session_end': 'CLOSE_POSITIONS_AT_SESSION_END',
            'alpaca_api_key': 'ALPACA_API_KEY',
            'alpaca_secret_key': 'ALPACA_SECRET_KEY',
            'anthropic_api_key': 'ANTHROPIC_API_KEY',
            'openai_api_key': 'OPENAI_API_KEY',
            'finnhub_api_key': 'FINNHUB_API_KEY',
            'watchlist': 'WATCHLIST',
        }

        for frontend_key, env_key in env_key_map.items():
            if frontend_key in updated_settings and frontend_key not in keys_updated:
                value = updated_settings[frontend_key]
                # Skip masked values (unchanged API keys) or empty values
                if isinstance(value, str) and (value.startswith('***') or value == ''):
                    continue
                # Format value appropriately
                if isinstance(value, bool):
                    formatted_value = str(value).lower()
                elif isinstance(value, list):
                    formatted_value = ','.join(value)
                else:
                    formatted_value = str(value)
                # Add the new key
                updated_lines.append(f"{env_key}={formatted_value}\n")
                keys_updated.add(frontend_key)
                logger.info(f"Added new key to .env: {env_key}")

        # Write updated .env file
        with open(env_path, 'w') as f:
            f.writelines(updated_lines)

        logger.info(f"Settings updated: {', '.join(keys_updated)}")

        # Reload settings from .env file (note: bot needs restart for full effect)
        state.settings = load_settings(reload_env=True)

        # Check if system is now fully configured
        is_configured, missing = state.settings.is_fully_configured()

        return {
            "status": "success",
            "message": "Settings saved successfully. Restart the bot for changes to take full effect.",
            "updated_keys": list(keys_updated),
            "configured": is_configured,
            "missing": missing
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
            market_is_open = state.trading_bot.broker.is_market_open()

            # Detect market state transitions for automatic snapshots
            if state._previous_market_open is not None:
                if not state._previous_market_open and market_is_open:
                    # Market just opened - capture market open snapshot
                    logger.info("Market opened - capturing market open snapshot")
                    state.report_manager.capture_snapshot("market_open")
                    # Reset the positions closed flag for new trading day
                    state._positions_closed_today = False
                elif state._previous_market_open and not market_is_open:
                    # Market just closed - capture market close snapshot
                    logger.info("Market closed - capturing market close snapshot")
                    state.report_manager.capture_snapshot("market_close")

            state._previous_market_open = market_is_open

            # Check if we should close positions near end of session
            # Close positions if this is the last scan before market close
            # (i.e., there won't be another full scan interval before market closes)
            if market_is_open and state.settings.close_positions_at_session_end:
                minutes_until_close = state.trading_bot.broker.get_minutes_until_close()
                scan_interval = state.settings.scan_interval_minutes

                # Close if time remaining is less than the scan interval
                # This ensures we close on the last possible scan while market is still open
                if minutes_until_close is not None and minutes_until_close <= scan_interval:
                    # Check if we haven't already closed positions this session
                    if not getattr(state, '_positions_closed_today', False):
                        logger.info(f"Market closing in {minutes_until_close} minutes (scan interval: {scan_interval}m) - this is the last scan, closing all positions")
                        await manager.broadcast({
                            "type": "session_closing",
                            "message": f"Market closing in {minutes_until_close} minutes - closing all positions on final scan",
                            "minutes_remaining": minutes_until_close,
                            "scan_interval": scan_interval,
                            "timestamp": datetime.now().isoformat()
                        })

                        try:
                            results = state.trading_bot.broker.close_all_positions()
                            state._positions_closed_today = True

                            # Calculate total P&L from closed positions
                            total_pnl = sum(r.get("pnl", 0) for r in results if r.get("status") == "closed")
                            closed_count = len([r for r in results if r.get("status") == "closed"])

                            await manager.broadcast({
                                "type": "positions_closed",
                                "message": f"Closed {closed_count} positions at end of session",
                                "total_pnl": total_pnl,
                                "results": results,
                                "timestamp": datetime.now().isoformat()
                            })

                            logger.info(f"End of session: Closed {closed_count} positions, Total P&L: ${total_pnl:.2f}")
                        except Exception as e:
                            logger.error(f"Error closing positions at session end: {e}")
                            await manager.broadcast({
                                "type": "error",
                                "message": f"Error closing positions: {str(e)}",
                                "timestamp": datetime.now().isoformat()
                            })

                        # Stop the bot after closing positions at end of session
                        logger.info("End of session - stopping bot. Restart manually tomorrow.")
                        state.bot_running = False
                        await manager.broadcast({
                            "type": "bot_status",
                            "running": False,
                            "message": "Bot stopped after closing all positions at end of session. Restart manually tomorrow.",
                            "timestamp": datetime.now().isoformat()
                        })
                        return  # Exit the trading loop

            if not market_is_open:
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
            watchlist = state.trading_bot.get_watchlist()

            # Get market sentiment and broadcast
            market_sentiment = state.trading_bot.get_market_sentiment()
            market_sentiment_data = None
            if market_sentiment:
                # Serialize sentiment for broadcast (datetime not JSON serializable)
                market_sentiment_data = {
                    "overall_score": market_sentiment.get("overall_score", 0),
                    "summary": market_sentiment.get("summary", "Unknown"),
                    "indicators": {}
                }
                for name, indicator in market_sentiment.get("indicators", {}).items():
                    market_sentiment_data["indicators"][name] = {
                        "score": indicator.get("score", 0),
                        "label": indicator.get("label", "N/A"),
                        "value": indicator.get("value"),
                        "change": indicator.get("change")
                    }

                await manager.broadcast({
                    "type": "market_sentiment",
                    "sentiment": market_sentiment_data,
                    "timestamp": datetime.now().isoformat()
                })

            await manager.broadcast({
                "type": "scan_started",
                "message": f"Scanning {len(watchlist)} symbols for opportunities",
                "symbols": watchlist,
                "market_sentiment": market_sentiment_data,
                "timestamp": datetime.now().isoformat()
            })

            try:
                # Analyze each symbol individually and broadcast results
                all_analyses = []
                actionable_signals = []

                for symbol in watchlist:
                    logger.info(f"Analyzing {symbol}...")

                    # Broadcast that we're analyzing this symbol
                    await manager.broadcast({
                        "type": "analyzing_symbol",
                        "symbol": symbol,
                        "timestamp": datetime.now().isoformat()
                    })

                    # Analyze the symbol
                    signal = state.trading_bot.analyze_symbol(symbol)

                    # Track signal analyzed in daily report
                    state.report_manager.record_signal_analyzed()

                    if signal:
                        # Determine if this is actionable (BUY/SELL with high confidence)
                        is_actionable = (
                            signal.signal != "HOLD" and
                            signal.confidence >= min_confidence
                        )

                        # Get stock-specific sentiment
                        stock_sentiment = state.trading_bot.get_stock_sentiment(symbol)
                        stock_sentiment_data = None
                        if stock_sentiment:
                            stock_sentiment_data = {
                                "overall_score": stock_sentiment.get("overall_score", 0),
                                "summary": stock_sentiment.get("summary", "Unknown"),
                                "sources": {}
                            }
                            for source_name, source_data in stock_sentiment.get("sources", {}).items():
                                if source_data:
                                    stock_sentiment_data["sources"][source_name] = {
                                        "score": source_data.get("score", 0),
                                        "label": source_data.get("label", "N/A")
                                    }

                        analysis_data = {
                            "symbol": signal.symbol,
                            "signal": signal.signal,
                            "confidence": signal.confidence,
                            "reasoning": signal.reasoning,
                            "entry_price": signal.entry_price,
                            "stop_loss": signal.stop_loss,
                            "take_profit": signal.take_profit,
                            "position_size": signal.position_size_recommendation,
                            "risk_factors": signal.risk_factors,
                            "time_horizon": signal.time_horizon,
                            "llm_provider": signal.llm_provider,
                            "is_actionable": is_actionable,
                            "stock_sentiment": stock_sentiment_data,
                            "timestamp": datetime.now().isoformat()
                        }

                        all_analyses.append(analysis_data)

                        # Broadcast individual stock analysis
                        await manager.broadcast({
                            "type": "stock_analysis",
                            **analysis_data
                        })

                        # Track actionable signals
                        if is_actionable:
                            actionable_signals.append(signal)
                    else:
                        # Broadcast analysis failure
                        await manager.broadcast({
                            "type": "stock_analysis",
                            "symbol": symbol,
                            "signal": "ERROR",
                            "confidence": 0,
                            "reasoning": "Failed to analyze symbol",
                            "is_actionable": False,
                            "timestamp": datetime.now().isoformat()
                        })

                # After all analyses, handle actionable signals
                if actionable_signals:
                    # Sort by confidence
                    actionable_signals.sort(key=lambda x: x.confidence, reverse=True)

                    if state.settings.enable_auto_trading:
                        # Auto-execute ALL actionable signals in order of confidence
                        logger.info(f"Auto-trading enabled - attempting to execute {len(actionable_signals)} signals")

                        for signal in actionable_signals:
                            logger.info(f"Attempting: {signal.signal} {signal.symbol} ({signal.confidence}%)")
                            success, reason, exec_quantity, exec_price, exec_realized_pnl = state.trading_bot.execute_signal(signal)

                            if success:
                                # Record trade in daily report with actual execution details
                                state.report_manager.record_trade({
                                    "symbol": signal.symbol,
                                    "side": "buy" if signal.signal == "BUY" else "sell",
                                    "quantity": exec_quantity,
                                    "price": exec_price,
                                    "signal_confidence": signal.confidence,
                                    "llm_provider": signal.llm_provider,
                                    "reasoning": signal.reasoning,
                                    "realized_pnl": exec_realized_pnl,  # Set when closing a position
                                })

                                await manager.broadcast({
                                    "type": "trade_executed",
                                    "success": True,
                                    "symbol": signal.symbol,
                                    "signal": signal.signal,
                                    "confidence": signal.confidence,
                                    "message": reason,
                                    "timestamp": datetime.now().isoformat()
                                })
                            else:
                                # Record blocked trade in daily report
                                state.report_manager.record_trade({
                                    "symbol": signal.symbol,
                                    "side": "buy" if signal.signal == "BUY" else "sell",
                                    "quantity": exec_quantity,  # May be 0 if blocked early
                                    "price": exec_price,
                                    "signal_confidence": signal.confidence,
                                    "llm_provider": signal.llm_provider,
                                    "reasoning": signal.reasoning,
                                    "block_reason": reason,
                                }, blocked=True)

                                # Trade blocked by risk manager - broadcast with detailed reason
                                await manager.broadcast({
                                    "type": "trade_blocked",
                                    "success": False,
                                    "symbol": signal.symbol,
                                    "signal": signal.signal,
                                    "confidence": signal.confidence,
                                    "message": f"Trade blocked for {signal.symbol}",
                                    "reason": reason,
                                    "timestamp": datetime.now().isoformat()
                                })
                    else:
                        # Add to pending trades for approval
                        logger.info(f"Auto-trading disabled - adding {len(actionable_signals)} signals to pending trades")
                        for s in actionable_signals:
                            trade_id = state.add_pending_trade(s)

                            await manager.broadcast({
                                "type": "trade_pending_approval",
                                "trade_id": trade_id,
                                "symbol": s.symbol,
                                "signal": s.signal,
                                "confidence": s.confidence,
                                "reasoning": s.reasoning,
                                "entry_price": s.entry_price,
                                "stop_loss": s.stop_loss,
                                "take_profit": s.take_profit,
                                "position_size": s.position_size_recommendation,
                                "risk_factors": s.risk_factors,
                                "time_horizon": s.time_horizon,
                                "llm_provider": s.llm_provider,
                                "timestamp": datetime.now().isoformat()
                            })

                # Broadcast scan complete summary
                await manager.broadcast({
                    "type": "scan_complete",
                    "message": f"Scan complete - analyzed {len(watchlist)} symbols",
                    "total_analyzed": len(watchlist),
                    "actionable_count": len(actionable_signals),
                    "analyses": all_analyses,
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

    # Check if system is fully configured
    if state.settings is None:
        raise HTTPException(status_code=503, detail="Settings not loaded")

    is_configured, missing = state.settings.is_fully_configured()
    if not is_configured:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start bot. Please configure: {', '.join(missing)}"
        )

    # Initialize if needed
    if not state.initialized or state.trading_bot is None:
        try:
            state._initialize_broker()
            state._initialize_trading_bot()
            state.initialized = True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize trading system: {str(e)}")

    try:
        state.bot_running = True

        # Get scan settings from config
        scan_interval_seconds = state.settings.scan_interval_minutes * 60
        min_confidence = state.settings.min_confidence_threshold

        # Start the bot loop as a background task
        state.bot_task = asyncio.create_task(
            run_trading_bot_loop(
                scan_interval=scan_interval_seconds,
                min_confidence=min_confidence
            )
        )

        logger.info(f"Trading bot started via API (scan every {state.settings.scan_interval_minutes} min, min confidence {min_confidence}%)")

        # Broadcast status update to WebSocket clients
        await manager.broadcast({
            "type": "bot_status",
            "running": True,
            "message": f"Trading bot started - scanning every {state.settings.scan_interval_minutes} minutes",
            "scan_interval_minutes": state.settings.scan_interval_minutes,
            "min_confidence_threshold": min_confidence,
            "timestamp": datetime.now().isoformat()
        })

        return {
            "status": "success",
            "message": f"Bot started successfully - scanning every {state.settings.scan_interval_minutes} minutes",
            "bot_running": True,
            "scan_interval_minutes": state.settings.scan_interval_minutes,
            "min_confidence_threshold": min_confidence,
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

# Pending trades endpoints
@app.get("/api/pending-trades")
async def get_pending_trades():
    """Get all pending trades awaiting approval"""
    return {
        "pending_trades": state.get_all_pending_trades(),
        "count": len(state.pending_trades),
        "auto_trading_enabled": state.settings.enable_auto_trading if state.settings else False
    }

@app.post("/api/pending-trades/{trade_id}/approve")
async def approve_trade(trade_id: str):
    """Approve and execute a pending trade"""
    trade = state.get_pending_trade(trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail=f"Trade {trade_id} not found")

    if trade.get("status") != "pending":
        raise HTTPException(status_code=400, detail=f"Trade {trade_id} is not pending")

    if not state.trading_bot:
        raise HTTPException(status_code=503, detail="Trading bot not initialized")

    try:
        # Get the original signal object
        signal = trade.get("_signal_obj")
        if not signal:
            raise HTTPException(status_code=500, detail="Signal data missing")

        # Execute the trade
        logger.info(f"User approved trade: {trade['signal']} {trade['symbol']}")
        success, reason, exec_quantity, exec_price, exec_realized_pnl = state.trading_bot.execute_signal(signal)

        # Record trade in daily report with actual execution details
        if success:
            state.report_manager.record_trade({
                "symbol": trade["symbol"],
                "side": "buy" if trade["signal"] == "BUY" else "sell",
                "quantity": exec_quantity,
                "price": exec_price,
                "signal_confidence": trade.get("confidence", 0),
                "llm_provider": trade.get("llm_provider", ""),
                "reasoning": trade.get("reasoning", ""),
                "realized_pnl": exec_realized_pnl,  # Set when closing a position
            })
        else:
            state.report_manager.record_trade({
                "symbol": trade["symbol"],
                "side": "buy" if trade["signal"] == "BUY" else "sell",
                "quantity": exec_quantity,  # May be 0 if blocked early
                "price": exec_price,
                "signal_confidence": trade.get("confidence", 0),
                "llm_provider": trade.get("llm_provider", ""),
                "reasoning": trade.get("reasoning", ""),
                "block_reason": reason,
            }, blocked=True)

        # Remove from pending
        state.remove_pending_trade(trade_id)

        # Broadcast execution result
        if success:
            await manager.broadcast({
                "type": "trade_executed",
                "success": True,
                "symbol": trade["symbol"],
                "signal": trade["signal"],
                "trade_id": trade_id,
                "approved_by": "user",
                "message": reason,
                "timestamp": datetime.now().isoformat()
            })
        else:
            # Trade was approved by user but blocked by risk manager
            await manager.broadcast({
                "type": "trade_blocked",
                "success": False,
                "symbol": trade["symbol"],
                "signal": trade["signal"],
                "trade_id": trade_id,
                "approved_by": "user",
                "message": f"Trade blocked for {trade['symbol']}",
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            })

        # Broadcast updated pending trades list
        await manager.broadcast({
            "type": "pending_trades_update",
            "pending_trades": state.get_all_pending_trades(),
            "count": len(state.pending_trades),
            "timestamp": datetime.now().isoformat()
        })

        return {
            "status": "success" if success else "failed",
            "message": f"Trade {'executed' if success else 'failed'}: {trade['signal']} {trade['symbol']}" + (f" - {reason}" if not success else ""),
            "reason": reason,
            "trade_id": trade_id,
            "symbol": trade["symbol"],
            "signal": trade["signal"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error executing approved trade: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute trade: {str(e)}")

@app.post("/api/pending-trades/{trade_id}/reject")
async def reject_trade(trade_id: str):
    """Reject a pending trade"""
    trade = state.get_pending_trade(trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail=f"Trade {trade_id} not found")

    if trade.get("status") != "pending":
        raise HTTPException(status_code=400, detail=f"Trade {trade_id} is not pending")

    logger.info(f"User rejected trade: {trade['signal']} {trade['symbol']}")

    # Remove from pending
    state.remove_pending_trade(trade_id)

    # Broadcast rejection
    await manager.broadcast({
        "type": "trade_rejected",
        "symbol": trade["symbol"],
        "signal": trade["signal"],
        "trade_id": trade_id,
        "timestamp": datetime.now().isoformat()
    })

    # Broadcast updated pending trades list
    await manager.broadcast({
        "type": "pending_trades_update",
        "pending_trades": state.get_all_pending_trades(),
        "count": len(state.pending_trades),
        "timestamp": datetime.now().isoformat()
    })

    return {
        "status": "rejected",
        "message": f"Trade rejected: {trade['signal']} {trade['symbol']}",
        "trade_id": trade_id,
        "symbol": trade["symbol"],
        "signal": trade["signal"],
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/pending-trades/clear")
async def clear_pending_trades():
    """Clear all pending trades"""
    count = len(state.pending_trades)
    state.pending_trades.clear()

    await manager.broadcast({
        "type": "pending_trades_update",
        "pending_trades": [],
        "count": 0,
        "timestamp": datetime.now().isoformat()
    })

    return {
        "status": "success",
        "message": f"Cleared {count} pending trades",
        "timestamp": datetime.now().isoformat()
    }


# ============================================
# Daily Reports API Endpoints
# ============================================

@app.get("/api/reports")
async def list_reports():
    """Get list of available daily reports"""
    try:
        report_dates = state.report_manager.list_available_reports()
        summaries = []
        for date_str in report_dates[:30]:  # Limit to last 30 reports
            summary = state.report_manager.get_report_summary(date_str)
            if summary:
                summaries.append(summary)

        return {
            "reports": summaries,
            "count": len(summaries),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reports/today")
async def get_today_report():
    """Get today's report (may be incomplete/in-progress)"""
    try:
        report = state.report_manager.get_or_create_today_report()
        return {
            "report": report.to_dict(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting today's report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reports/{date}")
async def get_report(date: str):
    """Get daily report for a specific date (YYYY-MM-DD format)"""
    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    try:
        report = state.report_manager.load_report(date)
        if not report:
            raise HTTPException(status_code=404, detail=f"No report found for {date}")

        return {
            "report": report.to_dict(),
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report for {date}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reports/snapshot")
async def capture_snapshot(body: dict = None):
    """Manually capture a portfolio snapshot"""
    if not state.initialized or state.broker is None:
        raise HTTPException(status_code=503, detail="Trading system not initialized")

    snapshot_type = "manual"
    if body and "snapshot_type" in body:
        snapshot_type = body["snapshot_type"]
        if snapshot_type not in ["market_open", "market_close", "manual"]:
            raise HTTPException(status_code=400, detail="Invalid snapshot_type. Use: market_open, market_close, or manual")

    try:
        snapshot = state.report_manager.capture_snapshot(snapshot_type)
        if not snapshot:
            raise HTTPException(status_code=500, detail="Failed to capture snapshot")

        return {
            "status": "success",
            "message": f"Captured {snapshot_type} snapshot",
            "snapshot": {
                "timestamp": snapshot.timestamp,
                "snapshot_type": snapshot.snapshot_type,
                "portfolio_value": snapshot.portfolio_value,
                "cash": snapshot.cash,
                "equity": snapshot.equity,
                "total_positions": snapshot.total_positions
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error capturing snapshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reports/{date}/pdf")
async def download_report_pdf(date: str):
    """Download a daily report as a PDF file"""
    from io import BytesIO

    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    try:
        pdf_bytes = state.report_manager.generate_pdf(date)
        if not pdf_bytes:
            raise HTTPException(status_code=404, detail=f"No report found for {date}")

        # Return as downloadable PDF
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=trading_report_{date}.pdf"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating PDF for {date}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
