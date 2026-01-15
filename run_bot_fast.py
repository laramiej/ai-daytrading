#!/usr/bin/env python3
"""
Run the trading bot with faster scans (every 1 minute)
⚠️  WARNING: More frequent scans = higher API costs
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import DayTradingBot

if __name__ == "__main__":
    print("=" * 70)
    print("AI DAY TRADING BOT - FAST SCAN MODE")
    print("=" * 70)
    print("\n⚙️  Configuration:")
    print("   • Scan Interval: 1 minute (60 seconds)")
    print("   • Minimum Confidence: 75%")
    print("   • Manual Approval: Required for all trades")
    print("\n⚠️  WARNING: Faster scans = higher API costs!")
    print("\n💡 Press Ctrl+C to stop at any time")
    print("=" * 70 + "\n")

    try:
        bot = DayTradingBot()
        bot.display_status()

        # Run with 1-minute intervals
        bot.run_continuous(
            scan_interval=60,       # 1 minute between scans
            min_confidence=75.0     # Higher confidence for fast mode
        )

    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("🛑 Trading bot stopped by user")
        print("=" * 70)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
