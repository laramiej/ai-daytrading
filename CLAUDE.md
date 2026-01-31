# CLAUDE.md - AI Day Trading System

This file provides guidance for Claude Code (claude.ai/claude-code) when working with this repository.

## Project Overview

This is an AI-powered day trading system that uses Large Language Models to analyze market data and generate trading signals. The system integrates with Alpaca for trade execution and supports multiple LLM providers.

## Architecture

```
ai_daytrading/
├── src/
│   ├── llm/                    # LLM provider abstraction layer
│   │   ├── base.py             # BaseLLMProvider abstract class, LLMResponse dataclass
│   │   ├── __init__.py         # LLMFactory with PROVIDERS registry
│   │   ├── anthropic_provider.py
│   │   ├── openai_provider.py
│   │   ├── google_provider.py
│   │   └── n8n_provider.py     # Webhook-based n8n workflow provider
│   ├── broker/
│   │   └── alpaca_broker.py    # Alpaca trading integration
│   ├── strategy/
│   │   ├── market_analyzer.py  # Technical indicators, market data fetching
│   │   └── trading_strategy.py # TradingStrategy class, signal generation
│   ├── risk/
│   │   └── risk_manager.py     # Risk checks, position limits
│   ├── utils/
│   │   ├── config.py           # Settings class with Pydantic, env loading
│   │   └── approval.py         # Trade approval workflows
│   └── main.py                 # DayTradingBot main class
├── web/
│   ├── backend/
│   │   └── api.py              # FastAPI REST endpoints
│   └── frontend/               # React + Vite dashboard
├── n8n/
│   └── stock_analysis_workflow.json  # n8n workflow for AI analysis
├── config/                     # Configuration files
├── logs/                       # Log files (trading.log)
└── tests/                      # Test files
```

## Key Patterns

### LLM Provider Factory Pattern

All LLM providers inherit from `BaseLLMProvider` and are registered in `LLMFactory.PROVIDERS`:

```python
# src/llm/__init__.py
class LLMFactory:
    PROVIDERS = {
        "anthropic": AnthropicProvider,
        "openai": OpenAIProvider,
        "google": GoogleProvider,
        "n8n": N8nProvider,
    }

    @staticmethod
    def create_provider(provider_name: str, api_key: str, model: Optional[str] = None):
        # Returns configured provider instance
```

To add a new provider:
1. Create `src/llm/new_provider.py` extending `BaseLLMProvider`
2. Implement `get_default_model()`, `generate_response()`, `analyze_market_data()`
3. Register in `LLMFactory.PROVIDERS` dict in `src/llm/__init__.py`
4. Add config settings in `src/utils/config.py`

### Configuration

Settings are managed via Pydantic in `src/utils/config.py`. Environment variables are loaded from `.env`:

```python
from src.utils.config import Settings
settings = Settings()
```

Key settings:
- `DEFAULT_LLM_PROVIDER`: anthropic, openai, google, or n8n
- `ALPACA_PAPER_TRADING`: Always true for safety during development
- `ENABLE_AUTO_TRADING`: false = manual approval required

### Trading Signal Flow

1. `TradingStrategy.analyze_symbol()` gathers market data
2. LLM provider's `analyze_market_data()` returns `LLMResponse`
3. Response parsed into `TradingSignal` dataclass
4. `RiskManager` validates against limits
5. Trade executed via `AlpacaBroker` (with approval if not auto-trading)

## Common Commands

### Running the Bot
```bash
# Activate virtual environment
source venv/bin/activate

# Run trading bot
python run_bot.py
# or
cd src && python main.py
```

### Running the Web Dashboard
```bash
# Backend (FastAPI)
cd web/backend
uvicorn api:app --reload --port 8000

# Frontend (React + Vite)
cd web/frontend
npm install
npm run dev
```

### Running Tests
```bash
pytest tests/
```

## n8n Integration

The n8n provider delegates AI analysis to an external n8n workflow:

- **Webhook URL**: Configured via `N8N_WEBHOOK_URL` env var
- **Workflow file**: `n8n/stock_analysis_workflow.json`
- **Endpoint**: POST `/webhook/stock-analysis` with `{"symbol": "AAPL"}`
- **Response**: JSON with signal, confidence, reasoning, entry/stop/target prices

To use n8n:
```env
DEFAULT_LLM_PROVIDER=n8n
N8N_WEBHOOK_URL=http://your-n8n-host:5678/webhook/stock-analysis
```

## Important Files

- `.env` - Environment configuration (never commit)
- `.env.example` - Template for environment variables
- `requirements.txt` - Python dependencies
- `logs/trading.log` - Trading activity log

## Safety Notes

- **ALPACA_PAPER_TRADING=true** should always be set during development
- **ENABLE_AUTO_TRADING=false** requires manual approval for all trades
- Risk limits are enforced in `src/risk/risk_manager.py`
- All trades are logged to `logs/trading.log`

## Documentation

Additional documentation files:
- `BULL_BEAR_JUDGE.md` - AI debate system for balanced trade decisions
- `PDF_REPORTS.md` - Daily trading report generation
- `AUTO_TRADING.md` - Auto vs manual trading modes
- `SHORT_SELLING.md` - Short selling configuration
- `WEB_QUICKSTART.md` - Web dashboard setup
- `QUICKSTART.md` - 5-minute getting started guide
- `ARCHITECTURE.md` - Detailed technical architecture
