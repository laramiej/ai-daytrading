# What's New: Short Selling Feature

## Summary

Your AI day trading system now supports **short selling** - the ability to profit from declining stock prices by selling stocks you don't own.

## What Changed

### 1. Configuration Option (`.env`)

Added new setting to control short selling:

```bash
ENABLE_SHORT_SELLING=true   # Default: enabled
```

### 2. Risk Manager Updates

**File: `src/risk/risk_manager.py`**

- Added `enable_short_selling` parameter to `RiskLimits`
- Modified position check logic to allow SELL orders without owning the stock
- Added warning when approving short sells: "⚠️ SHORT SELL - Selling stock you don't own"

**Behavior:**
- If `enable_short_selling=true`: SELL orders work for any stock (owned or not)
- If `enable_short_selling=false`: SELL orders only work for stocks you own (original behavior)

### 3. Portfolio Context Updates

**File: `src/strategy/portfolio_context.py`**

- Changed `can_sell` to always be `True` (instead of only when position exists)
- Added context message: "No position held - SELL would be a short sale"
- AI now sees that short selling is possible for stocks not owned

### 4. Main Application Updates

**File: `src/main.py`**

- Passes `enable_short_selling` setting to risk manager
- No other changes needed - everything flows through configuration

### 5. Configuration File Updates

**File: `src/utils/config.py`**

- Added `enable_short_selling: bool` field to Settings class
- Defaults to `True`
- Loaded from environment variable `ENABLE_SHORT_SELLING`

## How It Works Now

### Before (Old Behavior)

```
Scenario: AI suggests SELL for TSLA (you don't own it)
Result: ❌ Trade blocked - "No position found for TSLA"
```

### After (New Behavior)

```
Scenario: AI suggests SELL for TSLA (you don't own it)

If ENABLE_SHORT_SELLING=true:
  Result: ✅ Trade approved
  Warning: "⚠️ SHORT SELL - Selling stock you don't own"
  Execution: Opens short position

If ENABLE_SHORT_SELLING=false:
  Result: ❌ Trade blocked - "Short selling disabled. No position found for TSLA"
```

## Example Workflow

### 1. AI Detects Bearish Signal

```
📊 Analyzing TSLA...

Technical Analysis:
  - RSI: 78 (Overbought)
  - MACD: Bearish crossover
  - Price: $250 (near resistance)

AI Recommendation:
  Signal: SELL
  Confidence: 75%
  Reasoning: "Stock showing bearish signals, recommend short position"
```

### 2. Portfolio Context

```
Portfolio Context for TSLA:
  • No position held - SELL would be a short sale
  • Historical win rate: 60% (3/5 trades)
  • Can SELL: Yes (short selling enabled)
```

### 3. Trade Approval

```
======================================================================
📊 TRADING SIGNAL: SELL TSLA
======================================================================

Signal: SELL (Short Position)
Confidence: 75%

Entry Price: $250.00
Stop Loss: $260.00
Take Profit: $240.00

Position Size: SMALL
Quantity: 10 shares

💰 Estimated Value: $2,500.00

⚠️  SHORT SELL - Selling stock you don't own

🛡️  Risk Management:
  ✅ Trade approved - all risk checks passed

======================================================================
Approve this trade? (yes/no):
```

### 4. Position Tracking

After opening short:

```
📊 POSITIONS: 3/5
  • AAPL: 10 shares @ $170.50 (+2.64%)    [LONG]
  • MSFT: 5 shares @ $380.00 (-1.18%)     [LONG]
  • TSLA: -10 shares @ $250.00 (+0.00%)   [SHORT]
```

### 5. Closing the Short

When AI detects TSLA dropped:

```
📊 Analyzing TSLA...

Current Price: $240 (down from $250)
Portfolio: Short 10 shares @ $250

AI Recommendation:
  Signal: BUY
  Confidence: 70%
  Reasoning: "Target price reached, cover short position"

Approve this trade? (yes/no): yes

✅ BUY order executed: 10 shares @ $240
✅ Short position closed
💰 Profit: $100 (($250 - $240) × 10)
```

## Configuration Examples

### Enable Short Selling (Default)

**.env:**
```bash
ENABLE_SHORT_SELLING=true
```

**Result:**
- AI can suggest SELL for any stock on watchlist
- You'll be warned before executing shorts
- Can profit from declining stocks

### Disable Short Selling (Conservative)

**.env:**
```bash
ENABLE_SHORT_SELLING=false
```

**Result:**
- AI can only suggest SELL for stocks you own
- Short sells are blocked by risk manager
- Long-only trading (safer for beginners)

## Safety Features

### 1. Explicit Warnings

Every short sell shows:
```
⚠️  SHORT SELL - Selling stock you don't own
```

### 2. Manual Approval Required

You must type "yes" to approve each short sell

### 3. Stop Loss Protection

Risk manager calculates stop loss for shorts:
```
Entry: $250
Stop Loss: $260 (4% above entry)
Max Loss: $100 (controlled)
```

### 4. Position Limits Apply

Shorts count toward your limits:
```
MAX_OPEN_POSITIONS=5        # Includes both longs and shorts
MAX_POSITION_SIZE=1000      # Per short position
MAX_TOTAL_EXPOSURE=5000     # Total longs + shorts
```

### 5. Disable Anytime

Change config and restart:
```bash
# In .env
ENABLE_SHORT_SELLING=false
```

## Testing with Paper Trading

**Recommended first steps:**

1. Keep paper trading enabled:
```bash
ALPACA_PAPER_TRADING=true
```

2. Start with short selling enabled:
```bash
ENABLE_SHORT_SELLING=true
```

3. Run the bot and observe AI behavior:
```bash
python src/main.py
```

4. Watch for both BUY and SELL signals
5. Approve a short sell to see how it works
6. Monitor the short position
7. Close the short when AI suggests BUY

## Files Modified

1. ✅ `src/utils/config.py` - Added `enable_short_selling` setting
2. ✅ `src/risk/risk_manager.py` - Modified SELL order logic
3. ✅ `src/strategy/portfolio_context.py` - Updated recommendations
4. ✅ `src/main.py` - Pass setting to risk manager
5. ✅ `.env.example` - Added configuration example
6. ✅ `README.md` - Updated features list
7. ✅ `SHORT_SELLING.md` - Complete documentation (NEW)

## Quick Start

To use short selling right now:

1. **Check your `.env` file:**
```bash
cat .env | grep SHORT_SELLING
```

2. **If not set, add it:**
```bash
echo "ENABLE_SHORT_SELLING=true" >> .env
```

3. **Run the bot:**
```bash
python src/main.py
```

4. **Watch for SELL signals on stocks you don't own**

That's it! The AI will now suggest shorts when it detects bearish opportunities.

## Important Notes

⚠️ **Risks of Short Selling:**
- Unlimited loss potential (stock can rise infinitely)
- Margin requirements and borrowing fees
- Risk of forced buy-in (short squeeze)
- Always use stop losses!

✅ **Benefits:**
- Profit from declining stocks
- Hedge long positions
- More trading opportunities
- Works in bear markets

📚 **Full Documentation:**
Read [SHORT_SELLING.md](SHORT_SELLING.md) for comprehensive guide including:
- How short selling works
- Risk management strategies
- Real examples
- Best practices
- Troubleshooting

## Questions?

**Q: Is short selling enabled by default?**
A: Yes, `ENABLE_SHORT_SELLING=true` by default

**Q: Can I disable it?**
A: Yes, set `ENABLE_SHORT_SELLING=false` in `.env`

**Q: Will I be warned before shorts?**
A: Yes, every short shows "⚠️ SHORT SELL" warning

**Q: Does it work with paper trading?**
A: Yes, test shorts safely with Alpaca paper trading

**Q: Are there extra fees?**
A: Alpaca paper trading has no fees. Live trading may have borrowing fees.

**Q: Is this risky?**
A: Yes! Short selling is riskier than buying stocks. Always use stop losses.

---

**Bottom Line:** Your system can now suggest and execute short sales. Start with paper trading and read [SHORT_SELLING.md](SHORT_SELLING.md) before going live!
