import random
import math
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass

# ============================================================================
# BASE BOT CLASS
# ============================================================================

class TradingBot:
    """Base class for all trading bots that work on behalf of users"""
    
    def __init__(self, bot_id: str, user_id: str, parameters: Optional[Dict] = None):
        self.bot_id = bot_id
        self.user_id = user_id
        self.parameters = parameters or {}
        self.is_active = True
        self.last_action = "idle"
        
    def generate_signal(self, market: MarketData, wallet: UserWallet) -> Dict:
        """
        Generate a trading signal based on strategy
        
        Returns:
            {
                'action': 'buy' | 'sell' | 'hold',
                'amount': float,  # Amount of BC to trade
                'reason': str     # Human-readable explanation
            }
        """
        raise NotImplementedError("Subclasses must implement generate_signal")
    
    def execute_trade(self, signal: Dict, wallet: UserWallet, market: MarketData) -> Dict:
        """
        Execute the trade signal on the user's wallet
        
        Returns:
            {
                'success': bool,
                'executed_action': str,
                'executed_amount': float,
                'message': str
            }
        """
        if not self.is_active or signal['action'] == 'hold':
            return {
                'success': True,
                'executed_action': 'hold',
                'executed_amount': 0.0,
                'message': 'No trade executed'
            }
        
        action = signal['action']
        amount = signal['amount']
        price = market.current_price
        
        if action == 'buy':
            # Check if user has enough USD
            if not wallet.can_buy(amount, price):
                # Adjust amount to maximum affordable
                max_amount = wallet.usd / price
                if max_amount < 0.01:  # Minimum trade size
                    return {
                        'success': False,
                        'executed_action': 'buy',
                        'executed_amount': 0.0,
                        'message': 'Insufficient USD for trade'
                    }
                amount = max_amount * 0.95  # Use 95% to leave buffer
            
            cost = amount * price
            wallet.usd -= cost
            wallet.coins += amount
            wallet.last_interaction_time = market.timestamp
            
            return {
                'success': True,
                'executed_action': 'buy',
                'executed_amount': amount,
                'message': f'Bought {amount:.2f} BC for ${cost:.2f}'
            }
            
        elif action == 'sell':
            # Check if user has enough BC
            if not wallet.can_sell(amount):
                # Adjust amount to maximum available
                if wallet.coins < 0.01:  # Minimum trade size
                    return {
                        'success': False,
                        'executed_action': 'sell',
                        'executed_amount': 0.0,
                        'message': 'Insufficient BC for trade'
                    }
                amount = wallet.coins * 0.95  # Sell 95% to leave buffer
            
            revenue = amount * price
            wallet.coins -= amount
            wallet.usd += revenue
            wallet.last_interaction_time = market.timestamp
            
            return {
                'success': True,
                'executed_action': 'sell',
                'executed_amount': amount,
                'message': f'Sold {amount:.2f} BC for ${revenue:.2f}'
            }
        
        return {
            'success': False,
            'executed_action': 'unknown',
            'executed_amount': 0.0,
            'message': 'Invalid action'
        }


# ============================================================================
# CONCRETE BOT IMPLEMENTATIONS
# ============================================================================

class RandomTraderBot(TradingBot):
    """Trades small random amounts to keep bananas fresh"""
    
    def __init__(self, bot_id: str, user_id: str, parameters: Optional[Dict] = None):
        default_params = {
            'min_trade': 0.5,
            'max_trade': 3.0,
            'trade_probability': 0.3  # 30% chance to trade each tick
        }
        super().__init__(bot_id, user_id, {**default_params, **(parameters or {})})
    
    def generate_signal(self, market: MarketData, wallet: UserWallet) -> Dict:
        if random.random() > self.parameters['trade_probability']:
            return {'action': 'hold', 'amount': 0.0, 'reason': 'Random skip'}
        
        action = random.choice(['buy', 'sell'])
        amount = random.uniform(
            self.parameters['min_trade'],
            self.parameters['max_trade']
        )
        
        return {
            'action': action,
            'amount': amount,
            'reason': f'Random {action} to prevent decay'
        }


class MomentumBot(TradingBot):
    """Rides trends by comparing short-term and long-term moving averages"""
    
    def __init__(self, bot_id: str, user_id: str, parameters: Optional[Dict] = None):
        default_params = {
            'short_window': 5,
            'long_window': 20,
            'trade_size': 2.0,
            'aggressiveness': 1.0  # Multiplier for trade size
        }
        super().__init__(bot_id, user_id, {**default_params, **(parameters or {})})
    
    def generate_signal(self, market: MarketData, wallet: UserWallet) -> Dict:
        short_ma = market.moving_average(self.parameters['short_window'])
        long_ma = market.moving_average(self.parameters['long_window'])
        
        amount = self.parameters['trade_size'] * self.parameters['aggressiveness']
        
        if short_ma > long_ma * 1.02:  # 2% threshold to avoid noise
            return {
                'action': 'buy',
                'amount': amount,
                'reason': f'Uptrend detected (SMA={short_ma:.2f} > LMA={long_ma:.2f})'
            }
        elif short_ma < long_ma * 0.98:
            return {
                'action': 'sell',
                'amount': amount,
                'reason': f'Downtrend detected (SMA={short_ma:.2f} < LMA={long_ma:.2f})'
            }
        
        return {'action': 'hold', 'amount': 0.0, 'reason': 'No clear trend'}


class MeanReversionBot(TradingBot):
    """Exploits price overreactions by trading against extremes"""
    
    def __init__(self, bot_id: str, user_id: str, parameters: Optional[Dict] = None):
        default_params = {
            'lookback_window': 20,
            'std_threshold': 1.5,  # Number of standard deviations for signal
            'trade_size': 2.5
        }
        super().__init__(bot_id, user_id, {**default_params, **(parameters or {})})
    
    def generate_signal(self, market: MarketData, wallet: UserWallet) -> Dict:
        mean_price = market.moving_average(self.parameters['lookback_window'])
        
        # Calculate standard deviation
        if len(market.price_history) < 2:
            return {'action': 'hold', 'amount': 0.0, 'reason': 'Insufficient data'}
        
        prices = market.price_history[-self.parameters['lookback_window']:]
        variance = sum((p - mean_price) ** 2 for p in prices) / len(prices)
        std_dev = math.sqrt(variance)
        
        current_price = market.current_price
        z_score = (current_price - mean_price) / std_dev if std_dev > 0 else 0
        
        amount = self.parameters['trade_size']
        
        if z_score > self.parameters['std_threshold']:
            # Price is too high, sell
            return {
                'action': 'sell',
                'amount': amount,
                'reason': f'Price overextended (z={z_score:.2f}), expecting reversion'
            }
        elif z_score < -self.parameters['std_threshold']:
            # Price is too low, buy
            return {
                'action': 'buy',
                'amount': amount,
                'reason': f'Price oversold (z={z_score:.2f}), expecting bounce'
            }
        
        return {'action': 'hold', 'amount': 0.0, 'reason': f'Price near mean (z={z_score:.2f})'}


class MarketMakerBot(TradingBot):
    """Provides liquidity by maintaining balanced BC/USD positions"""
    
    def __init__(self, bot_id: str, user_id: str, parameters: Optional[Dict] = None):
        default_params = {
            'target_bc_ratio': 0.5,  # Target 50% of portfolio in BC
            'rebalance_threshold': 0.1,  # Rebalance if 10% off target
            'trade_size': 1.5
        }
        super().__init__(bot_id, user_id, {**default_params, **(parameters or {})})
    
    def generate_signal(self, market: MarketData, wallet: UserWallet) -> Dict:
        total_value = wallet.get_portfolio_value(market.current_price)
        bc_value = wallet.coins * market.current_price
        current_ratio = bc_value / total_value if total_value > 0 else 0
        
        target_ratio = self.parameters['target_bc_ratio']
        threshold = self.parameters['rebalance_threshold']
        
        if current_ratio < target_ratio - threshold:
            # Need more BC
            amount = self.parameters['trade_size']
            return {
                'action': 'buy',
                'amount': amount,
                'reason': f'Rebalancing: BC ratio {current_ratio:.2%} < target {target_ratio:.2%}'
            }
        elif current_ratio > target_ratio + threshold:
            # Need less BC
            amount = self.parameters['trade_size']
            return {
                'action': 'sell',
                'amount': amount,
                'reason': f'Rebalancing: BC ratio {current_ratio:.2%} > target {target_ratio:.2%}'
            }
        
        return {
            'action': 'hold',
            'amount': 0.0,
            'reason': f'Portfolio balanced (BC ratio: {current_ratio:.2%})'
        }


class HedgingBot(TradingBot):
    """Adjusts exposure based on market volatility"""
    
    def __init__(self, bot_id: str, user_id: str, parameters: Optional[Dict] = None):
        default_params = {
            'volatility_threshold': 0.05,  # 5% volatility threshold
            'low_vol_ratio': 0.7,  # Hold 70% BC in low volatility
            'high_vol_ratio': 0.3,  # Hold 30% BC in high volatility
            'trade_size': 2.0
        }
        super().__init__(bot_id, user_id, {**default_params, **(parameters or {})})
    
    def generate_signal(self, market: MarketData, wallet: UserWallet) -> Dict:
        volatility = market.volatility
        total_value = wallet.get_portfolio_value(market.current_price)
        bc_value = wallet.coins * market.current_price
        current_ratio = bc_value / total_value if total_value > 0 else 0
        
        # Determine target ratio based on volatility
        if volatility > self.parameters['volatility_threshold']:
            target_ratio = self.parameters['high_vol_ratio']
            regime = "high volatility"
        else:
            target_ratio = self.parameters['low_vol_ratio']
            regime = "low volatility"
        
        amount = self.parameters['trade_size']
        
        if current_ratio < target_ratio - 0.1:
            return {
                'action': 'buy',
                'amount': amount,
                'reason': f'Increasing BC exposure in {regime} (vol={volatility:.2%})'
            }
        elif current_ratio > target_ratio + 0.1:
            return {
                'action': 'sell',
                'amount': amount,
                'reason': f'Reducing BC exposure in {regime} (vol={volatility:.2%})'
            }
        
        return {
            'action': 'hold',
            'amount': 0.0,
            'reason': f'Position optimal for {regime} (vol={volatility:.2%})'
        }


# ============================================================================
# BOT MANAGER
# ============================================================================

class BotManager:
    """Manages all bots for all users in a game"""
    
    def __init__(self):
        self.bots: Dict[str, List[TradingBot]] = {}  # user_id -> [bots]
        self.bot_catalog = {
            'random': RandomTraderBot,
            'momentum': MomentumBot,
            'mean_reversion': MeanReversionBot,
            'market_maker': MarketMakerBot,
            'hedger': HedgingBot
        }
    
    def add_bot_to_user(self, user_id: str, bot_type: str, bot_id: str, 
                        parameters: Optional[Dict] = None) -> bool:
        """Add a bot to a user's portfolio"""
        if bot_type not in self.bot_catalog:
            return False
        
        if user_id not in self.bots:
            self.bots[user_id] = []
        
        bot_class = self.bot_catalog[bot_type]
        new_bot = bot_class(bot_id, user_id, parameters)
        self.bots[user_id].append(new_bot)
        return True
    
    def toggle_bot(self, user_id: str, bot_id: str) -> bool:
        """Toggle a bot on/off"""
        if user_id not in self.bots:
            return False
        
        for bot in self.bots[user_id]:
            if bot.bot_id == bot_id:
                bot.is_active = not bot.is_active
                return True
        return False
    
    def run_all_bots(self, market: MarketData, wallets: Dict[str, UserWallet]) -> List[Dict]:
        """Execute all active bots for all users"""
        results = []
        
        for user_id, user_bots in self.bots.items():
            if user_id not in wallets:
                continue
            
            wallet = wallets[user_id]
            
            for bot in user_bots:
                if not bot.is_active:
                    continue
                
                # Generate signal
                signal = bot.generate_signal(market, wallet)
                
                # Execute trade
                result = bot.execute_trade(signal, wallet, market)
                
                results.append({
                    'user_id': user_id,
                    'bot_id': bot.bot_id,
                    'bot_type': bot.__class__.__name__,
                    'signal': signal,
                    'result': result
                })
        
        return results


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Create market data
    market = MarketData(
        current_price=1.05,
        price_history=[1.0, 1.02, 1.01, 1.03, 1.04, 1.05],
        timestamp=datetime.now(),
        volatility=0.02
    )
    
    # Create user wallets
    wallets = {
        'user1': UserWallet('user1', coins=50.0, usd=500.0, last_interaction_time=datetime.now()),
        'user2': UserWallet('user2', coins=30.0, usd=700.0, last_interaction_time=datetime.now())
    }
    
    # Create bot manager
    manager = BotManager()
    
    # Add bots to users
    manager.add_bot_to_user('user1', 'momentum', 'bot1')
    manager.add_bot_to_user('user1', 'market_maker', 'bot2')
    manager.add_bot_to_user('user2', 'hedger', 'bot3')
    
    # Run all bots
    results = manager.run_all_bots(market, wallets)
    
    # Print results
    for result in results:
        print(f"\n{result['user_id']} - {result['bot_type']}:")
        print(f"  Signal: {result['signal']['action']} - {result['signal']['reason']}")
        print(f"  Result: {result['result']['message']}")
    
    # Print final wallets
    print("\n\nFinal Wallets:")
    for user_id, wallet in wallets.items():
        portfolio_value = wallet.get_portfolio_value(market.current_price)
        print(f"{user_id}: BC={wallet.coins:.2f}, USD=${wallet.usd:.2f}, Total=${portfolio_value:.2f}")