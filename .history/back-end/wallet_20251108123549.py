from dataclasses import dataclass

@dataclass
class UserWallet:
    """Represents a user's portfolio"""
    user_id: str
    coins: float  # BananaCoin balance
    usd: float    # USD balance
    last_interaction_tick: int  # Last tick when user/bot traded
    
    def get_portfolio_value(self, current_price: float) -> float:
        """Calculate total portfolio value in USD"""
        return self.usd + (self.coins * current_price)
    
    def can_buy(self, amount: float, price: float) -> bool:
        """Check if user has enough USD to buy"""
        return self.usd >= (amount * price)
    
    def can_sell(self, amount: float) -> bool:
        """Check if user has enough BC to sell"""
        return self.coins >= amount