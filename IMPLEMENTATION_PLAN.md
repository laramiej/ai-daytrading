# Implementation Plan: Advanced Technical Indicators

## Overview

This document provides step-by-step instructions to implement the top 5 missing technical indicators identified in PREDICTOR_ANALYSIS.md.

---

## Phase 1: Critical Indicators Implementation

### Target Completion: 1 Week
### Estimated Effort: 7 hours
### Expected Impact: +15-20% accuracy improvement

---

## Task 1: VWAP (Volume-Weighted Average Price)

### Priority: ⭐⭐⭐⭐⭐ CRITICAL
### Time Estimate: 2 hours
### Difficulty: Easy

### What It Does
VWAP shows the average price weighted by volume, indicating where institutions are buying/selling.

**Trading Signals**:
- Price > VWAP = Bullish (buyers in control)
- Price < VWAP = Bearish (sellers in control)
- VWAP acts as support/resistance

### Implementation

**File**: `src/strategy/market_analyzer.py`

**Location**: Add to `_calculate_technicals()` method after line 165

```python
# VWAP (Volume-Weighted Average Price)
if len(df) >= 1:
    vwap = (df["close"] * df["volume"]).sum() / df["volume"].sum()
    indicators["VWAP"] = round(vwap, 2)

    # Add VWAP position relative to current price
    current_price = df["close"].iloc[-1]
    indicators["VWAP_position"] = round(((current_price - vwap) / vwap) * 100, 2)
```

### Validation
- VWAP should be between daily high and low
- VWAP_position shows % above/below VWAP
- Positive = price above VWAP (bullish)

---

## Task 2: ATR (Average True Range)

### Priority: ⭐⭐⭐⭐⭐ CRITICAL
### Time Estimate: 2 hours
### Difficulty: Easy

### What It Does
ATR measures volatility - how much a stock moves. Critical for position sizing and stop-loss placement.

**Trading Usage**:
- High ATR = High volatility = Smaller position size
- Low ATR = Low volatility = Larger position size
- Stop loss = Entry ± (2 × ATR)

### Implementation

**File**: `src/strategy/market_analyzer.py`

**Step 1**: Add helper method after `_calculate_bollinger_bands()` (line 221)

```python
def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
    """
    Calculate Average True Range

    Args:
        df: DataFrame with OHLC data
        period: Lookback period (default 14)

    Returns:
        ATR value
    """
    # True Range = max(high-low, abs(high-prev_close), abs(low-prev_close))
    high_low = df["high"] - df["low"]
    high_close = abs(df["high"] - df["close"].shift(1))
    low_close = abs(df["low"] - df["close"].shift(1))

    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()

    return atr.iloc[-1] if not pd.isna(atr.iloc[-1]) else 0.0
```

**Step 2**: Add to `_calculate_technicals()` method after VWAP

```python
# ATR (Average True Range) - Volatility measure
if len(df) >= 14:
    atr = self._calculate_atr(df, 14)
    indicators["ATR_14"] = round(atr, 2)

    # ATR as % of price (normalized volatility)
    current_price = df["close"].iloc[-1]
    if current_price > 0:
        indicators["ATR_percent"] = round((atr / current_price) * 100, 2)
```

### Integration with Risk Manager

**File**: `src/risk/risk_manager.py`

After implementation, ATR can be used for dynamic position sizing:

```python
# Future enhancement: ATR-based position sizing
# position_size = risk_amount / (2 * ATR)
# This ensures consistent risk across different volatility levels
```

### Validation
- ATR should be positive
- High ATR stocks (>5% of price) = very volatile
- Low ATR stocks (<1% of price) = stable

---

## Task 3: Stochastic Oscillator

### Priority: ⭐⭐⭐⭐ HIGH
### Time Estimate: 1 hour
### Difficulty: Easy

### What It Does
Shows where price is relative to recent high/low range. Identifies overbought/oversold conditions.

**Trading Signals**:
- %K > 80 = Overbought (potential sell)
- %K < 20 = Oversold (potential buy)
- %K crosses %D = Momentum shift

### Implementation

**File**: `src/strategy/market_analyzer.py`

**Step 1**: Add helper method after `_calculate_atr()`

```python
def _calculate_stochastic(self, df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Dict[str, float]:
    """
    Calculate Stochastic Oscillator

    Args:
        df: DataFrame with OHLC data
        k_period: %K period (default 14)
        d_period: %D smoothing period (default 3)

    Returns:
        Dictionary with %K and %D values
    """
    # %K = 100 * (Close - Lowest Low) / (Highest High - Lowest Low)
    low_min = df["low"].rolling(window=k_period).min()
    high_max = df["high"].rolling(window=k_period).max()

    k = 100 * ((df["close"] - low_min) / (high_max - low_min))
    d = k.rolling(window=d_period).mean()

    return {
        "k": k.iloc[-1] if not pd.isna(k.iloc[-1]) else 50.0,
        "d": d.iloc[-1] if not pd.isna(d.iloc[-1]) else 50.0
    }
```

**Step 2**: Add to `_calculate_technicals()` method

```python
# Stochastic Oscillator
if len(df) >= 14:
    stoch = self._calculate_stochastic(df, 14, 3)
    indicators["STOCH_K"] = round(stoch["k"], 2)
    indicators["STOCH_D"] = round(stoch["d"], 2)

    # Overbought/Oversold status
    if stoch["k"] > 80:
        indicators["STOCH_signal"] = "Overbought"
    elif stoch["k"] < 20:
        indicators["STOCH_signal"] = "Oversold"
    else:
        indicators["STOCH_signal"] = "Neutral"
```

### Validation
- Both %K and %D should be 0-100
- %K is faster, %D is smoother
- Crossovers signal momentum changes

---

## Task 4: OBV (On-Balance Volume)

### Priority: ⭐⭐⭐⭐ HIGH
### Time Estimate: 1 hour
### Difficulty: Easy

### What It Does
Tracks cumulative volume flow. If price rises, volume is added; if price falls, volume is subtracted.

**Trading Signals**:
- OBV rising + Price rising = Strong uptrend
- OBV falling + Price rising = Weak uptrend (divergence)
- OBV confirms or contradicts price movement

### Implementation

**File**: `src/strategy/market_analyzer.py`

**Step 1**: Add helper method after `_calculate_stochastic()`

```python
def _calculate_obv(self, df: pd.DataFrame) -> float:
    """
    Calculate On-Balance Volume

    Args:
        df: DataFrame with close prices and volume

    Returns:
        Current OBV value
    """
    # OBV increases by volume when price rises, decreases when price falls
    price_change = df["close"].diff()
    direction = np.sign(price_change)  # +1, 0, or -1

    obv = (direction * df["volume"]).fillna(0).cumsum()

    return obv.iloc[-1]
```

**Step 2**: Add to `_calculate_technicals()` method

```python
# OBV (On-Balance Volume) - Volume flow indicator
if len(df) >= 10:
    obv = self._calculate_obv(df)
    indicators["OBV"] = int(obv)

    # OBV trend (10-period change)
    if len(df) >= 20:
        price_change_10 = df["close"].diff().tail(10)
        direction_10 = np.sign(price_change_10)
        obv_10_ago = (direction_10 * df["volume"].tail(10)).fillna(0).cumsum().iloc[0]
        obv_change = obv - obv_10_ago
        indicators["OBV_trend"] = "Rising" if obv_change > 0 else "Falling"
```

### Validation
- OBV is cumulative (can be positive or negative)
- Focus on trend, not absolute value
- Rising OBV = accumulation, Falling OBV = distribution

---

## Task 5: Pivot Points

### Priority: ⭐⭐⭐ MEDIUM
### Time Estimate: 1 hour
### Difficulty: Easy

### What It Does
Calculates support and resistance levels based on previous period's high/low/close. Used by traders for price targets.

**Trading Usage**:
- Pivot = Fair value
- R1, R2 = Resistance levels (price targets)
- S1, S2 = Support levels (stop loss)

### Implementation

**File**: `src/strategy/market_analyzer.py`

**Step 1**: Add helper method after `_calculate_obv()`

```python
def _calculate_pivot_points(self, df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate Pivot Points (Standard Method)

    Uses previous period's high, low, close to calculate support/resistance

    Args:
        df: DataFrame with OHLC data

    Returns:
        Dictionary with pivot levels
    """
    # Use previous bar's data
    high = df["high"].iloc[-2] if len(df) >= 2 else df["high"].iloc[-1]
    low = df["low"].iloc[-2] if len(df) >= 2 else df["low"].iloc[-1]
    close = df["close"].iloc[-2] if len(df) >= 2 else df["close"].iloc[-1]

    # Pivot Point
    pivot = (high + low + close) / 3

    # Support and Resistance levels
    r1 = (2 * pivot) - low
    s1 = (2 * pivot) - high
    r2 = pivot + (high - low)
    s2 = pivot - (high - low)
    r3 = high + 2 * (pivot - low)
    s3 = low - 2 * (high - pivot)

    return {
        "pivot": pivot,
        "resistance_1": r1,
        "resistance_2": r2,
        "resistance_3": r3,
        "support_1": s1,
        "support_2": s2,
        "support_3": s3
    }
```

**Step 2**: Add to `_calculate_technicals()` method

```python
# Pivot Points (Support/Resistance levels)
if len(df) >= 2:
    pivots = self._calculate_pivot_points(df)
    current_price = df["close"].iloc[-1]

    indicators["PIVOT"] = round(pivots["pivot"], 2)
    indicators["PIVOT_R1"] = round(pivots["resistance_1"], 2)
    indicators["PIVOT_S1"] = round(pivots["support_1"], 2)
    indicators["PIVOT_R2"] = round(pivots["resistance_2"], 2)
    indicators["PIVOT_S2"] = round(pivots["support_2"], 2)

    # Identify current position
    if current_price > pivots["resistance_1"]:
        indicators["PIVOT_position"] = "Above R1 (Strong)"
    elif current_price > pivots["pivot"]:
        indicators["PIVOT_position"] = "Above Pivot"
    elif current_price > pivots["support_1"]:
        indicators["PIVOT_position"] = "Below Pivot"
    else:
        indicators["PIVOT_position"] = "Below S1 (Weak)"
```

### Validation
- Pivot should be between high and low
- R1 > Pivot > S1
- R2 > R1 > Pivot > S1 > S2

---

## Complete Implementation Checklist

### Pre-Implementation

- [ ] Read PREDICTOR_ANALYSIS.md
- [ ] Review current `market_analyzer.py` code
- [ ] Create backup: `cp src/strategy/market_analyzer.py src/strategy/market_analyzer.py.backup`
- [ ] Ensure system is in paper trading mode (`ALPACA_PAPER_TRADING=true`)

### Implementation Steps

- [ ] **Task 1**: Implement VWAP (2 hours)
- [ ] **Task 2**: Implement ATR (2 hours)
- [ ] **Task 3**: Implement Stochastic Oscillator (1 hour)
- [ ] **Task 4**: Implement OBV (1 hour)
- [ ] **Task 5**: Implement Pivot Points (1 hour)

### Testing Steps

- [ ] Run system: `python src/main.py`
- [ ] Verify all 5 new indicators appear in logs
- [ ] Check indicator values are reasonable
- [ ] Review AI analysis to confirm it sees new data
- [ ] Run for 1 day in paper trading
- [ ] Monitor for any errors

### Documentation Steps

- [ ] Update README.md with new indicators
- [ ] Add new indicators to WHAT_AI_SEES.md
- [ ] Document expected ranges for each indicator
- [ ] Commit changes to git

---

## Code Integration Example

After implementing all 5 indicators, your `_calculate_technicals()` method will look like:

```python
def _calculate_technicals(self, df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate technical indicators"""
    indicators = {}

    try:
        # Existing indicators (7)
        if len(df) >= 20:
            indicators["SMA_20"] = round(df["close"].rolling(window=20).mean().iloc[-1], 2)
        # ... [existing RSI, MACD, Bollinger Bands, etc.]

        # NEW: VWAP
        if len(df) >= 1:
            vwap = (df["close"] * df["volume"]).sum() / df["volume"].sum()
            indicators["VWAP"] = round(vwap, 2)
            current_price = df["close"].iloc[-1]
            indicators["VWAP_position"] = round(((current_price - vwap) / vwap) * 100, 2)

        # NEW: ATR
        if len(df) >= 14:
            atr = self._calculate_atr(df, 14)
            indicators["ATR_14"] = round(atr, 2)
            current_price = df["close"].iloc[-1]
            if current_price > 0:
                indicators["ATR_percent"] = round((atr / current_price) * 100, 2)

        # NEW: Stochastic
        if len(df) >= 14:
            stoch = self._calculate_stochastic(df, 14, 3)
            indicators["STOCH_K"] = round(stoch["k"], 2)
            indicators["STOCH_D"] = round(stoch["d"], 2)
            if stoch["k"] > 80:
                indicators["STOCH_signal"] = "Overbought"
            elif stoch["k"] < 20:
                indicators["STOCH_signal"] = "Oversold"
            else:
                indicators["STOCH_signal"] = "Neutral"

        # NEW: OBV
        if len(df) >= 10:
            obv = self._calculate_obv(df)
            indicators["OBV"] = int(obv)
            if len(df) >= 20:
                # Calculate OBV trend
                price_change_10 = df["close"].diff().tail(10)
                direction_10 = np.sign(price_change_10)
                obv_10_ago = (direction_10 * df["volume"].tail(10)).fillna(0).cumsum().iloc[0]
                obv_change = obv - obv_10_ago
                indicators["OBV_trend"] = "Rising" if obv_change > 0 else "Falling"

        # NEW: Pivot Points
        if len(df) >= 2:
            pivots = self._calculate_pivot_points(df)
            current_price = df["close"].iloc[-1]
            indicators["PIVOT"] = round(pivots["pivot"], 2)
            indicators["PIVOT_R1"] = round(pivots["resistance_1"], 2)
            indicators["PIVOT_S1"] = round(pivots["support_1"], 2)
            indicators["PIVOT_R2"] = round(pivots["resistance_2"], 2)
            indicators["PIVOT_S2"] = round(pivots["support_2"], 2)

            if current_price > pivots["resistance_1"]:
                indicators["PIVOT_position"] = "Above R1 (Strong)"
            elif current_price > pivots["pivot"]:
                indicators["PIVOT_position"] = "Above Pivot"
            elif current_price > pivots["support_1"]:
                indicators["PIVOT_position"] = "Below Pivot"
            else:
                indicators["PIVOT_position"] = "Below S1 (Weak)"

    except Exception as e:
        logger.error(f"Error calculating technical indicators: {e}")

    return indicators
```

---

## Expected Log Output

After implementation, you should see in `logs/trading.log`:

```
📈 TECHNICAL INDICATORS:
  RSI(14): 62.34 (Neutral)
  MACD: 1.23, Signal: 0.98
  MACD Histogram: 0.25
  Bollinger Bands: Upper $178.45, Middle $175.20, Lower $171.95
  SMA(20): $174.80, SMA(50): $172.40
  EMA(12): $175.10, EMA(26): $173.90
  VWAP: $175.00 (Price +0.28% above)            ← NEW
  ATR(14): $2.50 (1.42% volatility)             ← NEW
  Stochastic: K=65.5, D=62.1 (Neutral)          ← NEW
  OBV: 12,345,678 (Rising)                      ← NEW
  Pivot: $174.50, R1=$176.20, S1=$172.80        ← NEW
```

---

## Validation Tests

### Test 1: VWAP Sanity Check
```python
# VWAP should be near the average price
assert daily_low < VWAP < daily_high
```

### Test 2: ATR Range Check
```python
# ATR should be positive and reasonable (0.5% - 10% of price)
assert 0 < ATR_percent < 10
```

### Test 3: Stochastic Range
```python
# Stochastic should be 0-100
assert 0 <= STOCH_K <= 100
assert 0 <= STOCH_D <= 100
```

### Test 4: OBV Trend
```python
# OBV should have a direction
assert OBV_trend in ["Rising", "Falling"]
```

### Test 5: Pivot Ordering
```python
# Pivots should be ordered correctly
assert PIVOT_R2 > PIVOT_R1 > PIVOT > PIVOT_S1 > PIVOT_S2
```

---

## Performance Impact

### Computation Time

**Current System**:
- 7 indicators: ~50ms per analysis

**After Phase 1**:
- 12 indicators: ~75ms per analysis (+50%)
- Still well within acceptable range

### Memory Usage

**Minimal Impact**:
- All calculations use existing OHLCV data
- No additional API calls
- Small increase in indicator dictionary size

---

## Rollback Plan

If issues occur:

1. **Restore Backup**:
   ```bash
   cp src/strategy/market_analyzer.py.backup src/strategy/market_analyzer.py
   ```

2. **Comment Out New Code**:
   - Add `#` before each new indicator section
   - System will still work with original 7 indicators

3. **Debug Individual Indicators**:
   - Implement one at a time
   - Test each before moving to next

---

## Next Steps After Phase 1

Once all 5 indicators are implemented and tested:

1. **Monitor Performance**:
   - Run for 1 week in paper trading
   - Track win rate improvement
   - Compare AI reasoning with/without new indicators

2. **Begin Phase 2** (if Phase 1 successful):
   - Fix broken sentiment analysis
   - Add FinBERT for improved news sentiment
   - Integrate Google Trends

3. **Document Results**:
   - Update PREDICTOR_ANALYSIS.md with actual results
   - Share findings in RESULTS.md

---

## Support

### Common Issues

**Issue**: "AttributeError: 'DataFrame' object has no attribute 'high'"
- **Fix**: Check that `df` has OHLCV columns from Alpaca

**Issue**: "Division by zero in VWAP"
- **Fix**: Add check `if df['volume'].sum() > 0`

**Issue**: "NaN values in indicators"
- **Fix**: Use `.fillna(0)` or return default values

**Issue**: "Stochastic returns >100"
- **Fix**: Add `.clip(0, 100)` to constrain range

### Getting Help

- Review existing indicator calculations in market_analyzer.py
- Check logs for specific error messages
- Test with single stock first before full watchlist

---

## Conclusion

This implementation plan provides:
- ✅ Step-by-step code for 5 critical indicators
- ✅ Expected ~15-20% accuracy improvement
- ✅ 7 hours total implementation time
- ✅ Validation tests for each indicator
- ✅ Rollback plan if issues occur

**Ready to begin?** Start with Task 1 (VWAP) and work sequentially through Task 5.

---

**Document Version**: 1.0
**Created**: 2026-01-15
**Status**: Ready for Implementation
