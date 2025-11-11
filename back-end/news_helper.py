"""
News Helper Module

Manages generic news headlines for market display.
"""

# Standard library imports
import logging
import os
import random
from typing import List

# Configure logging
logger = logging.getLogger(__name__)

# Default headlines if file not found
DEFAULT_HEADLINES = [
    "Market Analysts Predict Bullish Trend",
    "New Trading Features Announced",
    "Investor Confidence Remains High",
    "Price Stability Maintained",
    "Trading Activity Increases"
]


def load_generic_news() -> List[str]:
    """
    Load generic news headlines from generic_news.txt file.

    Returns:
        List of news headlines, or default headlines if file doesn't exist

    Note:
        File should contain one headline per line
    """
    news_file = os.path.join(os.path.dirname(__file__), 'generic_news.txt')

    try:
        if os.path.exists(news_file):
            with open(news_file, 'r', encoding='utf-8') as f:
                headlines = [line.strip() for line in f if line.strip()]
            return headlines if headlines else DEFAULT_HEADLINES
        else:
            logger.debug("generic_news.txt not found, using default headlines")
            return DEFAULT_HEADLINES
    except Exception as e:
        logger.error(f"Error loading generic news: {e}")
        return ["Market Activity Normal"]


def get_random_generic_news() -> str:
    """
    Get a random generic news headline.

    Returns:
        Random news headline string
    """
    headlines = load_generic_news()
    if headlines:
        return random.choice(headlines)
    return "Market Activity Normal"

