"""
Helper module for managing generic news headlines
"""
import random
import os

_cached_headlines: list[str] | None = None


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


def get_cached_generic_news() -> list[str]:
    """
    Get all generic news headlines with caching.
    Reads from disk only once, then returns the cached list.
    """
    global _cached_headlines
    if _cached_headlines is None:
        _cached_headlines = load_generic_news()
    return list(_cached_headlines)


def get_random_generic_news() -> str:
    """
    Get a random generic news headline.
    """
    headlines = get_cached_generic_news()
    if headlines:
        return random.choice(headlines)
    return "Market Activity Normal"

