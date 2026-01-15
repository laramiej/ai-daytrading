"""
Trade Approval Workflow
Handles manual approval for trades
"""
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ApprovalWorkflow:
    """Handles trade approval workflow"""

    def __init__(self, auto_approve: bool = False):
        """
        Initialize approval workflow

        Args:
            auto_approve: If True, automatically approve all trades (USE WITH CAUTION)
        """
        self.auto_approve = auto_approve
        self.pending_approvals = []

        if auto_approve:
            logger.warning(
                "⚠️  AUTO-APPROVAL ENABLED - All trades will execute automatically!"
            )

    def request_approval(
        self,
        signal,
        risk_decision,
        estimated_cost: float
    ) -> bool:
        """
        Request approval for a trade

        Args:
            signal: TradingSignal object
            risk_decision: TradeDecision from risk manager
            estimated_cost: Estimated cost of the trade

        Returns:
            True if approved, False otherwise
        """
        if self.auto_approve:
            logger.info(f"Trade auto-approved: {signal.signal} {signal.symbol}")
            return True

        # Display trade details
        print("\n" + "=" * 70)
        print("🤖 AI TRADING RECOMMENDATION")
        print("=" * 70)
        print(f"\nSymbol: {signal.symbol}")
        print(f"Action: {signal.signal}")
        print(f"Confidence: {signal.confidence}%")
        print(f"LLM Provider: {signal.llm_provider}")
        print(f"\nReasoning:")
        print(f"  {signal.reasoning}")

        if signal.entry_price:
            print(f"\nEntry Price: ${signal.entry_price:.2f}")

        if signal.stop_loss:
            print(f"Stop Loss: ${signal.stop_loss:.2f}")

        if signal.take_profit:
            print(f"Take Profit: ${signal.take_profit:.2f}")

        print(f"\nPosition Size: {signal.position_size_recommendation}")
        print(f"Time Horizon: {signal.time_horizon}")

        if signal.risk_factors:
            print(f"\n⚠️  Risk Factors:")
            for factor in signal.risk_factors:
                print(f"  - {factor}")

        print(f"\n💰 Estimated Cost: ${estimated_cost:.2f}")

        # Risk decision
        print(f"\n🛡️  Risk Management:")
        if risk_decision.approved:
            print(f"  ✅ {risk_decision.reason}")
        else:
            print(f"  ❌ {risk_decision.reason}")
            if risk_decision.recommended_quantity:
                print(f"  Recommended Quantity: {risk_decision.recommended_quantity}")

        if risk_decision.warnings:
            print(f"\n  Warnings:")
            for warning in risk_decision.warnings:
                print(f"    - {warning}")

        # Only ask for approval if risk checks passed
        if not risk_decision.approved:
            print("\n❌ Trade blocked by risk management")
            print("=" * 70)
            return False

        # Request user input
        print("\n" + "=" * 70)
        response = input("Approve this trade? (yes/no): ").strip().lower()

        approved = response in ["yes", "y"]

        if approved:
            print("✅ Trade approved by user")
        else:
            print("❌ Trade rejected by user")

        print("=" * 70 + "\n")

        return approved

    def get_quantity_approval(
        self,
        symbol: str,
        side: str,
        recommended_quantity: float,
        price: float
    ) -> Optional[float]:
        """
        Get quantity approval from user

        Args:
            symbol: Stock symbol
            side: 'buy' or 'sell'
            recommended_quantity: AI recommended quantity
            price: Current price

        Returns:
            Approved quantity or None if rejected
        """
        if self.auto_approve:
            return recommended_quantity

        print(f"\n📊 Position Sizing for {symbol}")
        print(f"Recommended Quantity: {recommended_quantity} shares")
        print(f"Estimated Cost: ${recommended_quantity * price:.2f}")
        print(f"Action: {side.upper()}")

        response = input(
            f"\nEnter quantity (or press Enter for {recommended_quantity}, 'n' to skip): "
        ).strip()

        if response.lower() in ["n", "no", "skip"]:
            return None

        if not response:
            return recommended_quantity

        try:
            quantity = float(response)
            if quantity <= 0:
                print("❌ Invalid quantity")
                return None
            return quantity
        except ValueError:
            print("❌ Invalid input")
            return None
