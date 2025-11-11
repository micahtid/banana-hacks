# Standard library imports
import json
import logging
import math
import random
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# Local imports
from redis_helper import get_redis_connection, serialize_datetime, deserialize_datetime

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class MarketData:
    """Represents the current and historical market state"""
    current_price: float
    price_history: List[float]  # Historical prices (1 per second)
    start_time: datetime  # When the game started
    current_tick: int  # Current tick number (seconds since start)
    volatility: float  # Standard deviation of recent returns
    dollar_supply: float
    bc_supply: float
    
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


class Market:
    """Market manager that handles users and market updates"""
    
    # Event titles pool
    EVENT_TITLES = [
        "Supply Crash",
        "Monkey Invasion",
        "Banana Shortage",
        "Golden Banana Found",
        "Tropical Storm",
        "Harvest Festival",
        "Market Panic",
        "Investor Frenzy",
        "Banana Boom",
        "Export Ban",
        "Celebrity Endorsement",
        "Disease Outbreak"
    ]
    
    def __init__(self, initial_price: float = 1.0, game_id: Optional[str] = None, duration: int = 300):
        """Initialize the market with starting price"""
        self.game_id = game_id or str(uuid.uuid4())
        self.start_time = datetime.now()
        self.current_tick = 0
        self.users: List[str] = []
        self.dollar_supply = 1000000
        self.bc_supply = 1000000
        
        # Generate random event time (between 30% and 70% of game duration)
        min_event_tick = int(duration * 0.3)
        max_event_tick = int(duration * 0.7)
        self.event_tick = random.randint(min_event_tick, max_event_tick)
        self.event_time = self.start_time + timedelta(seconds=self.event_tick)
        
        # Choose random event title
        self.event_title = random.choice(self.EVENT_TITLES)
        
        # Track if event has been triggered
        self.event_triggered = False
        
        # Initialize MarketData
        self.market_data = MarketData(
            current_price=initial_price,
            price_history=[initial_price],
            start_time=self.start_time,
            current_tick=self.current_tick,
            volatility=0.0,
            dollar_supply=self.dollar_supply,
            bc_supply=self.bc_supply
        )
        
        # Save initial state to Redis
        self.save_to_redis()
    
    def addUser(self, userID: str):
        """Add a user to the market"""
        if userID not in self.users:
            self.users.append(userID)
            self.save_to_redis()
    
    def removeUser(self, userID: str):
        """Remove a user from the market"""
        if userID in self.users:
            self.users.remove(userID)
            self.save_to_redis()
    
    def updateMarket(self, num_simulated_trades=20):
        """Update the market state (price, tick, volatility)"""
        # Increment tick
        self.current_tick += 1
        
        # Track if event state changed (needs to be saved)
        event_state_changed = False
        
        # Check if event should trigger
        if not self.event_triggered and self.current_tick >= self.event_tick:
            self.event_triggered = True
            self._trigger_event()
            event_state_changed = True
        
        # Reset event_triggered after 10 seconds (10 ticks) to allow front-end timeout to work
        # This ensures the event banner disappears after the timeout period
        if self.event_triggered and self.current_tick >= self.event_tick + 10:
            self.event_triggered = False
            event_state_changed = True
        
        # Ensure supplies are always above minimum thresholds BEFORE any calculations
        MIN_BC_SUPPLY = 10000.0  # Increased minimum to prevent extreme price swings
        MIN_DOLLAR_SUPPLY = 10000.0
        
        self.bc_supply = max(MIN_BC_SUPPLY, self.bc_supply)
        self.dollar_supply = max(MIN_DOLLAR_SUPPLY, self.dollar_supply)
        
        # Simulate market activity with random trades to change supplies
        # This creates realistic price movement with higher volatility
        for _ in range(num_simulated_trades):
            # Calculate current price safely
            if self.bc_supply <= 0:
                self.bc_supply = MIN_BC_SUPPLY
            if self.dollar_supply <= 0:
                self.dollar_supply = MIN_DOLLAR_SUPPLY
            
            current_price = self.dollar_supply / self.bc_supply
            
            # Much larger, variable trade sizes for more volatility
            # Trade between 0.3% to 1.5% of current BC supply (reduced to prevent extreme swings)
            min_trade = self.bc_supply * 0.003  # 0.3%
            max_trade = self.bc_supply * 0.015   # 1.5%
            trade_size = random.uniform(min_trade, max_trade)
            
            # Random buy or sell (50/50 chance)
            if random.random() > 0.5:
                # Simulated buy: BC leaves market, USD enters market
                new_bc_supply = self.bc_supply - trade_size
                new_dollar_supply = self.dollar_supply + current_price * trade_size
                
                # Only apply trade if it doesn't violate minimum constraints
                if new_bc_supply >= MIN_BC_SUPPLY and new_dollar_supply >= MIN_DOLLAR_SUPPLY:
                    self.bc_supply = new_bc_supply
                    self.dollar_supply = new_dollar_supply
            else:
                # Simulated sell: BC enters market, USD leaves market
                new_bc_supply = self.bc_supply + trade_size
                new_dollar_supply = self.dollar_supply - current_price * trade_size
                
                # Only apply trade if it doesn't violate minimum constraints
                if new_bc_supply >= MIN_BC_SUPPLY and new_dollar_supply >= MIN_DOLLAR_SUPPLY:
                    self.bc_supply = new_bc_supply
                    self.dollar_supply = new_dollar_supply
        
        # Ensure supplies are still above minimums after all trades
        self.bc_supply = max(MIN_BC_SUPPLY, self.bc_supply)
        self.dollar_supply = max(MIN_DOLLAR_SUPPLY, self.dollar_supply)
        
        # Calculate new price with updated supplies (guaranteed safe division)
        new_price = self.dollar_supply / self.bc_supply
        new_price = max(0.10, new_price)  # Ensure minimum price of $0.10 (no upper limit)
        
        # Update price history
        self.market_data.price_history.append(new_price)
        
        # Update market data
        self.market_data.current_price = new_price
        self.market_data.current_tick = self.current_tick
        self.market_data.dollar_supply = self.dollar_supply
        self.market_data.bc_supply = self.bc_supply
        
        # Calculate volatility from recent returns
        returns = self.market_data.returns(window=10)
        if len(returns) >= 2:
            mean_return = sum(returns) / len(returns)
            variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
            self.market_data.volatility = math.sqrt(variance) if variance > 0 else 0.0
        else:
            self.market_data.volatility = 0.0
        
        # Save to Redis after update
        # Always save, but if event state changed, ensure it's saved immediately
        self.save_to_redis()
        
        # If event state changed, save again to ensure it's persisted
        # This is important for frontend polling to see the state change
        if event_state_changed:
            self.save_to_redis()
    
    def _trigger_event(self):
        """Trigger a market event with sudden price change"""
        # Determine if event is positive or negative (50/50 chance)
        is_positive = random.random() > 0.5
        
        # Create a sudden supply shock
        if is_positive:
            # Positive event: Increase demand (reduce BC supply, increase dollar supply)
            shock_factor = random.uniform(0.15, 0.25)  # 15-25% shock
            self.bc_supply *= (1 - shock_factor)
            self.dollar_supply *= (1 + shock_factor * 0.5)
        else:
            # Negative event: Decrease demand (increase BC supply, reduce dollar supply)
            shock_factor = random.uniform(0.15, 0.25)  # 15-25% shock
            self.bc_supply *= (1 + shock_factor)
            self.dollar_supply *= (1 - shock_factor * 0.5)
        
        # Ensure supplies stay above minimums
        MIN_BC_SUPPLY = 10000.0
        MIN_DOLLAR_SUPPLY = 10000.0
        self.bc_supply = max(MIN_BC_SUPPLY, self.bc_supply)
        self.dollar_supply = max(MIN_DOLLAR_SUPPLY, self.dollar_supply)
        
        logger.info(f"EVENT TRIGGERED: {self.event_title} - {'Positive' if is_positive else 'Negative'} shock of {shock_factor*100:.1f}%")
    
    def save_to_redis(self):
        """Save all market data to Redis"""
        try:
            r = get_redis_connection()
            
            # Store market basic info
            market_key = f"market:{self.game_id}"
            r.hset(market_key, mapping={
                "game_id": self.game_id,
                "start_time": serialize_datetime(self.start_time),
                "current_tick": str(self.current_tick),
                "users": json.dumps(self.users),
                "dollar_supply": str(self.dollar_supply),
                "bc_supply": str(self.bc_supply),
                "event_tick": str(self.event_tick),
                "event_time": serialize_datetime(self.event_time),
                "event_title": self.event_title,
                "event_triggered": str(self.event_triggered)
            })
            
            # Store market data
            market_data_key = f"market:{self.game_id}:data"
            r.hset(market_data_key, mapping={
                "current_price": str(self.market_data.current_price),
                "price_history": json.dumps(self.market_data.price_history),
                "start_time": serialize_datetime(self.market_data.start_time),
                "current_tick": str(self.market_data.current_tick),
                "volatility": str(self.market_data.volatility),
                "dollar_supply": str(self.market_data.dollar_supply),
                "bc_supply": str(self.market_data.bc_supply)
            })
            
        except Exception as e:
            # Log error but don't fail the operation
            logger.warning(f"Failed to save market data to Redis: {e}")
    
    @classmethod
    def load_from_redis(cls, game_id: str) -> Optional['Market']:
        """Load market data from Redis by game_id"""
        try:
            r = get_redis_connection()
            
            # Check if market exists
            market_key = f"market:{game_id}"
            if not r.exists(market_key):
                return None
            
            # Load market basic info
            market_data = r.hgetall(market_key)
            if not market_data:
                return None
            
            # Create Market instance
            start_time = deserialize_datetime(market_data["start_time"])
            current_tick = int(market_data["current_tick"])
            users = json.loads(market_data["users"])
            dollar_supply = float(market_data["dollar_supply"])
            bc_supply = float(market_data["bc_supply"])
            event_tick = int(market_data.get("event_tick", 150))
            event_time = deserialize_datetime(market_data.get("event_time", serialize_datetime(start_time + timedelta(seconds=150))))
            event_title = market_data.get("event_title", "Market Event")
            event_triggered = market_data.get("event_triggered", "false").lower() == "true"
            # Load market data
            market_data_key = f"market:{game_id}:data"
            data = r.hgetall(market_data_key)
            if not data:
                return None
            
            # Reconstruct MarketData
            price_history = json.loads(data["price_history"])
            market_data_obj = MarketData(
                current_price=float(data["current_price"]),
                price_history=price_history,
                start_time=deserialize_datetime(data["start_time"]),
                current_tick=int(data["current_tick"]),
                volatility=float(data["volatility"]),
                dollar_supply=dollar_supply,
                bc_supply=bc_supply
            )
            
            # Create Market instance
            market = cls.__new__(cls)
            market.game_id = game_id
            market.start_time = start_time
            market.current_tick = current_tick
            market.users = users
            market.dollar_supply = dollar_supply
            market.bc_supply = bc_supply
            market.market_data = market_data_obj
            market.event_tick = event_tick
            market.event_time = event_time
            market.event_title = event_title
            market.event_triggered = event_triggered
            
            return market

        except Exception as e:
            logger.error(f"Error loading market from Redis: {e}")
            return None
    
    def remove_from_redis(self):
        """Remove market data from Redis"""
        try:
            r = get_redis_connection()
            market_key = f"market:{self.game_id}"
            market_data_key = f"market:{self.game_id}:data"
            r.delete(market_key)
            r.delete(market_data_key)
        except Exception as e:
            logger.warning(f"Failed to remove market data from Redis: {e}")
