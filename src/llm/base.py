"""
Base LLM Provider Interface
Defines the abstract interface for all LLM providers
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Standardized response from LLM providers"""
    content: str
    model: str
    provider: str
    tokens_used: Optional[int] = None
    cost_estimate: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""

    def __init__(self, api_key: str, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or self.get_default_model()
        self.provider_name = self.__class__.__name__.replace("Provider", "").lower()

    @abstractmethod
    def get_default_model(self) -> str:
        """Return the default model for this provider"""
        pass

    @abstractmethod
    def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """
        Generate a response from the LLM

        Args:
            prompt: The user prompt/question
            system_prompt: Optional system instructions
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse object with standardized response
        """
        pass

    @abstractmethod
    def analyze_market_data(
        self,
        market_data: Dict[str, Any],
        context: Optional[str] = None
    ) -> LLMResponse:
        """
        Analyze market data and provide trading insights

        Args:
            market_data: Dictionary containing market data (prices, indicators, news, etc.)
            context: Optional additional context

        Returns:
            LLMResponse with analysis
        """
        pass

    def critique_signal(
        self,
        signal_data: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> LLMResponse:
        """
        Critique a trading signal with a second AI call.

        This acts as a devil's advocate to challenge the original recommendation.

        Args:
            signal_data: The original signal (signal, reasoning, confidence, etc.)
            market_data: The market data used for the original analysis

        Returns:
            LLMResponse with critique and potentially adjusted recommendation
        """
        formatted_market = self.format_market_data(market_data)

        critique_prompt = f"""You are a SKEPTICAL trading risk analyst. Your job is to CHALLENGE trading recommendations and find flaws in the reasoning.

ORIGINAL RECOMMENDATION:
- Signal: {signal_data.get('signal', 'UNKNOWN')}
- Confidence: {signal_data.get('confidence', 0)}%
- Reasoning: {signal_data.get('reasoning', 'No reasoning provided')}
- Contrary Reasoning: {signal_data.get('contrary_reasoning', 'None provided')}

MARKET DATA:
{formatted_market}

YOUR TASK:
1. CHALLENGE the recommendation - what could go wrong?
2. Identify any indicators that CONTRADICT the recommendation
3. Consider if the opposite trade might actually be better
4. Evaluate if the confidence level is justified

Respond with valid JSON:
{{
  "critique": "Your detailed critique of the recommendation",
  "contradicting_indicators": ["list of indicators that contradict the recommendation"],
  "recommendation_valid": true or false,
  "adjusted_confidence": 0-100 (your adjusted confidence, may be lower or higher),
  "better_alternative": "BUY" | "SELL" | "HOLD" | "NONE" (if you think a different signal is better, or NONE if original is fine),
  "alternative_reasoning": "If you suggested a better alternative, explain why"
}}

Be tough but fair. If the recommendation is solid, say so. If it has flaws, expose them."""

        return self.generate_response(
            prompt=critique_prompt,
            system_prompt="You are a skeptical trading risk analyst who challenges recommendations.",
            temperature=0.4,
            max_tokens=1000
        )

    def make_bull_case(self, market_data: Dict[str, Any]) -> LLMResponse:
        """
        Make the strongest possible case for BUYING this stock.
        First part of the bull/bear/judge debate system.
        """
        formatted_market = self.format_market_data(market_data)
        symbol = market_data.get('symbol', 'UNKNOWN')

        bull_prompt = f"""You are a BULLISH stock analyst. Your job is to make the STRONGEST possible case for BUYING {symbol} RIGHT NOW.

MARKET DATA:
{formatted_market}

YOUR TASK:
Act as a passionate bull advocate. Find EVERY reason to BUY this stock for a day trade:
1. Identify ALL bullish technical signals (momentum, breakouts, support levels holding)
2. Highlight positive price action and volume patterns
3. Point out any bullish divergences or setups
4. Consider favorable market sentiment or news
5. Explain why NOW is a good entry point

You MUST argue for buying even if signals are mixed - find the bull case!

Respond with ONLY valid JSON (no other text):
{{
  "bull_case": "Your 2-3 sentence argument for buying",
  "key_bullish_signals": ["signal1", "signal2", "signal3"],
  "proposed_entry": 150.00,
  "proposed_stop_loss": 145.00,
  "proposed_take_profit": 160.00,
  "confidence": 75
}}

IMPORTANT: Keep bull_case SHORT (2-3 sentences max). Use actual numbers for prices. Your job is to advocate for buying."""

        return self.generate_response(
            prompt=bull_prompt,
            system_prompt="You are a bullish stock analyst. Respond with ONLY valid JSON, no other text.",
            temperature=0.3,
            max_tokens=800
        )

    def make_bear_case(self, market_data: Dict[str, Any]) -> LLMResponse:
        """
        Make the strongest possible case for SELLING this stock.
        Second part of the bull/bear/judge debate system.
        """
        formatted_market = self.format_market_data(market_data)
        symbol = market_data.get('symbol', 'UNKNOWN')

        bear_prompt = f"""You are a BEARISH stock analyst. Your job is to make the STRONGEST possible case for SELLING/SHORTING {symbol} RIGHT NOW.

MARKET DATA:
{formatted_market}

YOUR TASK:
Act as a passionate bear advocate. Find EVERY reason to SELL or SHORT this stock for a day trade:
1. Identify ALL bearish technical signals (overbought conditions, breakdowns, resistance rejections)
2. Highlight negative price action and volume patterns
3. Point out any bearish divergences or warning signs
4. Consider negative market sentiment or risks
5. Explain why the stock is likely to go DOWN from here

You MUST argue for selling even if signals are mixed - find the bear case!

Respond with ONLY valid JSON (no other text):
{{
  "bear_case": "Your 2-3 sentence argument for selling",
  "key_bearish_signals": ["signal1", "signal2", "signal3"],
  "proposed_entry": 150.00,
  "proposed_stop_loss": 155.00,
  "proposed_take_profit": 140.00,
  "confidence": 75
}}

IMPORTANT: Keep bear_case SHORT (2-3 sentences max). Use actual numbers for prices. Your job is to advocate for selling."""

        return self.generate_response(
            prompt=bear_prompt,
            system_prompt="You are a bearish stock analyst. Respond with ONLY valid JSON, no other text.",
            temperature=0.3,
            max_tokens=800
        )

    def judge_debate(
        self,
        bull_case: Dict[str, Any],
        bear_case: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> LLMResponse:
        """
        Judge the bull vs bear debate and make the final trading decision.
        Third part of the bull/bear/judge debate system.
        """
        formatted_market = self.format_market_data(market_data)
        symbol = market_data.get('symbol', 'UNKNOWN')

        judge_prompt = f"""You are a SKEPTICAL and IMPARTIAL trading judge. You've heard both the bull and bear cases for {symbol}.
Your job is to make the FINAL DECISION: BUY, SELL, or HOLD.

BEAR CASE (Advocate for SELLING/SHORTING):
{bear_case.get('bear_case', 'No bear case provided')}
Key Bearish Signals: {bear_case.get('key_bearish_signals', [])}
Bear Confidence: {bear_case.get('confidence', 0)}%

BULL CASE (Advocate for BUYING):
{bull_case.get('bull_case', 'No bull case provided')}
Key Bullish Signals: {bull_case.get('key_bullish_signals', [])}
Bull Confidence: {bull_case.get('confidence', 0)}%

MARKET DATA (for your reference):
{formatted_market}

CRITICAL JUDGING CRITERIA:
1. You are naturally SKEPTICAL - the default should be HOLD unless one side is clearly stronger
2. A trade needs STRONG conviction to be worth the risk - weak cases = HOLD
3. Consider the RISK first: what happens if the trade goes wrong?
4. The higher confidence case doesn't automatically win - evaluate the QUALITY of arguments
5. Day trading is risky - when in doubt, HOLD

You should HOLD (and this should be your most common decision) if:
- Both cases are within 15% confidence of each other
- Neither case has overwhelming technical evidence
- The risk/reward ratio is not clearly favorable (at least 1.5:1)
- You have any significant doubts about the trade

You should only choose BUY or SELL if:
- One case has clearly superior technical evidence
- The confidence gap is significant (>20%)
- The risk/reward is clearly favorable
- You are highly confident in the direction

Respond with ONLY valid JSON (no other text):
{{
  "decision": "HOLD",
  "reasoning": "2-3 sentence explanation",
  "winning_case": "NEITHER",
  "confidence": 50,
  "entry_price": null,
  "stop_loss": null,
  "take_profit": null,
  "position_size": "SMALL",
  "time_horizon": "HOURS",
  "risk_factors": ["risk1", "risk2"]
}}

Use "BUY", "SELL", or "HOLD" for decision. Use "BULL", "BEAR", or "NEITHER" for winning_case. For BUY/SELL use actual price numbers; for HOLD use null."""

        return self.generate_response(
            prompt=judge_prompt,
            system_prompt="You are an impartial trading judge. Respond with ONLY valid JSON, no other text.",
            temperature=0.3,
            max_tokens=800
        )

    def format_market_data(self, market_data: Dict[str, Any]) -> str:
        """
        Format market data into a readable prompt for DAY TRADING analysis.

        All data is INTRADAY - indicators are calculated on 1-minute bars.
        """
        formatted = []

        formatted.append("=" * 60)
        formatted.append("INTRADAY MARKET DATA (all indicators from 1-minute bars)")
        formatted.append("=" * 60)

        if "symbol" in market_data:
            formatted.append(f"\nSymbol: {market_data['symbol']}")

        if "current_price" in market_data:
            formatted.append(f"Current Price: ${market_data['current_price']:.2f}")

        # Daily context (for gap analysis)
        formatted.append("\n--- DAILY CONTEXT ---")
        if "today_open" in market_data:
            formatted.append(f"Today's Open: ${market_data['today_open']:.2f}")
        if "prev_close" in market_data:
            formatted.append(f"Previous Close: ${market_data['prev_close']:.2f}")
        if "gap_percent" in market_data:
            gap_dir = "up" if market_data['gap_percent'] > 0 else "down"
            formatted.append(f"Gap: {market_data['gap_percent']:+.2f}% ({gap_dir} from prev close)")
        if "daily_change_percent" in market_data:
            formatted.append(f"Daily Change (from prev close): {market_data['daily_change_percent']:+.2f}%")
        if "today_high" in market_data:
            formatted.append(f"Today's High: ${market_data['today_high']:.2f}")
        if "today_low" in market_data:
            formatted.append(f"Today's Low: ${market_data['today_low']:.2f}")

        # Intraday price action
        formatted.append("\n--- INTRADAY PRICE ACTION (last ~1.5 hours) ---")
        if "intraday_change_percent" in market_data:
            formatted.append(f"Intraday Change: {market_data['intraday_change_percent']:+.2f}%")
        if "intraday_high" in market_data:
            formatted.append(f"Intraday High: ${market_data['intraday_high']:.2f}")
        if "intraday_low" in market_data:
            formatted.append(f"Intraday Low: ${market_data['intraday_low']:.2f}")
        if "intraday_volume" in market_data:
            formatted.append(f"Intraday Volume: {market_data['intraday_volume']:,}")

        # Quote data
        if "bid" in market_data:
            formatted.append(f"\nBid: ${market_data['bid']:.2f} | Ask: ${market_data['ask']:.2f} | Spread: ${market_data['spread']:.4f}")

        # Technical indicators (all intraday)
        if "technical_indicators" in market_data:
            formatted.append("\n--- INTRADAY TECHNICAL INDICATORS ---")
            formatted.append("(All calculated on 1-minute bars - NOT daily/weekly data)")

            tech = market_data["technical_indicators"]

            # Group indicators by category for clarity
            # VWAP - most important for day trading
            if "VWAP" in tech:
                formatted.append(f"\nVWAP (Volume-Weighted Avg Price): ${tech['VWAP']}")
                if "VWAP_position" in tech:
                    formatted.append(f"  Position: {tech['VWAP_position']}")
                if "VWAP_distance_percent" in tech:
                    formatted.append(f"  Distance from VWAP: {tech['VWAP_distance_percent']:+.2f}%")

            # Moving Averages
            ma_keys = [k for k in tech if 'SMA' in k or 'EMA' in k]
            if ma_keys:
                formatted.append("\nIntraday Moving Averages:")
                for k in ma_keys:
                    formatted.append(f"  {k}: ${tech[k]}")

            # Momentum
            formatted.append("\nMomentum Indicators:")
            if "RSI_14min" in tech:
                formatted.append(f"  RSI (14-min): {tech['RSI_14min']}")
                if "RSI_signal" in tech:
                    formatted.append(f"    Signal: {tech['RSI_signal']}")
            if "momentum_5min_percent" in tech:
                formatted.append(f"  5-min Momentum: {tech['momentum_5min_percent']:+.2f}%")
            if "momentum_15min_percent" in tech:
                formatted.append(f"  15-min Momentum: {tech['momentum_15min_percent']:+.2f}%")
            if "MACD" in tech:
                formatted.append(f"  MACD: {tech['MACD']:.4f}")
                if "MACD_trend" in tech:
                    formatted.append(f"    Trend: {tech['MACD_trend']}")

            # Volatility
            formatted.append("\nVolatility:")
            if "BB_upper" in tech:
                formatted.append(f"  Bollinger Bands: ${tech['BB_lower']:.2f} - ${tech['BB_middle']:.2f} - ${tech['BB_upper']:.2f}")
                if "BB_signal" in tech:
                    formatted.append(f"    Signal: {tech['BB_signal']}")
            if "ATR_14min" in tech:
                formatted.append(f"  ATR (14-min): ${tech['ATR_14min']:.2f} ({tech.get('ATR_percent', 0):.2f}% of price)")

            # Volume
            formatted.append("\nVolume Analysis:")
            if "volume_ratio" in tech:
                formatted.append(f"  Volume Ratio: {tech['volume_ratio']:.2f}x average")
                if "volume_signal" in tech:
                    formatted.append(f"    Signal: {tech['volume_signal']}")
            if "OBV_trend" in tech:
                formatted.append(f"  OBV Trend: {tech['OBV_trend']}")

            # Stochastic
            if "STOCH_K" in tech:
                formatted.append(f"\nStochastic: K={tech['STOCH_K']:.1f}, D={tech['STOCH_D']:.1f}")
                if "STOCH_signal" in tech:
                    formatted.append(f"  Signal: {tech['STOCH_signal']}")

            # Support/Resistance
            if "intraday_pivot" in tech:
                formatted.append("\nIntraday Support/Resistance (from last 30 bars):")
                formatted.append(f"  Pivot: ${tech['intraday_pivot']:.2f}")
                formatted.append(f"  R1: ${tech['intraday_R1']:.2f} | R2: ${tech['intraday_R2']:.2f}")
                formatted.append(f"  S1: ${tech['intraday_S1']:.2f} | S2: ${tech['intraday_S2']:.2f}")
                if "pivot_position" in tech:
                    formatted.append(f"  Current Position: {tech['pivot_position']}")

        if "news" in market_data and market_data["news"]:
            formatted.append("\n--- RECENT NEWS ---")
            for i, headline in enumerate(market_data["news"][:5], 1):
                formatted.append(f"  {i}. {headline}")

        # Add market sentiment
        if "market_sentiment" in market_data:
            ms = market_data["market_sentiment"]
            formatted.append("\n--- OVERALL MARKET SENTIMENT ---")
            formatted.append(f"  Status: {ms.get('summary', 'Unknown')} (Score: {ms.get('overall_score', 0):.2f})")

            if "indicators" in ms:
                for name, data in ms["indicators"].items():
                    if "interpretation" in data:
                        formatted.append(f"  - {data['interpretation']}")

        # Add stock-specific sentiment
        if "stock_sentiment" in market_data:
            ss = market_data["stock_sentiment"]
            formatted.append(f"\n--- {market_data['symbol']} SPECIFIC SENTIMENT ---")
            formatted.append(f"  Status: {ss.get('summary', 'Unknown')} (Score: {ss.get('overall_score', 0):.2f})")

            if "sources" in ss:
                for name, data in ss["sources"].items():
                    if data and "interpretation" in data:
                        formatted.append(f"  - {data['interpretation']}")

        formatted.append("\n" + "=" * 60)

        return "\n".join(formatted)
