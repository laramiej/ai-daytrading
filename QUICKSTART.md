# Quick Start Guide

Get up and running with the AI Day Trading System in 5 minutes.

## Step 1: Get API Keys

### Alpaca (Required)
1. Go to https://alpaca.markets/
2. Sign up for a free account
3. Navigate to "Paper Trading" section
4. Copy your API Key and Secret Key

### LLM Provider (Pick at least one)

**Option A: Anthropic Claude (Recommended)**
1. Go to https://console.anthropic.com/
2. Sign up and get your API key
3. Copy the API key

**Option B: OpenAI**
1. Go to https://platform.openai.com/
2. Sign up and create an API key
3. Copy the API key

**Option C: Google Gemini**
1. Go to https://makersuite.google.com/
2. Get your API key
3. Copy the API key

## Step 2: Install

```bash
cd ai_daytrading

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Configure

```bash
# Copy example config
cp .env.example .env

# Edit with your favorite editor
nano .env  # or vim, code, etc.
```

**Minimum required configuration:**

```env
# Alpaca (required)
ALPACA_API_KEY=your_alpaca_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_here
ALPACA_PAPER_TRADING=true

# LLM (at least one required)
ANTHROPIC_API_KEY=your_anthropic_key_here
# OR
OPENAI_API_KEY=your_openai_key_here
# OR
GOOGLE_API_KEY=your_google_key_here

DEFAULT_LLM_PROVIDER=anthropic  # or openai, or google
```

## Step 4: Run

```bash
python run_bot.py
```

## What Happens Next?

1. **Status Display**: You'll see your account balance and current positions
2. **Market Scan**: The bot analyzes your watchlist (default: AAPL, MSFT, GOOGL, etc.)
3. **Trading Signals**: If opportunities are found, you'll see recommendations with:
   - Symbol and action (BUY/SELL)
   - Confidence score
   - AI reasoning
   - Entry/exit prices
   - Risk assessment
4. **Your Decision**: You approve or reject each trade
5. **Execution**: Approved trades are placed via Alpaca

## Example Output

```
======================================================================
📊 TRADING BOT STATUS
======================================================================

💰 Account Information:
  Portfolio Value: $100,000.00
  Cash: $95,000.00
  Buying Power: $100,000.00

📈 Open Positions: 2
  AAPL: 10 shares @ $170.50 (Current: $175.00, P&L: +$45.00 [+2.64%])
  MSFT: 5 shares @ $380.00 (Current: $375.50, P&L: -$22.50 [-1.18%])

🛡️  Risk Management:
  Daily P&L: $0.00
  Open Positions: 2 / 5
  Total Exposure: $5,000.00 / $5,000.00

🤖 AI Provider: anthropic (claude-3-5-sonnet-20241022)

🏛️  Market Status: 🟢 OPEN
======================================================================

🎯 Found 1 trading opportunities:
  1. TSLA: BUY (Confidence: 82%)
```

## Testing Without Risk

The system is configured for **paper trading by default**. This means:
- ✅ No real money is used
- ✅ All trades are simulated
- ✅ Safe for testing and learning
- ✅ Real market data

## Customization

### Change Watchlist

Edit `.env`:
```env
WATCHLIST=TSLA,NVDA,AMZN,SPY
```

### Adjust Risk Limits

Edit `.env`:
```env
MAX_POSITION_SIZE=500       # $500 max per trade
MAX_DAILY_LOSS=200          # Stop if lose $200 in a day
MAX_TOTAL_EXPOSURE=2000     # $2000 max total exposure
```

### Switch LLM Provider

In the code:
```python
from main import DayTradingBot

bot = DayTradingBot()

# Switch to OpenAI
bot.switch_llm_provider("openai")

# Run scan
bot.run_single_scan(min_confidence=70.0)
```

## Tips for Success

1. **Start Slow**: Watch the bot run for a few days before trusting its recommendations
2. **Review Reasoning**: Always read the AI's reasoning before approving trades
3. **Check Logs**: Review `logs/trading.log` to understand what's happening
4. **Adjust Confidence**: Start with high confidence thresholds (80%+)
5. **Respect Risk Limits**: Don't override risk management warnings
6. **Learn Continuously**: Study which signals work and which don't

## Common First-Time Issues

**"Market is closed"**
- Run during market hours: 9:30 AM - 4:00 PM ET, Monday-Friday

**"No signals found"**
- Lower the confidence threshold
- Try different symbols in watchlist
- Wait for different market conditions

**"API key not configured"**
- Double-check your `.env` file
- Make sure there are no spaces around the `=` sign
- Verify the key is correct (try it in the provider's web console)

## Next Steps

1. **Read the full README.md** for detailed documentation
2. **Experiment with different LLMs** to see which performs best
3. **Customize the strategy** in `src/strategy/trading_strategy.py`
4. **Add more technical indicators** in `src/strategy/market_analyzer.py`
5. **Monitor performance** and keep notes on what works

## Need Help?

- Check `logs/trading.log` for detailed error messages
- Review the full README.md
- Make sure all API keys are valid
- Verify you're running during market hours

## Important Reminder

This is **paper trading with simulated money**. Even though it's not real, treat it seriously to build good habits. When you're ready to consider real trading:

1. Test for at least 1 month with paper trading
2. Review all trades and results
3. Understand the system completely
4. Start with very small amounts
5. Never trade money you can't afford to lose

---

**Happy Trading! (Paper trading, that is)** 📈🤖
