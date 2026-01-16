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
    max_position_exposure_percent: float = 25.0  # Max % of total exposure per position


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
            logger.warning(f"TRADE BLOCKED [{symbol}]: Daily loss limit reached (${-self.daily_pnl:.2f} / ${self.limits.max_daily_loss:.2f})")
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
            logger.warning(f"TRADE BLOCKED [{symbol}]: Position size ${trade_value:.2f} exceeds limit ${self.limits.max_position_size:.2f}")
            return TradeDecision(
                approved=False,
                reason="Position size exceeds limit",
                recommended_quantity=recommended_qty,
                warnings=warnings
            )

        # Fetch positions once for multiple checks
        try:
            positions = self.broker.get_positions()
            existing_position = next((p for p in positions if p.symbol == symbol), None)
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return TradeDecision(
                approved=False,
                reason="Unable to verify open positions"
            )

        # Check 3: Maximum open positions (for new positions only)
        # Determine position side if we have an existing position
        existing_side = None
        if existing_position:
            existing_side = existing_position.side.lower() if hasattr(existing_position.side, 'lower') else str(existing_position.side).lower()

        # A position is "new" only if it opens a fresh position, not if it closes an existing one
        # BUY + no position = new long
        # BUY + short position = closing short (NOT new)
        # BUY + long position = adding to long (NOT new, just increasing)
        # SELL + no position = new short
        # SELL + long position = closing long (NOT new)
        # SELL + short position = adding to short (NOT new, just increasing)
        is_new_position = (
            (side.lower() == "buy" and not existing_position) or
            (side.lower() == "sell" and not existing_position)
        )
        if is_new_position:
            if len(positions) >= self.limits.max_open_positions:
                logger.warning(f"TRADE BLOCKED [{symbol}]: Maximum open positions reached ({len(positions)} / {self.limits.max_open_positions})")
                return TradeDecision(
                    approved=False,
                    reason=f"Maximum open positions reached ({len(positions)} / {self.limits.max_open_positions})"
                )

        # Check 4: Total exposure limit (only for new positions that increase exposure)
        try:
            account = self.broker.get_account_info()
            current_exposure = float(account["portfolio_value"]) - float(account["cash"])

            # Determine if this trade increases exposure
            # Key insight: CLOSING any position (long or short) REDUCES exposure
            if side.lower() == "buy" and existing_side == "short":
                # Buying to cover an existing SHORT position REDUCES exposure
                new_exposure = current_exposure - trade_value
                increases_exposure = False
                logger.info(f"BUY to cover SHORT for {symbol} - reduces exposure")
            elif side.lower() == "buy":
                # Opening new long or adding to long increases exposure
                new_exposure = current_exposure + trade_value
                increases_exposure = True
            elif side.lower() == "sell" and existing_side == "long":
                # Selling an existing LONG position REDUCES exposure
                new_exposure = current_exposure - trade_value
                increases_exposure = False
                logger.info(f"SELL to close LONG for {symbol} - reduces exposure")
            elif side.lower() == "sell" and existing_side == "short":
                # Adding to existing SHORT position increases exposure
                new_exposure = current_exposure + trade_value
                increases_exposure = True
            else:
                # Opening a new short position increases exposure (liability)
                new_exposure = current_exposure + trade_value
                increases_exposure = True

            # Only block if exposure would increase beyond limit
            if increases_exposure and new_exposure > self.limits.max_total_exposure:
                logger.warning(f"TRADE BLOCKED [{symbol}]: Total exposure would exceed limit (${new_exposure:.2f} / ${self.limits.max_total_exposure:.2f})")
                return TradeDecision(
                    approved=False,
                    reason=f"Total exposure would exceed limit (${new_exposure:.2f} / ${self.limits.max_total_exposure:.2f})"
                )

        except Exception as e:
            logger.error(f"Error checking exposure: {e}")
            warnings.append("Unable to verify total exposure")

        # Check 5: Buying power (for buy orders and new short positions)
        # Short selling also requires margin/buying power
        if is_new_position:
            try:
                account = self.broker.get_account_info()
                buying_power = float(account["buying_power"])

                if trade_value > buying_power:
                    is_short = side.lower() == "sell"
                    action_type = "short sell" if is_short else "buy"
                    logger.warning(f"TRADE BLOCKED [{symbol}]: Insufficient buying power for {action_type} (${buying_power:.2f} available, ${trade_value:.2f} needed)")
                    return TradeDecision(
                        approved=False,
                        reason=f"Insufficient buying power for {action_type} (${buying_power:.2f} available, ${trade_value:.2f} needed)"
                    )
            except Exception as e:
                logger.error(f"Error checking buying power: {e}")
                return TradeDecision(
                    approved=False,
                    reason="Unable to verify buying power"
                )

        # Check 6: Handle BUY orders that close SHORT positions
        if side.lower() == "buy" and existing_side == "short":
            # Buying to cover a short position
            if existing_position.quantity < quantity:
                logger.warning(f"TRADE BLOCKED [{symbol}]: Cannot buy more than short position (short {existing_position.quantity}, trying to buy {quantity})")
                return TradeDecision(
                    approved=False,
                    reason=f"Cannot buy more than short position (short {existing_position.quantity}, trying to buy {quantity})"
                )
            logger.info(f"BUY order for {symbol}: Closing existing SHORT position (buy to cover {quantity} shares)")

        # Check 7: Handle SELL orders (existing position or short sell)
        if side.lower() == "sell":
            if existing_position and existing_side == "long":
                # Selling existing LONG position (closing long)
                if existing_position.quantity < quantity:
                    logger.warning(f"TRADE BLOCKED [{symbol}]: Insufficient shares (have {existing_position.quantity}, trying to sell {quantity})")
                    return TradeDecision(
                        approved=False,
                        reason=f"Insufficient shares (have {existing_position.quantity}, trying to sell {quantity})"
                    )
                logger.info(f"SELL order for {symbol}: Closing existing LONG position ({existing_position.quantity} shares)")
            elif existing_position and existing_side == "short":
                # Adding to existing SHORT position
                logger.info(f"SELL order for {symbol}: Adding to existing SHORT position ({quantity} shares)")
            else:
                # No position - this would be a new short sell
                if not self.limits.enable_short_selling:
                    logger.warning(f"TRADE BLOCKED [{symbol}]: Short selling disabled. No position found for {symbol}")
                    return TradeDecision(
                        approved=False,
                        reason=f"Short selling disabled. No position found for {symbol}"
                    )
                # Short selling is enabled
                logger.info(f"SELL order for {symbol}: Opening new SHORT position ({quantity} shares)")
                warnings.append("⚠️  SHORT SELL - Selling stock you don't own")

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

    def calculate_dynamic_position_size(
        self,
        symbol: str,
        price: float,
        base_quantity: float
    ) -> Tuple[float, float, str]:
        """
        Calculate position size using dynamic allocation based on remaining exposure budget.

        This ensures each new position gets a fair share of remaining exposure capacity,
        preventing early trades from consuming all available budget.

        Args:
            symbol: Stock symbol
            price: Current/estimated price per share
            base_quantity: Initially calculated quantity (before dynamic limits)

        Returns:
            Tuple of (final_quantity, position_value, explanation)
        """
        try:
            account = self.broker.get_account_info()
            positions = self.broker.get_positions()

            # Calculate current exposure
            current_exposure = float(account["portfolio_value"]) - float(account["cash"])

            # Calculate remaining budget and slots
            remaining_exposure = max(0, self.limits.max_total_exposure - current_exposure)
            current_position_count = len(positions)
            remaining_slots = max(1, self.limits.max_open_positions - current_position_count)

            # Calculate the limits
            base_value = base_quantity * price

            # Limit 1: Hard dollar cap per position
            max_position_cap = self.limits.max_position_size

            # Limit 2: Percentage of max exposure cap (e.g., 25% of $50k = $12.5k)
            percent_cap = self.limits.max_total_exposure * (self.limits.max_position_exposure_percent / 100)

            # Limit 3: Fair share of remaining exposure (dynamic allocation)
            fair_share = remaining_exposure / remaining_slots

            # Take the minimum of all limits
            max_allowed_value = min(base_value, max_position_cap, percent_cap, fair_share)

            # Calculate final quantity
            final_quantity = max(0, int(max_allowed_value / price))
            final_value = final_quantity * price

            # Build explanation
            limiting_factor = "base calculation"
            if max_allowed_value == max_position_cap and max_position_cap < base_value:
                limiting_factor = f"max position size (${max_position_cap:,.0f})"
            elif max_allowed_value == percent_cap and percent_cap < base_value:
                limiting_factor = f"max {self.limits.max_position_exposure_percent:.0f}% exposure per position (${percent_cap:,.0f})"
            elif max_allowed_value == fair_share and fair_share < base_value:
                limiting_factor = f"fair share allocation (${fair_share:,.0f} for {remaining_slots} remaining slots)"

            explanation = (
                f"Position sized by {limiting_factor}. "
                f"Remaining exposure: ${remaining_exposure:,.0f}, "
                f"Open slots: {remaining_slots}/{self.limits.max_open_positions}"
            )

            logger.info(f"Dynamic position size for {symbol}: {final_quantity} shares @ ${price:.2f} = ${final_value:,.2f}")
            logger.info(f"  Limits - Base: ${base_value:,.0f}, Max: ${max_position_cap:,.0f}, "
                       f"Percent cap: ${percent_cap:,.0f}, Fair share: ${fair_share:,.0f}")

            return final_quantity, final_value, explanation

        except Exception as e:
            logger.error(f"Error calculating dynamic position size: {e}")
            # Fall back to base quantity if something goes wrong
            return base_quantity, base_quantity * price, f"Error in dynamic calc, using base: {str(e)}"

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
