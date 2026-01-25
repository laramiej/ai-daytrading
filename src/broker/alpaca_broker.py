"""
Alpaca Broker Integration
Handles all interactions with Alpaca trading API
"""
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, TakeProfitRequest, StopLossRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
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
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None


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
                # Alpaca returns negative qty for short positions, but we use the 'side' field
                # to track long/short. Always store positive quantity for consistency.
                quantity = abs(float(pos.qty))
                pnl = float(pos.unrealized_pl)
                pnl_percent = float(pos.unrealized_plpc) * 100

                # Get the side value - Alpaca returns an enum, we need the string value
                raw_side = pos.side
                if hasattr(raw_side, 'value'):
                    side_value = raw_side.value
                else:
                    side_value = str(raw_side)
                # Ensure it's lowercase for consistent comparison
                side_value = side_value.lower()
                logger.debug(f"Position {pos.symbol}: raw_side={raw_side}, type={type(raw_side)}, side_value={side_value}")

                result.append(Position(
                    symbol=pos.symbol,
                    quantity=quantity,
                    entry_price=entry_price,
                    current_price=current_price,
                    pnl=pnl,
                    pnl_percent=pnl_percent,
                    side=side_value
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
                    filled_price=float(order.filled_avg_price) if order.filled_avg_price else None,
                    limit_price=float(order.limit_price) if order.limit_price else None,
                    stop_price=float(order.stop_price) if order.stop_price else None
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

    def place_bracket_order(
        self,
        symbol: str,
        quantity: float,
        side: str,
        take_profit_price: Optional[float] = None,
        stop_loss_price: Optional[float] = None
    ) -> Order:
        """
        Place a bracket order with optional take-profit and stop-loss

        A bracket order enters a position and automatically places protective
        exit orders. When one exit order fills, the other is canceled.

        Args:
            symbol: Stock symbol
            quantity: Number of shares
            side: 'buy' or 'sell'
            take_profit_price: Limit price for take-profit exit (optional)
            stop_loss_price: Stop price for stop-loss exit (optional)

        Returns:
            Order object for the entry order
        """
        try:
            order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL

            # Build the order request based on what's provided
            if take_profit_price and stop_loss_price:
                # Full bracket order with both legs
                request = MarketOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=order_side,
                    time_in_force=TimeInForce.DAY,
                    order_class=OrderClass.BRACKET,
                    take_profit=TakeProfitRequest(limit_price=take_profit_price),
                    stop_loss=StopLossRequest(stop_price=stop_loss_price)
                )
                order_type_desc = "bracket"
            elif stop_loss_price:
                # OTO order with just stop-loss
                request = MarketOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=order_side,
                    time_in_force=TimeInForce.DAY,
                    order_class=OrderClass.OTO,
                    stop_loss=StopLossRequest(stop_price=stop_loss_price)
                )
                order_type_desc = "OTO (stop-loss only)"
            elif take_profit_price:
                # OTO order with just take-profit
                request = MarketOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=order_side,
                    time_in_force=TimeInForce.DAY,
                    order_class=OrderClass.OTO,
                    take_profit=TakeProfitRequest(limit_price=take_profit_price)
                )
                order_type_desc = "OTO (take-profit only)"
            else:
                # No protective orders, just a regular market order
                request = MarketOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=order_side,
                    time_in_force=TimeInForce.DAY
                )
                order_type_desc = "market"

            order = self.trading_client.submit_order(request)

            # Log the order details
            log_parts = [f"{order_type_desc.upper()} order placed: {side.upper()} {quantity} shares of {symbol}"]
            if take_profit_price:
                log_parts.append(f"TP: ${take_profit_price:.2f}")
            if stop_loss_price:
                log_parts.append(f"SL: ${stop_loss_price:.2f}")
            logger.info(" | ".join(log_parts))

            return Order(
                order_id=order.id,
                symbol=order.symbol,
                quantity=float(order.qty),
                side=order.side.value,
                order_type=order.type.value,
                status=order.status.value
            )
        except Exception as e:
            logger.error(f"Error placing bracket order: {e}")
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

    def cancel_orders_for_symbol(self, symbol: str) -> int:
        """
        Cancel all open orders for a specific symbol.
        This is useful when closing a position that has bracket orders attached.

        Args:
            symbol: Stock symbol

        Returns:
            Number of orders cancelled
        """
        try:
            orders = self.get_open_orders()
            symbol_orders = [o for o in orders if o.symbol == symbol]

            cancelled_count = 0
            for order in symbol_orders:
                if self.cancel_order(order.order_id):
                    cancelled_count += 1

            if cancelled_count > 0:
                logger.info(f"Cancelled {cancelled_count} orders for {symbol}")

            return cancelled_count
        except Exception as e:
            logger.error(f"Error cancelling orders for {symbol}: {e}")
            return 0

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
            from datetime import timezone

            # Map timeframe string to TimeFrame enum
            timeframe_map = {
                "1Min": TimeFrame.Minute,
                "5Min": TimeFrame(5, "Min"),
                "15Min": TimeFrame(15, "Min"),
                "1Hour": TimeFrame.Hour,
                "1Day": TimeFrame.Day
            }

            tf = timeframe_map.get(timeframe, TimeFrame.Minute)

            # Calculate start time to ensure we have a valid request range
            # For intraday, go back a few hours; for daily, go back a few days
            if timeframe == "1Day":
                start = datetime.now(timezone.utc) - timedelta(days=limit + 5)
            else:
                # For minute bars, go back enough time to get the requested limit
                minutes_back = limit * 2  # Extra buffer
                if timeframe == "5Min":
                    minutes_back = limit * 5 * 2
                elif timeframe == "15Min":
                    minutes_back = limit * 15 * 2
                elif timeframe == "1Hour":
                    minutes_back = limit * 60 * 2
                start = datetime.now(timezone.utc) - timedelta(minutes=minutes_back)

            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=tf,
                start=start,
                limit=limit
            )

            bars = self.data_client.get_stock_bars(request)
            result = []

            # Handle case where bars is None or empty
            if bars is None:
                logger.warning(f"No bar data returned for {symbol}")
                return result

            # The response is a dict-like object, check if symbol exists
            # Use data attribute if it exists (newer SDK versions)
            bars_data = bars.data if hasattr(bars, 'data') else bars

            if bars_data is None:
                logger.warning(f"No bar data for {symbol} (bars.data is None)")
                return result

            # Check if symbol exists in the response
            if hasattr(bars_data, 'get'):
                symbol_bars = bars_data.get(symbol)
            elif hasattr(bars_data, '__getitem__') and symbol in bars_data:
                symbol_bars = bars_data[symbol]
            else:
                symbol_bars = None

            if symbol_bars is None:
                logger.warning(f"No bar data for symbol {symbol} in response")
                return result

            for bar in symbol_bars:
                result.append({
                    "timestamp": bar.timestamp,
                    "open": float(bar.open),
                    "high": float(bar.high),
                    "low": float(bar.low),
                    "close": float(bar.close),
                    "volume": int(bar.volume)
                })

            return result
        except AttributeError as e:
            # Handle cases where Alpaca SDK receives None response
            # This can happen right at market open when there's no data yet
            if "'NoneType' object has no attribute" in str(e):
                logger.warning(f"No bar data available for {symbol} yet (market may have just opened)")
                return []
            logger.error(f"Error fetching bars for {symbol}: {e}")
            raise
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

    def get_minutes_until_close(self) -> Optional[int]:
        """
        Get the number of minutes until market close.

        Returns:
            Minutes until close, or None if market is closed or error
        """
        try:
            clock = self.trading_client.get_clock()
            if not clock.is_open:
                return None

            # Calculate minutes until close
            now = clock.timestamp
            close_time = clock.next_close
            delta = close_time - now
            minutes = int(delta.total_seconds() / 60)
            return max(0, minutes)
        except Exception as e:
            logger.error(f"Error getting minutes until close: {e}")
            return None

    def cancel_all_orders(self) -> int:
        """
        Cancel ALL open orders across all symbols.

        Returns:
            Number of orders cancelled
        """
        try:
            orders = self.get_open_orders()
            if not orders:
                logger.info("No open orders to cancel")
                return 0

            cancelled_count = 0
            for order in orders:
                if self.cancel_order(order.order_id):
                    cancelled_count += 1

            logger.info(f"Cancelled {cancelled_count} orders total")
            return cancelled_count
        except Exception as e:
            logger.error(f"Error cancelling all orders: {e}")
            return 0

    def close_all_positions(self) -> List[Dict[str, Any]]:
        """
        Close all open positions by placing market orders.
        This is used for end-of-session liquidation.

        Returns:
            List of dictionaries with position close results
        """
        import time

        results = []
        try:
            positions = self.get_positions()

            if not positions:
                logger.info("No open positions to close")
                return results

            logger.info(f"Closing {len(positions)} open positions")

            # First, cancel ALL open orders to free up held shares
            total_cancelled = self.cancel_all_orders()
            if total_cancelled > 0:
                logger.info(f"Cancelled {total_cancelled} orders before closing positions - waiting for settlement")
                # Wait for order cancellations to fully settle
                time.sleep(2.0)

            # Re-fetch positions after cancellation (quantities may have changed)
            positions = self.get_positions()

            for position in positions:
                max_retries = 3
                retry_delay = 1.0

                for attempt in range(max_retries):
                    try:
                        # Determine the side to close the position
                        # Long positions are closed with SELL, short positions with BUY
                        close_side = "sell" if position.side == "long" else "buy"

                        order = self.place_market_order(
                            symbol=position.symbol,
                            quantity=position.quantity,
                            side=close_side
                        )

                        results.append({
                            "symbol": position.symbol,
                            "quantity": position.quantity,
                            "side": close_side,
                            "position_side": position.side,
                            "entry_price": position.entry_price,
                            "close_price": position.current_price,
                            "pnl": position.pnl,
                            "order_id": order.order_id,
                            "status": "closed"
                        })

                        logger.info(
                            f"Closed {position.side} position: {position.symbol} "
                            f"({position.quantity} shares) - P&L: ${position.pnl:.2f}"
                        )
                        break  # Success, exit retry loop

                    except Exception as e:
                        error_msg = str(e)
                        if "insufficient qty" in error_msg.lower() and attempt < max_retries - 1:
                            # Shares still held - cancel any remaining orders and retry
                            logger.warning(f"Insufficient qty for {position.symbol}, cancelling orders and retrying (attempt {attempt + 1}/{max_retries})")
                            self.cancel_orders_for_symbol(position.symbol)
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                        else:
                            logger.error(f"Error closing position for {position.symbol}: {e}")
                            results.append({
                                "symbol": position.symbol,
                                "quantity": position.quantity,
                                "position_side": position.side,
                                "status": "error",
                                "error": str(e)
                            })
                            break  # Give up on this position

            return results

        except Exception as e:
            logger.error(f"Error closing all positions: {e}")
            raise
