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
