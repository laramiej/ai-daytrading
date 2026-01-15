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
        """Helper to format market data into a readable prompt"""
        formatted = []

        if "symbol" in market_data:
            formatted.append(f"Symbol: {market_data['symbol']}")

        if "current_price" in market_data:
            formatted.append(f"Current Price: ${market_data['current_price']:.2f}")

        if "change_percent" in market_data:
            formatted.append(f"Daily Change: {market_data['change_percent']:.2f}%")

        if "volume" in market_data:
            formatted.append(f"Volume: {market_data['volume']:,}")

        if "technical_indicators" in market_data:
            formatted.append("\nTechnical Indicators:")
            for indicator, value in market_data["technical_indicators"].items():
                formatted.append(f"  - {indicator}: {value}")

        if "news" in market_data:
            formatted.append("\nRecent News Headlines:")
            for i, headline in enumerate(market_data["news"][:5], 1):
                formatted.append(f"  {i}. {headline}")

        # Add market sentiment
        if "market_sentiment" in market_data:
            ms = market_data["market_sentiment"]
            formatted.append("\nOverall Market Sentiment:")
            formatted.append(f"  Status: {ms.get('summary', 'Unknown')} (Score: {ms.get('overall_score', 0):.2f})")

            if "indicators" in ms:
                for name, data in ms["indicators"].items():
                    if "interpretation" in data:
                        formatted.append(f"  - {data['interpretation']}")

        # Add stock-specific sentiment
        if "stock_sentiment" in market_data:
            ss = market_data["stock_sentiment"]
            formatted.append(f"\n{market_data['symbol']} Sentiment:")
            formatted.append(f"  Status: {ss.get('summary', 'Unknown')} (Score: {ss.get('overall_score', 0):.2f})")

            if "sources" in ss:
                for name, data in ss["sources"].items():
                    if data and "interpretation" in data:
                        formatted.append(f"  - {data['interpretation']}")

        return "\n".join(formatted)
