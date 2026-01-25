# System Architecture

## Overview

The AI Day Trading System is built with a modular, extensible architecture that separates concerns and makes it easy to swap components.

## Core Modules

### 1. LLM Module (`src/llm/`)

**Purpose**: Abstract interface for multiple LLM providers

**Components**:
- `base.py`: Abstract base class defining the LLM interface
- `anthropic_provider.py`: Anthropic Claude implementation
- `openai_provider.py`: OpenAI GPT implementation
- `google_provider.py`: Google Gemini implementation
- `__init__.py`: Factory pattern for creating providers

**Key Features**:
- Standardized response format across providers
- Easy switching between models
- Specialized market analysis prompts
- Token usage tracking
- **Bull/Bear/Judge Debate System**: Three-way AI debate for balanced decisions

**Bull/Bear/Judge System**:
The LLM module implements a sophisticated debate system:
1. **Bull Analyst**: Makes the strongest case for buying
2. **Bear Analyst**: Makes the strongest case for selling
3. **Impartial Judge**: Reviews both cases and makes final decision (defaults to HOLD)

See [BULL_BEAR_JUDGE.md](BULL_BEAR_JUDGE.md) for complete details.

**Adding New Providers**:
```python
class NewProvider(BaseLLMProvider):
    def get_default_model(self) -> str:
        return "model-name"

    def generate_response(self, prompt, ...):
        # Implementation
        pass
```

### 2. Broker Module (`src/broker/`)

**Purpose**: Interface with trading platforms

**Components**:
- `alpaca_broker.py`: Alpaca API integration
- Support for market orders, limit orders, positions, quotes

**Key Features**:
- Paper trading support
- Real-time market data
- Order management
- Account information
- Position tracking

**Data Structures**:
- `Position`: Represents open positions
- `Order`: Represents trading orders

### 3. Strategy Module (`src/strategy/`)

**Purpose**: Market analysis and signal generation

**Components**:
- `market_analyzer.py`: Fetches and analyzes market data
- `trading_strategy.py`: Generates trading signals using LLM

**Market Analyzer Features**:
- Real-time price quotes
- Technical indicators (RSI, MACD, Bollinger Bands, SMA, EMA)
- News headline fetching
- Multi-symbol analysis
- Volume analysis

**Trading Strategy Features**:
- LLM-powered analysis
- Confidence scoring
- Risk factor identification
- Entry/exit price recommendations
- Signal history tracking

### 4. Risk Management Module (`src/risk/`)

**Purpose**: Enforce trading limits and safety controls

**Components**:
- `risk_manager.py`: Comprehensive risk management

**Risk Controls**:
1. Position size limits
2. Daily loss limits
3. Total exposure caps
4. Maximum open positions
5. Buying power verification
6. Position existence checks

**Key Features**:
- Trade evaluation before execution
- Position sizing based on risk
- Daily P&L tracking
- Automatic limit resets

### 5. Utilities Module (`src/utils/`)

**Purpose**: Configuration and workflow management

**Components**:
- `config.py`: Environment-based configuration using Pydantic
- `approval.py`: Manual trade approval workflow

**Configuration Features**:
- Environment variable loading
- Validation
- Type safety
- Easy access to settings

**Approval Workflow**:
- Manual approval by default
- Detailed trade presentation
- Risk assessment display
- User input handling

## Data Flow

```
1. Market Data Collection
   └─> MarketAnalyzer fetches quotes, bars, news

2. Technical Analysis
   └─> MarketAnalyzer calculates intraday indicators

3. AI Debate System
   └─> Bull Analyst: Makes case for buying
   └─> Bear Analyst: Makes case for selling
   └─> Judge: Reviews both, makes final decision

4. Risk Evaluation
   └─> RiskManager validates against limits
   └─> Calculates position sizing

5. Human Approval
   └─> ApprovalWorkflow presents recommendation
   └─> User approves or rejects

6. Execution
   └─> AlpacaBroker places order
   └─> DailyReportManager records trade

7. Reporting
   └─> Portfolio snapshots at market open/close
   └─> Trade history with P&L tracking
   └─> PDF report generation on demand
```

## Key Design Patterns

### 1. Factory Pattern
Used in `LLMFactory` to create provider instances:
```python
provider = LLMFactory.create_provider("anthropic", api_key)
```

### 2. Strategy Pattern
LLM providers implement common interface but with different implementations

### 3. Facade Pattern
`DayTradingBot` class provides simple interface to complex subsystems

### 4. Singleton-like Pattern
Settings loaded once and shared across components

## Configuration Management

### Environment Variables
All configuration via `.env` file:
- API keys (never hardcoded)
- Trading limits
- Risk parameters
- Watchlist

### Type Safety
Pydantic models ensure type correctness and validation

### Defaults
Sensible defaults for all optional parameters

## Logging Architecture

### Log Levels
- `INFO`: Normal operations, trades, signals
- `WARNING`: Risk limit approaches, unusual conditions
- `ERROR`: API failures, execution errors

### Log Destinations
- Console: Real-time monitoring
- File (`logs/trading.log`): Audit trail and debugging

### What Gets Logged
- All trading signals
- Risk decisions
- Trade executions
- API calls
- Errors and exceptions

## Error Handling

### Graceful Degradation
- Failed API calls return None, don't crash
- Missing data triggers warnings, not errors
- Invalid signals are filtered out

### User Feedback
- Clear error messages
- Actionable guidance
- Detailed logging for debugging

## Security Considerations

### API Key Protection
- Never committed to git (.env in .gitignore)
- Loaded from environment only
- Never logged or printed

### Paper Trading Default
- System defaults to paper trading
- Explicit opt-in required for live trading
- Clear warnings when switching modes

### Manual Approval
- No automatic trade execution by default
- User must explicitly approve each trade
- Risk limits enforced before approval

## Extensibility Points

### Adding New Technical Indicators
Edit `market_analyzer.py` `_calculate_technicals()`:
```python
def _calculate_technicals(self, df):
    indicators = {}
    # Add your indicator
    indicators["MY_INDICATOR"] = calculate_my_indicator(df)
    return indicators
```

### Custom Trading Logic
Subclass `TradingStrategy`:
```python
class MyStrategy(TradingStrategy):
    def analyze_symbol(self, symbol, context=None):
        # Custom logic
        pass
```

### Additional Risk Rules
Extend `RiskManager.evaluate_trade()`:
```python
def evaluate_trade(self, symbol, side, quantity, price):
    decision = super().evaluate_trade(...)

    # Add custom rule
    if my_custom_check():
        decision.approved = False
        decision.reason = "Custom rule violated"

    return decision
```

### New Broker Integration
Implement broker interface:
```python
class NewBroker:
    def get_account_info(self): pass
    def get_positions(self): pass
    def place_market_order(self, ...): pass
    # etc.
```

## Testing Strategy

### Unit Tests
Test individual components in isolation:
- LLM provider responses
- Risk calculations
- Technical indicators

### Integration Tests
Test component interactions:
- Strategy + Market Analyzer
- Risk Manager + Broker
- End-to-end signal flow

### Paper Trading
Real-world testing without financial risk:
- Validate logic
- Test API integrations
- Monitor performance

## Performance Considerations

### API Rate Limits
- LLM providers have rate limits
- Broker APIs have rate limits
- Add delays between requests if needed

### Data Caching
- Market data is fetched on-demand
- Consider caching for high-frequency scans

### Concurrent Analysis
- Current: Sequential symbol analysis
- Future: Parallel analysis for speed

### Memory Management
- Signal history limited by design
- Logs rotated to prevent disk fill
- No long-term data storage currently

## Future Enhancements

### Potential Additions
1. **Backtesting Engine**: Test strategies on historical data
2. **Performance Analytics**: Track win rate, Sharpe ratio, etc.
3. **Portfolio Optimization**: Diversification analysis
4. **Real-time Monitoring**: WebSocket price feeds
5. **Machine Learning**: Train on successful patterns
6. **Multi-asset Support**: Options, crypto, forex
7. **Web Dashboard**: Visual interface
8. **Alert System**: Email/SMS notifications
9. **Strategy Comparison**: A/B test different approaches
10. **Advanced Orders**: OCO, bracket orders

### Architectural Improvements
1. **Database Integration**: Persistent storage of trades/signals
2. **Message Queue**: Decouple components with async messaging
3. **Microservices**: Split into separate services
4. **API Server**: RESTful API for remote control
5. **Cloud Deployment**: Run on AWS/GCP/Azure

## Dependencies

### Core Libraries
- `alpaca-py`: Broker integration
- `anthropic`, `openai`, `google-generativeai`: LLM providers
- `yfinance`: Market data
- `pandas`, `numpy`: Data analysis
- `pydantic`: Configuration validation

### Why These Choices?
- **Alpaca**: Free paper trading, good API, US-focused
- **Multiple LLMs**: Flexibility, comparison, redundancy
- **yfinance**: Free market data, easy to use
- **Pydantic**: Type safety, validation, modern Python

## Deployment Scenarios

### Local Development
- Run on local machine
- Manual monitoring
- Interactive approval

### Cloud Server
- Run on EC2/GCP/Azure
- Scheduled scans
- Remote approval via web interface

### Containerized
- Docker for consistent environment
- Kubernetes for scaling
- Isolated and reproducible

## Monitoring & Observability

### Current Logging
- File-based logs
- Console output
- Trade history

### Recommended Additions
- Application performance monitoring (APM)
- Error tracking (Sentry)
- Metrics collection (Prometheus)
- Dashboards (Grafana)

## Compliance & Regulations

### Disclaimers
- Not financial advice
- Educational purposes only
- User responsibility for trading decisions

### Audit Trail
- All trades logged
- Decision reasoning recorded
- Complete history available

### Best Practices
- Always start with paper trading
- Understand risks fully
- Comply with local regulations
- Consult financial professionals

---

This architecture is designed to be:
- **Modular**: Easy to modify individual components
- **Extensible**: Simple to add new features
- **Safe**: Multiple layers of risk management
- **Transparent**: Clear logging and decision trails
- **Maintainable**: Clean code, clear structure
