"""
Helper module for managing generic news headlines
"""
import random
import os

def load_generic_news() -> list[str]:
    """
    Load generic news headlines from generic_news.txt file.
    Returns a list of headlines, or empty list if file doesn't exist.
    """
    news_file = os.path.join(os.path.dirname(__file__), 'generic_news.txt')
    
    try:
        if os.path.exists(news_file):
            with open(news_file, 'r', encoding='utf-8') as f:
                headlines = [line.strip() for line in f if line.strip()]
            return headlines
        else:
            # Return default headlines if file doesn't exist
            return [
                "Market Analysts Predict Bullish Trend",
                "New Trading Features Announced",
                "Investor Confidence Remains High",
                "Price Stability Maintained",
                "Trading Activity Increases"
            ]
    except Exception as e:
        print(f"Error loading generic news: {e}")
        return ["Market Activity Normal"]

def get_random_generic_news() -> str:
    """
    Get a random generic news headline.
    """
    headlines = load_generic_news()
    if headlines:
        return random.choice(headlines)
    return "Market Activity Normal"

