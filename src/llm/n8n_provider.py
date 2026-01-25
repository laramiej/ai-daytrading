"""
n8n Workflow LLM Provider
Integrates with n8n workflow for comprehensive stock analysis
"""
import json
import logging
import requests
from typing import Optional, Dict, Any

from .base import BaseLLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class N8nProvider(BaseLLMProvider):
    """
    n8n workflow provider - delegates stock analysis to an n8n workflow.

    The n8n workflow handles:
    - Data fetching (TwelveData, NewsAPI)
    - Technical indicators calculation
    - Market context (SPY, VIX)
    - Sentiment analysis
    - Final trading recommendation

    This provider sends only the stock symbol and receives a complete analysis.
    """

    def __init__(
        self,
        api_key: str = None,
        model: Optional[str] = None,
        webhook_url: Optional[str] = None,
        timeout: int = 120
    ):
        """
        Initialize the n8n provider.

        Args:
            api_key: For compatibility - can be used as webhook_url if webhook_url not provided
            model: Model identifier (informational only for n8n)
            webhook_url: The n8n webhook URL to call
            timeout: Request timeout in seconds (default 120)
        """
        # n8n doesn't use traditional api_key, use it as webhook_url if needed
        self.webhook_url = webhook_url or api_key
        self.timeout = timeout
        self.model = model or self.get_default_model()
        self.provider_name = "n8n"

        if not self.webhook_url:
            raise ValueError("n8n webhook URL is required")

        logger.info(f"N8nProvider initialized with webhook: {self._mask_url(self.webhook_url)}")

    def _mask_url(self, url: str) -> str:
        """Mask URL for logging (show host but not full path)"""
        if not url:
            return "None"
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return f"{parsed.scheme}://{parsed.netloc}/..."
        except Exception:
            return "***"

    def get_default_model(self) -> str:
        """Return the default model identifier for n8n"""
        return "n8n-stock-analysis-v1"

    def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """
        n8n provider doesn't support generic prompts.

        The n8n workflow is designed for stock analysis, not general chat.
        Use analyze_market_data() instead.

        Raises:
            NotImplementedError: Always, as n8n doesn't support generic prompts
        """
        raise NotImplementedError(
            "N8nProvider doesn't support generic prompts. "
            "Use analyze_market_data() for stock analysis."
        )

    def analyze_market_data(
        self,
        market_data: Dict[str, Any],
        context: Optional[str] = None
    ) -> LLMResponse:
        """
        Send symbol to n8n workflow for comprehensive stock analysis.

        The n8n workflow handles all data fetching and analysis internally.
        We only need to send the stock symbol.

        Args:
            market_data: Must contain 'symbol' key with stock ticker
            context: Optional context (passed to workflow if supported)

        Returns:
            LLMResponse with JSON content containing trading signal

        Raises:
            ValueError: If market_data doesn't contain 'symbol'
            Exception: On network errors or workflow failures
        """
        symbol = market_data.get('symbol', '')
        if not symbol:
            raise ValueError("Market data must include 'symbol'")

        logger.info(f"Calling n8n workflow for symbol: {symbol}")

        try:
            # Prepare request payload
            payload = {
                "symbol": symbol
            }

            # Add context if provided (workflow may use it)
            if context:
                payload["context"] = context

            # Make the request to n8n webhook
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            # Parse JSON response
            result = response.json()
            logger.debug(f"n8n raw response: {json.dumps(result, indent=2)[:500]}...")

            # Check for workflow errors
            if isinstance(result, dict) and result.get('success') is False:
                error_msg = result.get('error', 'Unknown error from n8n workflow')
                raise Exception(f"n8n workflow error: {error_msg}")

            # Extract trading signal data from n8n response
            # n8n may return the data in different formats depending on workflow
            signal_data = self._extract_signal_data(result, symbol)

            # Format as JSON string for TradingStrategy to parse
            content = json.dumps(signal_data)

            return LLMResponse(
                content=content,
                model=self.model,
                provider="n8n",
                tokens_used=None,  # n8n doesn't track tokens
                metadata={
                    "webhook_url": self._mask_url(self.webhook_url),
                    "symbol": symbol,
                    "raw_response_type": type(result).__name__
                }
            )

        except requests.Timeout:
            logger.error(f"n8n workflow timed out after {self.timeout}s for {symbol}")
            raise Exception(f"n8n workflow timed out after {self.timeout}s")
        except requests.RequestException as e:
            logger.error(f"n8n webhook request failed for {symbol}: {str(e)}")
            raise Exception(f"n8n webhook request failed: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"n8n returned invalid JSON for {symbol}: {str(e)}")
            raise Exception(f"n8n returned invalid JSON response: {str(e)}")

    def _extract_signal_data(self, result: Any, symbol: str) -> Dict[str, Any]:
        """
        Extract trading signal data from n8n response.

        Handles various response formats the n8n workflow might return.

        Args:
            result: The parsed JSON response from n8n
            symbol: The stock symbol (for error messages)

        Returns:
            Dictionary with standardized signal fields
        """
        # If result is already a properly formatted signal dict
        if isinstance(result, dict):
            # Check if it has expected signal fields
            if 'signal' in result:
                return self._normalize_signal(result, symbol)

            # n8n might wrap in 'output' or 'data'
            if 'output' in result:
                return self._extract_signal_data(result['output'], symbol)
            if 'data' in result:
                return self._extract_signal_data(result['data'], symbol)

            # Try to find signal in nested structure
            for key in ['result', 'response', 'analysis']:
                if key in result:
                    return self._extract_signal_data(result[key], symbol)

        # If result is a string, try to parse it as JSON
        if isinstance(result, str):
            try:
                parsed = json.loads(result)
                return self._extract_signal_data(parsed, symbol)
            except json.JSONDecodeError:
                # It might be a plain text analysis - extract what we can
                return self._parse_text_response(result, symbol)

        # If result is a list, take the first item
        if isinstance(result, list) and len(result) > 0:
            return self._extract_signal_data(result[0], symbol)

        # Fallback - return HOLD signal
        logger.warning(f"Could not extract signal from n8n response for {symbol}, defaulting to HOLD")
        return {
            "signal": "HOLD",
            "confidence": 50,
            "reasoning": "Unable to parse n8n response - defaulting to HOLD",
            "contrary_reasoning": "",
            "entry_price": None,
            "stop_loss": None,
            "take_profit": None,
            "position_size_recommendation": "SMALL",
            "risk_factors": ["Unable to parse n8n workflow response"],
            "time_horizon": "intraday"
        }

    def _normalize_signal(self, data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """
        Normalize signal data to expected format.

        Maps various field names to the standard TradingSignal format.
        """
        # Map possible field name variations
        signal = data.get('signal') or data.get('decision') or data.get('action') or 'HOLD'
        signal = signal.upper() if isinstance(signal, str) else 'HOLD'

        # Normalize signal values
        if signal in ['BUY', 'LONG']:
            signal = 'BUY'
        elif signal in ['SELL', 'SHORT']:
            signal = 'SELL'
        else:
            signal = 'HOLD'

        confidence = data.get('confidence') or data.get('confidence_level') or 50
        if isinstance(confidence, str):
            try:
                confidence = float(confidence.replace('%', ''))
            except ValueError:
                confidence = 50

        return {
            "signal": signal,
            "confidence": min(100, max(0, float(confidence))),
            "reasoning": data.get('reasoning') or data.get('rationale') or data.get('analysis') or '',
            "contrary_reasoning": data.get('contrary_reasoning') or data.get('risks') or '',
            "entry_price": data.get('entry_price') or data.get('entry') or data.get('price'),
            "stop_loss": data.get('stop_loss') or data.get('stopLoss'),
            "take_profit": data.get('take_profit') or data.get('takeProfit') or data.get('target'),
            "position_size_recommendation": data.get('position_size_recommendation') or data.get('position_size') or 'SMALL',
            "risk_factors": data.get('risk_factors') or data.get('risks') or [],
            "time_horizon": data.get('time_horizon') or data.get('timeframe') or 'intraday'
        }

    def _parse_text_response(self, text: str, symbol: str) -> Dict[str, Any]:
        """
        Try to extract signal from plain text response.

        This is a fallback for when n8n returns markdown or plain text.
        """
        text_upper = text.upper()

        # Try to detect signal from text
        signal = 'HOLD'
        if 'BUY' in text_upper and 'SELL' not in text_upper:
            signal = 'BUY'
        elif 'SELL' in text_upper and 'BUY' not in text_upper:
            signal = 'SELL'

        # Try to extract confidence
        confidence = 50
        import re
        conf_match = re.search(r'confidence[:\s]*(\d+)', text, re.IGNORECASE)
        if conf_match:
            confidence = int(conf_match.group(1))

        return {
            "signal": signal,
            "confidence": confidence,
            "reasoning": text[:500] if len(text) > 500 else text,
            "contrary_reasoning": "",
            "entry_price": None,
            "stop_loss": None,
            "take_profit": None,
            "position_size_recommendation": "SMALL",
            "risk_factors": ["Response was plain text - limited parsing"],
            "time_horizon": "intraday"
        }

    # Override debate methods - n8n doesn't support separate debate calls
    def make_bull_case(self, market_data: Dict[str, Any]) -> LLMResponse:
        """
        n8n workflow provides complete analysis, not separate debate cases.

        Raises:
            NotImplementedError: n8n doesn't support separate debate calls
        """
        raise NotImplementedError(
            "N8nProvider provides complete analysis via analyze_market_data(). "
            "Separate bull/bear/judge calls are not supported."
        )

    def make_bear_case(self, market_data: Dict[str, Any]) -> LLMResponse:
        """
        n8n workflow provides complete analysis, not separate debate cases.

        Raises:
            NotImplementedError: n8n doesn't support separate debate calls
        """
        raise NotImplementedError(
            "N8nProvider provides complete analysis via analyze_market_data(). "
            "Separate bull/bear/judge calls are not supported."
        )

    def judge_debate(
        self,
        bull_case: Dict[str, Any],
        bear_case: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> LLMResponse:
        """
        n8n workflow provides complete analysis, not separate debate cases.

        Raises:
            NotImplementedError: n8n doesn't support separate debate calls
        """
        raise NotImplementedError(
            "N8nProvider provides complete analysis via analyze_market_data(). "
            "Separate bull/bear/judge calls are not supported."
        )
