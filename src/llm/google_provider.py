"""
Google Gemini LLM Provider
"""
import google.generativeai as genai
from typing import Optional, Dict, Any
from .base import BaseLLMProvider, LLMResponse


class GoogleProvider(BaseLLMProvider):
    """Google Gemini provider implementation"""

    def __init__(self, api_key: str, model: Optional[str] = None):
        super().__init__(api_key, model)
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(self.model)

    def get_default_model(self) -> str:
        return "gemini-pro"

    def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """Generate response using Gemini"""
        try:
            # Combine system prompt with user prompt for Gemini
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )

            response = self.client.generate_content(
                full_prompt,
                generation_config=generation_config
            )

            content = response.text

            return LLMResponse(
                content=content,
                model=self.model,
                provider="google",
                tokens_used=None,  # Gemini doesn't always provide token counts
                metadata={
                    "candidates": len(response.candidates) if hasattr(response, 'candidates') else 1
                }
            )
        except Exception as e:
            raise Exception(f"Google Gemini API error: {str(e)}")

    def analyze_market_data(
        self,
        market_data: Dict[str, Any],
        context: Optional[str] = None
    ) -> LLMResponse:
        """Analyze market data using Gemini"""
        formatted_data = self.format_market_data(market_data)

        system_prompt = """You are an expert day trader and financial analyst with deep knowledge of:
- Technical analysis (support/resistance, momentum, trend indicators)
- Fundamental analysis (earnings, news impact, market sentiment)
- Risk management and position sizing
- Market microstructure and order flow
- Both long and short trading strategies

Your analysis should be:
1. Data-driven and objective
2. Conservative with risk assessment
3. Clear about confidence levels
4. Specific about entry/exit points
5. Focused on day trading timeframes (intraday opportunities)
6. Reference specific data points in your reasoning
7. Consider BOTH bullish AND bearish opportunities

SIGNAL TYPES - You can recommend THREE different actions:
- BUY: Open a new long position (expecting price to rise) OR add to existing long position
- SELL: Either close an existing long position OR open a new short position (expecting price to fall)
- HOLD: No action - wait for a better setup

IMPORTANT: Look for opportunities in BOTH directions:
- Bullish setups: Oversold conditions, positive momentum, breakouts above resistance, bullish sentiment
- Bearish setups: Overbought conditions, negative momentum, breakdowns below support, bearish sentiment

When you see strong bearish signals (high RSI, breakdown below support, negative sentiment, bearish MACD crossover),
recommend SELL with high confidence - this can be used to SHORT the stock for profit as price falls.

CRITICAL: Your "reasoning" field must be detailed and reference the specific data you analyzed:
- Cite exact technical indicator values (e.g., "RSI at 75 indicates overbought conditions ripe for a pullback")
- Reference price levels (e.g., "Price at $175.50 broke below VWAP at $176.00 showing bearish institutional selling")
- Mention volume patterns (e.g., "Volume 1.5x average on down move confirms selling pressure")
- Reference sentiment data (e.g., "Negative news sentiment at -0.3 supports bearish thesis")
- Cite support/resistance levels (e.g., "Breaking below pivot S1 at $174.00 opens path to S2 at $172.50")
- Explain how multiple indicators align for either bullish or bearish setups

Your reasoning should be 3-5 detailed sentences that justify your signal with specific data points.

Format your response as JSON with these fields:
{
  "signal": "BUY" | "SELL" | "HOLD",
  "confidence": 0-100,
  "reasoning": "Detailed explanation citing specific technical indicators, price levels, volume, sentiment, and support/resistance levels from the data provided. Explain how these data points support your signal. 3-5 sentences required.",
  "entry_price": <number or null>,
  "stop_loss": <number or null>,
  "take_profit": <number or null>,
  "position_size_recommendation": "SMALL" | "MEDIUM" | "LARGE",
  "risk_factors": ["list", "of", "risks"],
  "time_horizon": "minutes or hours for this trade"
}"""

        prompt = f"""Analyze the following market data and provide a day trading recommendation:

{formatted_data}

{f'Additional Context: {context}' if context else ''}

Provide your analysis in the JSON format specified."""

        return self.generate_response(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=1500
        )
