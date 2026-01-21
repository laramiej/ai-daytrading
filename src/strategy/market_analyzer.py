"""
Market Data Analyzer
Fetches and analyzes market data for DAY TRADING decisions.

IMPORTANT: All indicators are calculated on INTRADAY data (1-minute bars).
This analyzer is specifically designed for day trading with a focus on:
- Short-term momentum (minutes to hours)
- Intraday support/resistance levels
- Volume patterns within the trading day
- Opening range breakouts
- VWAP (the most important day trading indicator)
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
        Fetch comprehensive INTRADAY market data for a symbol.

        This method is designed for DAY TRADING and provides:
        - Current quote data
        - Intraday 1-minute bars (last 100 bars = ~1.5 hours)
        - Daily context (today's open, previous close, daily high/low)
        - Intraday technical indicators
        - Opening range data (first 30 minutes high/low)

        Args:
            symbol: Stock symbol
            include_technicals: Include technical indicators
            include_news: Include recent news

        Returns:
            Dictionary with market data optimized for day trading
        """
        try:
            # Get latest quote
            quote = self.broker.get_latest_quote(symbol)

            # Get intraday 1-minute bars for short-term analysis
            bars_1min = self.broker.get_bars(symbol, timeframe="1Min", limit=100)

            if not bars_1min:
                logger.warning(f"No bar data available for {symbol}")
                return None

            # Get daily bars for context (previous day's close, today's open)
            daily_bars = self.broker.get_bars(symbol, timeframe="1Day", limit=2)

            # Calculate current price and change
            current_price = (quote["bid_price"] + quote["ask_price"]) / 2
            df = pd.DataFrame(bars_1min)

            market_data = {
                "symbol": symbol,
                "current_price": current_price,
                "bid": quote["bid_price"],
                "ask": quote["ask_price"],
                "spread": quote["ask_price"] - quote["bid_price"],
                "timestamp": datetime.now()
            }

            # Add daily context for gap analysis and daily levels
            if daily_bars and len(daily_bars) >= 1:
                today_daily = daily_bars[-1]  # Most recent (today)
                market_data["today_open"] = today_daily["open"]
                market_data["today_high"] = today_daily["high"]
                market_data["today_low"] = today_daily["low"]
                market_data["today_volume"] = today_daily["volume"]

                if len(daily_bars) >= 2:
                    yesterday = daily_bars[-2]
                    market_data["prev_close"] = yesterday["close"]
                    market_data["prev_high"] = yesterday["high"]
                    market_data["prev_low"] = yesterday["low"]

                    # Calculate gap from previous close
                    gap = today_daily["open"] - yesterday["close"]
                    gap_percent = (gap / yesterday["close"]) * 100
                    market_data["gap"] = gap
                    market_data["gap_percent"] = gap_percent

                    # Daily change from previous close
                    daily_change = current_price - yesterday["close"]
                    daily_change_percent = (daily_change / yesterday["close"]) * 100
                    market_data["daily_change"] = daily_change
                    market_data["daily_change_percent"] = daily_change_percent

            # Calculate intraday price change (from session data)
            if len(df) > 0:
                session_open = df.iloc[0]["open"]
                intraday_change = current_price - session_open
                intraday_change_percent = (intraday_change / session_open) * 100

                market_data["session_open"] = session_open
                market_data["intraday_change"] = intraday_change
                market_data["intraday_change_percent"] = intraday_change_percent
                market_data["intraday_volume"] = int(df["volume"].sum())
                market_data["intraday_high"] = df["high"].max()
                market_data["intraday_low"] = df["low"].min()

            # Add technical indicators (all calculated on intraday data)
            if include_technicals and len(df) > 0:
                market_data["technical_indicators"] = self._calculate_technicals(df, current_price)

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

    def _calculate_technicals(self, df: pd.DataFrame, current_price: float = None) -> Dict[str, Any]:
        """
        Calculate INTRADAY technical indicators from 1-minute bars.

        IMPORTANT: All indicators are calculated on 1-minute intraday data.
        The naming convention makes this explicit (e.g., "SMA_20min" not "SMA_20").

        Args:
            df: DataFrame with 1-minute OHLCV data
            current_price: Current price from quote (more accurate than last bar close)

        Returns:
            Dictionary of intraday technical indicators
        """
        indicators = {}

        # Use provided current price or fall back to last close
        if current_price is None:
            current_price = df["close"].iloc[-1]

        try:
            # ============================================================
            # INTRADAY MOVING AVERAGES (calculated on 1-minute bars)
            # ============================================================
            # SMA_9min = 9-minute simple moving average (very short-term)
            if len(df) >= 9:
                indicators["SMA_9min"] = round(df["close"].rolling(window=9).mean().iloc[-1], 2)

            # SMA_20min = 20-minute simple moving average (short-term trend)
            if len(df) >= 20:
                indicators["SMA_20min"] = round(df["close"].rolling(window=20).mean().iloc[-1], 2)

            # EMA_9min = 9-minute exponential moving average (fast)
            if len(df) >= 9:
                indicators["EMA_9min"] = round(df["close"].ewm(span=9, adjust=False).mean().iloc[-1], 2)

            # EMA_21min = 21-minute exponential moving average (popular for scalping)
            if len(df) >= 21:
                indicators["EMA_21min"] = round(df["close"].ewm(span=21, adjust=False).mean().iloc[-1], 2)

            # ============================================================
            # VWAP - THE MOST IMPORTANT DAY TRADING INDICATOR
            # ============================================================
            if len(df) >= 1 and df["volume"].sum() > 0:
                vwap = (df["close"] * df["volume"]).sum() / df["volume"].sum()
                indicators["VWAP"] = round(vwap, 2)

                # VWAP position - critical for day trading
                vwap_distance = current_price - vwap
                vwap_distance_percent = (vwap_distance / vwap) * 100
                indicators["VWAP_distance"] = round(vwap_distance, 2)
                indicators["VWAP_distance_percent"] = round(vwap_distance_percent, 2)

                if vwap_distance_percent > 0.5:
                    indicators["VWAP_position"] = "Above VWAP (Bullish)"
                elif vwap_distance_percent < -0.5:
                    indicators["VWAP_position"] = "Below VWAP (Bearish)"
                else:
                    indicators["VWAP_position"] = "At VWAP (Neutral)"

            # ============================================================
            # INTRADAY MOMENTUM INDICATORS
            # ============================================================
            # RSI on 14 1-minute bars (very responsive for day trading)
            if len(df) >= 14:
                rsi = self._calculate_rsi(df["close"], 14)
                indicators["RSI_14min"] = round(rsi, 2)

                # RSI interpretation for day trading
                if rsi > 70:
                    indicators["RSI_signal"] = "Overbought (sell opportunity)"
                elif rsi < 30:
                    indicators["RSI_signal"] = "Oversold (buy opportunity)"
                elif rsi > 60:
                    indicators["RSI_signal"] = "Bullish momentum"
                elif rsi < 40:
                    indicators["RSI_signal"] = "Bearish momentum"
                else:
                    indicators["RSI_signal"] = "Neutral"

            # MACD on 1-minute bars (12/26/9 periods = 12min/26min/9min)
            if len(df) >= 26:
                macd_data = self._calculate_macd(df["close"])
                indicators["MACD"] = round(macd_data["macd"], 4)
                indicators["MACD_signal"] = round(macd_data["signal"], 4)
                indicators["MACD_histogram"] = round(macd_data["histogram"], 4)

                # MACD crossover signal
                if macd_data["histogram"] > 0 and macd_data["macd"] > macd_data["signal"]:
                    indicators["MACD_trend"] = "Bullish (MACD above signal)"
                elif macd_data["histogram"] < 0 and macd_data["macd"] < macd_data["signal"]:
                    indicators["MACD_trend"] = "Bearish (MACD below signal)"
                else:
                    indicators["MACD_trend"] = "Neutral"

            # Short-term momentum (5-minute price change)
            if len(df) >= 5:
                momentum_5 = current_price - df["close"].iloc[-5]
                indicators["momentum_5min"] = round(momentum_5, 2)
                indicators["momentum_5min_percent"] = round((momentum_5 / df["close"].iloc[-5]) * 100, 2)

            # Medium-term momentum (15-minute price change)
            if len(df) >= 15:
                momentum_15 = current_price - df["close"].iloc[-15]
                indicators["momentum_15min"] = round(momentum_15, 2)
                indicators["momentum_15min_percent"] = round((momentum_15 / df["close"].iloc[-15]) * 100, 2)

            # ============================================================
            # INTRADAY VOLATILITY
            # ============================================================
            # Bollinger Bands (20-minute)
            if len(df) >= 20:
                bb = self._calculate_bollinger_bands(df["close"], 20)
                indicators["BB_upper"] = round(bb["upper"], 2)
                indicators["BB_middle"] = round(bb["middle"], 2)
                indicators["BB_lower"] = round(bb["lower"], 2)

                # Bollinger Band position
                bb_range = bb["upper"] - bb["lower"]
                if bb_range > 0:
                    bb_position = (current_price - bb["lower"]) / bb_range
                    indicators["BB_position"] = round(bb_position * 100, 1)  # 0-100 scale

                    if current_price > bb["upper"]:
                        indicators["BB_signal"] = "Above upper band (overbought)"
                    elif current_price < bb["lower"]:
                        indicators["BB_signal"] = "Below lower band (oversold)"
                    elif bb_position > 0.8:
                        indicators["BB_signal"] = "Near upper band"
                    elif bb_position < 0.2:
                        indicators["BB_signal"] = "Near lower band"
                    else:
                        indicators["BB_signal"] = "Middle of bands"

            # ATR (Average True Range) - 14-minute for day trading volatility
            if len(df) >= 14:
                atr = self._calculate_atr(df, 14)
                indicators["ATR_14min"] = round(atr, 2)
                indicators["ATR_percent"] = round((atr / current_price) * 100, 3)

            # ============================================================
            # INTRADAY VOLUME ANALYSIS
            # ============================================================
            if len(df) >= 20:
                avg_volume = df["volume"].rolling(window=20).mean().iloc[-1]
                current_volume = df["volume"].iloc[-1]
                indicators["volume_ratio"] = round(current_volume / avg_volume, 2) if avg_volume > 0 else 1.0

                # Volume trend
                if indicators["volume_ratio"] > 2.0:
                    indicators["volume_signal"] = "Very High (2x+ average)"
                elif indicators["volume_ratio"] > 1.5:
                    indicators["volume_signal"] = "High (1.5x average)"
                elif indicators["volume_ratio"] < 0.5:
                    indicators["volume_signal"] = "Low (below 0.5x average)"
                else:
                    indicators["volume_signal"] = "Normal"

            # OBV (On-Balance Volume) trend
            if len(df) >= 10:
                obv = self._calculate_obv(df)
                indicators["OBV"] = int(obv)

                # Compare OBV trend to price trend
                if len(df) >= 20:
                    price_change_10 = df["close"].diff().tail(10)
                    direction_10 = np.sign(price_change_10)
                    obv_10_ago = (direction_10 * df["volume"].tail(10)).fillna(0).cumsum().iloc[0]
                    obv_change = obv - obv_10_ago
                    indicators["OBV_trend"] = "Rising (accumulation)" if obv_change > 0 else "Falling (distribution)"

            # ============================================================
            # STOCHASTIC OSCILLATOR (14-minute for day trading)
            # ============================================================
            if len(df) >= 14:
                stoch = self._calculate_stochastic(df, 14, 3)
                indicators["STOCH_K"] = round(stoch["k"], 2)
                indicators["STOCH_D"] = round(stoch["d"], 2)

                # Stochastic signal for day trading
                if stoch["k"] > 80:
                    if stoch["k"] < stoch["d"]:
                        indicators["STOCH_signal"] = "Overbought + Bearish crossover (SELL)"
                    else:
                        indicators["STOCH_signal"] = "Overbought (potential reversal)"
                elif stoch["k"] < 20:
                    if stoch["k"] > stoch["d"]:
                        indicators["STOCH_signal"] = "Oversold + Bullish crossover (BUY)"
                    else:
                        indicators["STOCH_signal"] = "Oversold (potential reversal)"
                else:
                    indicators["STOCH_signal"] = "Neutral"

            # ============================================================
            # INTRADAY SUPPORT/RESISTANCE (from recent price action)
            # ============================================================
            if len(df) >= 30:
                # Calculate intraday pivot from recent bars (not daily data)
                recent_high = df["high"].tail(30).max()
                recent_low = df["low"].tail(30).min()
                recent_close = df["close"].iloc[-1]

                pivot = (recent_high + recent_low + recent_close) / 3
                r1 = (2 * pivot) - recent_low
                s1 = (2 * pivot) - recent_high
                r2 = pivot + (recent_high - recent_low)
                s2 = pivot - (recent_high - recent_low)

                indicators["intraday_pivot"] = round(pivot, 2)
                indicators["intraday_R1"] = round(r1, 2)
                indicators["intraday_S1"] = round(s1, 2)
                indicators["intraday_R2"] = round(r2, 2)
                indicators["intraday_S2"] = round(s2, 2)
                indicators["intraday_range"] = round(recent_high - recent_low, 2)

                # Position relative to pivot
                if current_price > r1:
                    indicators["pivot_position"] = "Above R1 (strong bullish)"
                elif current_price > pivot:
                    indicators["pivot_position"] = "Above pivot (bullish)"
                elif current_price > s1:
                    indicators["pivot_position"] = "Below pivot (bearish)"
                else:
                    indicators["pivot_position"] = "Below S1 (strong bearish)"

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
