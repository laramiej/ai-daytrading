#!/usr/bin/env python3
"""
Test script to demonstrate sentiment analysis
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from strategy.sentiment_analyzer import SentimentAnalyzer

def main():
    print("=" * 70)
    print("SENTIMENT ANALYSIS TEST")
    print("=" * 70)

    analyzer = SentimentAnalyzer()

    # Test market sentiment
    print("\n📊 Fetching overall market sentiment...")
    market_sentiment = analyzer.get_market_sentiment()

    if market_sentiment:
        print(f"\nOverall Market: {market_sentiment['summary']}")
        print(f"Sentiment Score: {market_sentiment['overall_score']:.2f} (-1 to +1)")
        print("\nIndicators:")

        for name, data in market_sentiment.get("indicators", {}).items():
            print(f"  • {name.upper()}: {data.get('label', 'N/A')}")
            if "interpretation" in data:
                print(f"    {data['interpretation']}")

    # Test stock-specific sentiment
    test_symbols = ["AAPL", "TSLA", "MSFT"]

    for symbol in test_symbols:
        print(f"\n" + "=" * 70)
        print(f"📈 {symbol} SENTIMENT ANALYSIS")
        print("=" * 70)

        stock_sentiment = analyzer.get_stock_sentiment(symbol)

        if stock_sentiment:
            print(f"\nOverall Sentiment: {stock_sentiment['summary']}")
            print(f"Sentiment Score: {stock_sentiment['overall_score']:.2f} (-1 to +1)")
            print("\nSources:")

            for source_name, data in stock_sentiment.get("sources", {}).items():
                if data:
                    print(f"\n  {source_name.upper()}:")
                    print(f"    Status: {data.get('label', 'N/A')}")
                    print(f"    Score: {data.get('score', 0):.2f}")
                    if "interpretation" in data:
                        print(f"    {data['interpretation']}")

                    # Show additional details
                    if source_name == "news" and "sample_headlines" in data:
                        print("    Recent headlines:")
                        for headline in data["sample_headlines"]:
                            print(f"      - {headline}")

    print("\n" + "=" * 70)
    print("✅ Sentiment analysis complete!")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Test cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
