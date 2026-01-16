#!/usr/bin/env python3
"""
Test Finnhub sentiment integration
"""
import sys
import os
sys.path.insert(0, '/Users/jasonlaramie/Documents/MyCode/ai_daytrading')

from dotenv import load_dotenv
from src.strategy.sentiment_analyzer import SentimentAnalyzer

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')

print("=" * 70)
print("FINNHUB SENTIMENT TEST")
print("=" * 70)
print()

if not FINNHUB_API_KEY or FINNHUB_API_KEY == 'your_finnhub_api_key_here':
    print("ERROR: No valid Finnhub API key found!")
    print()
    print("Please sign up at https://finnhub.io/register")
    print("and add your API key to .env file:")
    print("  FINNHUB_API_KEY=your_actual_key_here")
    print()
    sys.exit(1)

print(f"✓ API Key loaded: {FINNHUB_API_KEY[:10]}... (first 10 chars)")
print()

# Create sentiment analyzer with Finnhub
analyzer = SentimentAnalyzer(
    enable_google_trends=True,
    finnhub_api_key=FINNHUB_API_KEY,
    enable_finnhub=True
)

# Test market sentiment (SPY/QQQ)
print("=" * 70)
print("Testing Market Sentiment (SPY/QQQ)")
print("=" * 70)
market_sentiment = analyzer.get_market_sentiment()
print(f"\nMarket Sentiment Data:")
print(f"  Overall Score: {market_sentiment['overall_score']:.2f}")
print(f"  Summary: {market_sentiment['summary']}")
print(f"  Indicators available: {list(market_sentiment['indicators'].keys())}")

for key, data in market_sentiment['indicators'].items():
    print(f"\n  {key.upper()}:")
    print(f"    Score: {data.get('score', 'N/A')}")
    print(f"    Label: {data.get('label', 'N/A')}")
    if 'interpretation' in data:
        print(f"    {data['interpretation']}")

# Test stock sentiment for AAPL
print("\n" + "=" * 70)
print("Testing AAPL Stock Sentiment")
print("=" * 70)
aapl_sentiment = analyzer.get_stock_sentiment("AAPL")
print(f"\nAAPL Sentiment Data:")
print(f"  Overall Score: {aapl_sentiment['overall_score']:.2f}")
print(f"  Summary: {aapl_sentiment['summary']}")
print(f"  Sources available: {list(aapl_sentiment['sources'].keys())}")

for key, data in aapl_sentiment['sources'].items():
    if data:
        print(f"\n  {key.upper()}:")
        print(f"    Score: {data.get('score', 'N/A')}")
        print(f"    Label: {data.get('label', 'N/A')}")
        if 'interpretation' in data:
            print(f"    {data['interpretation']}")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
print()

if market_sentiment['overall_score'] != 0.0 or any(aapl_sentiment['sources'].values()):
    print("✓ SUCCESS! Finnhub is working!")
    print()
    print("You should now see:")
    print("  - Market sentiment from SPY/QQQ")
    print("  - Stock news sentiment")
    print("  - Analyst recommendations")
else:
    print("⚠ WARNING: Still seeing 0.0 scores")
    print()
    print("Possible issues:")
    print("  1. API key might be invalid")
    print("  2. Rate limit exceeded (60 calls/min)")
    print("  3. Network connectivity issue")
    print()
    print("Try:")
    print("  - Verify API key at https://finnhub.io/dashboard")
    print("  - Wait 60 seconds and try again")
