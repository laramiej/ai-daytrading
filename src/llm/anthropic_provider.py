"""
Anthropic Claude LLM Provider
"""
import anthropic
from typing import Optional, Dict, Any
from .base import BaseLLMProvider, LLMResponse


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider implementation"""

    def __init__(self, api_key: str, model: Optional[str] = None):
        super().__init__(api_key, model)
        self.client = anthropic.Anthropic(api_key=api_key)

    def get_default_model(self) -> str:
        # Using Claude 3 Haiku - fast and cost-effective model
        return "claude-3-haiku-20240307"

    def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """Generate response using Claude"""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt or "You are a professional financial analyst and day trader.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            content = message.content[0].text
            tokens_used = message.usage.input_tokens + message.usage.output_tokens

            return LLMResponse(
                content=content,
                model=self.model,
                provider="anthropic",
                tokens_used=tokens_used,
                metadata={
                    "input_tokens": message.usage.input_tokens,
                    "output_tokens": message.usage.output_tokens
                }
            )
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")

    def analyze_market_data(
        self,
        market_data: Dict[str, Any],
        context: Optional[str] = None
    ) -> LLMResponse:
        """Analyze market data using Claude"""
        formatted_data = self.format_market_data(market_data)

        system_prompt = """You are an expert INTRADAY day trader. You ONLY trade within a single day - no overnight positions.

CRITICAL: This is DAY TRADING ONLY. All data you receive is INTRADAY:
- Technical indicators are calculated on 1-MINUTE bars (not daily/weekly charts)
- "RSI_14min" means 14 one-minute bars, NOT 14 days
- "SMA_20min" means 20 one-minute average, NOT 20 days
- "momentum_5min" means price change over last 5 MINUTES
- You are looking for trades lasting MINUTES to HOURS, not days or weeks

KEY DAY TRADING INDICATORS TO PRIORITIZE:
1. VWAP (Volume-Weighted Average Price) - THE most important day trading indicator
   - Price above VWAP = bullish intraday bias
   - Price below VWAP = bearish intraday bias
   - Bounces off VWAP are high-probability setups

2. Intraday Momentum (5-min and 15-min momentum)
   - Shows very short-term price direction
   - Divergences from price action signal reversals

3. Volume Ratio - High volume confirms moves, low volume suggests weakness

4. Intraday Support/Resistance (pivot, R1, S1) - Key levels for the session

5. Gap Analysis - Gaps from previous close often fill during the day

Your analysis should be:
1. INTRADAY FOCUSED - trades expected to close today
2. Data-driven using the minute-level indicators provided
3. Conservative (day trading requires discipline)
4. Reference VWAP, intraday pivots, and short-term momentum

SIGNAL TYPES:
- BUY: Open a new long position (expecting price to rise) OR add to existing long position
- SELL: Either close an existing long position OR open a new short position (expecting price to fall)
- HOLD: No action - wait for a better intraday setup

LOOK FOR INTRADAY SETUPS:
- Bullish: Price reclaiming VWAP, oversold RSI bouncing, positive 5-min momentum, above intraday pivot
- Bearish: Price rejecting VWAP, overbought RSI failing, negative momentum, below intraday pivot
- Gap fills: Stocks that gapped up/down often revert toward previous close

CRITICAL - Your "reasoning" MUST reference INTRADAY data:
- "RSI_14min at 75 shows overbought on the 1-minute chart, expecting pullback"
- "Price broke below VWAP at $176.00, indicating intraday selling pressure"
- "5-min momentum at -0.5% with 2x volume confirms short-term bearish move"
- "Trading above intraday R1 at $180.50, next target is R2 at $182.00"
- "Stock gapped up 1.5% and failing at VWAP - gap fill trade to previous close"

Your reasoning should be 3-5 sentences citing specific INTRADAY indicator values.

Format your response as JSON:
{
  "signal": "BUY" | "SELL" | "HOLD",
  "confidence": 0-100,
  "reasoning": "Detailed explanation citing INTRADAY indicators (VWAP, RSI_14min, momentum_5min, intraday pivots, etc). 3-5 sentences required.",
  "entry_price": <number - current market price for entry>,
  "position_size_recommendation": "SMALL" | "MEDIUM" | "LARGE",
  "risk_factors": ["list", "of", "intraday", "risks"],
  "time_horizon": "X minutes" or "X hours" (must be INTRADAY)
}"""

        prompt = f"""Analyze the following market data and provide a day trading recommendation:

{formatted_data}

{f'Additional Context: {context}' if context else ''}

Provide your analysis in the JSON format specified."""

        return self.generate_response(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,  # Lower temperature for more consistent analysis
            max_tokens=1500
        )
