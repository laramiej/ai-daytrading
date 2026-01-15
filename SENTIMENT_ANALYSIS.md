# Sentiment Analysis Feature

The AI Day Trading System now includes comprehensive sentiment analysis to help make better-informed trading decisions.

## Overview

The system analyzes sentiment from multiple sources:

### 📊 Market Sentiment (Overall Market)
- **VIX (Fear Index)**: Measures market volatility and fear
- **S&P 500 Trend**: Overall large-cap market direction
- **NASDAQ Trend**: Tech-heavy index performance

### 📈 Stock-Specific Sentiment
- **News Sentiment**: Analysis of recent news headlines
- **Analyst Ratings**: Wall Street analyst recommendations
- **Price Momentum**: Recent price action and trends
- **Social Media** (placeholder): Reddit/Twitter mentions

## Installation

First, install the new sentiment analysis dependency:

```bash
cd /Users/jasonlaramie/Documents/MyCode/ai_daytrading
source venv/bin/activate
pip install textblob
python -m textblob.download_corpora  # Download required data
```

## How It Works

### Sentiment Scores

All sentiment is scored on a scale from **-1.0 to +1.0**:

| Score Range | Interpretation |
|-------------|---------------|
| 0.6 to 1.0  | Very Bullish |
| 0.3 to 0.6  | Bullish |
| 0 to 0.3    | Slightly Bullish |
| 0 to -0.3   | Slightly Bearish |
| -0.3 to -0.6| Bearish |
| -0.6 to -1.0| Very Bearish |

### Data Sources

#### 1. VIX (Volatility Index)
- **< 12**: Very low fear (bullish market)
- **12-20**: Normal volatility (neutral)
- **20-30**: Elevated fear (bearish)
- **> 30**: High fear (very bearish)

#### 2. News Sentiment
- Analyzes headlines using natural language processing
- Identifies positive/negative language
- Weighs recent news more heavily

#### 3. Analyst Recommendations
- Aggregates Wall Street analyst ratings
- Tracks upgrades/downgrades
- Considers recommendation strength

#### 4. Price Momentum
- Week-over-week change
- Month-over-month change
- Trend direction and strength

## Testing Sentiment Analysis

Run the test script to see sentiment in action:

```bash
python test_sentiment.py
```

This will show you:
- Current market sentiment
- Sentiment for AAPL, TSLA, and MSFT
- Breakdown by data source

Example output:

```
📊 MARKET SENTIMENT
--------------------------------------------------
Overall: Bullish (0.45)

  • VIX at 15.2 indicates neutral to bullish market sentiment
  • S&P 500 +2.1% over 10 days
  • NASDAQ +3.5% over 10 days

📈 AAPL SENTIMENT
--------------------------------------------------
Overall: Bullish (0.52)

  NEWS:
    Status: Positive
    Score: 0.35
    News sentiment is positive based on 8 headlines

  ANALYSTS:
    Status: Buy
    Score: 0.65
    Analysts consensus: Buy

  MOMENTUM:
    Status: Positive
    Score: 0.55
    Price momentum is positive (+2.1% week, +5.3% month)
```

## Integration with Trading Bot

Sentiment data is automatically included in the AI's analysis. The LLM receives:

1. **Market Context**: Overall market mood
2. **Stock Sentiment**: Specific sentiment for the symbol
3. **Sentiment Sources**: Breakdown of where sentiment comes from

### Example AI Prompt (Automatic)

```
Symbol: AAPL
Current Price: $175.50

Overall Market Sentiment:
  Status: Bullish (Score: 0.45)
  - VIX at 15.2 indicates neutral to bullish market sentiment
  - S&P 500 +2.1% over 10 days

AAPL Sentiment:
  Status: Bullish (Score: 0.52)
  - News sentiment is positive based on 8 headlines
  - Analysts consensus: Buy
  - Price momentum is positive (+2.1% week, +5.3% month)

[AI analyzes this data along with technical indicators]
```

## Customization

### Disable Sentiment Analysis

If you want to trade without sentiment:

Edit `src/main.py`:

```python
# Initialize market analyzer without sentiment
self.market_analyzer = MarketAnalyzer(
    self.broker,
    include_sentiment=False  # Disable sentiment
)
```

### Adjust Sentiment Weights

Edit `src/strategy/sentiment_analyzer.py`:

```python
# In _calculate_stock_sentiment() method
weights = {
    "news": 0.25,      # 25% weight
    "reddit": 0.15,    # 15% weight (if available)
    "analysts": 0.35,  # 35% weight
    "momentum": 0.25   # 25% weight
}
```

### Add Custom Sentiment Sources

You can extend the `SentimentAnalyzer` class:

```python
def _get_twitter_sentiment(self, symbol: str) -> Optional[Dict[str, Any]]:
    """Get sentiment from Twitter mentions"""
    # Your custom implementation
    pass
```

Then add it to the `get_stock_sentiment()` method.

## Caching

To improve performance:

- **Market sentiment** is cached for 15 minutes
  - Same data used for all stocks in a scan
  - Reduces API calls

- **Stock sentiment** is calculated per stock
  - Fresh data for each symbol
  - Can be slow for large watchlists

## Limitations

### Current Limitations

1. **No Real Social Media**
   - Reddit/Twitter integration is placeholder
   - Requires API keys and additional setup

2. **News Analysis is Basic**
   - Uses simple NLP (TextBlob)
   - No deep learning models
   - May miss nuanced sentiment

3. **Analyst Data Lag**
   - Ratings update slowly
   - May not reflect latest developments

4. **API Rate Limits**
   - yfinance has rate limits
   - Too many requests may fail

### Future Enhancements

- [ ] Reddit API integration (r/wallstreetbets)
- [ ] Twitter/X sentiment analysis
- [ ] Deep learning sentiment models
- [ ] Real-time news feeds
- [ ] Earnings call transcript analysis
- [ ] Insider trading activity
- [ ] Options flow sentiment

## Interpreting Results

### Strong Agreement Across Sources
When all sources show the same sentiment, confidence is higher:

```
News: Positive (0.4)
Analysts: Buy (0.6)
Momentum: Positive (0.5)
→ Overall: Strong Bullish (0.52)
```

### Mixed Signals
Conflicting sentiment suggests caution:

```
News: Positive (0.3)
Analysts: Hold (0.0)
Momentum: Negative (-0.4)
→ Overall: Neutral (-0.03)
```

### Market vs Stock Divergence

**Bullish Market + Bearish Stock** = Stock may be weak
**Bearish Market + Bullish Stock** = Stock showing strength

## Best Practices

1. **Don't Trade on Sentiment Alone**
   - Use with technical indicators
   - Consider fundamentals
   - Check risk management

2. **Watch for Extreme Sentiment**
   - Very bullish (>0.7) may indicate overbought
   - Very bearish (<-0.7) may indicate oversold

3. **Consider Market Context**
   - Stock bullish + Market bullish = Strong signal
   - Stock bullish + Market bearish = Relative strength
   - Stock bearish + Market bullish = Weak stock

4. **Monitor Sentiment Changes**
   - Improving sentiment = Potential uptrend
   - Deteriorating sentiment = Potential downtrend
   - Sudden shifts = Important events

## Troubleshooting

**"Could not fetch news"**
- Normal if no recent news
- yfinance API may be rate-limited
- Not critical - other sources still work

**"No analyst data available"**
- Stock may not be widely covered
- Common for small-cap stocks
- Sentiment will use other sources

**Sentiment seems wrong**
- NLP is imperfect
- Check sample headlines
- Compare multiple symbols

**Slow performance**
- Sentiment analysis adds time
- Consider disabling for faster scans
- Cache helps with market sentiment

## Example Trading Scenarios

### Scenario 1: Strong Bullish Signal
```
Market: Bullish (0.5)
Stock: Very Bullish (0.7)
Technical: RSI 45, MACD positive
→ Strong BUY candidate
```

### Scenario 2: Mixed Signal
```
Market: Bearish (-0.3)
Stock: Bullish (0.4)
Technical: Near resistance
→ Wait for better entry
```

### Scenario 3: Reversal Setup
```
Market: Neutral (0.1)
Stock: Very Bearish (-0.8)
Technical: Oversold RSI 25
→ Potential bounce play (risky)
```

## API Costs

Sentiment analysis uses free data sources:
- ✅ yfinance: Free
- ✅ TextBlob: Free (open source)
- ❌ Reddit API: Would require setup
- ❌ Twitter API: Would require paid tier

## Resources

- [TextBlob Documentation](https://textblob.readthedocs.io/)
- [VIX Information](https://www.cboe.com/tradable_products/vix/)
- [yfinance Library](https://github.com/ranaroussi/yfinance)

---

**Remember**: Sentiment analysis is one tool among many. Always use multiple indicators and proper risk management!
