import random
import math
import market, wallet
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import uuid

# ============================================================================
# BASE BOT CLASS
# ============================================================================

class TradingBot:
    """Base class for all trading bots that work on behalf of users"""
    
    def __init__(self, user_id: str, bot_id: Optional[str] = None, 
                 creation_tick: int = 0, creation_price: float = 1.0,
                 parameters: Optional[Dict] = None):
        self.bot_id = bot_id or str(uuid.uuid4())
        self.user_id = user_id
        self.parameters = parameters or {}
        self.is_active = True
        self.last_action = "idle"
        
        # Bot state tracking
        self.state = BotState(
            bot_id=self.bot_id,
            creation_tick=creation_tick,
            price_at_creation=creation_price
        )
        
    def generate_signal(self, market: market.MarketData, wallet: wallet.UserWallet) -> Dict:
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
    
    def execute_trade(self, signal: Dict, wallet: wallet.UserWallet, market: market.MarketData) -> Dict:
        """
        Execute the trade signal on the user's wallet
        
        Returns:
            {
                'success': bool,
                'executed_action': str,
                'executed_amount': float,
                'profit_loss': float,
                'message': str
            }
        """
        if not self.is_active or signal['action'] == 'hold':
            return {
                'success': True,
                'executed_action': 'hold',
                'executed_amount': 0.0,
                'profit_loss': 0.0,
                'message': 'No trade executed'
            }
        
        action = signal['action']
        amount = signal['amount']
        price = market.current_price
        
        portfolio_before = wallet.get_portfolio_value(price)
        
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
                        'profit_loss': 0.0,
                        'message': 'Insufficient USD for trade'
                    }
                amount = max_amount * 0.95  # Use 95% to leave buffer
            
            cost = amount * price
            wallet.usd -= cost
            wallet.coins += amount
            wallet.last_interaction_tick = market.current_tick
            
            portfolio_after = wallet.get_portfolio_value(price)
            profit_loss = portfolio_after - portfolio_before
            
            # Update bot state
            self.state.update_after_trade(profit_loss, market.current_tick)
            
            return {
                'success': True,
                'executed_action': 'buy',
                'executed_amount': amount,
                'profit_loss': profit_loss,
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
                        'profit_loss': 0.0,
                        'message': 'Insufficient BC for trade'
                    }
                amount = wallet.coins * 0.95  # Sell 95% to leave buffer
            
            revenue = amount * price
            wallet.coins -= amount
            wallet.usd += revenue
            wallet.last_interaction_tick = market.current_tick
            
            portfolio_after = wallet.get_portfolio_value(price)
            profit_loss = portfolio_after - portfolio_before
            
            # Update bot state
            self.state.update_after_trade(profit_loss, market.current_tick)
            
            return {
                'success': True,
                'executed_action': 'sell',
                'executed_amount': amount,
                'profit_loss': profit_loss,
                'message': f'Sold {amount:.2f} BC for ${revenue:.2f}'
            }
        
        return {
            'success': False,
            'executed_action': 'unknown',
            'executed_amount': 0.0,
            'profit_loss': 0.0,
            'message': 'Invalid action'
        }
    
    def get_performance_metrics(self, market: market.MarketData, wallet: wallet.UserWallet) -> Dict:
        """Get bot performance statistics"""
        relative_price = self.state.get_relative_price(market)
        ticks_alive = self.state.get_ticks_alive(market.current_tick)
        
        return {
            'bot_id': self.bot_id,
            'bot_type': self.__class__.__name__,
            'trades_executed': self.state.trades_executed,
            'total_profit_loss': self.state.total_profit_loss,
            'ticks_alive': ticks_alive,
            'creation_tick': self.state.creation_tick,
            'price_at_creation': self.state.price_at_creation,
            'relative_price_change': (relative_price - 1.0) * 100,  # Percentage
            'trades_per_tick': self.state.trades_executed / ticks_alive if ticks_alive > 0 else 0
        }


# ============================================================================
# CONCRETE BOT IMPLEMENTATIONS
# ============================================================================

class RandomTraderBot(TradingBot):
    """Trades small random amounts to keep bananas fresh"""
    
    def __init__(self, user_id: str, bot_id: Optional[str] = None,
                 creation_tick: int = 0, creation_price: float = 1.0,
                 parameters: Optional[Dict] = None):
        default_params = {
            'min_trade': 0.5,
            'max_trade': 3.0,
            'trade_probability': 0.3  # 30% chance to trade each tick
        }
        super().__init__(user_id, bot_id, creation_tick, creation_price, 
                        {**default_params, **(parameters or {})})
    
    def generate_signal(self, market: market.MarketData, wallet: wallet.UserWallet) -> Dict:
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
    
    def __init__(self, user_id: str, bot_id: Optional[str] = None,
                 creation_tick: int = 0, creation_price: float = 1.0,
                 parameters: Optional[Dict] = None):
        default_params = {
            'short_window': 5,
            'long_window': 20,
            'trade_size': 2.0,
            'aggressiveness': 1.0  # Multiplier for trade size
        }
        super().__init__(user_id, bot_id, creation_tick, creation_price,
                        {**default_params, **(parameters or {})})
    
    def generate_signal(self, market: market.MarketData, wallet: wallet.UserWallet) -> Dict:
        # Use prices since bot was created for more personalized strategy
        prices_since_creation = self.state.get_prices_since_creation(market)
        ticks_alive = len(prices_since_creation)
        
        # Fallback to all market prices if bot is too new
        if ticks_alive < self.parameters['long_window']:
            short_ma = market.moving_average(self.parameters['short_window'])
            long_ma = market.moving_average(self.parameters['long_window'])
        else:
            # Calculate MAs from bot's perspective (using indices relative to creation)
            end_tick = self.state.creation_tick + ticks_alive
            short_ma = market.moving_average(self.parameters['short_window'], end_tick)
            long_ma = market.moving_average(self.parameters['long_window'], end_tick)
        
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
    
    def __init__(self, user_id: str, bot_id: Optional[str] = None,
                 creation_tick: int = 0, creation_price: float = 1.0,
                 parameters: Optional[Dict] = None):
        default_params = {
            'lookback_window': 20,
            'std_threshold': 1.5,  # Number of standard deviations for signal
            'trade_size': 2.5
        }
        super().__init__(user_id, bot_id, creation_tick, creation_price,
                        {**default_params, **(parameters or {})})
    
    def generate_signal(self, market: market.MarketData, wallet: wallet.UserWallet) -> Dict:
        mean_price = market.moving_average(self.parameters['lookback_window'])
        
        # Calculate standard deviation
        prices = market.get_prices(self.parameters['lookback_window'])
        if len(prices) < 2:
            return {'action': 'hold', 'amount': 0.0, 'reason': 'Insufficient data'}
        
        variance = sum((p - mean_price) ** 2 for p in prices) / len(prices)
        std_dev = math.sqrt(variance)
        
        current_price = market.current_price
        z_score = (current_price - mean_price) / std_dev if std_dev > 0 else 0
        
        # Store z_score in bot memory for analysis
        self.state.memory['last_z_score'] = z_score
        
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
    
    def __init__(self, user_id: str, bot_id: Optional[str] = None,
                 creation_tick: int = 0, creation_price: float = 1.0,
                 parameters: Optional[Dict] = None):
        default_params = {
            'target_bc_ratio': 0.5,  # Target 50% of portfolio in BC
            'rebalance_threshold': 0.1,  # Rebalance if 10% off target
            'trade_size': 1.5
        }
        super().__init__(user_id, bot_id, creation_tick, creation_price,
                        {**default_params, **(parameters or {})})
    
    def generate_signal(self, market: market.MarketData, wallet: wallet.UserWallet) -> Dict:
        total_value = wallet.get_portfolio_value(market.current_price)
        bc_value = wallet.coins * market.current_price
        current_ratio = bc_value / total_value if total_value > 0 else 0
        
        # Store ratio in bot memory
        self.state.memory['current_bc_ratio'] = current_ratio
        
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
    
    def __init__(self, user_id: str, bot_id: Optional[str] = None,
                 creation_tick: int = 0, creation_price: float = 1.0,
                 parameters: Optional[Dict] = None):
        default_params = {
            'volatility_threshold': 0.05,  # 5% volatility threshold
            'low_vol_ratio': 0.7,  # Hold 70% BC in low volatility
            'high_vol_ratio': 0.3,  # Hold 30% BC in high volatility
            'trade_size': 2.0
        }
        super().__init__(user_id, bot_id, creation_tick, creation_price,
                        {**default_params, **(parameters or {})})
    
    def generate_signal(self, market: market.MarketData, wallet: wallet.UserWallet) -> Dict:
        volatility = market.volatility
        total_value = wallet.get_portfolio_value(market.current_price)
        bc_value = wallet.coins * market.current_price
        current_ratio = bc_value / total_value if total_value > 0 else 0
        
        # Store volatility in bot memory
        self.state.memory['volatility'] = volatility
        self.state.memory['current_bc_ratio'] = current_ratio
        
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
        self.bot_registry: Dict[str, TradingBot] = {}  # bot_id -> bot
        self.bot_catalog = {
            'random': RandomTraderBot,
            'momentum': MomentumBot,
            'mean_reversion': MeanReversionBot,
            'market_maker': MarketMakerBot,
            'hedger': HedgingBot
        }
    
    def add_bot_to_user(self, user_id: str, bot_type: str, 
                        current_tick: int, current_price: float,
                        bot_id: Optional[str] = None,
                        parameters: Optional[Dict] = None) -> Tuple[bool, Optional[str]]:
        """
        Add a bot to a user's portfolio
        
        Returns:
            (success: bool, bot_id: str or None)
        """
        if bot_type not in self.bot_catalog:
            return False, None
        
        if user_id not in self.bots:
            self.bots[user_id] = []
        
        bot_class = self.bot_catalog[bot_type]
        new_bot = bot_class(
            user_id=user_id,
            bot_id=bot_id,
            creation_tick=current_tick,
            creation_price=current_price,
            parameters=parameters
        )
        
        self.bots[user_id].append(new_bot)
        self.bot_registry[new_bot.bot_id] = new_bot
        
        return True, new_bot.bot_id
    
    def get_bot(self, bot_id: str) -> Optional[TradingBot]:
        """Get a bot by its ID"""
        return self.bot_registry.get(bot_id)
    
    def get_user_bots(self, user_id: str) -> List[TradingBot]:
        """Get all bots for a specific user"""
        return self.bots.get(user_id, [])
    
    def toggle_bot(self, bot_id: str) -> bool:
        """Toggle a bot on/off by bot ID"""
        bot = self.bot_registry.get(bot_id)
        if bot:
            bot.is_active = not bot.is_active
            return True
        return False
    
    def remove_bot(self, bot_id: str) -> bool:
        """Remove a bot completely"""
        bot = self.bot_registry.get(bot_id)
        if not bot:
            return False
        
        user_id = bot.user_id
        if user_id in self.bots:
            self.bots[user_id] = [b for b in self.bots[user_id] if b.bot_id != bot_id]
        
        del self.bot_registry[bot_id]
        return True
    
    def run_all_bots(self, market: market.MarketData, wallets: Dict[str, wallet.UserWallet]) -> List[Dict]:
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
                
                # Get performance metrics
                metrics = bot.get_performance_metrics(market, wallet)
                
                results.append({
                    'user_id': user_id,
                    'bot_id': bot.bot_id,
                    'bot_type': bot.__class__.__name__,
                    'signal': signal,
                    'result': result,
                    'metrics': metrics
                })
        
        return results
    
    def get_all_bot_performance(self, market: market.MarketData, wallets: Dict[str, wallet.UserWallet]) -> Dict:
        """Get performance metrics for all bots"""
        performance = {}
        
        for bot_id, bot in self.bot_registry.items():
            if bot.user_id in wallets:
                wallet = wallets[bot.user_id]
                performance[bot_id] = bot.get_performance_metrics(market, wallet)
        
        return performance


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Create market data with simple price array (1 price per second)
    game_start = datetime.now()
    price_history = [1.0, 1.02, 1.01, 1.03, 1.04, 1.05]
    current_tick = len(price_history) - 1
    
    market = MarketData(
        current_price=1.05,
        price_history=price_history,
        start_time=game_start,
        current_tick=current_tick,
        volatility=0.02
    )
    
    # Create user wallets (using ticks instead of timestamps)
    wallets = {
        'user1': UserWallet('user1', coins=50.0, usd=500.0, last_interaction_tick=current_tick),
        'user2': UserWallet('user2', coins=30.0, usd=700.0, last_interaction_tick=current_tick)
    }
    
    # Create bot manager
    manager = BotManager()
    
    # Add bots to users (pass current tick and price)
    success1, bot_id1 = manager.add_bot_to_user('user1', 'momentum', current_tick, 1.05)
    success2, bot_id2 = manager.add_bot_to_user('user1', 'market_maker', current_tick, 1.05)
    success3, bot_id3 = manager.add_bot_to_user('user2', 'hedger', current_tick, 1.05)
    
    print(f"Created bots: {bot_id1}, {bot_id2}, {bot_id3}")
    print(f"Game started at tick 0 (time: {game_start})")
    print(f"Current tick: {current_tick} (time: {market.current_time})")
    
    # Run all bots
    results = manager.run_all_bots(market, wallets)
    
    # Print results
    for result in results:
        bot_tick = manager.get_bot(result['bot_id']).state.creation_tick
        print(f"\n{result['user_id']} - {result['bot_type']} (ID: {result['bot_id'][:8]}, created at tick {bot_tick}):")
        print(f"  Signal: {result['signal']['action']} - {result['signal']['reason']}")
        print(f"  Result: {result['result']['message']}")
        print(f"  Metrics: {result['metrics']['trades_executed']} trades, ${result['metrics']['total_profit_loss']:.2f} P/L")
    
    # Print final wallets
    print("\n\nFinal Wallets:")
    for user_id, wallet in wallets.items():
        portfolio_value = wallet.get_portfolio_value(market.current_price)
        print(f"{user_id}: BC={wallet.coins:.2f}, USD=${wallet.usd:.2f}, Total=${portfolio_value:.2f}")
    
    # Print bot performance
    print("\n\nBot Performance:")
    performance = manager.get_all_bot_performance(market, wallets)
    for bot_id, metrics in performance.items():
        print(f"{metrics['bot_type']} (ID: {bot_id[:8]}): {metrics['trades_executed']} trades, {metrics['ticks_alive']} ticks alive")