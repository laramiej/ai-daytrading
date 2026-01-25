# PDF Report Generation

## Overview

The AI Day Trading System can generate professional PDF reports for any trading day. These reports provide a comprehensive summary of trading activity, portfolio performance, and individual trade details.

## Features

- **Daily Summary**: Portfolio value, P&L, win/loss statistics
- **Portfolio Snapshots**: Market open and close portfolio states
- **Trade Details**: Every trade with reasoning and P&L
- **Blocked Trades**: Trades that were blocked by risk management
- **Professional Formatting**: Clean, printable layout

## Generating Reports

### Via Web Interface

1. Navigate to the **Reports** tab in the web dashboard
2. Select a date from the available reports
3. Click the **Download PDF** button

### Via API

```bash
# Download PDF for a specific date
curl -o report.pdf "http://localhost:8000/api/reports/2026-01-25/pdf"
```

### Via Python

```python
from src.reports.daily_report import DailyReportManager

manager = DailyReportManager()
pdf_bytes = manager.generate_pdf("2026-01-25")

if pdf_bytes:
    with open("report.pdf", "wb") as f:
        f.write(pdf_bytes)
```

## Report Contents

### 1. Header Section
- Report date
- Generation timestamp

### 2. Daily Summary
| Metric | Description |
|--------|-------------|
| Total P&L | Combined realized + unrealized profit/loss |
| Realized P&L | Profit/loss from closed trades |
| Unrealized P&L | Profit/loss from open positions |
| Signals Analyzed | Number of stocks analyzed |
| Signals Actioned | Number of trades executed |
| Win Rate | Percentage of profitable trades |

### 3. Portfolio Snapshots

**Market Open Snapshot**:
- Portfolio value at market open
- Cash balance
- Open positions with entry prices
- Starting exposure

**Market Close Snapshot**:
- Portfolio value at market close
- Daily change in value
- Final positions with P&L
- Ending exposure

### 4. Executed Trades

For each trade:
| Field | Description |
|-------|-------------|
| Time | Execution timestamp |
| Symbol | Stock ticker |
| Side | BUY or SELL |
| Quantity | Number of shares |
| Price | Execution price |
| Total Value | Quantity × Price |
| Confidence | AI signal confidence |
| Realized P&L | Profit/loss (for closing trades) |
| Reasoning | AI's reasoning for the trade |

### 5. Blocked Trades

Trades that were blocked by risk management:
| Field | Description |
|-------|-------------|
| Time | When the trade was attempted |
| Symbol | Stock ticker |
| Side | Intended direction |
| Reason | Why it was blocked |

## Example Report

```
═══════════════════════════════════════════════════════
           AI DAY TRADING DAILY REPORT
                   2026-01-25
═══════════════════════════════════════════════════════

DAILY SUMMARY
─────────────────────────────────────────────────────
Total P&L:           +$342.50  (+1.71%)
Realized P&L:        +$215.00
Unrealized P&L:      +$127.50
Signals Analyzed:    25
Signals Actioned:    4
Win Rate:            75% (3 wins / 1 loss)

MARKET OPEN SNAPSHOT (09:30:05 ET)
─────────────────────────────────────────────────────
Portfolio Value:     $20,000.00
Cash:                $18,500.00
Positions:           1
Exposure:            $1,500.00

Position: AAPL
  Qty: 10 shares (LONG)
  Entry: $150.00
  Value: $1,500.00

MARKET CLOSE SNAPSHOT (16:00:02 ET)
─────────────────────────────────────────────────────
Portfolio Value:     $20,342.50  (+$342.50)
Cash:                $17,215.00
Positions:           2
Exposure:            $3,127.50

Position: AAPL
  Qty: 10 shares (LONG)
  Entry: $150.00
  Current: $152.75
  P&L: +$27.50 (+1.83%)

Position: NVDA
  Qty: 5 shares (LONG)
  Entry: $420.00
  Current: $440.00
  P&L: +$100.00 (+4.76%)

EXECUTED TRADES
─────────────────────────────────────────────────────
10:15:32  BUY 5 NVDA @ $420.00 ($2,100.00)
          Confidence: 78%
          Reasoning: RSI at 42 with MACD crossover...

11:45:18  SELL 10 MSFT @ $385.50 ($3,855.00)
          Confidence: 72%
          Realized P&L: +$155.00
          Reasoning: Overbought RSI at 75, approaching R2...

14:22:05  BUY 8 AMD @ $145.00 ($1,160.00)
          Confidence: 81%
          Reasoning: Breakout above VWAP with volume...

15:30:42  SELL 8 AMD @ $147.50 ($1,180.00)
          Confidence: 68%
          Realized P&L: +$60.00
          Reasoning: Taking profit at R1 resistance...

BLOCKED TRADES
─────────────────────────────────────────────────────
13:45:00  BUY TSLA - Blocked
          Reason: Maximum open positions reached (5/5)

═══════════════════════════════════════════════════════
Generated: 2026-01-25 16:05:00
AI Day Trading System v2.0
═══════════════════════════════════════════════════════
```

## Dependencies

PDF generation requires the `reportlab` library:

```bash
pip install reportlab>=4.0.0
```

This is already included in `requirements.txt`.

## File Storage

Reports are stored as JSON in `data/reports/`:
```
data/reports/
├── 2026-01-20.json
├── 2026-01-21.json
├── 2026-01-22.json
├── 2026-01-23.json
└── 2026-01-25.json
```

PDFs are generated on-demand from these JSON files and not stored permanently.

## API Endpoints

### List Available Reports
```
GET /api/reports
```
Returns list of dates with available reports.

### Get Report Data (JSON)
```
GET /api/reports/{date}
```
Returns the full report data as JSON.

### Download Report (PDF)
```
GET /api/reports/{date}/pdf
```
Returns the report as a downloadable PDF file.

## Customization

The PDF layout is defined in `src/reports/daily_report.py` in the `generate_pdf()` method. You can customize:

- Page size (default: US Letter 8.5" × 11")
- Margins (default: 0.5" all sides)
- Colors and fonts
- Table layouts
- Section ordering

## Troubleshooting

### "reportlab not found"
```bash
pip install reportlab>=4.0.0
```

### "Report not found for date"
- Ensure the trading bot ran on that date
- Check that `data/reports/{date}.json` exists
- Verify the date format is `YYYY-MM-DD`

### PDF is empty or incomplete
- Check `logs/trading.log` for errors
- Verify the JSON report file is valid
- Ensure sufficient disk space

---

**Updated**: 2026-01-25
**Version**: 1.0
