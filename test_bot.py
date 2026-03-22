from AppServices import NewsIntel
from database import SessionLocal
from BotServices import TradingBot
import json

def run_tests():
    print("--- 1. Testing AI Prompt (NewsIntel) ---")
    intel = NewsIntel()
    
    print("Testing AAPL (Apple)...")
    try:
        res = intel.get_sentiment_analysis("AAPL", "Apple", is_crypto=False, is_merval=False)
        print("Result of AI Analysis:")
        print(json.dumps(res, indent=2))
    except Exception as e:
        print(f"Error AI AAPL: {e}")

    print("\n--- 2. Testing Position Sizing Logic ---")
    db = SessionLocal()
    bot = TradingBot(db)
    size1 = bot._calculate_position_size(ai_score=85, bounce_prob=85)
    size2 = bot._calculate_position_size(ai_score=75, bounce_prob=70)
    size3 = bot._calculate_position_size(ai_score=50, bounce_prob=40)
    
    print(f"Setup A (High Conviction - Score 85, Bounce 85%): ${size1:.2f} USD")
    print(f"Setup B (Medium Conviction - Score 75, Bounce 70%): ${size2:.2f} USD")
    print(f"Setup C (Low Conviction - Score 50, Bounce 40%): ${size3:.2f} USD")
    
if __name__ == "__main__":
    run_tests()
