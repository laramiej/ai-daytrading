# Short Selling Feature

Your AI day trading system now supports **short selling** - the ability to sell stocks you don't own to profit from price declines.

## What is Short Selling?

Short selling allows you to:
- **SELL first**, then **BUY later** (opposite of normal trading)
- Profit when stock prices **go down**
- Capitalize on bearish market opportunities

### Example
```
1. AI detects TSLA is overvalued at $250
2. SELL 10 shares of TSLA @ $250 (you don't own it - this is a short)
3. TSLA drops to $230
4. BUY 10 shares @ $230 to close the short
5. Profit: ($250 - $230) × 10 = $200
```

## ⚠️ Important Risks

### Unlimited Loss Potential
Unlike buying stocks (max loss = initial investment), short selling has **unlimited risk**:

**Long Position (BUY):**
- Buy AAPL @ $100
- Worst case: Stock goes to $0
- Maximum loss: $100

**Short Position (SELL):**
- Sell AAPL @ $100 (short)
- Worst case: Stock goes to $500
- Maximum loss: $400 (and climbing!)

### Margin Requirements
- Short selling requires a **margin account**
- Broker charges **borrowing fees**
- Account must maintain **minimum equity**
- Margin calls can force position closure

### Additional Risks
1. **Forced Buy-In**: Broker may close your position if shares aren't available
2. **Dividend Payments**: You owe dividends if stock pays them while you're short
3. **Hard-to-Borrow Stocks**: Some stocks are expensive or impossible to short
4. **Market Rallies**: Bull markets can be devastating for shorts

## Configuration

### Enable/Disable Short Selling

Edit your `.env` file:

```bash
# Enable short selling (default)
ENABLE_SHORT_SELLING=true

# Disable short selling (safer)
ENABLE_SHORT_SELLING=false
```

**Default: Enabled** - The system allows short selling by default.

### Verify Your Configuration

Check if short selling is enabled:

```python
from main import DayTradingBot

bot = DayTradingBot()
print(f"Short selling: {bot.risk_manager.limits.enable_short_selling}")
```

## How It Works

### AI Recommendation Flow

1. **Stock Analysis**: AI analyzes watchlist stocks
2. **Bearish Signal**: AI detects downward momentum
3. **Check Position**:
   - Own the stock? → Suggests SELL to close position
   - Don't own it? → Suggests SELL to open short
4. **Risk Check**: Risk manager verifies short selling is enabled
5. **User Approval**: You approve or reject the trade
6. **Execution**: Order is sent to Alpaca

### Example AI Output

#### Scenario 1: Short Sell Opportunity
```
📊 TSLA Analysis
Signal: SELL
Confidence: 75%

Reasoning: "Stock showing bearish divergence, RSI overbought at 78,
price near resistance at $255. Momentum indicators suggest pullback.
Recommend short position targeting $240 support level."

Portfolio Context:
  • No position held - SELL would be a short sale

⚠️  SHORT SELL - Selling stock you don't own

[1] Approve  [2] Reject  [3] Details
```

#### Scenario 2: Close Long Position
```
📊 AAPL Analysis
Signal: SELL
Confidence: 80%

Reasoning: "Currently holding position with +8% gain. Technical
indicators show weakening momentum. Recommend taking profits."

Portfolio Context:
  • Currently holding 10 shares
  • Position is profitable: +8.2%

(This is closing an existing position, NOT a short sell)

[1] Approve  [2] Reject  [3] Details
```

### Trade Execution Warning

When you approve a short sell, you'll see:

```
⚠️  SHORT SELL WARNING
You are about to SELL 10 shares of TSLA that you DO NOT own.
This is a short sale with unlimited risk potential.

Current Price: $250.00
Max Loss: UNLIMITED
Estimated Value: $2,500

Are you sure? (yes/no):
```

## Position Management

### Viewing Short Positions

Your portfolio will show short positions:

```
📊 POSITIONS: 3/5
  • AAPL: 10 shares @ $170.50 (+2.64%)    [LONG]
  • MSFT: 5 shares @ $380.00 (-1.18%)     [LONG]
  • TSLA: -15 shares @ $250.00 (+4.50%)   [SHORT]
```

Note: Short positions show **negative quantity** and profit when price goes down.

### Closing Short Positions

To close a short, you **BUY** the stock:

1. You're short 10 shares of TSLA @ $250
2. AI suggests BUY signal when TSLA drops to $230
3. BUY 10 shares @ $230 closes the short
4. Profit: $200

The AI will automatically recognize you have a short position and suggest BUY to close it.

## Risk Management for Shorts

### Position Sizing

Short positions count toward your limits:

```
MAX_POSITION_SIZE=1000        # Applies to shorts too
MAX_TOTAL_EXPOSURE=5000       # Includes short exposure
MAX_OPEN_POSITIONS=5          # Longs + shorts combined
```

### Stop Loss (Critical for Shorts!)

Short positions should **always** have stop losses:

```
Short TSLA @ $250
Stop Loss: $260 (4% above entry)
Max Loss: $100 (controlled)
```

Without a stop loss, losses can spiral out of control.

### Daily Loss Limit

```
MAX_DAILY_LOSS=500
```

This protects you from catastrophic short squeezes.

## When to Use Short Selling

### Good Short Candidates

✅ **Technical Breakdown**: Clear downtrend, breaking support
✅ **Overvalued**: High RSI, extended above moving averages
✅ **Negative Catalysts**: Bad earnings, negative news
✅ **Market Weakness**: Bearish market sentiment, high VIX
✅ **Relative Weakness**: Stock weak vs. market

### Avoid Shorting

❌ **High Short Interest**: Risk of short squeeze
❌ **Low Float Stocks**: Can spike violently
❌ **Meme Stocks**: Irrational price action (GME, AMC)
❌ **Strong Uptrends**: Don't fight the trend
❌ **Before Earnings**: Binary events = unpredictable

## Examples

### Example 1: Successful Short

```
Day 1:
AI detects NFLX weakness @ $450
Signal: SELL (Short) - Confidence 72%
Execute: Sell 10 shares @ $450

Day 2:
NFLX drops to $430
AI suggests: BUY to close - Confidence 65%
Execute: Buy 10 shares @ $430

Result: Profit = ($450 - $430) × 10 = $200 ✅
```

### Example 2: Failed Short (Loss Controlled)

```
Day 1:
AI detects AMD weakness @ $150
Signal: SELL (Short) - Confidence 70%
Execute: Sell 10 shares @ $150
Stop Loss: $157 (4.7% risk)

Day 2:
AMD rallies to $157 (bad news priced in)
Stop Loss triggered: Buy 10 shares @ $157

Result: Loss = ($150 - $157) × 10 = -$70 ❌
(But loss was limited by stop!)
```

### Example 3: Disaster Scenario (Without Stop Loss)

```
Day 1:
Short TSLA @ $200
No stop loss set ⚠️

Day 2:
Elon Musk tweets positive news
TSLA spikes to $240 (+20%)

Day 3:
More buying pressure
TSLA at $280 (+40%)

Current Loss: ($200 - $280) × 10 = -$800 😱
Still climbing...
```

**This is why stop losses are critical!**

## Monitoring Shorts

### Portfolio Tracking

The system tracks shorts separately:

```python
# Get all positions
positions = bot.portfolio.get_portfolio_summary()

for pos in positions["positions"]["details"]:
    if pos["side"] == "short":
        print(f"Short Position: {pos['symbol']}")
        print(f"  Entry: ${pos['entry_price']:.2f}")
        print(f"  Current: ${pos['current_price']:.2f}")
        print(f"  P&L: ${pos['pnl']:.2f}")
```

### Performance Metrics

Track your short selling performance:

```
📈 PERFORMANCE
Total Trades: 15
  Long Trades: 10 (60% win rate)
  Short Trades: 5 (40% win rate)

Short Performance:
  Avg Win: $150
  Avg Loss: -$80
  Best Short: NFLX +$300
  Worst Short: TSLA -$200
```

## Best Practices

### 1. Start Small
- Test with paper trading first
- Use small position sizes initially
- Learn short selling behavior

### 2. Always Use Stop Losses
- **Never** short without a stop
- Set stops 3-5% above entry
- Honor your stops (no exceptions!)

### 3. Watch Market Conditions
- Shorts work best in bear markets
- Bull markets are dangerous for shorts
- Check VIX for volatility

### 4. Diversify Direction
- Don't go 100% short
- Mix longs and shorts
- Hedge your portfolio

### 5. Respect the AI Confidence
- High confidence shorts (>75%) preferred
- Skip low confidence shorts (<60%)
- Consider market sentiment

### 6. Monitor Closely
- Shorts can move against you fast
- Check positions regularly
- Be ready to cut losses

## Disabling Short Selling

If you want to trade **long-only** (safer):

1. Edit `.env`:
```bash
ENABLE_SHORT_SELLING=false
```

2. Restart the bot:
```bash
python src/main.py
```

3. AI will only suggest:
   - **BUY** for stocks you don't own
   - **SELL** for stocks you do own
   - **HOLD** otherwise

## Alpaca Requirements

To short sell on Alpaca:

1. **Account Type**: Must have a margin account
2. **Minimum Equity**: Usually $2,000 minimum
3. **Pattern Day Trader**: If making >3 day trades/week, need $25,000
4. **Borrowable Shares**: Stock must be available to borrow

Check with Alpaca:
```python
from broker import AlpacaBroker

broker = AlpacaBroker(...)
account = broker.get_account_info()

print(f"Account Type: {account.get('account_type', 'Unknown')}")
print(f"Shorting Enabled: {account.get('shorting_enabled', False)}")
```

## Troubleshooting

**"Short selling disabled"**
- Check `.env` has `ENABLE_SHORT_SELLING=true`
- Restart the bot after changing config

**"No shares available to borrow"**
- Stock is hard to borrow
- Alpaca doesn't have shares
- Try a different stock

**"Insufficient buying power for short"**
- Need more margin in account
- Position size too large
- Check account equity

**"Pattern Day Trader restriction"**
- >3 day trades in 5 days
- Need $25,000 account minimum
- Switch to swing trading (hold >1 day)

## Summary

✅ **Short selling is now enabled** by default
✅ AI can suggest SELL signals for stocks you don't own
✅ Risk manager warns you before executing shorts
✅ Portfolio tracking includes short positions
✅ Can disable with `ENABLE_SHORT_SELLING=false`

⚠️ **Remember**: Short selling is risky. Always use stop losses and start with paper trading!

---

**Pro Tip**: In volatile markets, short selling can be very profitable, but in strong bull markets, it's better to focus on long positions. Let the AI guide you, but respect the risks!
