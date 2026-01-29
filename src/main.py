"""
AI Day Trading System - Main Application
"""
import logging
import sys
import time
from typing import Optional, List
from datetime import datetime

from llm import LLMFactory
from broker import AlpacaBroker
from strategy import MarketAnalyzer, TradingStrategy
from strategy.portfolio_context import PortfolioContext
from risk import RiskManager, RiskLimits
from utils import load_settings, ApprovalWorkflow
from reports.daily_report import DailyReportManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/trading.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class DayTradingBot:
    """Main day trading bot application"""

    def __init__(self):
        """Initialize the trading bot"""
        logger.info("Initializing AI Day Trading Bot...")

        # Load configuration
        self.settings = load_settings()

        # Initialize broker
        self.broker = AlpacaBroker(
            api_key=self.settings.alpaca_api_key,
            secret_key=self.settings.alpaca_secret_key,
            paper_trading=self.settings.alpaca_paper_trading
        )

        # Initialize LLM provider
        self.llm_provider = self._initialize_llm()

        # Initialize market analyzer
        # Note: Sentiment analysis improved in Phase 2 with Google Trends and Finnhub
        self.market_analyzer = MarketAnalyzer(
            self.broker,
            include_sentiment=True,  # Re-enabled with Phase 2 improvements
            enable_google_trends=self.settings.enable_google_trends,
            finnhub_api_key=self.settings.finnhub_api_key,
            enable_finnhub=self.settings.enable_finnhub
        )

        # Initialize risk manager
        self.risk_manager = RiskManager(
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
        self.portfolio = PortfolioContext(self.broker, self.risk_manager)

        # Auto-disable AI critique/debate for n8n provider (n8n doesn't support separate bull/bear/judge calls)
        enable_critique = getattr(self.settings, 'enable_ai_critique', False)
        if self.settings.default_llm_provider == "n8n" and enable_critique:
            logger.warning("AI critique/debate is not supported with n8n provider - auto-disabling")
            enable_critique = False

        # Initialize trading strategy with portfolio context
        self.strategy = TradingStrategy(
            self.llm_provider,
            self.market_analyzer,
            self.portfolio,  # Pass portfolio context
            enable_critique=enable_critique
        )

        # Initialize approval workflow
        self.approval = ApprovalWorkflow(
            auto_approve=self.settings.enable_auto_trading
        )

        # Initialize daily report manager for session snapshots
        self.daily_report = DailyReportManager(
            broker=self.broker,
            risk_manager=self.risk_manager,
            portfolio=self.portfolio
        )

        logger.info("✅ Bot initialized successfully")

    def start_session(self):
        """Start trading session - capture market open snapshot"""
        logger.info("Starting trading session...")
        snapshot = self.daily_report.capture_snapshot("market_open")
        if snapshot:
            logger.info(f"📸 Market open snapshot captured - Portfolio: ${snapshot.portfolio_value:,.2f}")
        else:
            logger.warning("Failed to capture market open snapshot")
        return snapshot

    def end_session(self):
        """End trading session - capture market close snapshot"""
        logger.info("Ending trading session...")
        snapshot = self.daily_report.capture_snapshot("market_close")
        if snapshot:
            logger.info(f"📸 Market close snapshot captured - Portfolio: ${snapshot.portfolio_value:,.2f}")
            logger.info(f"💰 Daily P&L: ${snapshot.daily_pnl:,.2f}")

            # Log summary of the day
            report = self.daily_report.get_or_create_today_report()
            logger.info(f"📊 Session Summary:")
            logger.info(f"   Trades executed: {report.trade_count}")
            logger.info(f"   Realized P&L: ${report.realized_pnl:,.2f}")
            logger.info(f"   Unrealized P&L: ${report.unrealized_pnl:,.2f}")
            logger.info(f"   Total P&L: ${report.total_pnl:,.2f}")
        else:
            logger.warning("Failed to capture market close snapshot")
        return snapshot

    def _initialize_llm(self):
        """Initialize LLM provider"""
        provider_name = self.settings.default_llm_provider

        # Validate configuration
        is_valid, error_msg = self.settings.validate_llm_config(provider_name)
        if not is_valid:
            raise Exception(f"LLM configuration error: {error_msg}")

        # Get API key
        api_key = self.settings.get_llm_api_key(provider_name)

        # Create provider
        provider = LLMFactory.create_provider(provider_name, api_key)

        logger.info(f"Using LLM provider: {provider_name} ({provider.model})")

        return provider

    def switch_llm_provider(self, provider_name: str):
        """
        Switch to a different LLM provider

        Args:
            provider_name: Name of the provider (anthropic, openai, google)
        """
        try:
            # Validate configuration
            is_valid, error_msg = self.settings.validate_llm_config(provider_name)
            if not is_valid:
                logger.error(f"Cannot switch to {provider_name}: {error_msg}")
                return False

            # Get API key
            api_key = self.settings.get_llm_api_key(provider_name)

            # Create new provider
            new_provider = LLMFactory.create_provider(provider_name, api_key)

            # Update strategy
            self.llm_provider = new_provider
            self.strategy.llm_provider = new_provider

            logger.info(f"Switched to LLM provider: {provider_name} ({new_provider.model})")
            return True

        except Exception as e:
            logger.error(f"Error switching LLM provider: {e}")
            return False

    def display_status(self):
        """Display current system status"""
        print("\n" + "=" * 70)
        print("📊 TRADING BOT STATUS")
        print("=" * 70)

        # Account info
        try:
            account = self.broker.get_account_info()
            print(f"\n💰 Account Information:")
            print(f"  Portfolio Value: ${account['portfolio_value']:,.2f}")
            print(f"  Cash: ${account['cash']:,.2f}")
            print(f"  Buying Power: ${account['buying_power']:,.2f}")
            print(f"  Equity: ${account['equity']:,.2f}")
        except Exception as e:
            print(f"  Error fetching account info: {e}")

        # Open positions
        try:
            positions = self.broker.get_positions()
            print(f"\n📈 Open Positions: {len(positions)}")
            for pos in positions:
                pnl_sign = "+" if pos.pnl >= 0 else ""
                print(
                    f"  {pos.symbol}: {pos.quantity} shares @ ${pos.entry_price:.2f} "
                    f"(Current: ${pos.current_price:.2f}, "
                    f"P&L: {pnl_sign}${pos.pnl:.2f} [{pnl_sign}{pos.pnl_percent:.2f}%])"
                )
        except Exception as e:
            print(f"  Error fetching positions: {e}")

        # Risk status
        try:
            risk_status = self.risk_manager.get_current_risk_status()
            print(f"\n🛡️  Risk Management:")
            print(f"  Daily P&L: ${risk_status['daily_pnl']:.2f}")
            print(f"  Open Positions: {risk_status['open_positions']} / {risk_status['max_positions']}")
            print(f"  Total Exposure: ${risk_status['current_exposure']:.2f} / ${risk_status['max_exposure']:.2f}")

            if risk_status['loss_limit_reached']:
                print(f"  ⚠️  DAILY LOSS LIMIT REACHED")
        except Exception as e:
            print(f"  Error fetching risk status: {e}")

        # LLM provider
        print(f"\n🤖 AI Provider: {self.llm_provider.provider_name} ({self.llm_provider.model})")

        # Trading mode
        trading_mode = "🤖 AUTO-TRADING" if self.settings.enable_auto_trading else "👤 MANUAL APPROVAL"
        print(f"⚙️  Trading Mode: {trading_mode}")

        # Market status
        try:
            market_open = self.broker.is_market_open()
            status = "🟢 OPEN" if market_open else "🔴 CLOSED"
            print(f"\n🏛️  Market Status: {status}")
        except Exception as e:
            print(f"\n🏛️  Market Status: Unknown ({e})")

        print("=" * 70 + "\n")

    def scan_opportunities(self, min_confidence: float = 70.0):
        """
        Scan watchlist for trading opportunities

        Args:
            min_confidence: Minimum confidence threshold
        """
        logger.info("Scanning watchlist for opportunities...")

        # Check if market is open
        if not self.broker.is_market_open():
            logger.warning("Market is closed - skipping scan")
            return []

        # Get watchlist
        watchlist = self.settings.get_watchlist()
        logger.info(f"Analyzing {len(watchlist)} symbols...")

        # Analyze symbols
        signals = self.strategy.analyze_watchlist(
            symbols=watchlist,
            min_confidence=min_confidence
        )

        if not signals:
            logger.info("No high-confidence signals found")
            return []

        # Display signals
        print(f"\n🎯 Found {len(signals)} trading opportunities:")
        for i, signal in enumerate(signals, 1):
            print(
                f"  {i}. {signal.symbol}: {signal.signal} "
                f"(Confidence: {signal.confidence}%)"
            )

        return signals

    def execute_signal(self, signal):
        """
        Execute a trading signal

        Args:
            signal: TradingSignal object
        """
        logger.info(f"Processing signal: {signal.signal} {signal.symbol}")

        try:
            # Get current quote
            quote = self.broker.get_latest_quote(signal.symbol)
            current_price = (quote["bid_price"] + quote["ask_price"]) / 2

            # Check for existing position (needed for both BUY and SELL)
            side = "buy" if signal.signal == "BUY" else "sell"
            positions = self.broker.get_positions()
            existing_position = next((p for p in positions if p.symbol == signal.symbol), None)

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

            # Determine quantity based on signal type and existing position
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
                if not self.settings.enable_short_selling:
                    logger.warning(f"⚠️ BLOCKED: Short selling is DISABLED in settings - cannot short {signal.symbol}")
                    return False
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
                logger.warning(f"Calculated quantity is 0 or less for {signal.symbol} - insufficient exposure budget")
                return False

            # Evaluate risk
            risk_decision = self.risk_manager.evaluate_trade(
                symbol=signal.symbol,
                side=side,
                quantity=quantity,
                estimated_price=current_price
            )

            # Calculate estimated cost
            estimated_cost = quantity * current_price

            # Check if auto-trading is enabled
            if self.settings.enable_auto_trading:
                # Auto-trading mode: Only check risk manager approval
                if not risk_decision.approved:
                    logger.warning(f"Auto-trade blocked by risk manager: {risk_decision.reason}")
                    print(f"\n⚠️  AUTO-TRADE BLOCKED")
                    print(f"Symbol: {signal.symbol}")
                    print(f"Action: {signal.signal}")
                    print(f"Reason: {risk_decision.reason}")
                    if risk_decision.warnings:
                        print(f"Warnings:")
                        for warning in risk_decision.warnings:
                            print(f"  - {warning}")
                    return False

                # Use recommended quantity from risk manager
                final_quantity = risk_decision.recommended_quantity or quantity

                # Log auto-execution
                logger.info(f"🤖 AUTO-EXECUTING: {side.upper()} {final_quantity} {signal.symbol}")
                print(f"\n🤖 AUTO-EXECUTING TRADE")
                print(f"Symbol: {signal.symbol}")
                print(f"Action: {signal.signal}")
                print(f"Quantity: {final_quantity} shares")
                print(f"Price: ~${current_price:.2f}")
                print(f"Estimated Cost: ${estimated_cost:.2f}")
                print(f"Confidence: {signal.confidence}%")
                print(f"Reasoning: {signal.reasoning}")
            else:
                # Manual approval mode
                approved = self.approval.request_approval(
                    signal=signal,
                    risk_decision=risk_decision,
                    estimated_cost=estimated_cost
                )

                if not approved:
                    logger.info("Trade not approved")
                    return False

                # Get final quantity (user may have adjusted it)
                final_quantity = self.approval.get_quantity_approval(
                    symbol=signal.symbol,
                    side=side,
                    recommended_quantity=quantity,
                    price=current_price
                )

                if not final_quantity:
                    logger.info("Trade cancelled during quantity approval")
                    return False

            # Determine stop-loss and take-profit prices
            # Use AI-provided prices if available, otherwise calculate from settings
            stop_loss_price = None
            take_profit_price = None

            # Only set protective orders for NEW positions (not for closing positions)
            is_closing_position = (
                (side == "buy" and position_side == "short") or
                (side == "sell" and position_side == "long")
            )

            if not is_closing_position:
                # Use AI-provided prices only - no percentage fallback
                # AI is required to provide stop_loss and take_profit based on indicators
                if signal.stop_loss:
                    stop_loss_price = signal.stop_loss
                else:
                    logger.warning(f"AI did not provide stop_loss for {signal.symbol} - no protective stop will be set")

                if signal.take_profit:
                    take_profit_price = signal.take_profit
                else:
                    logger.warning(f"AI did not provide take_profit for {signal.symbol} - no take profit will be set")

            # Execute trade
            logger.info(f"Executing: {side.upper()} {final_quantity} {signal.symbol}")

            # Place order (bracket if protective orders, simple market otherwise)
            if stop_loss_price or take_profit_price:
                order = self.broker.place_bracket_order(
                    symbol=signal.symbol,
                    quantity=final_quantity,
                    side=side,
                    take_profit_price=take_profit_price,
                    stop_loss_price=stop_loss_price
                )
                order_type = "BRACKET"
            else:
                order = self.broker.place_market_order(
                    symbol=signal.symbol,
                    quantity=final_quantity,
                    side=side
                )
                order_type = "MARKET"

            # Record trade in risk manager
            self.risk_manager.record_trade(
                symbol=signal.symbol,
                side=side,
                quantity=final_quantity,
                price=current_price
            )

            # Record trade in portfolio context for history
            self.portfolio.record_trade(
                symbol=signal.symbol,
                side=side,
                quantity=final_quantity,
                price=current_price,
                signal_confidence=signal.confidence,
                llm_provider=signal.llm_provider
            )

            print(f"\n✅ {order_type} order placed successfully!")
            print(f"   Order ID: {order.order_id}")
            print(f"   Status: {order.status}")
            if stop_loss_price:
                print(f"   Stop Loss: ${stop_loss_price:.2f}")
            if take_profit_price:
                print(f"   Take Profit: ${take_profit_price:.2f}")
            print()

            return True

        except Exception as e:
            logger.error(f"Error executing signal: {e}")
            return False

    def run_single_scan(self, min_confidence: float = 70.0, auto_execute: bool = False):
        """
        Run a single scan and optionally execute signals

        Args:
            min_confidence: Minimum confidence threshold
            auto_execute: Automatically execute top signal
        """
        self.display_status()

        # Scan for opportunities
        signals = self.scan_opportunities(min_confidence)

        if not signals:
            return

        if auto_execute and signals:
            # Execute the highest confidence signal
            self.execute_signal(signals[0])
        else:
            # Let user choose
            self._present_signal_menu(signals)

    def _present_signal_menu(self, signals: List):
        """
        Present interactive menu for executing signals

        Args:
            signals: List of TradingSignal objects
        """
        print("\n" + "=" * 70)
        print("📊 TRADING SIGNALS MENU")
        print("=" * 70)

        # Display all signals
        for i, signal in enumerate(signals, 1):
            print(f"\n  {i}. {signal.symbol} - {signal.signal}")
            print(f"     Confidence: {signal.confidence}%")
            print(f"     Reasoning: {signal.reasoning[:80]}...")

        print("\n" + "=" * 70)
        print("\nOptions:")
        print("  [1-{}]  Execute specific signal".format(len(signals)))
        print("  [a]     Approve and execute ALL signals")
        print("  [r]     Review signals in detail")
        print("  [0]     Skip all and continue")
        print("=" * 70)

        try:
            choice = input("\nYour choice: ").strip().lower()

            if choice == '0':
                print("Skipping all signals")
                return

            elif choice == 'a':
                # Approve all
                self._execute_all_signals(signals)

            elif choice == 'r':
                # Review each in detail
                self._review_signals(signals)

            elif choice.isdigit():
                # Execute specific signal
                idx = int(choice) - 1
                if 0 <= idx < len(signals):
                    self.execute_signal(signals[idx])
                else:
                    print("Invalid signal number")

            else:
                print("Invalid choice")

        except (ValueError, KeyboardInterrupt):
            print("\nCancelled by user")

    def _execute_all_signals(self, signals: List):
        """
        Execute all signals with batch approval

        Args:
            signals: List of TradingSignal objects
        """
        print("\n" + "=" * 70)
        print("🚀 BATCH EXECUTION - APPROVE ALL")
        print("=" * 70)

        # Show summary
        print(f"\nYou are about to execute {len(signals)} trades:")
        total_estimated_cost = 0

        for i, signal in enumerate(signals, 1):
            try:
                quote = self.broker.get_latest_quote(signal.symbol)
                current_price = (quote["bid_price"] + quote["ask_price"]) / 2

                # Estimate quantity (using default position size)
                estimated_qty = self.settings.max_position_size / current_price
                estimated_cost = estimated_qty * current_price
                total_estimated_cost += estimated_cost

                print(f"  {i}. {signal.signal} {signal.symbol}")
                print(f"     @ ${current_price:.2f} (~{int(estimated_qty)} shares)")
                print(f"     Estimated: ${estimated_cost:.2f}")

            except Exception as e:
                print(f"  {i}. {signal.signal} {signal.symbol} (Error getting quote: {e})")

        print(f"\n💰 Total Estimated Cost: ${total_estimated_cost:.2f}")

        # Get account info
        try:
            account = self.broker.get_account_info()
            buying_power = float(account["buying_power"])
            print(f"💵 Available Buying Power: ${buying_power:.2f}")

            if total_estimated_cost > buying_power:
                print("\n⚠️  WARNING: Total cost exceeds buying power!")

        except Exception as e:
            print(f"\n⚠️  Could not verify buying power: {e}")

        print("\n" + "=" * 70)
        confirm = input("Confirm batch execution? (yes/no): ").strip().lower()

        if confirm not in ['yes', 'y']:
            print("Batch execution cancelled")
            return

        # Execute all signals
        print("\n🔄 Executing trades...")
        successful = 0
        failed = 0
        results = []  # Track results for summary

        for i, signal in enumerate(signals, 1):
            print(f"\n[{i}/{len(signals)}] Processing {signal.symbol}...")

            try:
                success = self.execute_signal(signal)
                if success:
                    successful += 1
                    results.append((signal.symbol, signal.signal, "✅ Executed"))
                else:
                    failed += 1
                    results.append((signal.symbol, signal.signal, "❌ Blocked by risk manager"))

            except Exception as e:
                logger.error(f"Error executing {signal.symbol}: {e}")
                failed += 1
                results.append((signal.symbol, signal.signal, f"❌ Error: {str(e)[:30]}"))

            # Small delay between trades
            if i < len(signals):
                time.sleep(1)

        # Summary
        print("\n" + "=" * 70)
        print("📊 BATCH EXECUTION COMPLETE")
        print("=" * 70)
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Total: {len(signals)}")
        print("\n📋 RESULTS BY SYMBOL:")
        for symbol, action, status in results:
            print(f"  {symbol} ({action}): {status}")
        print("=" * 70)

    def _review_signals(self, signals: List):
        """
        Review each signal in detail with option to execute

        Args:
            signals: List of TradingSignal objects
        """
        for i, signal in enumerate(signals, 1):
            print("\n" + "=" * 70)
            print(f"SIGNAL {i}/{len(signals)}: {signal.symbol}")
            print("=" * 70)

            print(f"\nAction: {signal.signal}")
            print(f"Confidence: {signal.confidence}%")
            print(f"Provider: {signal.llm_provider}")

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

            print("\n" + "=" * 70)
            choice = input("Execute this trade? (yes/no/skip remaining): ").strip().lower()

            if choice in ['yes', 'y']:
                self.execute_signal(signal)
            elif choice in ['skip', 's', 'skip remaining']:
                print("Skipping remaining signals")
                break
            else:
                print("Skipping this signal")

    def run_continuous(
        self,
        scan_interval: int = 300,
        min_confidence: float = 70.0
    ):
        """
        Run continuous trading loop

        Args:
            scan_interval: Seconds between scans (default 300 = 5 minutes)
            min_confidence: Minimum confidence threshold
        """
        logger.info(f"Starting continuous trading (scan interval: {scan_interval}s)")

        try:
            while True:
                self.run_single_scan(min_confidence, auto_execute=False)

                logger.info(f"Waiting {scan_interval} seconds until next scan...")
                time.sleep(scan_interval)

        except KeyboardInterrupt:
            logger.info("Continuous trading stopped by user")


def main():
    """Main entry point"""
    bot = None
    try:
        # Initialize bot
        bot = DayTradingBot()

        # Start trading session - capture market open snapshot
        bot.start_session()

        # Display status
        bot.display_status()

        # Run continuous trading (scans every 5 minutes)
        # Press Ctrl+C to stop
        bot.run_continuous(scan_interval=300, min_confidence=70.0)

        # For single scan only, use this instead:
        # bot.run_single_scan(min_confidence=70.0)

    except KeyboardInterrupt:
        logger.info("\nShutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Always capture market close snapshot on shutdown
        if bot is not None:
            logger.info("\n" + "=" * 70)
            logger.info("SHUTTING DOWN - Capturing final session state...")
            logger.info("=" * 70)
            bot.end_session()
            logger.info("✅ Session ended successfully. Goodbye!")


if __name__ == "__main__":
    main()
