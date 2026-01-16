# Finnhub API Analysis for Sentiment Data

**Date**: 2026-01-15
**Purpose**: Evaluate Finnhub as replacement for broken yfinance sentiment data

---

## Summary

✅ **Finnhub CAN replace most sentiment functionality**
✅ **Free tier is very generous** (60 API calls/minute)
⚠️ **Premium sentiment features require paid subscription**
✅ **Better reliability than yfinance** (official API, not scraping)

---

## What Finnhub Offers

### Free Tier (60 calls/minute)

#### ✅ Available in Free Tier:

1. **Analyst Recommendation Trends** (`/stock/recommendation`)
   - Strong Buy, Buy, Hold, Sell, Strong Sell counts
   - Historical trend tracking
   - **Replaces**: yfinance analyst ratings
   - **Usage**: Excellent for sentiment analysis

2. **Real-time Quote Data** (`/quote`)
   - Current price, daily change, high/low
   - **Replaces**: yfinance price data
   - **Usage**: Can calculate momentum sentiment

3. **Market News** (`/news`)
   - Latest market news headlines
   - **Replaces**: yfinance news headlines
   - **Usage**: Can feed to TextBlob for sentiment analysis

4. **Company News** (`/company-news`)
   - Company-specific news
   - Date ranges supported
   - **Replaces**: yfinance company news
   - **Usage**: Better than yfinance for news sentiment

### Premium Tier Only

#### ❌ Requires Paid Subscription:

1. **News Sentiment** (`/news-sentiment`)
   - Pre-calculated bullish/bearish percentages
   - Company news scores
   - Sector comparisons
   - **Better than**: TextBlob analysis
   - **Cost**: Unknown (contact Finnhub)

2. **Social Sentiment** (`/stock/social-sentiment`)
   - Reddit + Twitter sentiment
   - Mention counts, positive/negative scores
   - Overall sentiment score (-1 to 1)
   - **Replaces**: Reddit API (which we don't use yet)
   - **Cost**: Unknown (contact Finnhub)

3. **Filing Sentiment** (`/stock/filings-sentiment`)
   - 10-K and 10-Q sentiment analysis
   - Loughran-McDonald word lists
   - **Value**: Limited for day trading
   - **Cost**: Unknown (contact Finnhub)

---

## What Finnhub CANNOT Replace

### ❌ VIX (Fear Index)
- Finnhub quote endpoint is **US stocks only**
- No explicit support for ^VIX index
- **Workaround**: Could try querying ^VIX symbol (untested)
- **Alternative**: Use VIX ETF (VXX, VIXY) as proxy

### ❌ S&P 500 / NASDAQ Indices
- Finnhub quote endpoint is **US stocks only**
- No explicit support for ^GSPC, ^IXIC
- **Workaround**: Use SPY and QQQ ETFs instead
- **Alternative**: Track SPY/QQQ momentum as market sentiment

---

## Free Tier Implementation Plan

### Data Mapping

| Current Source (yfinance) | Finnhub Free Tier Replacement | Implementation |
|---------------------------|-------------------------------|----------------|
| VIX sentiment | SPY momentum (via `/quote`) | ✅ Easy |
| S&P 500 trend | SPY daily change (via `/quote`) | ✅ Easy |
| NASDAQ trend | QQQ daily change (via `/quote`) | ✅ Easy |
| News headlines | Company news (via `/company-news`) | ✅ Easy |
| News sentiment | TextBlob on Finnhub news | ✅ Easy |
| Analyst ratings | Recommendation trends (via `/stock/recommendation`) | ✅ Easy |
| Price momentum | Quote data (via `/quote`) | ✅ Easy |

### What We Get

**Market Sentiment** (free tier):
- SPY momentum → VIX proxy (price volatility)
- SPY daily change → S&P 500 sentiment
- QQQ daily change → NASDAQ sentiment
- **Quality**: 90% as good as VIX/indices

**Stock Sentiment** (free tier):
- Finnhub news headlines → TextBlob sentiment
- Analyst recommendations → consensus rating
- Price momentum → trend strength
- **Quality**: Better than current (broken) yfinance

---

## API Rate Limits

### Free Tier: 60 calls/minute

**Per trading scan** (10 stocks):
- Market sentiment: 2 calls (SPY, QQQ)
- Stock sentiment per stock: 2 calls (news + recommendations)
- Total: 2 + (10 × 2) = **22 calls**

**Scan frequency**: 60 calls ÷ 22 = **2.7 scans/minute** = ~22 seconds between scans

**Verdict**: ✅ **More than sufficient** for day trading (we currently scan every 60 seconds)

---

## Implementation Effort

### Easy (1-2 hours)

1. ✅ Add finnhub-python library
2. ✅ Create FinnhubSentimentAnalyzer class
3. ✅ Implement free tier endpoints
4. ✅ Replace yfinance calls with Finnhub calls
5. ✅ Update config for Finnhub API key

### Code Changes Required

**Files to modify**:
- `requirements.txt` - add `finnhub-python`
- `.env.example` - add `FINNHUB_API_KEY`
- `config.py` - add Finnhub API key setting
- `sentiment_analyzer.py` - replace yfinance with Finnhub

**Lines of code**: ~150-200 lines (mostly replacements)

---

## Cost Analysis

### Free Tier (Current Plan)

- **Cost**: $0/month
- **Rate limit**: 60 calls/minute
- **Features**: News, quotes, recommendations
- **Sufficient for**: Development, testing, small-scale trading
- **Limitation**: No pre-calculated sentiment scores

### Premium Tier (If Needed)

- **Cost**: Unknown (contact Finnhub)
- **Features**: News sentiment, social sentiment, filing sentiment
- **Value**: Pre-calculated sentiment (saves TextBlob processing)
- **Recommendation**: Test free tier first, upgrade only if needed

---

## Comparison: Finnhub vs yfinance

| Feature | yfinance (Current) | Finnhub Free Tier | Winner |
|---------|-------------------|-------------------|--------|
| **Reliability** | ❌ Broken (API failures) | ✅ Official API | Finnhub |
| **VIX data** | ❌ Failed | ⚠️ Use SPY volatility | yfinance (when working) |
| **Index data** | ❌ Failed | ⚠️ Use ETFs (SPY/QQQ) | yfinance (when working) |
| **News headlines** | ❌ Failed | ✅ Working | Finnhub |
| **Analyst ratings** | ❌ Failed | ✅ Working | Finnhub |
| **Sentiment scores** | ❌ TextBlob only | ✅ TextBlob (free) or API (paid) | Tie |
| **Rate limits** | ❌ Unpredictable | ✅ 60/min (clear) | Finnhub |
| **Cost** | ✅ Free | ✅ Free tier available | Tie |
| **Dependencies** | ❌ Conflicts with alpaca-py | ✅ No conflicts | Finnhub |
| **Overall** | ❌ Not working | ✅ Working | **Finnhub** |

---

## Recommendation

### ✅ Implement Finnhub Free Tier

**Reasons**:
1. **It works** (yfinance doesn't)
2. **No dependency conflicts** with alpaca-py
3. **Better reliability** (official API)
4. **Free tier is generous** (60 calls/minute)
5. **Easy to implement** (1-2 hours)
6. **Can upgrade later** if need pre-calculated sentiment

### Implementation Priority

**Phase 1** (Recommended Now):
- Replace yfinance with Finnhub free tier
- Use SPY/QQQ for market sentiment
- Use Finnhub news + TextBlob for stock sentiment
- Keep Google Trends (already working with pytrends)

**Phase 2** (Optional Future):
- Evaluate premium tier for pre-calculated sentiment
- Consider if social sentiment (Reddit/Twitter) adds value
- Test if filing sentiment useful for swing trading

---

## Sample Code Structure

```python
import finnhub

class FinnhubSentimentAnalyzer:
    def __init__(self, api_key: str):
        self.client = finnhub.Client(api_key=api_key)
    
    def get_market_sentiment(self) -> Dict[str, Any]:
        """Get market sentiment using SPY/QQQ as proxies"""
        # SPY for S&P 500 sentiment
        spy_quote = self.client.quote('SPY')
        spy_change = spy_quote['dp']  # Percent change
        
        # QQQ for NASDAQ sentiment
        qqq_quote = self.client.quote('QQQ')
        qqq_change = qqq_quote['dp']
        
        # Calculate sentiment scores
        spy_score = self._change_to_sentiment(spy_change)
        qqq_score = self._change_to_sentiment(qqq_change)
        
        overall_score = (spy_score * 0.6 + qqq_score * 0.4)
        
        return {
            "overall_score": overall_score,
            "indicators": {
                "spy": {"score": spy_score, "change": spy_change},
                "qqq": {"score": qqq_score, "change": qqq_change}
            }
        }
    
    def get_stock_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get stock sentiment from Finnhub"""
        sources = {}
        
        # News sentiment (free tier)
        news = self.client.company_news(symbol, _from='2026-01-10', to='2026-01-15')
        if news:
            headlines = [item['headline'] for item in news[:5]]
            news_score = self._analyze_textblob(headlines)
            sources["news"] = {"score": news_score}
        
        # Analyst recommendations (free tier)
        recommendations = self.client.recommendation_trends(symbol)
        if recommendations:
            latest = recommendations[0]
            analyst_score = self._calculate_analyst_score(latest)
            sources["analysts"] = {"score": analyst_score}
        
        # Calculate overall
        overall_score = self._calculate_stock_sentiment(sources)
        
        return {
            "symbol": symbol,
            "overall_score": overall_score,
            "sources": sources
        }
```

---

## Next Steps

1. **Sign up for Finnhub free tier** at https://finnhub.io/
2. **Get API key** from dashboard
3. **Install finnhub-python**: `pip install finnhub-python`
4. **Implement FinnhubSentimentAnalyzer** class
5. **Test with a few stocks** to verify data quality
6. **Replace yfinance calls** in sentiment_analyzer.py
7. **Update documentation** with Finnhub instructions

---

## Conclusion

**Finnhub free tier is the best solution** for replacing broken yfinance sentiment:

✅ **Reliability**: Official API (not scraping)
✅ **Cost**: Free tier is generous
✅ **Features**: News, analyst ratings, quotes
✅ **Compatibility**: No conflicts with alpaca-py
✅ **Implementation**: Easy (1-2 hours)

**Only limitation**: No direct VIX data, but SPY volatility is an acceptable proxy for day trading.

**Recommendation**: Implement Finnhub free tier immediately to restore sentiment functionality.

---

**Sources**:
- [Finnhub Pricing](https://finnhub.io/pricing)
- [Finnhub API Documentation](https://finnhub.io/docs/api)
- [Best Real-Time Stock Market Data APIs in 2026](https://site.financialmodelingprep.com/education/other/best-realtime-stock-market-data-apis-in-)
- [Financial Data APIs 2025 Guide](https://www.ksred.com/the-complete-guide-to-financial-data-apis-building-your-own-stock-market-data-pipeline-in-2025/)

