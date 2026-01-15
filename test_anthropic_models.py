#!/usr/bin/env python3
"""
Quick script to test which Anthropic models work with your API key
"""
import anthropic
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    print("❌ ANTHROPIC_API_KEY not found in .env file")
    exit(1)

print(f"✓ API key found: {api_key[:20]}...")

# List of models to test
models_to_test = [
    "claude-3-5-sonnet-20241022",  # Latest Sonnet 3.5 v2
    "claude-3-5-sonnet-20240620",  # Sonnet 3.5 v1
    "claude-3-opus-20240229",      # Opus
    "claude-3-sonnet-20240229",    # Sonnet 3
    "claude-3-haiku-20240307",     # Haiku
]

client = anthropic.Anthropic(api_key=api_key)

print("\nTesting models...\n")

working_models = []

for model in models_to_test:
    try:
        print(f"Testing {model}...", end=" ")

        response = client.messages.create(
            model=model,
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )

        print("✅ WORKS")
        working_models.append(model)

    except Exception as e:
        if "not_found_error" in str(e):
            print("❌ Not available for your API key")
        elif "rate_limit" in str(e).lower():
            print("⚠️  Rate limited (but model exists)")
            working_models.append(model)
        else:
            print(f"❌ Error: {str(e)[:50]}")

print("\n" + "="*60)
print("SUMMARY")
print("="*60)

if working_models:
    print(f"\n✅ You have access to {len(working_models)} model(s):\n")
    for model in working_models:
        print(f"   • {model}")

    print(f"\n📝 Recommended model to use: {working_models[0]}")
    print(f"\nUpdate this in: src/llm/anthropic_provider.py")
    print(f"Change line 17-18 to:")
    print(f'    return "{working_models[0]}"')
else:
    print("\n❌ No models available with your API key")
    print("\nPossible issues:")
    print("   1. API key is invalid")
    print("   2. API key is for an older tier")
    print("   3. Network/connection issue")
    print("\n💡 Try:")
    print("   • Check your API key at https://console.anthropic.com/")
    print("   • Generate a new API key")
    print("   • Or switch to OpenAI (edit .env: DEFAULT_LLM_PROVIDER=openai)")
