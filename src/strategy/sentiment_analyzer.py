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

# Try to import pytrends (optional)
try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False
    logger.warning("pytrends not installed. Google Trends analysis will be disabled. Install with: pip install pytrends")

# Try to import finnhub (optional)
try:
    import finnhub
    FINNHUB_AVAILABLE = True
except ImportError:
    FINNHUB_AVAILABLE = False
    logger.warning("finnhub-python not installed. Finnhub sentiment analysis will be disabled. Install with: pip install finnhub-python")


class SentimentAnalyzer:
    """Analyzes market and stock sentiment from various sources"""

    def __init__(self, enable_google_trends: bool = True, finnhub_api_key: Optional[str] = None, enable_finnhub: bool = True):
        """
        Initialize sentiment analyzer

        Args:
            enable_google_trends: Whether to enable Google Trends analysis
            finnhub_api_key: Finnhub API key (optional)
            enable_finnhub: Whether to enable Finnhub analysis
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        # Google Trends
        self.enable_google_trends = enable_google_trends and PYTRENDS_AVAILABLE
        self.pytrends = None
        if self.enable_google_trends:
            try:
                self.pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
                logger.info("Google Trends integration enabled")
            except Exception as e:
                logger.warning(f"Could not initialize Google Trends: {e}")
                self.enable_google_trends = False

        # Finnhub
        self.enable_finnhub = enable_finnhub and FINNHUB_AVAILABLE and finnhub_api_key
        self.finnhub_client = None
        if self.enable_finnhub:
            try:
                self.finnhub_client = finnhub.Client(api_key=finnhub_api_key)
                logger.info("Finnhub integration enabled")
            except Exception as e:
                logger.warning(f"Could not initialize Finnhub: {e}")
                self.enable_finnhub = False

        # Company name cache for Google Trends
        self.company_names = {
            "AAPL": "Apple",
            "MSFT": "Microsoft",
            "GOOGL": "Google",
            "AMZN": "Amazon",
            "TSLA": "Tesla",
            "NVDA": "NVIDIA",
            "META": "Meta",
            "AMD": "AMD",
            "NFLX": "Netflix",
            "SPY": "S&P 500",
            "QQQ": "NASDAQ"
        }

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
            # Try Finnhub first (more reliable), fall back to yfinance
            if self.enable_finnhub:
                # SPY for S&P 500 sentiment
                spy_sentiment = self._get_finnhub_etf_sentiment("SPY", "S&P 500")
                if spy_sentiment:
                    sentiment_data["indicators"]["sp500"] = spy_sentiment

                # QQQ for NASDAQ sentiment
                qqq_sentiment = self._get_finnhub_etf_sentiment("QQQ", "NASDAQ")
                if qqq_sentiment:
                    sentiment_data["indicators"]["nasdaq"] = qqq_sentiment
            else:
                # Fall back to yfinance (may not work)
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
            # Try Finnhub first (more reliable), fall back to yfinance
            if self.enable_finnhub:
                # News sentiment from Finnhub
                news_sentiment = self._get_finnhub_news_sentiment(symbol)
                if news_sentiment:
                    sentiment_data["sources"]["news"] = news_sentiment

                # Analyst ratings from Finnhub
                analyst_sentiment = self._get_finnhub_analyst_sentiment(symbol)
                if analyst_sentiment:
                    sentiment_data["sources"]["analysts"] = analyst_sentiment
            else:
                # Fall back to yfinance (may not work)
                # News sentiment
                news_sentiment = self._analyze_news_sentiment(symbol)
                if news_sentiment:
                    sentiment_data["sources"]["news"] = news_sentiment

                # Analyst ratings sentiment
                analyst_sentiment = self._get_analyst_sentiment(symbol)
                if analyst_sentiment:
                    sentiment_data["sources"]["analysts"] = analyst_sentiment

            # Google Trends sentiment (works independently)
            trends_sentiment = self._get_google_trends_sentiment(symbol)
            if trends_sentiment:
                sentiment_data["sources"]["trends"] = trends_sentiment

            # Social media sentiment (Reddit) - placeholder
            reddit_sentiment = self._get_reddit_sentiment(symbol)
            if reddit_sentiment:
                sentiment_data["sources"]["reddit"] = reddit_sentiment

            # Price momentum sentiment (uses Alpaca data, not yfinance)
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
        """
        Get VIX (fear index) sentiment with fallback

        Returns VIX sentiment or None if unavailable
        """
        try:
            vix = yf.Ticker("^VIX")
            hist = vix.history(period="5d")

            if hist.empty or len(hist) == 0:
                logger.debug("VIX data not available from yfinance")
                return None

            current_vix = hist['Close'].iloc[-1]

            # Validate VIX value (typical range: 10-80)
            if current_vix < 5 or current_vix > 100:
                logger.warning(f"VIX value {current_vix} outside expected range")
                return None

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

    def _get_google_trends_sentiment(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get sentiment from Google search trends

        Args:
            symbol: Stock symbol

        Returns:
            Dictionary with trend sentiment data
        """
        if not self.enable_google_trends or not self.pytrends:
            return None

        try:
            # Get company name for better search results
            company_name = self.company_names.get(symbol, symbol)

            # Build payload with both symbol and company name
            keywords = [symbol, company_name]
            self.pytrends.build_payload(keywords, timeframe='now 7-d', geo='US')

            # Get interest over time
            interest = self.pytrends.interest_over_time()

            if interest.empty or len(interest) < 3:
                return None

            # Calculate trend (recent vs baseline)
            # Recent = last 2 days, Baseline = first 5 days
            recent_data = interest[keywords].tail(2)
            baseline_data = interest[keywords].head(5)

            recent_avg = recent_data.mean().mean()
            baseline_avg = baseline_data.mean().mean()

            if baseline_avg == 0 or recent_avg == 0:
                return None

            # Trend ratio: how much interest changed
            trend_ratio = recent_avg / baseline_avg

            # Convert to sentiment score (-1 to 1)
            # 1.0 = no change, >1.0 = rising interest, <1.0 = falling interest
            score = (trend_ratio - 1.0)

            # Clamp between -1 and 1
            score = max(-1, min(1, score))

            # Classify trend
            if score > 0.3:
                label = "Surging Interest"
            elif score > 0.1:
                label = "Rising Interest"
            elif score > -0.1:
                label = "Stable Interest"
            elif score > -0.3:
                label = "Declining Interest"
            else:
                label = "Collapsing Interest"

            return {
                "score": float(score),
                "label": label,
                "recent_interest": float(recent_avg),
                "baseline_interest": float(baseline_avg),
                "trend_ratio": float(trend_ratio),
                "interpretation": f"Google search interest is {label.lower()} (trend: {trend_ratio:.2f}x baseline)"
            }

        except Exception as e:
            logger.debug(f"Could not get Google Trends for {symbol}: {e}")
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

    def _get_finnhub_etf_sentiment(self, symbol: str, name: str) -> Optional[Dict[str, Any]]:
        """
        Get sentiment from ETF price movement using Finnhub

        Args:
            symbol: ETF symbol (SPY, QQQ)
            name: Display name (S&P 500, NASDAQ)

        Returns:
            Dictionary with sentiment data
        """
        if not self.enable_finnhub or not self.finnhub_client:
            return None

        try:
            # Get quote data
            quote = self.finnhub_client.quote(symbol)

            if not quote or 'dp' not in quote:
                logger.debug(f"No Finnhub quote data for {symbol}")
                return None

            # Get daily percent change
            daily_change = quote['dp']  # Percent change

            # Convert daily change to sentiment score
            # Positive change = bullish, negative = bearish
            # Scale: 0-1% = slight, 1-2% = moderate, 2%+ = strong
            if daily_change > 2.0:
                score = 0.8
                label = "Very Bullish"
            elif daily_change > 1.0:
                score = 0.5
                label = "Bullish"
            elif daily_change > 0:
                score = 0.2
                label = "Slightly Bullish"
            elif daily_change > -1.0:
                score = -0.2
                label = "Slightly Bearish"
            elif daily_change > -2.0:
                score = -0.5
                label = "Bearish"
            else:
                score = -0.8
                label = "Very Bearish"

            return {
                "score": float(score),
                "label": label,
                "daily_change_pct": float(daily_change),
                "price": float(quote.get('c', 0)),
                "interpretation": f"{name} sentiment is {label.lower()} ({daily_change:+.2f}% today)"
            }

        except Exception as e:
            logger.debug(f"Could not get Finnhub ETF sentiment for {symbol}: {e}")
            return None

    def _get_finnhub_news_sentiment(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get news sentiment using Finnhub company news

        Args:
            symbol: Stock symbol

        Returns:
            Dictionary with news sentiment data
        """
        if not self.enable_finnhub or not self.finnhub_client:
            return None

        try:
            # Get news from last 7 days
            to_date = datetime.now().strftime('%Y-%m-%d')
            from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

            news = self.finnhub_client.company_news(symbol, _from=from_date, to=to_date)

            if not news or len(news) == 0:
                return None

            # Analyze up to 10 most recent headlines
            headlines = [item.get('headline', '') for item in news[:10] if item.get('headline')]

            if not headlines:
                return None

            # Use TextBlob for sentiment analysis
            sentiments = []
            for headline in headlines:
                try:
                    blob = TextBlob(headline)
                    sentiments.append(blob.sentiment.polarity)
                except:
                    continue

            if not sentiments:
                return None

            # Calculate average sentiment
            avg_sentiment = sum(sentiments) / len(sentiments)

            # Classify sentiment
            if avg_sentiment > 0.3:
                label = "Very Positive"
            elif avg_sentiment > 0.1:
                label = "Positive"
            elif avg_sentiment > -0.1:
                label = "Neutral"
            elif avg_sentiment > -0.3:
                label = "Negative"
            else:
                label = "Very Negative"

            return {
                "score": float(avg_sentiment),
                "label": label,
                "article_count": len(headlines),
                "interpretation": f"News sentiment is {label.lower()} based on {len(headlines)} articles"
            }

        except Exception as e:
            logger.debug(f"Could not get Finnhub news for {symbol}: {e}")
            return None

    def _get_finnhub_analyst_sentiment(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get analyst recommendation sentiment using Finnhub

        Args:
            symbol: Stock symbol

        Returns:
            Dictionary with analyst sentiment data
        """
        if not self.enable_finnhub or not self.finnhub_client:
            return None

        try:
            # Get recommendation trends
            recommendations = self.finnhub_client.recommendation_trends(symbol)

            if not recommendations or len(recommendations) == 0:
                return None

            # Get most recent recommendation period
            latest = recommendations[0]

            # Extract counts
            strong_buy = latest.get('strongBuy', 0)
            buy = latest.get('buy', 0)
            hold = latest.get('hold', 0)
            sell = latest.get('sell', 0)
            strong_sell = latest.get('strongSell', 0)

            total = strong_buy + buy + hold + sell + strong_sell

            if total == 0:
                return None

            # Calculate weighted score (-1 to 1)
            score = (
                (strong_buy * 1.0) +
                (buy * 0.5) +
                (hold * 0.0) +
                (sell * -0.5) +
                (strong_sell * -1.0)
            ) / total

            # Classify consensus
            if score > 0.6:
                label = "Strong Buy"
                consensus = "Strong Buy"
            elif score > 0.2:
                label = "Buy"
                consensus = "Buy"
            elif score > -0.2:
                label = "Hold"
                consensus = "Hold"
            elif score > -0.6:
                label = "Sell"
                consensus = "Sell"
            else:
                label = "Strong Sell"
                consensus = "Strong Sell"

            return {
                "score": float(score),
                "label": label,
                "strong_buy": strong_buy,
                "buy": buy,
                "hold": hold,
                "sell": sell,
                "strong_sell": strong_sell,
                "total_analysts": total,
                "interpretation": f"Analyst consensus: {consensus} ({total} analysts)"
            }

        except Exception as e:
            logger.debug(f"Could not get Finnhub analyst recommendations for {symbol}: {e}")
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
            "news": 0.20,
            "trends": 0.15,     # Google Trends
            "reddit": 0.10,
            "analysts": 0.30,
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
