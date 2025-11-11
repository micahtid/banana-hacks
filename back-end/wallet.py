"""
User Wallet Data Class

Simple data structure for user portfolio tracking.
"""

from dataclasses import dataclass


@dataclass
class UserWallet:
    """
    Represents a user's portfolio in the game.

    Attributes:
        user_id: Unique user identifier
        coins: BananaCoin balance
        usd: USD balance
        last_interaction_tick: Last tick when user/bot traded
    """
    user_id: str
    coins: float
    usd: float
    last_interaction_tick: int

    def get_portfolio_value(self, current_price: float) -> float:
        """
        Calculate total portfolio value in USD.

        Args:
            current_price: Current BananaCoin price

        Returns:
            Total portfolio value in USD
        """
        return self.usd + (self.coins * current_price)

    def can_buy(self, amount: float, price: float) -> bool:
        """
        Check if user has enough USD to buy.

        Args:
            amount: Amount of BC to buy
            price: Price per BC

        Returns:
            True if user can afford the purchase
        """
        return self.usd >= (amount * price)

    def can_sell(self, amount: float) -> bool:
        """
        Check if user has enough BC to sell.

        Args:
            amount: Amount of BC to sell

        Returns:
            True if user has enough BC
        """
        return self.coins >= amount