"""
Sentiment Analysis Module
Analyzes market sentiment and stock-specific sentiment from multiple sources
"""
import requests
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import yfinance as yf
from textblob import TextBlob

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Analyzes market and stock sentiment from various sources"""

    def __init__(self):
        """Initialize sentiment analyzer"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def get_market_sentiment(self) -> Dict[str, Any]:
        """
        Get overall market sentiment from multiple indicators

        Returns:
            Dictionary with market sentiment data
        """
        sentiment_data = {
            "timestamp": datetime.now(),
            "overall_score": 0.0,
            "indicators": {}
        }

        try:
            # VIX (Fear Index)
            vix_sentiment = self._get_vix_sentiment()
            if vix_sentiment:
                sentiment_data["indicators"]["vix"] = vix_sentiment

            # S&P 500 trend
            sp500_sentiment = self._get_index_sentiment("^GSPC", "S&P 500")
            if sp500_sentiment:
                sentiment_data["indicators"]["sp500"] = sp500_sentiment

            # NASDAQ trend
            nasdaq_sentiment = self._get_index_sentiment("^IXIC", "NASDAQ")
            if nasdaq_sentiment:
                sentiment_data["indicators"]["nasdaq"] = nasdaq_sentiment

            # Calculate overall score
            sentiment_data["overall_score"] = self._calculate_overall_sentiment(
                sentiment_data["indicators"]
            )

            sentiment_data["summary"] = self._get_sentiment_summary(
                sentiment_data["overall_score"]
            )

        except Exception as e:
            logger.error(f"Error getting market sentiment: {e}")

        return sentiment_data

    def get_stock_sentiment(self, symbol: str) -> Dict[str, Any]:
        """
        Get sentiment for a specific stock

        Args:
            symbol: Stock symbol

        Returns:
            Dictionary with stock sentiment data
        """
        sentiment_data = {
            "symbol": symbol,
            "timestamp": datetime.now(),
            "overall_score": 0.0,
            "sources": {}
        }

        try:
            # News sentiment
            news_sentiment = self._analyze_news_sentiment(symbol)
            if news_sentiment:
                sentiment_data["sources"]["news"] = news_sentiment

            # Social media sentiment (Reddit)
            reddit_sentiment = self._get_reddit_sentiment(symbol)
            if reddit_sentiment:
                sentiment_data["sources"]["reddit"] = reddit_sentiment

            # Analyst ratings sentiment
            analyst_sentiment = self._get_analyst_sentiment(symbol)
            if analyst_sentiment:
                sentiment_data["sources"]["analysts"] = analyst_sentiment

            # Price momentum sentiment
            momentum_sentiment = self._get_momentum_sentiment(symbol)
            if momentum_sentiment:
                sentiment_data["sources"]["momentum"] = momentum_sentiment

            # Calculate overall score
            sentiment_data["overall_score"] = self._calculate_stock_sentiment(
                sentiment_data["sources"]
            )

            sentiment_data["summary"] = self._get_sentiment_summary(
                sentiment_data["overall_score"]
            )

        except Exception as e:
            logger.error(f"Error getting sentiment for {symbol}: {e}")

        return sentiment_data

    def _get_vix_sentiment(self) -> Optional[Dict[str, Any]]:
        """Get VIX (fear index) sentiment"""
        try:
            vix = yf.Ticker("^VIX")
            hist = vix.history(period="5d")

            if hist.empty:
                return None

            current_vix = hist['Close'].iloc[-1]

            # VIX interpretation:
            # < 12: Very low fear (bullish)
            # 12-20: Low to moderate fear (neutral to bullish)
            # 20-30: Elevated fear (bearish)
            # > 30: High fear (very bearish)

            if current_vix < 12:
                score = 0.8
                label = "Very Bullish"
            elif current_vix < 20:
                score = 0.5
                label = "Neutral to Bullish"
            elif current_vix < 30:
                score = -0.3
                label = "Bearish"
            else:
                score = -0.7
                label = "Very Bearish"

            return {
                "vix_level": float(current_vix),
                "score": score,
                "label": label,
                "interpretation": f"VIX at {current_vix:.2f} indicates {label.lower()} market sentiment"
            }

        except Exception as e:
            logger.debug(f"Could not get VIX data: {e}")
            return None

    def _get_index_sentiment(self, symbol: str, name: str) -> Optional[Dict[str, Any]]:
        """Get sentiment from market index performance"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="10d")

            if hist.empty:
                return None

            # Calculate trend
            recent_close = hist['Close'].iloc[-1]
            week_ago_close = hist['Close'].iloc[0]
            change_pct = ((recent_close - week_ago_close) / week_ago_close) * 100

            # Score based on performance
            if change_pct > 2:
                score = 0.7
                label = "Strong Bullish"
            elif change_pct > 0:
                score = 0.3
                label = "Bullish"
            elif change_pct > -2:
                score = -0.3
                label = "Bearish"
            else:
                score = -0.7
                label = "Strong Bearish"

            return {
                "name": name,
                "change_pct": float(change_pct),
                "score": score,
                "label": label,
                "interpretation": f"{name} {'+' if change_pct > 0 else ''}{change_pct:.2f}% over 10 days"
            }

        except Exception as e:
            logger.debug(f"Could not get {name} data: {e}")
            return None

    def _analyze_news_sentiment(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Analyze sentiment from news headlines"""
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news

            if not news:
                return None

            sentiments = []
            headlines = []

            for item in news[:10]:  # Analyze last 10 headlines
                if isinstance(item, dict) and 'title' in item:
                    headline = item['title']
                    headlines.append(headline)

                    # Simple sentiment analysis using TextBlob
                    blob = TextBlob(headline)
                    sentiments.append(blob.sentiment.polarity)

            if not sentiments:
                return None

            avg_sentiment = sum(sentiments) / len(sentiments)

            # Convert to -1 to 1 score
            if avg_sentiment > 0.2:
                label = "Positive"
            elif avg_sentiment > 0:
                label = "Slightly Positive"
            elif avg_sentiment > -0.2:
                label = "Slightly Negative"
            else:
                label = "Negative"

            return {
                "score": float(avg_sentiment),
                "label": label,
                "headline_count": len(headlines),
                "sample_headlines": headlines[:3],
                "interpretation": f"News sentiment is {label.lower()} based on {len(headlines)} headlines"
            }

        except Exception as e:
            logger.debug(f"Could not analyze news sentiment for {symbol}: {e}")
            return None

    def _get_reddit_sentiment(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get sentiment from Reddit (wallstreetbets mentions)
        Note: This is a placeholder. Real implementation would need Reddit API
        """
        try:
            # Placeholder for Reddit sentiment
            # In production, you'd use Reddit API (praw library)
            # For now, return None to indicate no data
            return None

        except Exception as e:
            logger.debug(f"Could not get Reddit sentiment for {symbol}: {e}")
            return None

    def _get_analyst_sentiment(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get sentiment from analyst recommendations"""
        try:
            ticker = yf.Ticker(symbol)
            recommendations = ticker.recommendations

            if recommendations is None or recommendations.empty:
                return None

            # Get recent recommendations (last 3 months)
            recent = recommendations.tail(10)

            # Count recommendation types
            rec_counts = recent['To Grade'].value_counts()

            # Scoring system
            score_map = {
                'Strong Buy': 1.0,
                'Buy': 0.6,
                'Outperform': 0.4,
                'Hold': 0.0,
                'Neutral': 0.0,
                'Underperform': -0.4,
                'Sell': -0.6,
                'Strong Sell': -1.0
            }

            total_score = 0
            total_count = 0

            for grade, count in rec_counts.items():
                if grade in score_map:
                    total_score += score_map[grade] * count
                    total_count += count

            if total_count == 0:
                return None

            avg_score = total_score / total_count

            if avg_score > 0.5:
                label = "Strong Buy"
            elif avg_score > 0.2:
                label = "Buy"
            elif avg_score > -0.2:
                label = "Hold"
            elif avg_score > -0.5:
                label = "Sell"
            else:
                label = "Strong Sell"

            return {
                "score": float(avg_score),
                "label": label,
                "recommendation_count": int(total_count),
                "top_grade": rec_counts.index[0] if len(rec_counts) > 0 else "N/A",
                "interpretation": f"Analysts consensus: {label}"
            }

        except Exception as e:
            logger.debug(f"Could not get analyst sentiment for {symbol}: {e}")
            return None

    def _get_momentum_sentiment(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get sentiment based on price momentum"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1mo")

            if hist.empty:
                return None

            # Calculate momentum metrics
            current_price = hist['Close'].iloc[-1]
            week_ago = hist['Close'].iloc[-5] if len(hist) >= 5 else hist['Close'].iloc[0]
            month_ago = hist['Close'].iloc[0]

            week_change = ((current_price - week_ago) / week_ago) * 100
            month_change = ((current_price - month_ago) / month_ago) * 100

            # Score based on momentum
            momentum_score = (week_change * 0.6 + month_change * 0.4) / 10  # Normalize

            # Clamp between -1 and 1
            momentum_score = max(-1, min(1, momentum_score))

            if momentum_score > 0.3:
                label = "Strong Positive"
            elif momentum_score > 0:
                label = "Positive"
            elif momentum_score > -0.3:
                label = "Negative"
            else:
                label = "Strong Negative"

            return {
                "score": float(momentum_score),
                "label": label,
                "week_change_pct": float(week_change),
                "month_change_pct": float(month_change),
                "interpretation": f"Price momentum is {label.lower()} ({week_change:+.2f}% week, {month_change:+.2f}% month)"
            }

        except Exception as e:
            logger.debug(f"Could not get momentum sentiment for {symbol}: {e}")
            return None

    def _calculate_overall_sentiment(self, indicators: Dict[str, Any]) -> float:
        """Calculate overall market sentiment score"""
        if not indicators:
            return 0.0

        scores = []
        weights = {
            "vix": 0.4,      # VIX is important
            "sp500": 0.35,   # S&P 500 trend
            "nasdaq": 0.25   # NASDAQ trend
        }

        for key, data in indicators.items():
            if "score" in data:
                weight = weights.get(key, 1.0)
                scores.append(data["score"] * weight)

        if not scores:
            return 0.0

        return sum(scores) / sum(weights.values())

    def _calculate_stock_sentiment(self, sources: Dict[str, Any]) -> float:
        """Calculate overall stock sentiment score"""
        if not sources:
            return 0.0

        scores = []
        weights = {
            "news": 0.25,
            "reddit": 0.15,
            "analysts": 0.35,
            "momentum": 0.25
        }

        for key, data in sources.items():
            if data and "score" in data:
                weight = weights.get(key, 1.0)
                scores.append(data["score"] * weight)

        if not scores:
            return 0.0

        total_weight = sum(weights[k] for k in sources.keys() if sources[k] and "score" in sources[k])
        return sum(scores) / total_weight if total_weight > 0 else 0.0

    def _get_sentiment_summary(self, score: float) -> str:
        """Convert sentiment score to human-readable summary"""
        if score > 0.6:
            return "Very Bullish"
        elif score > 0.3:
            return "Bullish"
        elif score > 0:
            return "Slightly Bullish"
        elif score > -0.3:
            return "Slightly Bearish"
        elif score > -0.6:
            return "Bearish"
        else:
            return "Very Bearish"

    def format_sentiment_report(
        self,
        market_sentiment: Dict[str, Any],
        stock_sentiment: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format sentiment data into readable report

        Args:
            market_sentiment: Market sentiment data
            stock_sentiment: Optional stock-specific sentiment

        Returns:
            Formatted sentiment report string
        """
        report = []

        # Market sentiment
        report.append("📊 MARKET SENTIMENT")
        report.append("-" * 50)
        report.append(f"Overall: {market_sentiment['summary']} ({market_sentiment['overall_score']:.2f})")
        report.append("")

        for name, data in market_sentiment.get("indicators", {}).items():
            if "interpretation" in data:
                report.append(f"  • {data['interpretation']}")

        # Stock sentiment
        if stock_sentiment:
            report.append("")
            report.append(f"📈 {stock_sentiment['symbol']} SENTIMENT")
            report.append("-" * 50)
            report.append(f"Overall: {stock_sentiment['summary']} ({stock_sentiment['overall_score']:.2f})")
            report.append("")

            for name, data in stock_sentiment.get("sources", {}).items():
                if data and "interpretation" in data:
                    report.append(f"  • {name.title()}: {data['interpretation']}")

        return "\n".join(report)
