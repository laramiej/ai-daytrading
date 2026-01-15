"""
Portfolio Context Module
Provides portfolio awareness to the trading strategy
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class TradeHistory:
    """Historical trade record"""
    timestamp: datetime
    symbol: str
    side: str
    quantity: float
    price: float
    pnl: Optional[float] = None
    signal_confidence: Optional[float] = None
    llm_provider: Optional[str] = None


class PortfolioContext:
    """Manages portfolio context for AI-aware trading"""

    def __init__(self, broker, risk_manager):
        """
        Initialize portfolio context

        Args:
            broker: Broker client instance
            risk_manager: Risk manager instance
        """
        self.broker = broker
        self.risk_manager = risk_manager
        self.trade_history: List[TradeHistory] = []
        self.symbol_performance: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "total_pnl": 0.0,
            "avg_confidence": 0.0
        })

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive portfolio summary

        Returns:
            Dictionary with portfolio data
        """
        try:
            account = self.broker.get_account_info()
            positions = self.broker.get_positions()

            # Calculate portfolio metrics
            total_value = float(account["portfolio_value"])
            cash = float(account["cash"])
            equity = float(account["equity"])
            invested = total_value - cash

            # Position details
            position_details = []
            for pos in positions:
                position_details.append({
                    "symbol": pos.symbol,
                    "quantity": pos.quantity,
                    "entry_price": pos.entry_price,
                    "current_price": pos.current_price,
                    "value": pos.quantity * pos.current_price,
                    "pnl": pos.pnl,
                    "pnl_percent": pos.pnl_percent,
                    "side": pos.side
                })

            # Risk metrics
            risk_status = self.risk_manager.get_current_risk_status()

            summary = {
                "account": {
                    "total_value": total_value,
                    "cash": cash,
                    "equity": equity,
                    "invested": invested,
                    "invested_percent": (invested / total_value * 100) if total_value > 0 else 0
                },
                "positions": {
                    "count": len(positions),
                    "max_allowed": self.risk_manager.limits.max_open_positions,
                    "positions_available": self.risk_manager.limits.max_open_positions - len(positions),
                    "details": position_details
                },
                "risk": {
                    "daily_pnl": risk_status.get("daily_pnl", 0),
                    "daily_loss_limit": risk_status.get("daily_loss_limit", 0),
                    "loss_limit_reached": risk_status.get("loss_limit_reached", False),
                    "current_exposure": risk_status.get("current_exposure", 0),
                    "max_exposure": risk_status.get("max_exposure", 0),
                    "exposure_percent": (risk_status.get("current_exposure", 0) / risk_status.get("max_exposure", 1) * 100)
                },
                "performance": self._calculate_performance_metrics()
            }

            return summary

        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return {}

    def has_position(self, symbol: str) -> bool:
        """Check if we have an open position in a symbol"""
        try:
            positions = self.broker.get_positions()
            return any(p.symbol == symbol for p in positions)
        except Exception as e:
            logger.error(f"Error checking position for {symbol}: {e}")
            return False

    def get_position_details(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get details for a specific position"""
        try:
            positions = self.broker.get_positions()
            position = next((p for p in positions if p.symbol == symbol), None)

            if not position:
                return None

            return {
                "symbol": position.symbol,
                "quantity": position.quantity,
                "entry_price": position.entry_price,
                "current_price": position.current_price,
                "value": position.quantity * position.current_price,
                "pnl": position.pnl,
                "pnl_percent": position.pnl_percent,
                "side": position.side
            }

        except Exception as e:
            logger.error(f"Error getting position details for {symbol}: {e}")
            return None

    def record_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        signal_confidence: Optional[float] = None,
        llm_provider: Optional[str] = None
    ):
        """
        Record a trade for history tracking

        Args:
            symbol: Stock symbol
            side: 'buy' or 'sell'
            quantity: Number of shares
            price: Execution price
            signal_confidence: AI confidence score
            llm_provider: Which LLM generated the signal
        """
        trade = TradeHistory(
            timestamp=datetime.now(),
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            signal_confidence=signal_confidence,
            llm_provider=llm_provider
        )

        self.trade_history.append(trade)

        # Update symbol performance tracking
        if side.lower() == "sell":
            # Calculate P&L for this trade
            position = self.get_position_details(symbol)
            if position:
                pnl = position["pnl"]
                trade.pnl = pnl

                perf = self.symbol_performance[symbol]
                perf["total_trades"] += 1
                perf["total_pnl"] += pnl

                if pnl > 0:
                    perf["wins"] += 1
                else:
                    perf["losses"] += 1

                if signal_confidence:
                    # Update average confidence
                    perf["avg_confidence"] = (
                        (perf["avg_confidence"] * (perf["total_trades"] - 1) + signal_confidence)
                        / perf["total_trades"]
                    )

        logger.info(f"Recorded trade: {side.upper()} {quantity} {symbol} @ ${price:.2f}")

    def get_symbol_history(self, symbol: str) -> Dict[str, Any]:
        """
        Get trading history and performance for a specific symbol

        Args:
            symbol: Stock symbol

        Returns:
            Dictionary with symbol trading history
        """
        symbol_trades = [t for t in self.trade_history if t.symbol == symbol]
        perf = self.symbol_performance.get(symbol, {})

        return {
            "symbol": symbol,
            "total_trades": len(symbol_trades),
            "recent_trades": symbol_trades[-5:],  # Last 5 trades
            "performance": perf,
            "currently_holding": self.has_position(symbol)
        }

    def get_trade_recommendations(self, symbol: str) -> Dict[str, Any]:
        """
        Get AI-ready recommendations based on portfolio context

        Args:
            symbol: Stock symbol

        Returns:
            Dictionary with context-aware recommendations
        """
        recommendations = {
            "can_buy": True,
            "can_sell": True,  # Now always True (can close long OR open short)
            "reasons": [],
            "considerations": []
        }

        # Check if we already have a position
        has_position = self.has_position(symbol)
        position_details = self.get_position_details(symbol) if has_position else None

        if has_position:
            recommendations["reasons"].append(
                f"Currently holding {position_details['quantity']} shares"
            )

            if position_details["pnl_percent"] > 0:
                recommendations["considerations"].append(
                    f"Position is profitable: +{position_details['pnl_percent']:.2f}%"
                )
            else:
                recommendations["considerations"].append(
                    f"Position is at loss: {position_details['pnl_percent']:.2f}%"
                )
        else:
            # No position - can short sell if enabled
            if self.risk_manager.limits.enable_short_selling:
                recommendations["considerations"].append(
                    "No position held - SELL would be a short sale"
                )

        # Check position limits
        try:
            positions = self.broker.get_positions()
            if len(positions) >= self.risk_manager.limits.max_open_positions:
                recommendations["can_buy"] = False
                recommendations["reasons"].append(
                    f"Maximum positions reached ({len(positions)}/{self.risk_manager.limits.max_open_positions})"
                )
        except Exception as e:
            logger.error(f"Error checking position limits: {e}")

        # Check daily loss limit
        daily_stats = self.risk_manager.get_daily_stats()
        if daily_stats["loss_limit_reached"]:
            recommendations["can_buy"] = False
            recommendations["can_sell"] = True  # Can still exit positions
            recommendations["reasons"].append("Daily loss limit reached")

        # Add symbol performance history
        symbol_hist = self.get_symbol_history(symbol)
        if symbol_hist["performance"].get("total_trades", 0) > 0:
            perf = symbol_hist["performance"]
            win_rate = (perf["wins"] / perf["total_trades"] * 100) if perf["total_trades"] > 0 else 0

            recommendations["considerations"].append(
                f"Historical win rate: {win_rate:.1f}% ({perf['wins']}/{perf['total_trades']} trades)"
            )

            if perf["total_pnl"] != 0:
                recommendations["considerations"].append(
                    f"Cumulative P&L: ${perf['total_pnl']:.2f}"
                )

        return recommendations

    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate overall trading performance metrics"""
        if not self.trade_history:
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "best_trade": None,
                "worst_trade": None
            }

        completed_trades = [t for t in self.trade_history if t.pnl is not None]

        if not completed_trades:
            return {
                "total_trades": len(self.trade_history),
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "best_trade": None,
                "worst_trade": None
            }

        wins = [t for t in completed_trades if t.pnl > 0]
        losses = [t for t in completed_trades if t.pnl <= 0]

        total_pnl = sum(t.pnl for t in completed_trades)
        win_rate = (len(wins) / len(completed_trades) * 100) if completed_trades else 0

        avg_win = (sum(t.pnl for t in wins) / len(wins)) if wins else 0
        avg_loss = (sum(t.pnl for t in losses) / len(losses)) if losses else 0

        best_trade = max(completed_trades, key=lambda t: t.pnl) if completed_trades else None
        worst_trade = min(completed_trades, key=lambda t: t.pnl) if completed_trades else None

        return {
            "total_trades": len(completed_trades),
            "win_rate": win_rate,
            "wins": len(wins),
            "losses": len(losses),
            "total_pnl": total_pnl,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "best_trade": {
                "symbol": best_trade.symbol,
                "pnl": best_trade.pnl,
                "date": best_trade.timestamp
            } if best_trade else None,
            "worst_trade": {
                "symbol": worst_trade.symbol,
                "pnl": worst_trade.pnl,
                "date": worst_trade.timestamp
            } if worst_trade else None
        }

    def format_portfolio_context(self) -> str:
        """
        Format portfolio context for AI consumption

        Returns:
            Formatted string with portfolio information
        """
        summary = self.get_portfolio_summary()

        if not summary:
            return "Portfolio information unavailable"

        lines = []

        # Account info
        acc = summary["account"]
        lines.append("💰 PORTFOLIO STATUS")
        lines.append(f"Total Value: ${acc['total_value']:,.2f}")
        lines.append(f"Cash: ${acc['cash']:,.2f}")
        lines.append(f"Invested: ${acc['invested']:,.2f} ({acc['invested_percent']:.1f}%)")

        # Positions
        pos = summary["positions"]
        lines.append(f"\n📊 POSITIONS: {pos['count']}/{pos['max_allowed']}")

        if pos["details"]:
            for p in pos["details"]:
                pnl_sign = "+" if p["pnl"] >= 0 else ""
                lines.append(
                    f"  • {p['symbol']}: {p['quantity']} shares @ ${p['entry_price']:.2f} "
                    f"({pnl_sign}{p['pnl_percent']:.2f}%)"
                )
        else:
            lines.append("  • No open positions")

        # Risk status
        risk = summary["risk"]
        lines.append(f"\n🛡️  RISK STATUS")
        lines.append(f"Daily P&L: ${risk['daily_pnl']:.2f}")
        lines.append(f"Exposure: ${risk['current_exposure']:,.2f}/{risk['max_exposure']:,.2f} ({risk['exposure_percent']:.1f}%)")

        if risk["loss_limit_reached"]:
            lines.append("⚠️  Daily loss limit REACHED")

        # Performance
        perf = summary["performance"]
        if perf["total_trades"] > 0:
            lines.append(f"\n📈 PERFORMANCE")
            lines.append(f"Total Trades: {perf['total_trades']}")
            lines.append(f"Win Rate: {perf['win_rate']:.1f}% ({perf['wins']}W/{perf['losses']}L)")
            lines.append(f"Total P&L: ${perf['total_pnl']:.2f}")

        return "\n".join(lines)
