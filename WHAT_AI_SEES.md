# What the AI Actually Sees

## Short Answer

**YES** - The AI receives **comprehensive real market data**, not just a prompt asking about buying/selling.

## Complete Data Flow

### 1. Market Data Collection

**Source: `src/strategy/market_analyzer.py`**

The system fetches real-time data from Alpaca:

```python
# Real market data fetched:
- Latest bid/ask quotes (real-time prices)
- Last 100 1-minute bars (OHLCV data)
- Current volume
- Recent news headlines
- Market sentiment indicators (if enabled)
- 12 technical indicators (see below)
```

### 2. Technical Analysis Calculation

The system **calculates** (not just retrieves) technical indicators:

```python
indicators = {
    # Moving Averages
    "SMA_20": 174.80,          # 20-period Simple Moving Average
    "SMA_50": 172.40,          # 50-period Simple Moving Average
    "EMA_12": 175.10,          # 12-period Exponential Moving Average
    "EMA_26": 173.90,          # 26-period Exponential Moving Average

    # Momentum Oscillators
    "RSI_14": 62.34,           # Relative Strength Index
    "STOCH_K": 65.5,           # Stochastic %K
    "STOCH_D": 62.1,           # Stochastic %D
    "STOCH_signal": "Neutral", # Overbought/Oversold status

    # Trend Indicators
    "MACD": 1.23,              # MACD line
    "MACD_signal": 0.98,       # MACD signal line
    "MACD_histogram": 0.25,    # MACD histogram

    # Volatility Indicators
    "BB_upper": 178.45,        # Bollinger Band upper
    "BB_middle": 175.20,       # Bollinger Band middle
    "BB_lower": 171.95,        # Bollinger Band lower
    "ATR_14": 2.50,            # Average True Range (14-period)
    "ATR_percent": 1.42,       # ATR as % of price

    # Volume Indicators
    "volume_ratio": 1.2,       # Current volume vs 20-day average
    "VWAP": 175.00,            # Volume-Weighted Average Price
    "VWAP_position": 0.28,     # Price position relative to VWAP (%)
    "OBV": 12345678,           # On-Balance Volume
    "OBV_trend": "Rising",     # Volume flow direction

    # Support/Resistance
    "PIVOT": 174.50,           # Pivot Point
    "PIVOT_R1": 176.20,        # Resistance Level 1
    "PIVOT_R2": 177.80,        # Resistance Level 2
    "PIVOT_S1": 172.80,        # Support Level 1
    "PIVOT_S2": 171.20,        # Support Level 2
    "PIVOT_position": "Above Pivot",  # Current position

    # Price Action
    "momentum_10": 2.5         # 10-period price momentum
}
```

### 3. Data Formatting for AI

**Source: `src/llm/base.py` → `format_market_data()`**

The data is formatted into a structured prompt:

```
Symbol: AAPL
Current Price: $175.50
Daily Change: +0.75%
Volume: 45,234,567

Technical Indicators:
  Moving Averages:
  - SMA_20: 174.80
  - SMA_50: 172.40
  - EMA_12: 175.10
  - EMA_26: 173.90

  Momentum Oscillators:
  - RSI_14: 62.34 (Neutral)
  - Stochastic K: 65.5, D: 62.1 (Neutral)

  Trend Indicators:
  - MACD: 1.23
  - MACD_signal: 0.98
  - MACD_histogram: 0.25

  Volatility Indicators:
  - BB_upper: 178.45
  - BB_middle: 175.20
  - BB_lower: 171.95
  - ATR_14: 2.50 (1.42% volatility)

  Volume Indicators:
  - Volume_ratio: 1.2x average
  - VWAP: 175.00 (Price +0.28% above)
  - OBV: 12,345,678 (Rising)

  Support/Resistance:
  - Pivot: 174.50
  - R1: 176.20, S1: 172.80
  - Position: Above Pivot

  Price Action:
  - Momentum_10: 2.5

Recent News Headlines:
  1. Apple announces new product line with strong pre-orders
  2. Tech sector rallies on positive economic data
  3. Analysts upgrade AAPL target price to $190
```

### 4. Additional Context

**Portfolio information** is appended:

```
💰 PORTFOLIO STATUS
Total Value: $100,000.00
Cash: $95,000.00
Invested: $5,000.00 (5.0%)

📊 POSITIONS: 2/5
  • MSFT: 5 shares @ $380.00 (-1.18%)
  • GOOGL: 8 shares @ $140.00 (+2.50%)

🛡️ RISK STATUS
Daily P&L: $22.50
Exposure: $5,000/$5,000 (100.0%)

Trading Recommendations:
  - No position held - SELL would be a short sale
  - Historical win rate: 60.0% (3/5 trades)
```

### 5. Complete AI Prompt

**Source: `src/llm/anthropic_provider.py`**

Here's the **EXACT prompt** sent to Claude:

```
SYSTEM PROMPT:
You are an expert day trader and financial analyst with deep knowledge of:
- Technical analysis (support/resistance, momentum, trend indicators)
- Fundamental analysis (earnings, news impact, market sentiment)
- Risk management and position sizing
- Market microstructure and order flow

Your analysis should be:
1. Data-driven and objective
2. Conservative with risk assessment
3. Clear about confidence levels
4. Specific about entry/exit points
5. Focused on day trading timeframes (intraday opportunities)

Format your response as JSON with these fields:
{
  "signal": "BUY" | "SELL" | "HOLD",
  "confidence": 0-100,
  "reasoning": "Brief explanation",
  "entry_price": <number or null>,
  "stop_loss": <number or null>,
  "take_profit": <number or null>,
  "position_size_recommendation": "SMALL" | "MEDIUM" | "LARGE",
  "risk_factors": ["list", "of", "risks"],
  "time_horizon": "minutes or hours for this trade"
}

USER PROMPT:
Analyze the following market data and provide a day trading recommendation:

Symbol: AAPL
Current Price: $175.50
Daily Change: +0.75%
Volume: 45,234,567

Technical Indicators:
  Moving Averages:
  - SMA_20: 174.80
  - SMA_50: 172.40
  - EMA_12: 175.10
  - EMA_26: 173.90

  Momentum Oscillators:
  - RSI_14: 62.34 (Neutral)
  - Stochastic K: 65.5, D: 62.1 (Neutral)

  Trend Indicators:
  - MACD: 1.23
  - MACD_signal: 0.98
  - MACD_histogram: 0.25

  Volatility Indicators:
  - BB_upper: 178.45
  - BB_middle: 175.20
  - BB_lower: 171.95
  - ATR_14: 2.50 (1.42% volatility)

  Volume Indicators:
  - Volume_ratio: 1.2x average
  - VWAP: 175.00 (Price +0.28% above)
  - OBV: 12,345,678 (Rising)

  Support/Resistance:
  - Pivot: 174.50
  - R1: 176.20, S1: 172.80
  - Position: Above Pivot

  Price Action:
  - Momentum_10: 2.5

Recent News Headlines:
  1. Apple announces new product line with strong pre-orders
  2. Tech sector rallies on positive economic data
  3. Analysts upgrade AAPL target price to $190

Additional Context:
💰 PORTFOLIO STATUS
Total Value: $100,000.00
Cash: $95,000.00
Invested: $5,000.00 (5.0%)

📊 POSITIONS: 2/5
  • MSFT: 5 shares @ $380.00 (-1.18%)

Trading Recommendations:
  - No position held - SELL would be a short sale

Provide your analysis in the JSON format specified.
```

## What AI Does NOT See

❌ **Historical price charts** (only 100 recent bars for calculations)
❌ **Order book depth** (level 2 data)
❌ **Options flow** data
❌ **Insider trading** activity
❌ **Earnings estimates** (beyond news headlines)
❌ **Analyst price targets** (beyond news)
❌ **Competitor data**
❌ **Macroeconomic indicators** (GDP, CPI, etc.)

## Data Quality

### Real-Time Data
- ✅ Bid/Ask prices updated every API call
- ✅ 1-minute bars (last 100 minutes)
- ✅ Current volume
- ✅ Real news headlines

### Calculated Indicators
All technical indicators are **calculated in real-time** from the bar data:
- RSI uses actual 14-period price changes
- MACD uses actual 12/26 EMA calculations
- Bollinger Bands use actual 20-period std dev
- Moving averages use actual price data

### Not Mocked or Simulated
The data comes from:
1. **Alpaca API** (real broker data)
2. **yfinance** (Yahoo Finance data for news)
3. **Actual calculations** on real price bars

## Example: How RSI is Calculated

```python
# From market_analyzer.py line 172-181
def _calculate_rsi(prices, period=14):
    # Uses REAL price data from last 100 bars
    delta = prices.diff()  # Price changes
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    return rsi.iloc[-1]  # Returns actual RSI value
```

This is **real technical analysis**, not simulated.

## AI's Decision Process

Based on the real data, the AI:

1. **Analyzes price action**
   - Is price above/below moving averages?
   - Is trend bullish or bearish?

2. **Evaluates momentum**
   - RSI overbought/oversold?
   - MACD showing strength?

3. **Checks volatility**
   - Bollinger Band position?
   - Price stability?

4. **Considers volume**
   - Above/below average?
   - Confirming price moves?

5. **Reviews news sentiment**
   - Positive or negative headlines?
   - Market-moving events?

6. **Factors portfolio context**
   - Already own the stock?
   - Portfolio at capacity?
   - Risk limits reached?

7. **Generates recommendation**
   - BUY/SELL/HOLD signal
   - Confidence percentage
   - Entry/exit prices
   - Risk assessment

## Verification

You can verify what the AI receives by:

### 1. Check the Logs

The new logging shows exactly what's sent:

```bash
tail -f logs/trading.log
```

You'll see:
```
📊 AI ANALYSIS INPUT SUMMARY FOR AAPL
💵 PRICE DATA:
  Current: $175.50
📈 TECHNICAL INDICATORS:
  RSI(14): 62.34 (Neutral)
  [... all the data ...]
```

### 2. Inspect the Code

Look at these files:
- `src/strategy/market_analyzer.py` - Data fetching
- `src/llm/base.py` - Data formatting
- `src/llm/anthropic_provider.py` - Prompt construction

### 3. Add Debug Logging

Add this to `src/llm/anthropic_provider.py` line 91:

```python
print("=" * 70)
print("EXACT PROMPT SENT TO AI:")
print("=" * 70)
print(prompt)
print("=" * 70)
```

## Summary

### The AI Receives:

✅ **Real-time prices** from Alpaca
✅ **100 bars of price history** (OHLCV)
✅ **Calculated technical indicators** (11+ indicators)
✅ **Recent news headlines**
✅ **Market sentiment** (if enabled)
✅ **Portfolio context** (your positions, limits)
✅ **Trading constraints** (can buy/sell)

### The AI Does NOT Just Get:

❌ "Should I buy AAPL?" (vague question)
❌ Just current price
❌ Just news headlines
❌ Generic market advice

### The AI Actually Gets:

✅ **Comprehensive market data**
✅ **Detailed technical analysis**
✅ **Full context about your portfolio**
✅ **Specific constraints and rules**
✅ **Expert system prompt** guiding analysis

## Conclusion

**Your AI is analyzing REAL market data with REAL technical indicators.**

It's not just being asked "should I buy this?" - it's receiving the same type of data a professional trader would use, formatted in a way that allows it to make informed, data-driven trading decisions.

The system:
1. ✅ Fetches real-time market data
2. ✅ Calculates real technical indicators
3. ✅ Formats comprehensive context
4. ✅ Sends everything to the AI
5. ✅ AI analyzes like a professional trader
6. ✅ Returns data-driven recommendation

This is **real technical analysis**, not guesswork!

---

**Want to see it yourself?** Run the bot and watch `logs/trading.log` - you'll see every piece of data the AI receives before making each decision.
