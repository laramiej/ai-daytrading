"""
Risk Management Module
Enforces trading limits and risk controls
"""
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class TradeDecision:
    """Represents a decision on whether to execute a trade"""
    approved: bool
    reason: str
    recommended_quantity: Optional[float] = None
    warnings: List[str] = field(default_factory=list)


@dataclass
class RiskLimits:
    """Risk management limits"""
    max_position_size: float  # Maximum USD per position
    max_daily_loss: float  # Maximum daily loss in USD
    max_total_exposure: float  # Maximum total portfolio exposure
    stop_loss_percentage: float  # Default stop loss %
    take_profit_percentage: float  # Default take profit %
    max_open_positions: int  # Maximum concurrent positions
    enable_short_selling: bool = True  # Allow short selling


class RiskManager:
    """Manages risk and enforces trading limits"""

    def __init__(self, broker, limits: RiskLimits):
        """
        Initialize risk manager

        Args:
            broker: Broker client instance
            limits: Risk limits configuration
        """
        self.broker = broker
        self.limits = limits
        self.daily_pnl = 0.0
        self.daily_trades = []
        self.last_reset_date = datetime.now().date()

    def evaluate_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        estimated_price: float
    ) -> TradeDecision:
        """
        Evaluate if a trade meets risk management criteria

        Args:
            symbol: Stock symbol
            side: 'buy' or 'sell'
            quantity: Number of shares
            estimated_price: Estimated execution price

        Returns:
            TradeDecision with approval status and reasoning
        """
        warnings = []

        # Reset daily tracking if new day
        self._check_daily_reset()

        # Calculate trade value
        trade_value = quantity * estimated_price

        # Check 1: Daily loss limit
        if self.daily_pnl <= -self.limits.max_daily_loss:
            return TradeDecision(
                approved=False,
                reason=f"Daily loss limit reached (${-self.daily_pnl:.2f} / ${self.limits.max_daily_loss:.2f})"
            )

        # Check 2: Position size limit
        if trade_value > self.limits.max_position_size:
            # Calculate reduced quantity
            recommended_qty = self.limits.max_position_size / estimated_price
            warnings.append(
                f"Trade value ${trade_value:.2f} exceeds position limit "
                f"${self.limits.max_position_size:.2f}"
            )

            return TradeDecision(
                approved=False,
                reason="Position size exceeds limit",
                recommended_quantity=recommended_qty,
                warnings=warnings
            )

        # Check 3: Maximum open positions (for buy orders)
        if side.lower() == "buy":
            try:
                positions = self.broker.get_positions()
                if len(positions) >= self.limits.max_open_positions:
                    return TradeDecision(
                        approved=False,
                        reason=f"Maximum open positions reached ({len(positions)} / {self.limits.max_open_positions})"
                    )
            except Exception as e:
                logger.error(f"Error checking positions: {e}")
                return TradeDecision(
                    approved=False,
                    reason="Unable to verify open positions"
                )

        # Check 4: Total exposure limit
        try:
            account = self.broker.get_account_info()
            current_exposure = float(account["portfolio_value"]) - float(account["cash"])

            if side.lower() == "buy":
                new_exposure = current_exposure + trade_value
            else:
                new_exposure = current_exposure - trade_value

            if new_exposure > self.limits.max_total_exposure:
                return TradeDecision(
                    approved=False,
                    reason=f"Total exposure would exceed limit (${new_exposure:.2f} / ${self.limits.max_total_exposure:.2f})"
                )

        except Exception as e:
            logger.error(f"Error checking exposure: {e}")
            warnings.append("Unable to verify total exposure")

        # Check 5: Buying power (for buy orders)
        if side.lower() == "buy":
            try:
                account = self.broker.get_account_info()
                buying_power = float(account["buying_power"])

                if trade_value > buying_power:
                    return TradeDecision(
                        approved=False,
                        reason=f"Insufficient buying power (${buying_power:.2f} available, ${trade_value:.2f} needed)"
                    )
            except Exception as e:
                logger.error(f"Error checking buying power: {e}")
                return TradeDecision(
                    approved=False,
                    reason="Unable to verify buying power"
                )

        # Check 6: Handle SELL orders (existing position or short sell)
        if side.lower() == "sell":
            try:
                positions = self.broker.get_positions()
                position = next((p for p in positions if p.symbol == symbol), None)

                if position:
                    # Selling existing position (closing long)
                    if position.quantity < quantity:
                        return TradeDecision(
                            approved=False,
                            reason=f"Insufficient shares (have {position.quantity}, trying to sell {quantity})"
                        )
                    logger.info(f"SELL order for {symbol}: Closing existing long position")
                else:
                    # No position - this would be a short sell
                    if not self.limits.enable_short_selling:
                        return TradeDecision(
                            approved=False,
                            reason=f"Short selling disabled. No position found for {symbol}"
                        )
                    # Short selling is enabled
                    logger.info(f"SELL order for {symbol}: Opening short position")
                    warnings.append("⚠️  SHORT SELL - Selling stock you don't own")

            except Exception as e:
                logger.error(f"Error checking position: {e}")
                return TradeDecision(
                    approved=False,
                    reason="Unable to verify position"
                )

        # All checks passed
        return TradeDecision(
            approved=True,
            reason="Trade approved - all risk checks passed",
            recommended_quantity=quantity,
            warnings=warnings
        )

    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss_price: float,
        risk_percentage: float = 1.0
    ) -> Tuple[float, str]:
        """
        Calculate appropriate position size based on risk

        Args:
            symbol: Stock symbol
            entry_price: Intended entry price
            stop_loss_price: Stop loss price
            risk_percentage: Percentage of account to risk (default 1%)

        Returns:
            Tuple of (quantity, explanation)
        """
        try:
            account = self.broker.get_account_info()
            account_value = float(account["portfolio_value"])

            # Calculate risk amount
            risk_amount = account_value * (risk_percentage / 100)

            # Calculate price risk per share
            price_risk = abs(entry_price - stop_loss_price)

            if price_risk == 0:
                return 0, "Invalid stop loss (same as entry price)"

            # Calculate position size
            quantity = risk_amount / price_risk

            # Limit by max position size
            max_shares = self.limits.max_position_size / entry_price
            if quantity > max_shares:
                quantity = max_shares
                explanation = f"Limited by max position size (${self.limits.max_position_size})"
            else:
                explanation = f"Risking {risk_percentage}% of account (${risk_amount:.2f})"

            return round(quantity, 0), explanation

        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0, f"Error: {str(e)}"

    def update_daily_pnl(self, pnl: float):
        """
        Update daily P&L tracking

        Args:
            pnl: Profit/loss amount to add
        """
        self._check_daily_reset()
        self.daily_pnl += pnl

        logger.info(f"Daily P&L updated: ${self.daily_pnl:.2f}")

        if self.daily_pnl <= -self.limits.max_daily_loss:
            logger.warning(
                f"DAILY LOSS LIMIT REACHED: ${-self.daily_pnl:.2f} / "
                f"${self.limits.max_daily_loss:.2f}"
            )

    def record_trade(self, symbol: str, side: str, quantity: float, price: float):
        """
        Record a trade for tracking

        Args:
            symbol: Stock symbol
            side: 'buy' or 'sell'
            quantity: Number of shares
            price: Execution price
        """
        self._check_daily_reset()

        trade = {
            "timestamp": datetime.now(),
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "value": quantity * price
        }

        self.daily_trades.append(trade)
        logger.info(f"Trade recorded: {side.upper()} {quantity} {symbol} @ ${price:.2f}")

    def get_daily_stats(self) -> Dict[str, Any]:
        """Get daily trading statistics"""
        self._check_daily_reset()

        return {
            "date": self.last_reset_date.isoformat(),
            "pnl": self.daily_pnl,
            "trades_count": len(self.daily_trades),
            "remaining_loss_capacity": max(0, self.limits.max_daily_loss + self.daily_pnl),
            "loss_limit_reached": self.daily_pnl <= -self.limits.max_daily_loss
        }

    def _check_daily_reset(self):
        """Reset daily tracking if it's a new day"""
        today = datetime.now().date()

        if today > self.last_reset_date:
            logger.info(f"Resetting daily tracking for {today}")
            self.daily_pnl = 0.0
            self.daily_trades = []
            self.last_reset_date = today

    def get_current_risk_status(self) -> Dict[str, Any]:
        """Get current risk status and limits"""
        try:
            positions = self.broker.get_positions()
            account = self.broker.get_account_info()

            current_exposure = float(account["portfolio_value"]) - float(account["cash"])

            return {
                "open_positions": len(positions),
                "max_positions": self.limits.max_open_positions,
                "current_exposure": current_exposure,
                "max_exposure": self.limits.max_total_exposure,
                "daily_pnl": self.daily_pnl,
                "daily_loss_limit": self.limits.max_daily_loss,
                "loss_limit_reached": self.daily_pnl <= -self.limits.max_daily_loss,
                "buying_power": float(account["buying_power"]),
                "portfolio_value": float(account["portfolio_value"])
            }

        except Exception as e:
            logger.error(f"Error getting risk status: {e}")
            return {"error": str(e)}
