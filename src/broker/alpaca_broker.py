"""
Alpaca Broker Integration
Handles all interactions with Alpaca trading API
"""
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Represents a trading position"""
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    pnl: float
    pnl_percent: float
    side: str


@dataclass
class Order:
    """Represents a trading order"""
    order_id: str
    symbol: str
    quantity: float
    side: str
    order_type: str
    status: str
    filled_price: Optional[float] = None


class AlpacaBroker:
    """Alpaca broker client for trading operations"""

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        paper_trading: bool = True
    ):
        """
        Initialize Alpaca broker client

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper_trading: Use paper trading (default True)
        """
        self.paper_trading = paper_trading
        self.trading_client = TradingClient(
            api_key=api_key,
            secret_key=secret_key,
            paper=paper_trading
        )
        self.data_client = StockHistoricalDataClient(
            api_key=api_key,
            secret_key=secret_key
        )

        logger.info(
            f"Alpaca broker initialized "
            f"({'PAPER' if paper_trading else 'LIVE'} trading)"
        )

    def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        try:
            account = self.trading_client.get_account()
            return {
                "cash": float(account.cash),
                "portfolio_value": float(account.portfolio_value),
                "buying_power": float(account.buying_power),
                "equity": float(account.equity),
                "last_equity": float(account.last_equity),
                "pattern_day_trader": account.pattern_day_trader,
                "trading_blocked": account.trading_blocked,
                "account_blocked": account.account_blocked,
            }
        except Exception as e:
            logger.error(f"Error fetching account info: {e}")
            raise

    def get_positions(self) -> List[Position]:
        """Get all open positions"""
        try:
            positions = self.trading_client.get_all_positions()
            result = []

            for pos in positions:
                current_price = float(pos.current_price)
                entry_price = float(pos.avg_entry_price)
                quantity = float(pos.qty)
                pnl = float(pos.unrealized_pl)
                pnl_percent = float(pos.unrealized_plpc) * 100

                result.append(Position(
                    symbol=pos.symbol,
                    quantity=quantity,
                    entry_price=entry_price,
                    current_price=current_price,
                    pnl=pnl,
                    pnl_percent=pnl_percent,
                    side=pos.side
                ))

            return result
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            raise

    def get_open_orders(self) -> List[Order]:
        """Get all open orders"""
        try:
            orders = self.trading_client.get_orders()
            result = []

            for order in orders:
                result.append(Order(
                    order_id=order.id,
                    symbol=order.symbol,
                    quantity=float(order.qty),
                    side=order.side.value,
                    order_type=order.type.value,
                    status=order.status.value,
                    filled_price=float(order.filled_avg_price) if order.filled_avg_price else None
                ))

            return result
        except Exception as e:
            logger.error(f"Error fetching orders: {e}")
            raise

    def place_market_order(
        self,
        symbol: str,
        quantity: float,
        side: str
    ) -> Order:
        """
        Place a market order

        Args:
            symbol: Stock symbol
            quantity: Number of shares
            side: 'buy' or 'sell'

        Returns:
            Order object
        """
        try:
            order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL

            request = MarketOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=order_side,
                time_in_force=TimeInForce.DAY
            )

            order = self.trading_client.submit_order(request)

            logger.info(
                f"Market order placed: {side.upper()} {quantity} shares of {symbol}"
            )

            return Order(
                order_id=order.id,
                symbol=order.symbol,
                quantity=float(order.qty),
                side=order.side.value,
                order_type=order.type.value,
                status=order.status.value
            )
        except Exception as e:
            logger.error(f"Error placing market order: {e}")
            raise

    def place_limit_order(
        self,
        symbol: str,
        quantity: float,
        side: str,
        limit_price: float
    ) -> Order:
        """
        Place a limit order

        Args:
            symbol: Stock symbol
            quantity: Number of shares
            side: 'buy' or 'sell'
            limit_price: Limit price

        Returns:
            Order object
        """
        try:
            order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL

            request = LimitOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=order_side,
                time_in_force=TimeInForce.DAY,
                limit_price=limit_price
            )

            order = self.trading_client.submit_order(request)

            logger.info(
                f"Limit order placed: {side.upper()} {quantity} shares of {symbol} @ ${limit_price}"
            )

            return Order(
                order_id=order.id,
                symbol=order.symbol,
                quantity=float(order.qty),
                side=order.side.value,
                order_type=order.type.value,
                status=order.status.value
            )
        except Exception as e:
            logger.error(f"Error placing limit order: {e}")
            raise

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order by ID"""
        try:
            self.trading_client.cancel_order_by_id(order_id)
            logger.info(f"Order {order_id} cancelled")
            return True
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False

    def get_latest_quote(self, symbol: str) -> Dict[str, Any]:
        """Get latest quote for a symbol"""
        try:
            request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quotes = self.data_client.get_stock_latest_quote(request)
            quote = quotes[symbol]

            return {
                "symbol": symbol,
                "bid_price": float(quote.bid_price),
                "ask_price": float(quote.ask_price),
                "bid_size": int(quote.bid_size),
                "ask_size": int(quote.ask_size),
                "timestamp": quote.timestamp
            }
        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {e}")
            raise

    def get_bars(
        self,
        symbol: str,
        timeframe: str = "1Min",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get historical bars for a symbol

        Args:
            symbol: Stock symbol
            timeframe: Timeframe (1Min, 5Min, 15Min, 1Hour, 1Day)
            limit: Number of bars to fetch

        Returns:
            List of bar data dictionaries
        """
        try:
            # Map timeframe string to TimeFrame enum
            timeframe_map = {
                "1Min": TimeFrame.Minute,
                "5Min": TimeFrame(5, "Min"),
                "15Min": TimeFrame(15, "Min"),
                "1Hour": TimeFrame.Hour,
                "1Day": TimeFrame.Day
            }

            tf = timeframe_map.get(timeframe, TimeFrame.Minute)

            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=tf,
                limit=limit
            )

            bars = self.data_client.get_stock_bars(request)
            result = []

            for bar in bars[symbol]:
                result.append({
                    "timestamp": bar.timestamp,
                    "open": float(bar.open),
                    "high": float(bar.high),
                    "low": float(bar.low),
                    "close": float(bar.close),
                    "volume": int(bar.volume)
                })

            return result
        except Exception as e:
            logger.error(f"Error fetching bars for {symbol}: {e}")
            raise

    def is_market_open(self) -> bool:
        """Check if market is currently open"""
        try:
            clock = self.trading_client.get_clock()
            return clock.is_open
        except Exception as e:
            logger.error(f"Error checking market status: {e}")
            return False
