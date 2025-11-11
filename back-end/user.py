"""
User Module

Comprehensive user data model with trading and bot management capabilities.
"""

# Standard library imports
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class User:
    """Represents a user in the game with portfolio and bots"""
    
    user_id: str
    user_name: str
    coins: float = 1000.0  # BananaCoin balance
    usd: float = 1000.0    # USD balance
    last_interaction_v: int = 0  # Last interaction tick/version
    last_interaction_t: Optional[datetime] = None  # Last interaction timestamp
    bots: List[Dict[str, str]] = field(default_factory=list)  # List of {botId, botName}
    
    def __post_init__(self):
        """Initialize last_interaction_t if not provided"""
        if self.last_interaction_t is None:
            self.last_interaction_t = datetime.now()
    
    # ============================================================================
    # GETTER METHODS
    # ============================================================================
    
    def get_user_id(self) -> str:
        """Get the user ID"""
        return self.user_id
    
    def get_user_name(self) -> str:
        """Get the user name"""
        return self.user_name
    
    def get_dollar(self) -> float:
        """Get USD balance"""
        return self.usd
    
    def get_bc(self) -> float:
        """Get BananaCoin balance"""
        return self.coins
    
    def get_coins(self) -> float:
        """Get BananaCoin balance (alias for get_bc)"""
        return self.coins
    
    def get_usd(self) -> float:
        """Get USD balance (alias for get_dollar)"""
        return self.usd
    
    # CamelCase aliases for compatibility with inspiration code
    def getUserID(self) -> str:
        """Get the user ID (camelCase alias)"""
        return self.user_id
    
    def getDollar(self) -> float:
        """Get USD balance (camelCase alias)"""
        return self.usd
    
    def getBC(self) -> float:
        """Get BananaCoin balance (camelCase alias)"""
        return self.coins
    
    def get_last_interaction_v(self) -> int:
        """Get last interaction version/tick"""
        return self.last_interaction_v
    
    def get_last_interaction_t(self) -> Optional[datetime]:
        """Get last interaction timestamp"""
        return self.last_interaction_t
    
    def get_bots(self) -> List[Dict[str, str]]:
        """Get list of all bots"""
        return self.bots.copy()
    
    # ============================================================================
    # TRADING METHODS
    # ============================================================================
    
    def buy_bc(self, amount: float, price: float, current_tick: int = 0) -> bool:
        """
        Buy BananaCoins with USD
        
        Args:
            amount: Amount of BC to buy
            price: Price per BC in USD
            current_tick: Current market tick (optional)
        
        Returns:
            True if successful, False if insufficient funds
        """
        cost = amount * price
        if self.usd < cost:
            return False
        
        self.usd -= cost
        self.coins += amount
        self._update_interaction(current_tick)
        return True
    
    def sell_bc(self, amount: float, price: float, current_tick: int = 0) -> bool:
        """
        Sell BananaCoins for USD
        
        Args:
            amount: Amount of BC to sell
            price: Price per BC in USD
            current_tick: Current market tick (optional)
        
        Returns:
            True if successful, False if insufficient BC
        """
        if self.coins < amount:
            return False
        
        revenue = amount * price
        self.coins -= amount
        self.usd += revenue
        self._update_interaction(current_tick)
        return True
    
    # CamelCase aliases for compatibility with inspiration code
    def buyBC(self, amount: float, price: float = 1.0, current_tick: int = 0) -> bool:
        """
        Buy BananaCoins with USD (camelCase alias)
        
        Note: In the inspiration code, buyBC(amount) treats amount as USD cost
        when price=1.0 (spend amount USD, get amount BC). This method maintains
        that behavior. For explicit BC amount buying, use buy_bc().
        
        Args:
            amount: USD cost to spend (when price=1.0) or BC amount (when price != 1.0)
            price: Price per BC (default 1.0 for compatibility with inspiration)
            current_tick: Current market tick (optional)
        
        Returns:
            True if successful, False if insufficient funds
        """
        # When price=1.0, amount is USD cost (matching inspiration: spend amount USD, get amount BC)
        # When price != 1.0, amount is BC amount
        if price == 1.0:
            # Inspiration behavior: amount is USD cost, and you get amount BC
            usd_cost = amount
            bc_amount = amount
        else:
            # Standard behavior: amount is BC amount
            bc_amount = amount
            usd_cost = amount * price
        
        if self.usd < usd_cost:
            return False
        
        self.usd -= usd_cost
        self.coins += bc_amount
        self._update_interaction(current_tick)
        return True
    
    def sellBC(self, amount: float, price: float = 1.0, current_tick: int = 0) -> bool:
        """
        Sell BananaCoins for USD (camelCase alias)
        
        Args:
            amount: Amount of BC to sell
            price: Price per BC (default 1.0 for compatibility)
            current_tick: Current market tick (optional)
        
        Returns:
            True if successful, False if insufficient BC
        """
        return self.sell_bc(amount, price, current_tick)
    
    # ============================================================================
    # BOT MANAGEMENT METHODS
    # ============================================================================
    
    def add_bot(self, bot_id: str, bot_name: str) -> bool:
        """
        Add a bot to the user's collection
        
        Args:
            bot_id: Unique bot identifier
            bot_name: Name/type of the bot
        
        Returns:
            True if added, False if bot_id already exists
        """
        # Check if bot already exists
        if any(bot.get("botId") == bot_id for bot in self.bots):
            return False
        
        self.bots.append({
            "botId": bot_id,
            "botName": bot_name
        })
        return True
    
    def remove_bot(self, bot_id: str) -> bool:
        """
        Remove a bot from the user's collection
        
        Args:
            bot_id: Bot identifier to remove
        
        Returns:
            True if removed, False if bot not found
        """
        initial_length = len(self.bots)
        self.bots = [bot for bot in self.bots if bot.get("botId") != bot_id]
        return len(self.bots) < initial_length
    
    def get_bot(self, bot_id: str) -> Optional[Dict[str, str]]:
        """
        Get a specific bot by ID
        
        Args:
            bot_id: Bot identifier
        
        Returns:
            Bot dictionary or None if not found
        """
        for bot in self.bots:
            if bot.get("botId") == bot_id:
                return bot.copy()
        return None
    
    def has_bot(self, bot_id: str) -> bool:
        """Check if user has a bot with the given ID"""
        return any(bot.get("botId") == bot_id for bot in self.bots)
    
    # ============================================================================
    # PORTFOLIO METHODS
    # ============================================================================
    
    def get_portfolio_value(self, current_price: float) -> float:
        """
        Calculate total portfolio value in USD
        
        Args:
            current_price: Current BC price in USD
        
        Returns:
            Total portfolio value
        """
        return self.usd + (self.coins * current_price)
    
    def can_buy(self, amount: float, price: float) -> bool:
        """
        Check if user has enough USD to buy
        
        Args:
            amount: Amount of BC to buy
            price: Price per BC
        
        Returns:
            True if user can afford the purchase
        """
        return self.usd >= (amount * price)
    
    def can_sell(self, amount: float) -> bool:
        """
        Check if user has enough BC to sell
        
        Args:
            amount: Amount of BC to sell
        
        Returns:
            True if user has enough BC
        """
        return self.coins >= amount
    
    # ============================================================================
    # INTERACTION TRACKING
    # ============================================================================
    
    def _update_interaction(self, current_tick: int = 0):
        """Update last interaction timestamp and tick"""
        self.last_interaction_t = datetime.now()
        if current_tick > 0:
            self.last_interaction_v = current_tick
    
    def update_interaction(self, current_tick: int):
        """
        Manually update interaction tracking
        
        Args:
            current_tick: Current market tick
        """
        self._update_interaction(current_tick)
    
    # ============================================================================
    # SERIALIZATION
    # ============================================================================
    
    def to_dict(self) -> Dict:
        """
        Convert user to dictionary format for API/Firebase
        
        Returns:
            Dictionary representation of user
        """
        return {
            "userId": self.user_id,
            "userName": self.user_name,
            "coins": self.coins,
            "usd": self.usd,
            "lastInteractionV": self.last_interaction_v,
            "lastInteractionT": self.last_interaction_t.isoformat() if self.last_interaction_t else None,
            "bots": self.bots.copy()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        """
        Create User instance from dictionary
        
        Args:
            data: Dictionary with user data
        
        Returns:
            User instance
        """
        # Handle both camelCase and snake_case keys
        user_id = data.get("userId") or data.get("user_id")
        user_name = data.get("userName") or data.get("user_name")
        coins = data.get("coins", 1000.0)
        usd = data.get("usd", 1000.0)
        last_interaction_v = data.get("lastInteractionV") or data.get("last_interaction_v") or data.get("last_interaction_tick", 0)
        
        # Parse timestamp if present
        last_interaction_t = None
        if "lastInteractionT" in data and data["lastInteractionT"]:
            if isinstance(data["lastInteractionT"], str):
                last_interaction_t = datetime.fromisoformat(data["lastInteractionT"])
            elif isinstance(data["lastInteractionT"], datetime):
                last_interaction_t = data["lastInteractionT"]
        elif "last_interaction_t" in data and data["last_interaction_t"]:
            if isinstance(data["last_interaction_t"], str):
                last_interaction_t = datetime.fromisoformat(data["last_interaction_t"])
            elif isinstance(data["last_interaction_t"], datetime):
                last_interaction_t = data["last_interaction_t"]
        
        bots = data.get("bots", [])
        
        return cls(
            user_id=user_id,
            user_name=user_name,
            coins=coins,
            usd=usd,
            last_interaction_v=last_interaction_v,
            last_interaction_t=last_interaction_t,
            bots=bots
        )

