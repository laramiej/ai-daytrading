# Portfolio-Aware Trading

Your AI day trading system now has **full portfolio awareness**! The AI considers your current positions, past trades, and portfolio constraints when making recommendations.

## What's Included

### ✅ Current Implementation

**1. Position Tracking**
- ✅ Knows what stocks you currently own
- ✅ Tracks quantity, entry price, current P&L
- ✅ Prevents buying duplicate positions (unless configured)
- ✅ Only suggests SELL for stocks you own

**2. Portfolio Limits**
- ✅ Respects maximum position count
- ✅ Enforces position size limits
- ✅ Tracks total portfolio exposure
- ✅ Monitors buying power
- ✅ Enforces daily loss limits

**3. Trade History**
- ✅ Records all trades
- ✅ Tracks win/loss ratio per symbol
- ✅ Calculates cumulative P&L
- ✅ Remembers AI confidence scores
- ✅ Associates trades with LLM provider used

**4. AI Context**
- ✅ AI sees your entire portfolio
- ✅ Knows your current positions
- ✅ Understands portfolio constraints
- ✅ Considers past performance
- ✅ Makes context-aware recommendations

## How It Works

### AI Receives Full Context

When analyzing a stock, the AI now sees:

```
💰 PORTFOLIO STATUS
Total Value: $100,000.00
Cash: $95,000.00
Invested: $5,000.00 (5.0%)

📊 POSITIONS: 2/5
  • AAPL: 10 shares @ $170.50 (+2.64%)
  • MSFT: 5 shares @ $380.00 (-1.18%)

🛡️  RISK STATUS
Daily P&L: $22.50
Exposure: $5,000/$5,000 (100.0%)

📈 PERFORMANCE
Total Trades: 8
Win Rate: 62.5% (5W/3L)
Total P&L: $450.00

Trading Recommendations:
  - Currently holding 10 shares
  - Position is profitable: +2.64%
  - Historical win rate: 60.0% (3/5 trades)
  - Cumulative P&L: $125.00
```

### Smart Recommendations

The AI makes intelligent decisions based on your portfolio:

**Scenario 1: Already Own the Stock**
```
Symbol: AAPL
Position: Own 10 shares @ $170 (up +5%)

AI sees:
- Current position is profitable
- Might suggest SELL to lock in gains
- OR suggest HOLD if bullish continues
- Won't suggest BUY (already exposed)
```

**Scenario 2: Maximum Positions Reached**
```
Positions: 5/5 (MAXED OUT)

AI sees:
- Cannot open new BUY positions
- Can only SELL existing positions
- Recommends which position to exit if needed
```

**Scenario 3: Daily Loss Limit Hit**
```
Daily P&L: -$500 (LIMIT REACHED)

AI sees:
- Trading is restricted
- Can only close losing positions
- Will not suggest new BUY orders
```

**Scenario 4: Stock Performance History**
```
Symbol: TSLA
Past trades: 0W/3L
Historical P&L: -$350

AI sees:
- Poor historical performance
- Might be more cautious
- Could skip or suggest smaller position
```

## What This Prevents

### ❌ Problems Avoided

1. **Double Positions**
   - Won't buy AAPL if you already own it
   - Unless you explicitly want to average up/down

2. **Over-Exposure**
   - Won't exceed max position count
   - Respects total exposure limits

3. **Ignoring Losers**
   - AI knows which stocks lost money before
   - Can factor this into decisions

4. **Blind Trading**
   - AI understands your portfolio state
   - Makes context-aware recommendations

5. **Forgetting Past Performance**
   - Tracks what works and what doesn't
   - Learns from historical results

## Usage Examples

### Example 1: Fresh Start

```
Portfolio: Empty
Cash: $100,000

AI Analysis: "I can open up to 5 positions.
Let me find the best opportunities..."

Result: Suggests top 3 BUY signals
```

### Example 2: Partial Portfolio

```
Portfolio:
- AAPL: +5%
- MSFT: -2%
- GOOGL: +3%

Positions: 3/5

AI Analysis: "You have 3 positions, 2 profitable.
I can open 2 more positions. MSFT is at a loss -
consider exiting or holding for recovery."

Result: May suggest:
- SELL MSFT (cut losses)
- BUY 2 new opportunities
```

### Example 3: Full Portfolio

```
Portfolio: 5/5 positions
All profitable

AI Analysis: "Portfolio is full and performing well.
Cannot open new positions. If a strong opportunity
appears, consider exiting weakest position first."

Result: Might suggest:
- HOLD all (if all strong)
- SELL weakest to rotate into better opportunity
```

## Performance Tracking

The system tracks detailed performance metrics:

### Per-Symbol Stats
- Win rate for each stock
- Average P&L per stock
- Number of trades per stock
- Average confidence when trading

### Overall Performance
```python
{
    "total_trades": 15,
    "win_rate": 66.7%,
    "wins": 10,
    "losses": 5,
    "total_pnl": $1,250.00,
    "avg_win": $200.00,
    "avg_loss": -$90.00,
    "best_trade": {
        "symbol": "NVDA",
        "pnl": $450.00
    },
    "worst_trade": {
        "symbol": "TSLA",
        "pnl": -$250.00
    }
}
```

## Configuration

### Enable/Disable Portfolio Context

You can toggle portfolio awareness:

```python
# In src/strategy/trading_strategy.py

# Analyze WITH portfolio context (default)
signal = strategy.analyze_symbol("AAPL", include_portfolio_context=True)

# Analyze WITHOUT portfolio context
signal = strategy.analyze_symbol("AAPL", include_portfolio_context=False)
```

### Access Portfolio Data Directly

```python
from strategy.portfolio_context import PortfolioContext

# Get portfolio summary
summary = bot.portfolio.get_portfolio_summary()

# Check if we own a stock
has_aapl = bot.portfolio.has_position("AAPL")

# Get position details
aapl_position = bot.portfolio.get_position_details("AAPL")

# Get symbol history
aapl_history = bot.portfolio.get_symbol_history("AAPL")

# Get trade recommendations
recommendations = bot.portfolio.get_trade_recommendations("AAPL")
```

## Advanced Features

### Win Rate Analysis

The system tracks which stocks work best for your strategy:

```python
# Get performance for a specific stock
history = bot.portfolio.get_symbol_history("AAPL")

print(f"AAPL Performance:")
print(f"  Trades: {history['total_trades']}")
print(f"  Win Rate: {history['performance']['wins']/history['total_trades']*100:.1f}%")
print(f"  Total P&L: ${history['performance']['total_pnl']:.2f}")
```

### LLM Provider Performance

Track which AI model performs best:

```python
# Filter trades by LLM provider
claude_trades = [t for t in bot.portfolio.trade_history if t.llm_provider == "anthropic"]
gpt_trades = [t for t in bot.portfolio.trade_history if t.llm_provider == "openai"]

# Compare performance
# (You'd calculate win rates and P&L for each)
```

### Portfolio Rebalancing

The AI can suggest portfolio rebalancing:

```
Current: 5/5 positions
- AAPL: +10%
- MSFT: +8%
- GOOGL: +2%
- TSLA: -5%
- NVDA: +15%

AI might suggest:
"NVDA and AAPL are strong winners. GOOGL is weak and TSLA is losing.
Consider: SELL TSLA (cut losses), SELL GOOGL (weak),
then BUY 2 new strong opportunities."
```

## Best Practices

### 1. Review Performance Regularly

```bash
# Check your stats
python -c "
from main import DayTradingBot
bot = DayTradingBot()
summary = bot.portfolio.get_portfolio_summary()
print(bot.portfolio.format_portfolio_context())
"
```

### 2. Learn from History

- Check which stocks have good win rates
- Avoid stocks with consistent losses
- Note AI confidence on winners vs losers

### 3. Respect the Limits

- Daily loss limit protects capital
- Position limits prevent over-concentration
- Exposure limits control overall risk

### 4. Use AI Insights

The AI now understands:
- Your risk tolerance (via portfolio size)
- Your success rate (via win/loss history)
- Your position status (what you own)
- Your constraints (limits reached?)

## Limitations

### Current Limitations

1. **No Cross-Session Persistence**
   - Trade history resets when bot restarts
   - Future: Add database storage

2. **No Performance Attribution**
   - Doesn't analyze WHY trades won/lost
   - Future: Add trade post-mortems

3. **Simple Position Management**
   - Doesn't handle partial exits
   - Doesn't track avg-up/avg-down strategies

4. **No Tax Awareness**
   - Doesn't consider wash sales
   - Doesn't optimize for tax efficiency

### Future Enhancements

- [ ] Persistent trade history (database)
- [ ] Advanced position sizing (Kelly Criterion)
- [ ] Tax-loss harvesting
- [ ] Correlation analysis (diversification)
- [ ] Drawdown management
- [ ] Performance attribution analysis
- [ ] Multi-timeframe position tracking
- [ ] Options positions support

## Troubleshooting

**AI still suggests buying stocks I own**
- Check `include_portfolio_context=True` in strategy
- Verify portfolio context is initialized in main.py
- Check logs for "Portfolio context" messages

**Performance metrics seem wrong**
- Trade history resets on bot restart
- Ensure trades are being recorded properly
- Check `portfolio.trade_history` list

**Position count incorrect**
- Refresh by calling `broker.get_positions()`
- Check Alpaca dashboard for actual positions
- Sync issues can occur with rapid trading

## Summary

Your trading bot now has full **portfolio intelligence**:

✅ **Sees** your current positions
✅ **Remembers** past trades
✅ **Respects** risk limits
✅ **Learns** from history
✅ **Makes** context-aware decisions

This makes the AI a true portfolio manager, not just a signal generator!

---

**Pro Tip**: The AI's recommendations become more sophisticated as you build trading history. The more you trade, the smarter it gets!
