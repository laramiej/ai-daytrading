#!/usr/bin/env python3
"""
Run the trading bot in continuous mode with custom settings
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import DayTradingBot

if __name__ == "__main__":
    print("=" * 70)
    print("AI DAY TRADING BOT - CONTINUOUS MODE")
    print("=" * 70)
    print("\n⚙️  Configuration:")
    print("   • Scan Interval: 5 minutes (300 seconds)")
    print("   • Minimum Confidence: 70%")
    print("   • Manual Approval: Required for all trades")
    print("\n💡 Press Ctrl+C to stop at any time")
    print("=" * 70 + "\n")

    try:
        # Initialize bot
        bot = DayTradingBot()

        # Display initial status
        bot.display_status()

        # Run continuous mode
        # Scans watchlist every 5 minutes and presents opportunities
        bot.run_continuous(
            scan_interval=300,      # 5 minutes between scans
            min_confidence=70.0     # Only show signals with 70%+ confidence
        )

    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("🛑 Trading bot stopped by user")
        print("=" * 70)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
