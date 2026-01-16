"""
Configuration Management
Loads and validates configuration from environment variables
"""
import os
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Alpaca API Keys (optional at startup, required to run bot)
    alpaca_api_key: Optional[str] = Field(None, env="ALPACA_API_KEY")
    alpaca_secret_key: Optional[str] = Field(None, env="ALPACA_SECRET_KEY")
    alpaca_paper_trading: bool = Field(True, env="ALPACA_PAPER_TRADING")

    # LLM API Keys
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    google_api_key: Optional[str] = Field(None, env="GOOGLE_API_KEY")

    # Trading Configuration
    default_llm_provider: str = Field("anthropic", env="DEFAULT_LLM_PROVIDER")
    max_position_size: float = Field(1000.0, env="MAX_POSITION_SIZE")
    max_daily_loss: float = Field(500.0, env="MAX_DAILY_LOSS")
    max_total_exposure: float = Field(5000.0, env="MAX_TOTAL_EXPOSURE")
    enable_auto_trading: bool = Field(False, env="ENABLE_AUTO_TRADING")

    # Bot Scheduling
    scan_interval_minutes: int = Field(5, env="SCAN_INTERVAL_MINUTES")  # How often to scan for opportunities
    min_confidence_threshold: float = Field(70.0, env="MIN_CONFIDENCE_THRESHOLD")  # Minimum confidence to act on signals

    # Risk Management
    stop_loss_percentage: float = Field(2.0, env="STOP_LOSS_PERCENTAGE")
    take_profit_percentage: float = Field(5.0, env="TAKE_PROFIT_PERCENTAGE")
    max_open_positions: int = Field(5, env="MAX_OPEN_POSITIONS")
    enable_short_selling: bool = Field(True, env="ENABLE_SHORT_SELLING")
    max_position_exposure_percent: float = Field(25.0, env="MAX_POSITION_EXPOSURE_PERCENT")  # Max % of total exposure per position

    # Sentiment Analysis (Phase 2)
    enable_google_trends: bool = Field(True, env="ENABLE_GOOGLE_TRENDS")
    finnhub_api_key: Optional[str] = Field(None, env="FINNHUB_API_KEY")
    enable_finnhub: bool = Field(True, env="ENABLE_FINNHUB")

    # Market Data
    watchlist: str = Field(
        "AAPL,MSFT,GOOGL,AMZN,TSLA,NVDA,META,AMD,NFLX,SPY",
        env="WATCHLIST"
    )

    class Config:
        env_file = ".env"
        case_sensitive = False

    def get_watchlist(self) -> List[str]:
        """Parse watchlist into list of symbols"""
        return [s.strip() for s in self.watchlist.split(",") if s.strip()]

    def get_llm_api_key(self, provider: Optional[str] = None) -> Optional[str]:
        """
        Get API key for specified LLM provider

        Args:
            provider: Provider name (anthropic, openai, google)
                     If None, uses default provider

        Returns:
            API key or None if not configured
        """
        provider = provider or self.default_llm_provider

        key_map = {
            "anthropic": self.anthropic_api_key,
            "openai": self.openai_api_key,
            "google": self.google_api_key
        }

        return key_map.get(provider.lower())

    def validate_llm_config(self, provider: Optional[str] = None) -> tuple[bool, str]:
        """
        Validate LLM provider configuration

        Args:
            provider: Provider name to validate (or default if None)

        Returns:
            Tuple of (is_valid, error_message)
        """
        provider = provider or self.default_llm_provider

        api_key = self.get_llm_api_key(provider)

        if not api_key or api_key.startswith("your_"):
            return False, f"API key for '{provider}' not configured"

        return True, ""

    def validate_alpaca_config(self) -> tuple[bool, str]:
        """
        Validate Alpaca broker configuration

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.alpaca_api_key or self.alpaca_api_key.startswith("your_"):
            return False, "Alpaca API key not configured"
        if not self.alpaca_secret_key or self.alpaca_secret_key.startswith("your_"):
            return False, "Alpaca secret key not configured"
        return True, ""

    def is_fully_configured(self) -> tuple[bool, List[str]]:
        """
        Check if all required configuration is present to run the bot

        Returns:
            Tuple of (is_configured, list_of_missing_items)
        """
        missing = []

        # Check Alpaca
        alpaca_valid, alpaca_msg = self.validate_alpaca_config()
        if not alpaca_valid:
            missing.append(alpaca_msg)

        # Check LLM
        llm_valid, llm_msg = self.validate_llm_config()
        if not llm_valid:
            missing.append(llm_msg)

        return len(missing) == 0, missing


def load_settings(reload_env: bool = False) -> Settings:
    """Load and return settings

    Args:
        reload_env: If True, reload .env file to pick up changes
    """
    try:
        if reload_env:
            # Reload .env file to pick up any changes
            load_dotenv(override=True)
        settings = Settings()
        return settings
    except Exception as e:
        raise Exception(f"Failed to load settings: {str(e)}")
