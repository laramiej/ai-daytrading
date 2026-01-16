"""
Market Data Analyzer
Fetches and analyzes market data for trading decisions
"""
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from .sentiment_analyzer import SentimentAnalyzer

logger = logging.getLogger(__name__)


class MarketAnalyzer:
    """Analyzes market data and calculates technical indicators"""

    def __init__(self, broker, include_sentiment: bool = True, enable_google_trends: bool = True, finnhub_api_key: str = None, enable_finnhub: bool = True):
        """
        Initialize market analyzer

        Args:
            broker: Broker client instance for fetching data
            include_sentiment: Whether to include sentiment analysis
            enable_google_trends: Whether to enable Google Trends analysis
            finnhub_api_key: Finnhub API key (optional)
            enable_finnhub: Whether to enable Finnhub analysis
        """
        self.broker = broker
        self.include_sentiment = include_sentiment
        self.sentiment_analyzer = SentimentAnalyzer(
            enable_google_trends=enable_google_trends,
            finnhub_api_key=finnhub_api_key,
            enable_finnhub=enable_finnhub
        ) if include_sentiment else None
        self._market_sentiment_cache = None
        self._market_sentiment_time = None

    def get_market_data(
        self,
        symbol: str,
        include_technicals: bool = True,
        include_news: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch comprehensive market data for a symbol

        Args:
            symbol: Stock symbol
            include_technicals: Include technical indicators
            include_news: Include recent news

        Returns:
            Dictionary with market data
        """
        try:
            # Get latest quote
            quote = self.broker.get_latest_quote(symbol)

            # Get recent bars for technical analysis
            bars = self.broker.get_bars(symbol, timeframe="1Min", limit=100)

            if not bars:
                logger.warning(f"No bar data available for {symbol}")
                return None

            # Calculate current price and change
            current_price = (quote["bid_price"] + quote["ask_price"]) / 2
            df = pd.DataFrame(bars)

            market_data = {
                "symbol": symbol,
                "current_price": current_price,
                "bid": quote["bid_price"],
                "ask": quote["ask_price"],
                "spread": quote["ask_price"] - quote["bid_price"],
                "timestamp": datetime.now()
            }

            # Calculate price change
            if len(df) > 0:
                open_price = df.iloc[0]["open"]
                change = current_price - open_price
                change_percent = (change / open_price) * 100

                market_data["open_price"] = open_price
                market_data["change"] = change
                market_data["change_percent"] = change_percent
                market_data["volume"] = int(df["volume"].sum())

            # Add technical indicators
            if include_technicals and len(df) > 0:
                market_data["technical_indicators"] = self._calculate_technicals(df)

            # Add news
            if include_news:
                market_data["news"] = self._fetch_news(symbol)

            # Add sentiment analysis
            if self.include_sentiment and self.sentiment_analyzer:
                # Get market sentiment (cached for 15 minutes)
                market_sentiment = self._get_cached_market_sentiment()
                if market_sentiment:
                    market_data["market_sentiment"] = market_sentiment

                # Get stock-specific sentiment
                stock_sentiment = self.sentiment_analyzer.get_stock_sentiment(symbol)
                if stock_sentiment:
                    market_data["stock_sentiment"] = stock_sentiment

            return market_data

        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {e}")
            return None

    def _calculate_technicals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate technical indicators

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Dictionary of technical indicators
        """
        indicators = {}

        try:
            # Simple Moving Averages
            if len(df) >= 20:
                indicators["SMA_20"] = round(df["close"].rolling(window=20).mean().iloc[-1], 2)

            if len(df) >= 50:
                indicators["SMA_50"] = round(df["close"].rolling(window=50).mean().iloc[-1], 2)

            # Exponential Moving Averages
            if len(df) >= 12:
                indicators["EMA_12"] = round(df["close"].ewm(span=12, adjust=False).mean().iloc[-1], 2)

            if len(df) >= 26:
                indicators["EMA_26"] = round(df["close"].ewm(span=26, adjust=False).mean().iloc[-1], 2)

            # RSI (Relative Strength Index)
            if len(df) >= 14:
                indicators["RSI_14"] = round(self._calculate_rsi(df["close"], 14), 2)

            # MACD
            if len(df) >= 26:
                macd_data = self._calculate_macd(df["close"])
                indicators["MACD"] = round(macd_data["macd"], 2)
                indicators["MACD_signal"] = round(macd_data["signal"], 2)
                indicators["MACD_histogram"] = round(macd_data["histogram"], 2)

            # Bollinger Bands
            if len(df) >= 20:
                bb = self._calculate_bollinger_bands(df["close"], 20)
                indicators["BB_upper"] = round(bb["upper"], 2)
                indicators["BB_middle"] = round(bb["middle"], 2)
                indicators["BB_lower"] = round(bb["lower"], 2)

            # Volume analysis
            if len(df) >= 20:
                avg_volume = df["volume"].rolling(window=20).mean().iloc[-1]
                current_volume = df["volume"].iloc[-1]
                indicators["volume_ratio"] = round(current_volume / avg_volume, 2) if avg_volume > 0 else 1.0

            # Price momentum
            if len(df) >= 10:
                momentum = df["close"].iloc[-1] - df["close"].iloc[-10]
                indicators["momentum_10"] = round(momentum, 2)

            # VWAP (Volume-Weighted Average Price)
            if len(df) >= 1 and df["volume"].sum() > 0:
                vwap = (df["close"] * df["volume"]).sum() / df["volume"].sum()
                indicators["VWAP"] = round(vwap, 2)

                # VWAP position relative to current price
                current_price = df["close"].iloc[-1]
                indicators["VWAP_position"] = round(((current_price - vwap) / vwap) * 100, 2)

            # ATR (Average True Range) - Volatility measure
            if len(df) >= 14:
                atr = self._calculate_atr(df, 14)
                indicators["ATR_14"] = round(atr, 2)

                # ATR as % of price (normalized volatility)
                current_price = df["close"].iloc[-1]
                if current_price > 0:
                    indicators["ATR_percent"] = round((atr / current_price) * 100, 2)

            # Stochastic Oscillator
            if len(df) >= 14:
                stoch = self._calculate_stochastic(df, 14, 3)
                indicators["STOCH_K"] = round(stoch["k"], 2)
                indicators["STOCH_D"] = round(stoch["d"], 2)

                # Overbought/Oversold status
                if stoch["k"] > 80:
                    indicators["STOCH_signal"] = "Overbought"
                elif stoch["k"] < 20:
                    indicators["STOCH_signal"] = "Oversold"
                else:
                    indicators["STOCH_signal"] = "Neutral"

            # OBV (On-Balance Volume) - Volume flow indicator
            if len(df) >= 10:
                obv = self._calculate_obv(df)
                indicators["OBV"] = int(obv)

                # OBV trend (10-period change)
                if len(df) >= 20:
                    price_change_10 = df["close"].diff().tail(10)
                    direction_10 = np.sign(price_change_10)
                    obv_10_ago = (direction_10 * df["volume"].tail(10)).fillna(0).cumsum().iloc[0]
                    obv_change = obv - obv_10_ago
                    indicators["OBV_trend"] = "Rising" if obv_change > 0 else "Falling"

            # Pivot Points (Support/Resistance levels)
            if len(df) >= 2:
                pivots = self._calculate_pivot_points(df)
                current_price = df["close"].iloc[-1]

                indicators["PIVOT"] = round(pivots["pivot"], 2)
                indicators["PIVOT_R1"] = round(pivots["resistance_1"], 2)
                indicators["PIVOT_S1"] = round(pivots["support_1"], 2)
                indicators["PIVOT_R2"] = round(pivots["resistance_2"], 2)
                indicators["PIVOT_S2"] = round(pivots["support_2"], 2)

                # Identify current position
                if current_price > pivots["resistance_1"]:
                    indicators["PIVOT_position"] = "Above R1 (Strong)"
                elif current_price > pivots["pivot"]:
                    indicators["PIVOT_position"] = "Above Pivot"
                elif current_price > pivots["support_1"]:
                    indicators["PIVOT_position"] = "Below Pivot"
                else:
                    indicators["PIVOT_position"] = "Below S1 (Weak)"

        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")

        return indicators

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0

    def _calculate_macd(
        self,
        prices: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Dict[str, float]:
        """Calculate MACD indicator"""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()

        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line

        return {
            "macd": macd.iloc[-1],
            "signal": signal_line.iloc[-1],
            "histogram": histogram.iloc[-1]
        }

    def _calculate_bollinger_bands(
        self,
        prices: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Dict[str, float]:
        """Calculate Bollinger Bands"""
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()

        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        return {
            "upper": upper.iloc[-1],
            "middle": middle.iloc[-1],
            "lower": lower.iloc[-1]
        }

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """
        Calculate Average True Range

        Args:
            df: DataFrame with OHLC data
            period: Lookback period (default 14)

        Returns:
            ATR value
        """
        # True Range = max(high-low, abs(high-prev_close), abs(low-prev_close))
        high_low = df["high"] - df["low"]
        high_close = abs(df["high"] - df["close"].shift(1))
        low_close = abs(df["low"] - df["close"].shift(1))

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()

        return atr.iloc[-1] if not pd.isna(atr.iloc[-1]) else 0.0

    def _calculate_stochastic(self, df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Dict[str, float]:
        """
        Calculate Stochastic Oscillator

        Args:
            df: DataFrame with OHLC data
            k_period: %K period (default 14)
            d_period: %D smoothing period (default 3)

        Returns:
            Dictionary with %K and %D values
        """
        # %K = 100 * (Close - Lowest Low) / (Highest High - Lowest Low)
        low_min = df["low"].rolling(window=k_period).min()
        high_max = df["high"].rolling(window=k_period).max()

        k = 100 * ((df["close"] - low_min) / (high_max - low_min))
        d = k.rolling(window=d_period).mean()

        return {
            "k": k.iloc[-1] if not pd.isna(k.iloc[-1]) else 50.0,
            "d": d.iloc[-1] if not pd.isna(d.iloc[-1]) else 50.0
        }

    def _calculate_obv(self, df: pd.DataFrame) -> float:
        """
        Calculate On-Balance Volume

        Args:
            df: DataFrame with close prices and volume

        Returns:
            Current OBV value
        """
        # OBV increases by volume when price rises, decreases when price falls
        price_change = df["close"].diff()
        direction = np.sign(price_change)  # +1, 0, or -1

        obv = (direction * df["volume"]).fillna(0).cumsum()

        return obv.iloc[-1]

    def _calculate_pivot_points(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate Pivot Points (Standard Method)

        Uses previous period's high, low, close to calculate support/resistance

        Args:
            df: DataFrame with OHLC data

        Returns:
            Dictionary with pivot levels
        """
        # Use previous bar's data
        high = df["high"].iloc[-2] if len(df) >= 2 else df["high"].iloc[-1]
        low = df["low"].iloc[-2] if len(df) >= 2 else df["low"].iloc[-1]
        close = df["close"].iloc[-2] if len(df) >= 2 else df["close"].iloc[-1]

        # Pivot Point
        pivot = (high + low + close) / 3

        # Support and Resistance levels
        r1 = (2 * pivot) - low
        s1 = (2 * pivot) - high
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)
        r3 = high + 2 * (pivot - low)
        s3 = low - 2 * (high - pivot)

        return {
            "pivot": pivot,
            "resistance_1": r1,
            "resistance_2": r2,
            "resistance_3": r3,
            "support_1": s1,
            "support_2": s2,
            "support_3": s3
        }

    def _fetch_news(self, symbol: str, max_items: int = 5) -> List[str]:
        """
        Fetch recent news headlines for a symbol

        Args:
            symbol: Stock symbol
            max_items: Maximum number of news items

        Returns:
            List of news headlines
        """
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news

            if not news:
                return []

            headlines = []
            for item in news[:max_items]:
                if isinstance(item, dict) and "title" in item:
                    headlines.append(item["title"])

            return headlines

        except Exception as e:
            # News fetching is optional, just log and continue
            logger.debug(f"Could not fetch news for {symbol}: {e}")
            return []

    def _get_cached_market_sentiment(self) -> Optional[Dict[str, Any]]:
        """
        Get market sentiment with 15-minute caching

        Returns:
            Market sentiment data or None
        """
        now = datetime.now()

        # Check if we have a recent cache
        if (self._market_sentiment_cache is not None and
            self._market_sentiment_time is not None and
            (now - self._market_sentiment_time).total_seconds() < 900):  # 15 minutes
            return self._market_sentiment_cache

        # Fetch new market sentiment
        try:
            sentiment = self.sentiment_analyzer.get_market_sentiment()
            self._market_sentiment_cache = sentiment
            self._market_sentiment_time = now
            return sentiment
        except Exception as e:
            logger.debug(f"Could not get market sentiment: {e}")
            return None

    def analyze_multiple_symbols(
        self,
        symbols: List[str],
        include_technicals: bool = True,
        include_news: bool = False
    ) -> Dict[str, Dict[str, Any]]:
        """
        Analyze multiple symbols

        Args:
            symbols: List of stock symbols
            include_technicals: Include technical indicators
            include_news: Include news

        Returns:
            Dictionary mapping symbols to their market data
        """
        results = {}

        for symbol in symbols:
            logger.info(f"Analyzing {symbol}...")
            data = self.get_market_data(
                symbol,
                include_technicals=include_technicals,
                include_news=include_news
            )

            if data:
                results[symbol] = data

        return results
