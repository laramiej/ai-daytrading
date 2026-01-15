#!/usr/bin/env python3
"""
Run the trading bot for a single scan (useful for testing)
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import DayTradingBot

if __name__ == "__main__":
    print("=" * 70)
    print("AI DAY TRADING BOT - SINGLE SCAN MODE")
    print("=" * 70)
    print("\n⚙️  Configuration:")
    print("   • Mode: Single scan only")
    print("   • Minimum Confidence: 70%")
    print("   • Manual Approval: Required for all trades")
    print("=" * 70 + "\n")

    try:
        # Initialize bot
        bot = DayTradingBot()

        # Display status
        bot.display_status()

        # Run single scan
        bot.run_single_scan(min_confidence=70.0)

        print("\n" + "=" * 70)
        print("✅ Scan complete!")
        print("=" * 70)

    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("🛑 Scan cancelled by user")
        print("=" * 70)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
