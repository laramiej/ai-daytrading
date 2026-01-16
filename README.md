# AI Day Trading System

An intelligent day trading system that uses Large Language Models (LLMs) to analyze market data and generate trading signals. The system supports multiple LLM providers (Anthropic Claude, OpenAI GPT, Google Gemini) and integrates with Alpaca for trade execution.

## Features

- **Multi-LLM Support**: Seamlessly switch between Anthropic Claude, OpenAI GPT-4, and Google Gemini
- **Intelligent Analysis**: AI-powered market analysis using 12 technical indicators, price data, and news
- **Short Selling Support**: Profit from declining stocks with configurable short selling (see [SHORT_SELLING.md](SHORT_SELLING.md))
- **Portfolio Awareness**: AI considers your current positions, past trades, and portfolio constraints
- **Sentiment Analysis**: Market and stock-specific sentiment from news, analysts, and momentum
- **Batch Trading**: Approve multiple recommendations at once for efficiency
- **Risk Management**: Comprehensive risk controls including position limits, daily loss limits, and exposure caps
- **Trading Modes**: Choose between manual approval or auto-trading mode (see [AUTO_TRADING.md](AUTO_TRADING.md))
- **Manual Approval**: Conservative default mode with approval required for all trades
- **Auto-Trading**: Advanced mode for hands-free execution (still respects all risk limits)
- **Paper Trading**: Safe testing environment with Alpaca paper trading
- **Real-time Data**: Live market data and technical indicator calculations
- **Extensible Architecture**: Clean, modular design for easy customization

## System Architecture

```
ai_daytrading/
├── src/
│   ├── llm/                 # LLM provider abstraction
│   │   ├── base.py          # Base provider interface
│   │   ├── anthropic_provider.py
│   │   ├── openai_provider.py
│   │   └── google_provider.py
│   ├── broker/              # Trading broker integration
│   │   └── alpaca_broker.py
│   ├── strategy/            # Trading strategy and analysis
│   │   ├── market_analyzer.py
│   │   └── trading_strategy.py
│   ├── risk/                # Risk management
│   │   └── risk_manager.py
│   ├── utils/               # Utilities
│   │   ├── config.py
│   │   └── approval.py
│   └── main.py              # Main application
├── config/                  # Configuration files
├── logs/                    # Log files
├── requirements.txt         # Python dependencies
├── .env.example             # Example environment variables
└── run_bot.py               # Convenience script
```

## Prerequisites

- Python 3.9 or higher
- Alpaca account (free paper trading account available at https://alpaca.markets/)
- At least one LLM API key:
  - Anthropic API key (https://console.anthropic.com/)
  - OpenAI API key (https://platform.openai.com/)
  - Google API key (https://makersuite.google.com/)

## Installation

1. **Clone or download this repository**

2. **Create a virtual environment**
   ```bash
   cd ai_daytrading
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and preferences
   ```

## Configuration

Edit the `.env` file with your settings:

### Required Settings

```env
# Alpaca API Keys (required)
ALPACA_API_KEY=your_alpaca_api_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_key_here
ALPACA_PAPER_TRADING=true  # KEEP TRUE for safety!

# LLM API Keys (at least one required)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Default LLM Provider
DEFAULT_LLM_PROVIDER=anthropic  # Options: anthropic, openai, google
```

### Risk Management Settings

```env
# Position and Risk Limits
MAX_POSITION_SIZE=1000        # Maximum USD per position
MAX_DAILY_LOSS=500           # Maximum daily loss in USD
MAX_TOTAL_EXPOSURE=5000      # Maximum total portfolio exposure
MAX_OPEN_POSITIONS=5         # Maximum concurrent positions

# Stop Loss and Take Profit
STOP_LOSS_PERCENTAGE=2.0     # Default stop loss %
TAKE_PROFIT_PERCENTAGE=5.0   # Default take profit %

# Automation (STRONGLY RECOMMEND KEEPING FALSE)
ENABLE_AUTO_TRADING=false    # Require manual approval for trades
```

### Watchlist

```env
# Stocks to Monitor
WATCHLIST=AAPL,MSFT,GOOGL,AMZN,TSLA,NVDA,META,AMD,NFLX,SPY
```

## Usage

### Basic Usage

Run the bot with default settings:

```bash
python run_bot.py
```

Or directly:

```bash
cd src
python main.py
```

### What the Bot Does

1. **Displays Status**: Shows account balance, positions, and risk metrics
2. **Scans Watchlist**: Analyzes each symbol using the configured LLM
3. **Generates Signals**: Identifies BUY/SELL opportunities with confidence scores
4. **Risk Evaluation**: Checks all trades against risk management rules
5. **Manual Approval**: Presents recommendations and waits for your approval
6. **Executes Trades**: Places orders through Alpaca (paper trading by default)

### Switching LLM Providers

You can switch between LLM providers in your code:

```python
from main import DayTradingBot

bot = DayTradingBot()

# Switch to OpenAI
bot.switch_llm_provider("openai")

# Switch to Google Gemini
bot.switch_llm_provider("google")

# Switch back to Anthropic
bot.switch_llm_provider("anthropic")
```

### Running Continuous Scans

Modify `src/main.py` to enable continuous trading:

```python
def main():
    bot = DayTradingBot()

    # Run continuous scans every 5 minutes
    bot.run_continuous(scan_interval=300, min_confidence=70.0)
```

## Understanding the Output

### Trading Signal

When a trading opportunity is found, you'll see:

```
======================================================================
🤖 AI TRADING RECOMMENDATION
======================================================================

Symbol: AAPL
Action: BUY
Confidence: 85%
LLM Provider: anthropic

Reasoning:
  Strong technical momentum with RSI at 45 indicating room for upside.
  Positive news catalyst from recent product announcement.

Entry Price: $175.50
Stop Loss: $172.00
Take Profit: $182.00

Position Size: MEDIUM
Time Horizon: 2-4 hours

⚠️  Risk Factors:
  - Market volatility elevated
  - Approaching resistance level

💰 Estimated Cost: $875.00

🛡️  Risk Management:
  ✅ Trade approved - all risk checks passed

======================================================================
Approve this trade? (yes/no):
```

### Risk Management Blocks

If a trade violates risk rules:

```
🛡️  Risk Management:
  ❌ Daily loss limit reached ($500.00 / $500.00)

❌ Trade blocked by risk management
```

## Safety Features

### Conservative Defaults

- **Manual Approval Required**: Every trade needs your explicit approval
- **Paper Trading Default**: No real money at risk until you explicitly change it
- **Multiple Risk Checks**: Position limits, daily loss limits, exposure caps
- **Stop Loss Enforcement**: Automatic calculation of safe position sizes

### Risk Management Rules

The system enforces:

1. **Maximum Position Size**: Limits USD exposure per trade
2. **Daily Loss Limit**: Stops trading if daily losses exceed threshold
3. **Total Exposure Cap**: Limits total portfolio exposure
4. **Position Count Limit**: Maximum number of open positions
5. **Buying Power Check**: Verifies sufficient capital before trades
6. **Position Verification**: Confirms positions exist before selling

### Logging

All activity is logged to `logs/trading.log` for audit trail and debugging.

## Customization

### Adding a New LLM Provider

1. Create a new provider class in `src/llm/`:

```python
from .base import BaseLLMProvider, LLMResponse

class MyLLMProvider(BaseLLMProvider):
    def get_default_model(self) -> str:
        return "my-model-name"

    def generate_response(self, prompt, system_prompt=None, temperature=0.7, max_tokens=2000):
        # Implement your LLM API call
        pass
```

2. Register it in `src/llm/__init__.py`:

```python
from .my_llm_provider import MyLLMProvider

class LLMFactory:
    PROVIDERS = {
        "anthropic": AnthropicProvider,
        "openai": OpenAIProvider,
        "google": GoogleProvider,
        "mylm": MyLLMProvider,  # Add here
    }
```

### Modifying Trading Strategy

Edit `src/strategy/trading_strategy.py` to customize:

- Signal confidence thresholds
- Technical indicator weights
- Analysis prompts
- Signal filtering logic

### Adjusting Technical Indicators

The system includes 12 technical indicators (see [PREDICTOR_ANALYSIS.md](PREDICTOR_ANALYSIS.md)):

**Moving Averages**: SMA (20, 50), EMA (12, 26)
**Momentum**: RSI, Stochastic Oscillator
**Trend**: MACD
**Volatility**: Bollinger Bands, ATR
**Volume**: Volume Ratio, VWAP, OBV
**Support/Resistance**: Pivot Points

Modify `src/strategy/market_analyzer.py` to:

- Add new technical indicators
- Adjust calculation periods
- Change data sources
- Customize news fetching

## Important Warnings

### Financial Risk

- **This is experimental software**: Do not use with real money without extensive testing
- **Not financial advice**: The AI makes suggestions, but YOU are responsible for all trading decisions
- **Past performance ≠ future results**: Historical data does not guarantee future success
- **Significant losses possible**: Day trading is risky and most day traders lose money

### Technical Limitations

- **LLM accuracy varies**: AI models can make mistakes or hallucinate information
- **Market data delays**: Real-time data may have slight delays
- **API rate limits**: LLM and broker APIs have usage limits
- **No guarantee of execution**: Orders may not fill at expected prices

### Best Practices

1. **Start with paper trading**: Test thoroughly before considering real money
2. **Start small**: Use minimum position sizes when beginning
3. **Monitor closely**: Don't leave the bot running unattended initially
4. **Review logs**: Check `logs/trading.log` regularly
5. **Understand the code**: Review the source before using
6. **Keep API keys secure**: Never commit `.env` to version control
7. **Test risk limits**: Verify risk management works as expected

## Troubleshooting

### Common Issues

**Error: "API key for 'anthropic' not configured"**
- Solution: Add your API key to the `.env` file

**Error: "Market is closed - skipping scan"**
- Solution: Run during market hours (9:30 AM - 4:00 PM ET, Monday-Friday)

**Error: "Unable to verify open positions"**
- Solution: Check your Alpaca API keys and network connection

**No signals generated**
- Solution: Lower `min_confidence` threshold or adjust watchlist

### Getting Help

1. Check the logs in `logs/trading.log` for detailed error messages
2. Verify all API keys are correct in `.env`
3. Ensure market is open for live trading
4. Test with paper trading first

## Additional Documentation

- **[AUTO_TRADING.md](AUTO_TRADING.md)** - Auto-trading vs manual approval modes
- **[SHORT_SELLING.md](SHORT_SELLING.md)** - Complete guide to short selling stocks
- **[PORTFOLIO_AWARENESS.md](PORTFOLIO_AWARENESS.md)** - Portfolio tracking and trade history
- **[SENTIMENT_ANALYSIS.md](SENTIMENT_ANALYSIS.md)** - Market and stock sentiment features
- **[BATCH_TRADING.md](BATCH_TRADING.md)** - Batch approval workflow guide
- **[LOGGING_GUIDE.md](LOGGING_GUIDE.md)** - Understanding AI analysis logs
- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute quick start guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical architecture details

## Development

### Running Tests

```bash
pytest tests/
```

### Code Structure

- `llm/`: LLM provider abstraction and implementations
- `broker/`: Trading broker integration (currently Alpaca)
- `strategy/`: Market analysis and trading signal generation
- `risk/`: Risk management and position sizing
- `utils/`: Configuration, approval workflows, helpers

## License

This software is provided as-is for educational purposes. Use at your own risk.

## Disclaimer

This software is for educational and research purposes only. It is not intended to provide financial, investment, or trading advice. Trading stocks and securities involves substantial risk of loss. The creators and contributors of this software are not responsible for any financial losses incurred through its use.

Always conduct your own research and consult with licensed financial advisors before making investment decisions.

## Credits

Built with:
- Anthropic Claude API
- OpenAI GPT API
- Google Gemini API
- Alpaca Trading API
- yfinance for market data

---

**Remember: Never trade with money you can't afford to lose. Always start with paper trading.**
