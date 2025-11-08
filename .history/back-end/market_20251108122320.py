import random
import math
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import uuid

@dataclass
class MarketData:
    """Represents the current and historical market state"""
    current_price: float
    price_history: List[float]  # Historical prices (1 per second)
    start_time: datetime  # When the game started
    current_tick: int  # Current tick number (seconds since start)
    volatility: float  # Standard deviation of recent returns
    
    @property
    def current_time(self) -> datetime:
        """Get the current timestamp based on tick"""
        return self.start_time + timedelta(seconds=self.current_tick)
    
    def get_price_at_tick(self, tick: int) -> Optional[float]:
        """Get the price at a specific tick"""
        if 0 <= tick < len(self.price_history):
            return self.price_history[tick]
        return None
    
    def get_prices(self, count: Optional[int] = None, end_tick: Optional[int] = None) -> List[float]:
        """
        Get the most recent N prices
        
        Args:
            count: Number of prices to get (None = all)
            end_tick: End at this tick (None = current)
        """
        if end_tick is None:
            end_tick = len(self.price_history)
        
        if count is None:
            return self.price_history[:end_tick]
        
        start_tick = max(0, end_tick - count)
        return self.price_history[start_tick:end_tick]
    
    def moving_average(self, window: int, end_tick: Optional[int] = None) -> float:
        """Calculate moving average over the last `window` prices"""
        prices = self.get_prices(window, end_tick)
        if not prices:
            return self.current_price
        return sum(prices) / len(prices)
    
    def price_change(self, periods: int = 1) -> float:
        """Calculate price change over the last `periods`"""
        if len(self.price_history) < periods + 1:
            return 0.0
        return self.current_price - self.price_history[-(periods + 1)]
    
    def returns(self, window: int = 10) -> List[float]:
        """Calculate returns over the last `window` periods"""
        if len(self.price_history) < 2:
            return []
        
        start_idx = max(0, len(self.price_history) - window - 1)
        returns = []
        for i in range(start_idx + 1, len(self.price_history)):
            if self.price_history[i-1] != 0:
                returns.append((self.price_history[i] - self.price_history[i-1]) / self.price_history[i-1])
        return returns