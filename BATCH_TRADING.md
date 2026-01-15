# Batch Trading Guide

The AI day trading system now supports **batch execution** - approve and execute multiple trades at once!

## New Interactive Menu

When the bot finds multiple trading opportunities, you'll see:

```
======================================================================
📊 TRADING SIGNALS MENU
======================================================================

  1. AAPL - BUY
     Confidence: 85%
     Reasoning: Strong momentum with positive earnings catalyst...

  2. MSFT - BUY
     Confidence: 78%
     Reasoning: Technical breakout above resistance with high volume...

  3. TSLA - SELL
     Confidence: 72%
     Reasoning: Overbought conditions, recommend taking profits...

======================================================================

Options:
  [1-3]   Execute specific signal
  [a]     Approve and execute ALL signals
  [r]     Review signals in detail
  [0]     Skip all and continue
======================================================================

Your choice:
```

## Menu Options

### Option 1: Execute Specific Signal

Type `1`, `2`, `3`, etc. to execute a single trade:

```
Your choice: 1

[Executes AAPL trade only]
```

### Option 2: Approve All (Batch Execution)

Type `a` to approve all signals at once:

```
Your choice: a

======================================================================
🚀 BATCH EXECUTION - APPROVE ALL
======================================================================

You are about to execute 3 trades:
  1. BUY AAPL
     @ $175.50 (~5 shares)
     Estimated: $877.50

  2. BUY MSFT
     @ $380.25 (~2 shares)
     Estimated: $760.50

  3. SELL TSLA
     @ $245.80 (~4 shares)
     Estimated: $983.20

💰 Total Estimated Cost: $1,638.00
💵 Available Buying Power: $95,000.00

======================================================================
Confirm batch execution? (yes/no): yes

🔄 Executing trades...

[1/3] Processing AAPL...
✅ Order placed successfully!

[2/3] Processing MSFT...
✅ Order placed successfully!

[3/3] Processing TSLA...
✅ Order placed successfully!

======================================================================
📊 BATCH EXECUTION COMPLETE
======================================================================
✅ Successful: 3
❌ Failed: 0
📈 Total: 3
======================================================================
```

### Option 3: Review Signals

Type `r` to review each signal in detail before deciding:

```
Your choice: r

======================================================================
SIGNAL 1/3: AAPL
======================================================================

Action: BUY
Confidence: 85%
Provider: anthropic

Reasoning:
  Strong momentum indicator with RSI at 55 showing room for upside.
  Recent earnings beat expectations, positive analyst upgrades.

Entry Price: $175.50
Stop Loss: $172.00
Take Profit: $182.00

Position Size: MEDIUM
Time Horizon: 2-4 hours

⚠️  Risk Factors:
  - Market volatility is elevated
  - Approaching previous resistance level

======================================================================
Execute this trade? (yes/no/skip remaining): yes

✅ Order placed successfully!

======================================================================
SIGNAL 2/3: MSFT
======================================================================

[Shows next signal details...]
Execute this trade? (yes/no/skip remaining): skip remaining

Skipping remaining signals
```

### Option 4: Skip All

Type `0` to skip all signals and continue:

```
Your choice: 0

Skipping all signals
```

## Batch Execution Safety Features

### Pre-Execution Checks

Before executing all trades, the system shows:

1. **All trades to be executed**
   - Symbol and action
   - Estimated price and quantity
   - Estimated cost per trade

2. **Total estimated cost**
   - Sum of all trade values

3. **Available buying power**
   - Current cash available

4. **Warning if insufficient funds**
   - Alerts if total cost exceeds buying power

### Risk Management Still Active

Even with batch execution, all risk checks apply:

✅ **Position limits** - Won't exceed max positions
✅ **Daily loss limit** - Stops if limit reached
✅ **Exposure limits** - Respects total exposure cap
✅ **Individual approval** - Each trade goes through risk manager

### Failed Trades Don't Stop Batch

If one trade fails, the rest continue:

```
[1/3] Processing AAPL...
✅ Order placed successfully!

[2/3] Processing MSFT...
❌ Failed: Insufficient buying power

[3/3] Processing TSLA...
✅ Order placed successfully!

======================================================================
📊 BATCH EXECUTION COMPLETE
======================================================================
✅ Successful: 2
❌ Failed: 1
📈 Total: 3
======================================================================
```

## Use Cases

### Use Case 1: Morning Rush

Market opens with multiple opportunities:

```
Bot finds 5 strong signals
→ Review quickly with [r]
→ Approve best 3 with [a]
→ Execute efficiently
```

### Use Case 2: Selective Execution

Bot finds mixed quality signals:

```
3 signals: 2 strong, 1 weak
→ Type [1] for first signal
→ Type [2] for second signal
→ Skip the third
```

### Use Case 3: Portfolio Rebalancing

Bot suggests multiple exits:

```
3 SELL signals for profit-taking
→ Use [a] to exit all at once
→ Quick portfolio rebalancing
```

### Use Case 4: Detailed Review

Want to understand each signal:

```
→ Type [r] for review mode
→ See full details for each
→ Decide individually
```

## Best Practices

### 1. Review Before Batch Approval

Always look at the batch summary:
- Check total cost
- Verify buying power
- Confirm all symbols make sense

### 2. Use Review Mode for Learning

When learning the system:
- Use [r] to see full signal details
- Understand AI reasoning
- Learn what makes good trades

### 3. Batch Execute Similar Trades

Good for batch:
- ✅ Multiple BUYs in same sector
- ✅ Multiple exits for profit-taking
- ✅ Portfolio rebalancing trades

Review individually:
- ⚠️  Very different confidence levels
- ⚠️  Mix of BUY and SELL
- ⚠️  Large position sizes

### 4. Check Risk Limits First

Before batch execution:
- Verify you have available positions (X/5)
- Check daily P&L isn't near limit
- Ensure sufficient buying power

## Keyboard Shortcuts

Quick reference:

| Key | Action |
|-----|--------|
| `1-9` | Execute specific signal |
| `a` | Approve all (batch) |
| `r` | Review mode |
| `0` | Skip all |
| `Ctrl+C` | Cancel/Exit |

## Configuration

### Delay Between Trades

In batch mode, there's a 1-second delay between trades:

```python
# In src/main.py, _execute_all_signals method
time.sleep(1)  # Delay between trades

# Adjust if needed:
time.sleep(2)  # 2 second delay
time.sleep(0.5)  # Half second delay
```

### Auto-Approve All (Advanced)

For fully automated batch execution, modify `.env`:

```env
ENABLE_AUTO_TRADING=true  # WARNING: No approval required!
```

⚠️ **Not recommended** - removes safety checks!

## Examples

### Example 1: Quick Batch Execution

```
Found 3 signals
→ Press 'a'
→ Confirm with 'yes'
→ All 3 trades executed in ~5 seconds
```

### Example 2: Selective Execution

```
Found 4 signals
→ Press '1' for AAPL
→ Wait for completion
→ Press '3' for GOOGL
→ Press '0' to skip rest
```

### Example 3: Review and Execute

```
Found 5 signals
→ Press 'r' for review
→ See full AAPL details → 'yes'
→ See full MSFT details → 'yes'
→ See full TSLA details → 'no'
→ See full NVDA details → 'yes'
→ See full AMD details → 'skip remaining'
```

## Troubleshooting

**Batch execution partially failed**
- Check logs for specific errors
- Verify each symbol individually
- Common causes: insufficient funds, market closed, position limits

**Can't see all signals in menu**
- Increase terminal height
- Or use review mode [r] to see one at a time

**Batch approval seems slow**
- 1-second delay is intentional (broker rate limits)
- Don't reduce below 0.5 seconds

**Want to cancel mid-batch**
- Press `Ctrl+C` to stop
- Already executed trades remain
- Can manually close positions if needed

## Safety Reminders

🛡️ **Safety Features Active**
- Individual risk checks for each trade
- Position limits enforced
- Daily loss limits checked
- Buying power verified

⚠️ **Your Responsibility**
- Review batch summary before confirming
- Understand total exposure
- Monitor execution results
- Close positions if needed

✅ **Best Practice**
- Start with review mode [r]
- Use batch [a] only when confident
- Check portfolio after batch execution

---

**Pro Tip**: Use batch execution during high-opportunity periods (market open, earnings season) and review mode [r] during normal hours for learning!
