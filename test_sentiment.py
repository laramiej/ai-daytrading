#!/usr/bin/env python3
"""
Test sentiment analysis to diagnose 0.0 score issue
"""
import sys
sys.path.insert(0, '/Users/jasonlaramie/Documents/MyCode/ai_daytrading')

from src.strategy.sentiment_analyzer import SentimentAnalyzer

# Create sentiment analyzer
analyzer = SentimentAnalyzer(enable_google_trends=True)

# Test market sentiment
print("=" * 60)
print("Testing Market Sentiment")
print("=" * 60)
market_sentiment = analyzer.get_market_sentiment()
print(f"\nMarket Sentiment Data:")
print(f"  Overall Score: {market_sentiment['overall_score']}")
print(f"  Summary: {market_sentiment['summary']}")
print(f"  Indicators available: {list(market_sentiment['indicators'].keys())}")

for key, data in market_sentiment['indicators'].items():
    print(f"\n  {key.upper()}:")
    print(f"    Score: {data.get('score', 'N/A')}")
    print(f"    Label: {data.get('label', 'N/A')}")
    if 'interpretation' in data:
        print(f"    {data['interpretation']}")

# Test stock sentiment for SPY
print("\n" + "=" * 60)
print("Testing SPY Stock Sentiment")
print("=" * 60)
spy_sentiment = analyzer.get_stock_sentiment("SPY")
print(f"\nSPY Sentiment Data:")
print(f"  Overall Score: {spy_sentiment['overall_score']}")
print(f"  Summary: {spy_sentiment['summary']}")
print(f"  Sources available: {list(spy_sentiment['sources'].keys())}")

for key, data in spy_sentiment['sources'].items():
    if data:
        print(f"\n  {key.upper()}:")
        print(f"    Score: {data.get('score', 'N/A')}")
        print(f"    Label: {data.get('label', 'N/A')}")
        if 'interpretation' in data:
            print(f"    {data['interpretation']}")
