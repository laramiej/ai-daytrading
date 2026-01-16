# Phase 2 Implementation Plan: Advanced Sentiment Analysis

## Overview

Phase 2 focuses on fixing broken sentiment analysis and adding alternative data sources to improve prediction accuracy by +10-15%.

**Status**: Planning Complete
**Timeline**: 1-2 weeks
**Expected Impact**: +10-15% accuracy improvement

---

## Current Issues

### Problem 1: yfinance API Failures ❌
**Current Code**: `sentiment_analyzer.py` uses yfinance for VIX, S&P 500, NASDAQ
**Issue**: yfinance has frequent API failures and rate limits
**Impact**: Sentiment analysis disabled in main.py

### Problem 2: Basic Sentiment Analysis ⚠️
**Current**: TextBlob for news sentiment (generic NLP)
**Better**: FinBERT (finance-specific sentiment model)
**Impact**: 10-15% accuracy improvement per research

### Problem 3: No Alternative Data ❌
**Missing**: Google Trends, Wikipedia pageviews, social media
**Impact**: Missing attention/hype signals

---

## Phase 2A: Fix Core Sentiment (Priority: CRITICAL)

### Task 1: Add Backup Data Sources

Replace failing yfinance calls with multiple fallback sources:

**Option 1: Alpha Vantage (Free Tier)**
- 25 API calls/day free
- Reliable market index data
- VIX data available

**Option 2: Finnhub (Free Tier)**
- 60 API calls/minute free
- Market indicators
- News sentiment API

**Option 3: Yahoo Finance Alternative**
- Use direct API calls instead of yfinance wrapper
- Less likely to fail

**Recommendation**: Implement fallback chain:
1. Try yfinance (current)
2. Fall back to Alpha Vantage
3. Fall back to Finnhub
4. If all fail, use cached data or neutral score

### Implementation:
```python
def _get_market_data_with_fallback(self):
    """Try multiple sources for market data"""
    # Try yfinance first (fast, no API key needed)
    try:
        return self._get_yfinance_data()
    except:
        pass

    # Try Alpha Vantage
    if self.alpha_vantage_key:
        try:
            return self._get_alpha_vantage_data()
        except:
            pass

    # Try Finnhub
    if self.finnhub_key:
        try:
            return self._get_finnhub_data()
        except:
            pass

    # Return neutral sentiment
    return {"score": 0.0, "source": "fallback"}
```

---

## Phase 2B: Google Trends Integration (Priority: HIGH)

### What Google Trends Provides

**Predictive Value**: Medium (5-10% accuracy boost)
**Use Case**: Detects attention spikes before price movements
**Timeframe**: Best for 1-3 day predictions

### Implementation

**Library**: `pytrends` (unofficial Google Trends API)

```python
from pytrends.request import TrendReq

def get_search_trend(self, symbol: str, company_name: str) -> Dict[str, Any]:
    """
    Get Google search trend for stock/company

    Args:
        symbol: Stock ticker (e.g., "AAPL")
        company_name: Company name (e.g., "Apple")

    Returns:
        Trend data with score
    """
    try:
        pytrends = TrendReq(hl='en-US', tz=360)

        # Search for both ticker and company name
        keywords = [symbol, company_name]
        pytrends.build_payload(keywords, timeframe='now 7-d', geo='US')

        # Get interest over time
        interest = pytrends.interest_over_time()

        if interest.empty:
            return None

        # Calculate trend (recent vs baseline)
        recent_avg = interest[keywords].tail(2).mean().mean()
        baseline_avg = interest[keywords].head(5).mean().mean()

        if baseline_avg == 0:
            return None

        # Trend score: recent interest vs baseline
        trend_ratio = recent_avg / baseline_avg
        score = (trend_ratio - 1.0)  # Normalize: 1.0 = no change

        # Clamp between -1 and 1
        score = max(-1, min(1, score))

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
            "interpretation": f"Google search interest is {label.lower()} (trend: {trend_ratio:.2f}x)"
        }

    except Exception as e:
        logger.debug(f"Could not get Google Trends for {symbol}: {e}")
        return None
```

### Integration

Add to `get_stock_sentiment()`:
```python
# Google Trends
trends_sentiment = self._get_search_trend(symbol, company_name)
if trends_sentiment:
    sentiment_data["sources"]["trends"] = trends_sentiment
```

Update weights:
```python
weights = {
    "news": 0.20,
    "trends": 0.15,      # NEW
    "analysts": 0.30,
    "momentum": 0.20,
    "reddit": 0.15
}
```

---

## Phase 2C: FinBERT Integration (Priority: MEDIUM)

### What FinBERT Provides

**Current**: TextBlob (generic sentiment)
**Upgrade**: FinBERT (finance-specific model)
**Impact**: +10-15% accuracy on news sentiment

### Challenge: Model Size

FinBERT is a transformer model (>400MB). Two options:

**Option 1: Local Model (Better accuracy)**
```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

class FinBERTAnalyzer:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        self.model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")

    def analyze_sentiment(self, text: str) -> float:
        """
        Analyze financial text sentiment

        Returns:
            Score from -1 (negative) to +1 (positive)
        """
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        outputs = self.model(**inputs)
        predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)

        # FinBERT outputs: [positive, negative, neutral]
        pos_score = predictions[0][0].item()
        neg_score = predictions[0][1].item()
        neu_score = predictions[0][2].item()

        # Convert to -1 to 1 scale
        return (pos_score - neg_score)
```

**Option 2: API Service (Faster, no local model)**
Use a sentiment API service (e.g., Finnhub News Sentiment API)

**Recommendation**: Start with Option 2 (API), add Option 1 later if needed

---

## Phase 2D: Alternative Data Sources (Priority: LOW)

### Wikipedia Pageviews

**Predictive Value**: Low (useful for major events)
**Use Case**: Detects attention spikes
**Implementation**: Easy (free API)

```python
import requests

def get_wikipedia_views(self, company_name: str) -> Dict[str, Any]:
    """
    Get Wikipedia pageview trend

    Example: https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/Apple_Inc./daily/20240101/20240107
    """
    try:
        # Get last 7 days of pageviews
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")

        article = company_name.replace(" ", "_")
        url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/{article}/daily/{start_date}/{end_date}"

        response = self.session.get(url)
        data = response.json()

        if "items" not in data:
            return None

        views = [item["views"] for item in data["items"]]

        if len(views) < 2:
            return None

        # Compare recent vs baseline
        recent_avg = sum(views[-2:]) / 2
        baseline_avg = sum(views[:-2]) / (len(views) - 2)

        trend_ratio = recent_avg / baseline_avg if baseline_avg > 0 else 1.0
        score = (trend_ratio - 1.0) * 0.5  # Scale down (Wikipedia is weak signal)

        return {
            "score": float(score),
            "recent_views": int(recent_avg),
            "baseline_views": int(baseline_avg),
            "trend_ratio": float(trend_ratio)
        }

    except Exception as e:
        logger.debug(f"Could not get Wikipedia views: {e}")
        return None
```

### StockTwits / Twitter

**Predictive Value**: Medium (social sentiment)
**Issue**: Requires API access ($$$ or complicated auth)
**Recommendation**: Skip for now, add in Phase 3

---

## Implementation Order

### Week 1: Core Fixes

1. **Day 1-2**: Fix market sentiment with fallback sources
   - Add Alpha Vantage support
   - Add Finnhub support
   - Implement fallback chain

2. **Day 3-4**: Google Trends integration
   - Add pytrends dependency
   - Implement trend fetching
   - Add to stock sentiment

3. **Day 5**: Testing
   - Test with paper trading
   - Verify sentiment scores
   - Monitor API call limits

### Week 2: Advanced Features (Optional)

4. **Day 6-8**: FinBERT integration (if needed)
   - Try Finnhub Sentiment API first
   - Fall back to local FinBERT if API insufficient

5. **Day 9-10**: Wikipedia pageviews
   - Implement pageview tracking
   - Add to sentiment scoring

---

## Dependencies to Add

### Required for Week 1:
```bash
pip install pytrends  # Google Trends
```

### Optional for Week 2:
```bash
pip install transformers torch  # FinBERT (large dependencies!)
# OR
# Use Finnhub API (no dependencies)
```

### requirements.txt additions:
```
# Phase 2: Advanced Sentiment
pytrends==4.9.2           # Google Trends
# transformers==4.35.0    # FinBERT (optional, large)
# torch==2.1.0            # FinBERT (optional, large)
```

---

## Configuration Changes

### .env additions:
```bash
# Phase 2: Sentiment Data Sources (Optional)
ALPHA_VANTAGE_API_KEY=your_key_here  # Free tier: 25 calls/day
FINNHUB_API_KEY=your_key_here        # Free tier: 60 calls/min

# Enable/Disable Advanced Sentiment
ENABLE_GOOGLE_TRENDS=true
ENABLE_FINBERT=false                  # Set true if using local FinBERT
```

---

## Expected Results

### Before Phase 2:
- Sentiment analysis: Broken (disabled)
- News sentiment: Basic TextBlob
- Alternative data: None
- Estimated accuracy: 75-80% (after Phase 1)

### After Phase 2:
- Sentiment analysis: Working with fallbacks
- News sentiment: FinBERT or improved API
- Alternative data: Google Trends, optionally Wikipedia
- Estimated accuracy: 85-90% (+10-15% improvement)

---

## Testing Plan

### Test 1: Market Sentiment Reliability
- Run for 1 week
- Monitor VIX, S&P 500, NASDAQ sentiment
- Verify fallback sources work when yfinance fails

### Test 2: Google Trends Accuracy
- Compare trend scores vs price movements
- Identify false positives (hype without price change)
- Adjust scoring weights

### Test 3: API Rate Limits
- Track API call counts
- Verify free tier limits not exceeded
- Implement caching if needed

### Test 4: Overall Impact
- Compare win rate before/after Phase 2
- Track improvement in sentiment-driven trades
- Measure if sentiment improves entry/exit timing

---

## Risk Mitigation

### Risk 1: API Rate Limits
**Mitigation**: Implement caching, fallback to less-frequent updates

### Risk 2: Google Trends Rate Limits
**Mitigation**: Cache for 15 minutes, batch queries

### Risk 3: FinBERT Performance
**Mitigation**: Use API service instead of local model

### Risk 4: False Signals from Hype
**Mitigation**: Weight alternative data lower, focus on technicals

---

## Rollback Plan

If Phase 2 causes issues:

1. Set `ENABLE_GOOGLE_TRENDS=false`
2. Set `include_sentiment=False` in MarketAnalyzer
3. System falls back to Phase 1 (technical indicators only)

---

## Success Metrics

After 1 week of testing:

1. **Sentiment Availability**: >90% (vs 0% currently)
2. **API Reliability**: <5% failure rate
3. **Win Rate**: Improvement of 5-10% on sentiment-driven trades
4. **False Positive Rate**: <20% for Google Trends signals

---

## Next Steps

1. ✅ Review this plan
2. ⏳ Add pytrends to requirements.txt
3. ⏳ Implement market sentiment fallbacks
4. ⏳ Add Google Trends integration
5. ⏳ Test for 1 week
6. ⏳ Evaluate FinBERT necessity

---

**Document Version**: 1.0
**Created**: 2026-01-15
**Status**: Ready for Implementation
