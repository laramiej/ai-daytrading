"""
AI Trading Strategy Engine
Uses LLM to analyze market data and generate trading signals
"""
import json
import logging
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class TradingSignal:
    """Represents a trading signal from the AI"""
    symbol: str
    signal: str  # BUY, SELL, HOLD
    confidence: float
    reasoning: str
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    position_size_recommendation: str
    risk_factors: List[str]
    time_horizon: str
    timestamp: datetime
    llm_provider: str
    contrary_reasoning: Optional[str] = None  # Why the opposite signal is wrong
    # Debate data (populated when enable_ai_critique/debate is True)
    bull_case: Optional[str] = None  # The bull's argument for buying
    bull_signals: Optional[List[str]] = None  # Key bullish signals identified
    bull_confidence: Optional[float] = None  # Bull's confidence in BUY
    bear_case: Optional[str] = None  # The bear's argument for selling
    bear_signals: Optional[List[str]] = None  # Key bearish signals identified
    bear_confidence: Optional[float] = None  # Bear's confidence in SELL
    judge_reasoning: Optional[str] = None  # The judge's reasoning for the final decision
    winning_case: Optional[str] = None  # "BULL", "BEAR", or "NEITHER"


class TradingStrategy:
    """AI-powered trading strategy using LLM analysis"""

    def __init__(self, llm_provider, market_analyzer, portfolio_context=None, enable_critique: bool = False):
        """
        Initialize trading strategy

        Args:
            llm_provider: LLM provider instance
            market_analyzer: Market analyzer instance
            portfolio_context: Optional portfolio context for portfolio-aware trading
            enable_critique: Whether to run a second AI call to critique recommendations
        """
        self.llm_provider = llm_provider
        self.market_analyzer = market_analyzer
        self.portfolio_context = portfolio_context
        self.enable_critique = enable_critique
        self.signal_history = []

    def analyze_symbol(
        self,
        symbol: str,
        context: Optional[str] = None,
        include_portfolio_context: bool = True
    ) -> Optional[TradingSignal]:
        """
        Analyze a symbol and generate a trading signal

        Args:
            symbol: Stock symbol to analyze
            context: Optional additional context

        Returns:
            TradingSignal or None if analysis fails
        """
        try:
            logger.info(f"Analyzing {symbol} with {self.llm_provider.provider_name}")

            # Fetch market data
            market_data = self.market_analyzer.get_market_data(
                symbol,
                include_technicals=True,
                include_news=True
            )

            if not market_data:
                logger.error(f"Failed to fetch market data for {symbol}")
                return None

            # Log market data summary
            self._log_market_data_summary(symbol, market_data)

            # Add portfolio context if available
            if include_portfolio_context and self.portfolio_context:
                portfolio_info = self.portfolio_context.format_portfolio_context()
                recommendations = self.portfolio_context.get_trade_recommendations(symbol)

                # Log portfolio context
                logger.info(f"Portfolio context for {symbol}:")
                logger.info(f"  Can BUY: {recommendations.get('can_buy', False)}")
                logger.info(f"  Can SELL: {recommendations.get('can_sell', False)}")
                if recommendations.get('reasons'):
                    for reason in recommendations['reasons']:
                        logger.info(f"    - {reason}")

                # Append to context
                context_parts = []
                if context:
                    context_parts.append(context)

                context_parts.append("\n" + portfolio_info)

                # Check current position status
                has_position = self.portfolio_context.has_position(symbol)
                position_details = self.portfolio_context.get_position_details(symbol) if has_position else None
                short_selling_enabled = self.portfolio_context.risk_manager.limits.enable_short_selling

                # Add clear position status
                context_parts.append("\n📍 CURRENT POSITION STATUS:")
                if position_details:
                    pnl_str = f"+${position_details['pnl']:.2f}" if position_details['pnl'] >= 0 else f"-${abs(position_details['pnl']):.2f}"
                    pnl_pct = position_details['pnl_percent']
                    position_side = position_details.get('side', 'long').upper()

                    if position_side == "LONG":
                        # We have a LONG position
                        context_parts.append(f"  📈 LONG POSITION: {position_details['quantity']} shares of {symbol}")
                        context_parts.append(f"     Entry: ${position_details['entry_price']:.2f} | Current: ${position_details['current_price']:.2f}")
                        context_parts.append(f"     P&L: {pnl_str} ({pnl_pct:+.2f}%)")
                        context_parts.append(f"  → BUY signal: ADD to existing long position (increase position)")
                        context_parts.append(f"  → SELL signal: CLOSE this long position (sell all {position_details['quantity']} shares)")
                    else:
                        # We have a SHORT position
                        context_parts.append(f"  📉 SHORT POSITION: {position_details['quantity']} shares of {symbol}")
                        context_parts.append(f"     Entry: ${position_details['entry_price']:.2f} | Current: ${position_details['current_price']:.2f}")
                        context_parts.append(f"     P&L: {pnl_str} ({pnl_pct:+.2f}%) - Profit when price goes DOWN")
                        context_parts.append(f"  → BUY signal: CLOSE this short position (buy to cover {position_details['quantity']} shares)")
                        context_parts.append(f"  → SELL signal: ADD to existing short position (increase short exposure)")
                else:
                    context_parts.append(f"  ❌ NO POSITION in {symbol}")
                    context_parts.append(f"  → BUY signal: OPEN a new LONG position (profit from price increase)")
                    if short_selling_enabled:
                        context_parts.append(f"  → SELL signal: OPEN a new SHORT position (profit from price decline)")
                    else:
                        context_parts.append(f"  → SELL signal: REJECTED (short selling disabled, no position to close)")

                # Add trading capabilities
                context_parts.append("\n📊 TRADING CAPABILITIES:")
                context_parts.append(f"  Short Selling: {'ENABLED' if short_selling_enabled else 'DISABLED'}")

                if recommendations:
                    context_parts.append("\n📋 Trading Recommendations:")
                    if not recommendations["can_buy"]:
                        context_parts.append("  ⚠️  Cannot open new BUY positions")
                    for reason in recommendations["reasons"]:
                        context_parts.append(f"  - {reason}")
                    for consideration in recommendations["considerations"]:
                        context_parts.append(f"  - {consideration}")

                context = "\n".join(context_parts)

            # Choose analysis method based on critique/debate setting and provider
            # n8n provider handles all analysis externally, so skip debate system
            is_n8n = self.llm_provider.provider_name == "n8n"

            if self.enable_critique and not is_n8n:
                # Use Bull/Bear/Judge debate system (3 AI calls)
                logger.info(f"🎭 Using DEBATE system for {symbol} (Bull vs Bear vs Judge)")
                signal = self._run_debate(symbol, market_data)
            else:
                # Use single AI call (original method, or n8n workflow)
                if is_n8n:
                    logger.info(f"🔗 Using n8n workflow for {symbol} (external analysis)")
                else:
                    logger.info(f"Sending analysis request to {self.llm_provider.provider_name}...")

                response = self.llm_provider.analyze_market_data(
                    market_data=market_data,
                    context=context
                )

                # Parse the JSON response
                signal = self._parse_llm_response(
                    response.content,
                    symbol,
                    self.llm_provider.provider_name
                )

            if signal:
                # Log AI output summary
                self._log_signal_summary(signal)
                self.signal_history.append(signal)

            return signal

        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None

    def _run_debate(self, symbol: str, market_data: Dict[str, Any]) -> Optional[TradingSignal]:
        """
        Run the bull/bear/judge debate system for a symbol.

        This replaces the old critique system with a more balanced approach:
        1. Bull AI argues for buying
        2. Bear AI argues for selling
        3. Judge AI decides: BUY, SELL, or HOLD

        Args:
            symbol: Stock symbol being analyzed
            market_data: Market data for the symbol

        Returns:
            TradingSignal based on the judge's decision, or None if debate fails
        """
        try:
            provider = self.llm_provider.provider_name

            # Step 1: Get Bull Case
            logger.info(f"🐂 Getting BULL case for {symbol}...")
            bull_response = self.llm_provider.make_bull_case(market_data)
            bull_data = self._parse_debate_json(bull_response.content, "BULL")

            logger.info("=" * 70)
            logger.info(f"🐂 BULL CASE FOR {symbol}")
            logger.info("=" * 70)
            logger.info(f"📈 Argument: {bull_data.get('bull_case', 'N/A')}")
            logger.info(f"📊 Bullish Signals: {bull_data.get('key_bullish_signals', [])}")
            logger.info(f"💪 Bull Confidence: {bull_data.get('confidence', 0)}%")
            logger.info("=" * 70)

            # Step 2: Get Bear Case
            logger.info(f"🐻 Getting BEAR case for {symbol}...")
            bear_response = self.llm_provider.make_bear_case(market_data)
            bear_data = self._parse_debate_json(bear_response.content, "BEAR")

            logger.info("=" * 70)
            logger.info(f"🐻 BEAR CASE FOR {symbol}")
            logger.info("=" * 70)
            logger.info(f"📉 Argument: {bear_data.get('bear_case', 'N/A')}")
            logger.info(f"📊 Bearish Signals: {bear_data.get('key_bearish_signals', [])}")
            logger.info(f"💪 Bear Confidence: {bear_data.get('confidence', 0)}%")
            logger.info("=" * 70)

            # Step 3: Judge decides
            logger.info(f"⚖️ JUDGE evaluating {symbol}...")
            judge_response = self.llm_provider.judge_debate(bull_data, bear_data, market_data)
            judge_data = self._parse_debate_json(judge_response.content, "JUDGE")

            decision = judge_data.get('decision', 'HOLD').upper()
            confidence = float(judge_data.get('confidence', 50))
            winning_case = judge_data.get('winning_case', 'NEITHER')

            logger.info("=" * 70)
            logger.info(f"⚖️ JUDGE DECISION FOR {symbol}")
            logger.info("=" * 70)
            logger.info(f"🎯 Decision: {decision}")
            logger.info(f"📊 Confidence: {confidence}%")
            logger.info(f"🏆 Winning Case: {winning_case}")
            logger.info(f"💭 Reasoning: {judge_data.get('reasoning', 'N/A')}")
            logger.info("=" * 70)

            # Build risk factors from both cases' signals
            risk_factors = []
            if decision == 'BUY':
                # If buying, bear signals are risk factors
                risk_factors = bear_data.get('key_bearish_signals', [])[:3]
            elif decision == 'SELL':
                # If selling, bull signals are risk factors
                risk_factors = bull_data.get('key_bullish_signals', [])[:3]
            else:
                # If holding, both are considerations
                risk_factors = ["Mixed signals - no clear direction"]

            # Add any risk factors from judge
            risk_factors.extend(judge_data.get('risk_factors', []))

            return TradingSignal(
                symbol=symbol,
                signal=decision,
                confidence=confidence,
                reasoning=judge_data.get('reasoning', 'Judge decision based on bull/bear debate'),
                entry_price=judge_data.get('entry_price'),
                stop_loss=judge_data.get('stop_loss'),
                take_profit=judge_data.get('take_profit'),
                position_size_recommendation=judge_data.get('position_size', 'MEDIUM'),
                risk_factors=risk_factors,
                time_horizon=judge_data.get('time_horizon', 'HOURS'),
                timestamp=datetime.now(),
                llm_provider=provider,
                contrary_reasoning=None,  # Not used in debate system
                # Debate data
                bull_case=bull_data.get('bull_case'),
                bull_signals=bull_data.get('key_bullish_signals', []),
                bull_confidence=bull_data.get('confidence'),
                bear_case=bear_data.get('bear_case'),
                bear_signals=bear_data.get('key_bearish_signals', []),
                bear_confidence=bear_data.get('confidence'),
                judge_reasoning=judge_data.get('reasoning'),
                winning_case=winning_case
            )

        except Exception as e:
            logger.error(f"Error running debate for {symbol}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _extract_json(self, text: str) -> str:
        """Extract JSON from LLM response that may contain markdown code blocks."""
        text = text.strip()

        # Try to extract from markdown code blocks first
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()

        # Try to find JSON object directly (starts with { ends with })
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            return json_match.group(0)

        return text

    def _parse_debate_json(self, text: str, stage: str) -> Dict[str, Any]:
        """Parse JSON from debate response with better error handling."""
        try:
            json_str = self._extract_json(text)
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in {stage}: {e}")
            logger.error(f"Raw response (first 500 chars): {text[:500]}")

            # Try to fix common JSON issues
            json_str = self._extract_json(text)

            # Fix trailing commas
            json_str = re.sub(r',\s*}', '}', json_str)
            json_str = re.sub(r',\s*]', ']', json_str)

            # Try again
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                logger.error(f"Could not parse JSON even after fixes. Extracted JSON: {json_str[:500]}")
                raise

    def analyze_watchlist(
        self,
        symbols: List[str],
        min_confidence: float = 60.0
    ) -> List[TradingSignal]:
        """
        Analyze multiple symbols and return high-confidence signals

        Args:
            symbols: List of stock symbols
            min_confidence: Minimum confidence threshold (0-100)

        Returns:
            List of trading signals above confidence threshold
        """
        signals = []

        for symbol in symbols:
            try:
                signal = self.analyze_symbol(symbol)

                if signal and signal.signal != "HOLD" and signal.confidence >= min_confidence:
                    signals.append(signal)

            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
                continue

        # Sort by confidence (highest first)
        signals.sort(key=lambda x: x.confidence, reverse=True)

        return signals

    def _parse_llm_response(
        self,
        response_text: str,
        symbol: str,
        provider: str
    ) -> Optional[TradingSignal]:
        """
        Parse LLM response into TradingSignal

        Args:
            response_text: Raw LLM response
            symbol: Stock symbol
            provider: LLM provider name

        Returns:
            TradingSignal or None if parsing fails
        """
        try:
            # Try to extract JSON from the response
            # LLMs sometimes wrap JSON in markdown code blocks
            response_text = response_text.strip()

            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()

            # Parse JSON
            data = json.loads(response_text)

            # Validate required fields
            required_fields = ["signal", "confidence", "reasoning"]
            for field in required_fields:
                if field not in data:
                    logger.error(f"Missing required field: {field}")
                    return None

            # Normalize signal value
            signal = data["signal"].upper()
            if signal not in ["BUY", "SELL", "HOLD"]:
                logger.error(f"Invalid signal value: {signal}")
                return None

            # Create TradingSignal
            return TradingSignal(
                symbol=symbol,
                signal=signal,
                confidence=float(data["confidence"]),
                reasoning=data["reasoning"],
                entry_price=float(data.get("entry_price")) if data.get("entry_price") else None,
                stop_loss=float(data.get("stop_loss")) if data.get("stop_loss") else None,
                take_profit=float(data.get("take_profit")) if data.get("take_profit") else None,
                position_size_recommendation=data.get("position_size_recommendation", "SMALL"),
                risk_factors=data.get("risk_factors", []),
                time_horizon=data.get("time_horizon", "intraday"),
                timestamp=datetime.now(),
                llm_provider=provider,
                contrary_reasoning=data.get("contrary_reasoning")
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text}")
            return None
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return None

    def _log_market_data_summary(self, symbol: str, market_data: Dict[str, Any]):
        """
        Log a summary of market data being analyzed

        Args:
            symbol: Stock symbol
            market_data: Market data dictionary
        """
        logger.info("=" * 70)
        logger.info(f"📊 AI ANALYSIS INPUT SUMMARY FOR {symbol}")
        logger.info("=" * 70)

        # Price data (using actual keys from market_analyzer.py)
        if "current_price" in market_data:
            logger.info(f"💵 PRICE DATA:")
            logger.info(f"  Current: ${market_data.get('current_price', 0):.2f}")
            logger.info(f"  Bid: ${market_data.get('bid', 0):.2f}")
            logger.info(f"  Ask: ${market_data.get('ask', 0):.2f}")
            logger.info(f"  Spread: ${market_data.get('spread', 0):.4f}")

            if "open_price" in market_data:
                logger.info(f"  Open: ${market_data.get('open_price', 0):.2f}")
            if "volume" in market_data:
                logger.info(f"  Volume: {market_data.get('volume', 0):,}")
            if "change_percent" in market_data:
                logger.info(f"  Change: {market_data.get('change_percent', 0):+.2f}%")

        # Technical indicators (INTRADAY - calculated on 1-minute bars)
        if "technical_indicators" in market_data:
            tech = market_data["technical_indicators"]
            logger.info(f"📈 INTRADAY TECHNICAL INDICATORS (1-minute bars):")

            # VWAP - most important for day trading
            if "VWAP" in tech:
                vwap = tech["VWAP"]
                vwap_pos = tech.get("VWAP_position", "N/A")
                vwap_dist = tech.get("VWAP_distance_percent", 0)
                logger.info(f"  VWAP: ${vwap:.2f} ({vwap_pos}, {vwap_dist:+.2f}% from VWAP)")

            # RSI (14-minute)
            if "RSI_14min" in tech:
                rsi = tech["RSI_14min"]
                rsi_signal = tech.get("RSI_signal", "N/A")
                logger.info(f"  RSI (14-min): {rsi:.2f} - {rsi_signal}")

            # Momentum
            if "momentum_5min_percent" in tech:
                logger.info(f"  5-min Momentum: {tech['momentum_5min_percent']:+.2f}%")
            if "momentum_15min_percent" in tech:
                logger.info(f"  15-min Momentum: {tech['momentum_15min_percent']:+.2f}%")

            # MACD
            if "MACD" in tech:
                logger.info(f"  MACD: {tech.get('MACD', 0):.4f}, Signal: {tech.get('MACD_signal', 0):.4f}")
                if "MACD_trend" in tech:
                    logger.info(f"    Trend: {tech['MACD_trend']}")

            # Bollinger Bands
            if "BB_upper" in tech:
                logger.info(f"  Bollinger Bands: ${tech.get('BB_lower', 0):.2f} - ${tech.get('BB_middle', 0):.2f} - ${tech.get('BB_upper', 0):.2f}")
                if "BB_signal" in tech:
                    logger.info(f"    Signal: {tech['BB_signal']}")

            # Moving Averages (intraday)
            if "SMA_9min" in tech:
                logger.info(f"  SMA (9-min): ${tech['SMA_9min']:.2f}")
            if "SMA_20min" in tech:
                logger.info(f"  SMA (20-min): ${tech['SMA_20min']:.2f}")
            if "EMA_9min" in tech:
                logger.info(f"  EMA (9-min): ${tech['EMA_9min']:.2f}")
            if "EMA_21min" in tech:
                logger.info(f"  EMA (21-min): ${tech['EMA_21min']:.2f}")

            # Volume
            if "volume_ratio" in tech:
                vol_signal = tech.get("volume_signal", "N/A")
                logger.info(f"  Volume Ratio: {tech['volume_ratio']:.2f}x average ({vol_signal})")
            if "OBV_trend" in tech:
                logger.info(f"  OBV Trend: {tech['OBV_trend']}")

            # ATR (14-minute)
            if "ATR_14min" in tech:
                atr = tech["ATR_14min"]
                atr_pct = tech.get("ATR_percent", 0)
                logger.info(f"  ATR (14-min): ${atr:.2f} ({atr_pct:.3f}% volatility)")

            # Stochastic
            if "STOCH_K" in tech:
                stoch_k = tech["STOCH_K"]
                stoch_d = tech.get("STOCH_D", 0)
                stoch_signal = tech.get("STOCH_signal", "N/A")
                logger.info(f"  Stochastic: K={stoch_k:.1f}, D={stoch_d:.1f} ({stoch_signal})")

            # Intraday Pivot Points
            if "intraday_pivot" in tech:
                pivot = tech["intraday_pivot"]
                r1 = tech.get("intraday_R1", 0)
                s1 = tech.get("intraday_S1", 0)
                position = tech.get("pivot_position", "N/A")
                logger.info(f"  Intraday Pivot: ${pivot:.2f}, R1=${r1:.2f}, S1=${s1:.2f}")
                logger.info(f"    Position: {position}")

        # Sentiment data (if available)
        if "market_sentiment" in market_data:
            sentiment = market_data["market_sentiment"]
            logger.info(f"🎭 MARKET SENTIMENT:")
            logger.info(f"  Overall: {sentiment.get('summary', 'N/A')} (Score: {sentiment.get('overall_score', 0):.2f})")

        if "stock_sentiment" in market_data:
            sentiment = market_data["stock_sentiment"]
            logger.info(f"📰 {symbol} SENTIMENT:")
            logger.info(f"  Overall: {sentiment.get('summary', 'N/A')} (Score: {sentiment.get('overall_score', 0):.2f})")
            if sentiment.get("sources"):
                sources = sentiment["sources"]
                if sources.get("news"):
                    logger.info(f"  News: {sources['news'].get('label', 'N/A')}")
                if sources.get("analysts"):
                    logger.info(f"  Analysts: {sources['analysts'].get('label', 'N/A')}")
                if sources.get("momentum"):
                    logger.info(f"  Momentum: {sources['momentum'].get('label', 'N/A')}")

        # News headlines (if available)
        if "news" in market_data and market_data["news"]:
            news = market_data["news"]
            logger.info(f"📰 RECENT NEWS: ({len(news)} headlines)")
            for i, headline in enumerate(news[:3], 1):  # Show first 3
                logger.info(f"  {i}. {headline.get('title', 'N/A')[:60]}...")

        logger.info("=" * 70)

    def _log_signal_summary(self, signal: TradingSignal):
        """
        Log a summary of the AI's trading signal

        Args:
            signal: TradingSignal object
        """
        logger.info("=" * 70)
        logger.info(f"🤖 AI ANALYSIS OUTPUT FOR {signal.symbol}")
        logger.info("=" * 70)

        # Signal and confidence
        emoji = "🟢" if signal.signal == "BUY" else "🔴" if signal.signal == "SELL" else "⚪"
        logger.info(f"{emoji} SIGNAL: {signal.signal}")
        logger.info(f"📊 CONFIDENCE: {signal.confidence}%")

        # Confidence interpretation
        if signal.confidence >= 80:
            confidence_level = "Very High"
        elif signal.confidence >= 70:
            confidence_level = "High"
        elif signal.confidence >= 60:
            confidence_level = "Moderate"
        elif signal.confidence >= 50:
            confidence_level = "Low"
        else:
            confidence_level = "Very Low"
        logger.info(f"   ({confidence_level} confidence)")

        # Reasoning
        logger.info(f"💭 REASONING:")
        logger.info(f"   {signal.reasoning}")

        # Contrary reasoning (why not the opposite signal)
        if signal.contrary_reasoning:
            logger.info(f"🔄 WHY NOT THE OPPOSITE:")
            logger.info(f"   {signal.contrary_reasoning}")

        # Price targets
        if signal.entry_price:
            logger.info(f"🎯 PRICE TARGETS:")
            logger.info(f"   Entry: ${signal.entry_price:.2f}")
            if signal.stop_loss:
                logger.info(f"   Stop Loss: ${signal.stop_loss:.2f}")
            if signal.take_profit:
                logger.info(f"   Take Profit: ${signal.take_profit:.2f}")

        # Position sizing
        logger.info(f"📏 POSITION SIZE: {signal.position_size_recommendation}")

        # Risk factors
        if signal.risk_factors:
            logger.info(f"⚠️  RISK FACTORS:")
            for risk in signal.risk_factors:
                logger.info(f"   - {risk}")

        # Time horizon
        logger.info(f"⏰ TIME HORIZON: {signal.time_horizon}")

        # Provider info
        logger.info(f"🔧 GENERATED BY: {signal.llm_provider}")

        logger.info("=" * 70)

    def get_signal_history(
        self,
        symbol: Optional[str] = None,
        limit: int = 10
    ) -> List[TradingSignal]:
        """
        Get recent signal history

        Args:
            symbol: Optional symbol filter
            limit: Maximum number of signals to return

        Returns:
            List of recent signals
        """
        signals = self.signal_history

        if symbol:
            signals = [s for s in signals if s.symbol == symbol]

        return signals[-limit:]
