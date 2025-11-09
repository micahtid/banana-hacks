import random
import math
from typing import List, Dict, Optional
from dataclasses import dataclass
import uuid
import json
from redis_helper import get_redis_connection

# ============================================================================
# BOT CLASS
# ============================================================================

class Bot:
    """
    Basic Bot constructor with own wallet and trading capabilities.
    Works directly with Redis game room data.
    """
    
    def __init__(self, bot_id: Optional[str] = None,
                 is_toggled: bool = True, usd_given: float = 0.0,
                 usd: float = 0.0, bc: float = 0.0, bot_type: Optional[str] = None,
                 behavior_coefficient: Optional[float] = None, user_id: Optional[str] = None):
        """
        Initialize a bot
        
        Args:
            bot_id: Unique bot identifier (generated if not provided)
            is_toggled: Boolean indicating if bot is on/off
            usd_given: Initial USD capital given to the bot (startingBalance in Redis)
            usd: Current USD balance in bot's wallet (balance in Redis)
            bc: Current BC (Banana Coin) balance in bot's wallet (not in Redis structure, but needed for trading)
            bot_type: Type of bot strategy (random, momentum, mean_reversion, market_maker, hedger)
            behavior_coefficient: Bot's behavior coefficient (0.8-1.2). If None, generated from bot_id
            user_id: Owner user ID
        """
        self.bot_id = bot_id or str(uuid.uuid4())
        self.is_toggled = is_toggled
        self.usd_given = usd_given
        self.usd = usd
        self.bc = bc
        self.bot_type = bot_type or 'random'
        self.user_id = user_id
        self.parameters = self._get_default_parameters()
        
        # Bot-specific randomness seed based on bot_id for consistent uniqueness
        self._random_seed = hash(self.bot_id) % 10000
        random.seed(self._random_seed)
        # behaviorCoefficient: stored as public attribute for Redis persistence
        # Range: 0.8 to 1.2 (represents bot's unique personality/behavior variation)
        if behavior_coefficient is not None:
            self.behavior_coefficient = float(behavior_coefficient)
        else:
            self.behavior_coefficient = 0.8 + (hash(self.bot_id) % 40) / 100.0
        self._personality_factor = self.behavior_coefficient  # Alias for internal use
        random.seed()  # Reset to system randomness
    
    def _get_default_parameters(self) -> Dict:
        """Get default parameters based on bot type"""
        defaults = {
            'random': {
                'min_trade': 0.5,
                'max_trade': 3.0,
                'trade_probability': 0.3
            },
            'momentum': {
                'short_window': 5,
                'long_window': 20,
                'trade_size': 2.0,
                'aggressiveness': 1.0
            },
            'mean_reversion': {
                'lookback_window': 20,
                'std_threshold': 1.5,
                'trade_size': 2.5
            },
            'market_maker': {
                'target_bc_ratio': 0.5,
                'rebalance_threshold': 0.1,
                'trade_size': 1.5
            },
            'hedger': {
                'volatility_threshold': 0.05,
                'low_vol_ratio': 0.7,
                'high_vol_ratio': 0.3,
                'trade_size': 2.0
            }
        }
        return defaults.get(self.bot_type, defaults['random'])
    
    def analyze(self, coins: List[float], current_price: Optional[float] = None) -> Dict:
        """
        Analyze market conditions and determine trading action
        
        Args:
            coins: List of coin prices (price history)
            current_price: Current coin price (if None, uses last price in coins array)
        
        Returns:
            {
                'action': 'buy' | 'sell' | 'hold',
                'amount': float  # Amount of BC to trade
            }
        """
        if not coins or len(coins) < 1:
            return {'action': 'hold', 'amount': 0.0}
        
        if current_price is None:
            current_price = coins[-1]
        
        if self.bot_type == 'random':
            return self._analyze_random()
        elif self.bot_type == 'momentum':
            return self._analyze_momentum(coins, current_price)
        elif self.bot_type == 'mean_reversion':
            return self._analyze_mean_reversion(coins, current_price)
        elif self.bot_type == 'market_maker':
            return self._analyze_market_maker(current_price)
        elif self.bot_type == 'hedger':
            return self._analyze_hedger(coins, current_price)
        else:
            return {'action': 'hold', 'amount': 0.0}
    
    def _analyze_random(self) -> Dict:
        """Random trading strategy with bot-specific variation"""
        # Bot-specific trade probability variation
        base_prob = self.parameters['trade_probability']
        bot_prob = base_prob * self._personality_factor
        
        if random.random() > bot_prob:
            return {'action': 'hold', 'amount': 0.0}
        
        action = random.choice(['buy', 'sell'])
        # Bot-specific amount variation
        min_trade = self.parameters['min_trade'] * self._personality_factor
        max_trade = self.parameters['max_trade'] * self._personality_factor
        amount = random.uniform(min_trade, max_trade)
        
        return {'action': action, 'amount': amount}
    
    def _analyze_momentum(self, coins: List[float], current_price: float) -> Dict:
        """Momentum trading strategy with bot-specific variation"""
        if len(coins) < 2:
            return {'action': 'hold', 'amount': 0.0}
        
        # Bot-specific window variation
        short_window = max(3, int(self.parameters['short_window'] * self._personality_factor))
        long_window = max(short_window + 1, int(self.parameters['long_window'] * self._personality_factor))
        
        prices = coins[-long_window:] if len(coins) >= long_window else coins
        
        if len(prices) < short_window:
            return {'action': 'hold', 'amount': 0.0}
        
        short_prices = prices[-short_window:]
        long_prices = prices[-long_window:] if len(prices) >= long_window else prices
        
        short_ma = sum(short_prices) / len(short_prices)
        long_ma = sum(long_prices) / len(long_prices)
        
        # Bot-specific threshold variation (1.5% to 2.5% instead of fixed 2%)
        threshold = 0.015 + (hash(self.bot_id) % 10) / 1000.0  # 0.015 to 0.025
        
        # Bot-specific amount variation
        base_amount = self.parameters['trade_size'] * self.parameters['aggressiveness']
        amount = base_amount * (0.8 + (hash(self.bot_id + 'amount') % 40) / 100.0)  # ±20% variation
        
        # Add small random factor to decision (5% chance to ignore signal)
        if random.random() < 0.05:
            return {'action': 'hold', 'amount': 0.0}
        
        if short_ma > long_ma * (1.0 + threshold):
            return {'action': 'buy', 'amount': amount}
        elif short_ma < long_ma * (1.0 - threshold):
            return {'action': 'sell', 'amount': amount}
        
        return {'action': 'hold', 'amount': 0.0}
    
    def _analyze_mean_reversion(self, coins: List[float], current_price: float) -> Dict:
        """Mean reversion trading strategy with bot-specific variation"""
        # Bot-specific lookback window variation
        base_lookback = self.parameters['lookback_window']
        lookback = max(5, int(base_lookback * (0.8 + (hash(self.bot_id + 'lookback') % 40) / 100.0)))
        
        prices = coins[-lookback:] if len(coins) >= lookback else coins
        
        if len(prices) < 2:
            return {'action': 'hold', 'amount': 0.0}
        
        mean_price = sum(prices) / len(prices)
        variance = sum((p - mean_price) ** 2 for p in prices) / len(prices)
        std_dev = math.sqrt(variance) if variance > 0 else 0
        
        z_score = (current_price - mean_price) / std_dev if std_dev > 0 else 0
        
        # Bot-specific threshold variation (1.2 to 1.8 instead of fixed 1.5)
        base_threshold = self.parameters['std_threshold']
        threshold = base_threshold * (0.8 + (hash(self.bot_id + 'threshold') % 40) / 100.0)
        
        # Bot-specific amount variation
        base_amount = self.parameters['trade_size']
        amount = base_amount * (0.7 + (hash(self.bot_id + 'amount') % 60) / 100.0)  # ±30% variation
        
        # Add small random factor (3% chance to ignore signal)
        if random.random() < 0.03:
            return {'action': 'hold', 'amount': 0.0}
        
        if z_score > threshold:
            return {'action': 'sell', 'amount': amount}
        elif z_score < -threshold:
            return {'action': 'buy', 'amount': amount}
        
        return {'action': 'hold', 'amount': 0.0}
    
    def _analyze_market_maker(self, current_price: float) -> Dict:
        """Market maker strategy with bot-specific variation"""
        total_value = self.usd + (self.bc * current_price)
        if total_value == 0:
            return {'action': 'hold', 'amount': 0.0}
        
        bc_value = self.bc * current_price
        current_ratio = bc_value / total_value
        
        # Bot-specific target ratio variation (0.4 to 0.6 instead of fixed 0.5)
        base_target = self.parameters['target_bc_ratio']
        target_ratio = base_target * (0.8 + (hash(self.bot_id + 'target') % 40) / 100.0)
        
        # Bot-specific threshold variation (0.08 to 0.12 instead of fixed 0.1)
        base_threshold = self.parameters['rebalance_threshold']
        threshold = base_threshold * (0.8 + (hash(self.bot_id + 'threshold') % 40) / 100.0)
        
        # Bot-specific trade size variation
        base_size = self.parameters['trade_size']
        amount = base_size * (0.6 + (hash(self.bot_id + 'size') % 80) / 100.0)  # ±40% variation
        
        # Add small random factor (5% chance to skip rebalancing)
        if random.random() < 0.05:
            return {'action': 'hold', 'amount': 0.0}
        
        if current_ratio < target_ratio - threshold:
            return {'action': 'buy', 'amount': amount}
        elif current_ratio > target_ratio + threshold:
            return {'action': 'sell', 'amount': amount}
        
        return {'action': 'hold', 'amount': 0.0}
    
    def _analyze_hedger(self, coins: List[float], current_price: float) -> Dict:
        """Hedging strategy with bot-specific variation"""
        if len(coins) < 2:
            return {'action': 'hold', 'amount': 0.0}
        
        # Bot-specific volatility calculation window
        base_window = 10
        vol_window = max(5, int(base_window * (0.7 + (hash(self.bot_id + 'window') % 60) / 100.0)))
        
        recent_prices = coins[-vol_window:] if len(coins) >= vol_window else coins
        returns = [(recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1] 
                  for i in range(1, len(recent_prices)) if recent_prices[i-1] > 0]
        
        if not returns:
            return {'action': 'hold', 'amount': 0.0}
        
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        volatility = math.sqrt(variance) if variance > 0 else 0
        
        total_value = self.usd + (self.bc * current_price)
        if total_value == 0:
            return {'action': 'hold', 'amount': 0.0}
        
        bc_value = self.bc * current_price
        current_ratio = bc_value / total_value
        
        # Bot-specific volatility threshold variation (0.04 to 0.06 instead of fixed 0.05)
        base_threshold = self.parameters['volatility_threshold']
        vol_threshold = base_threshold * (0.8 + (hash(self.bot_id + 'vol_threshold') % 40) / 100.0)
        
        # Bot-specific ratio targets variation
        if volatility > vol_threshold:
            base_high = self.parameters['high_vol_ratio']
            target_ratio = base_high * (0.8 + (hash(self.bot_id + 'high_vol') % 40) / 100.0)
        else:
            base_low = self.parameters['low_vol_ratio']
            target_ratio = base_low * (0.8 + (hash(self.bot_id + 'low_vol') % 40) / 100.0)
        
        # Bot-specific rebalance threshold (0.08 to 0.12 instead of fixed 0.1)
        rebalance_threshold = 0.1 * (0.8 + (hash(self.bot_id + 'rebalance') % 40) / 100.0)
        
        # Bot-specific trade size variation
        base_size = self.parameters['trade_size']
        amount = base_size * (0.7 + (hash(self.bot_id + 'size') % 60) / 100.0)  # ±30% variation
        
        # Add small random factor (4% chance to ignore signal)
        if random.random() < 0.04:
            return {'action': 'hold', 'amount': 0.0}
        
        if current_ratio < target_ratio - rebalance_threshold:
            return {'action': 'buy', 'amount': amount}
        elif current_ratio > target_ratio + rebalance_threshold:
            return {'action': 'sell', 'amount': amount}
        
        return {'action': 'hold', 'amount': 0.0}
    
    def buy(self, amount: float, price: float, game_data: Dict, user_id: Optional[str] = None) -> bool:
        """
        Execute buy trade
        
        Args:
            amount: Amount of BC to buy
            price: Price per BC
            game_data: Game room data dict (will be modified)
            user_id: Owner user ID (if applicable)
        
        Returns:
            True if successful, False otherwise
        """
        cost = amount * price
        
        # Check if bot has enough USD
        if self.usd < cost:
            return False
        
        # Update bot wallet
        self.usd -= cost
        self.bc += amount
        
        # Update game totals (market supplies) - convert from string if needed
        total_bc = float(game_data.get('totalBc', 0.0))
        total_usd = float(game_data.get('totalUsd', 0.0))
        game_data['totalBc'] = total_bc - amount
        game_data['totalUsd'] = total_usd + cost
        
        # Update user wallet if user_id is provided
        if user_id and 'players' in game_data:
            for player in game_data['players']:
                # Check both userId and playerId for compatibility
                player_id = player.get('userId') or player.get('playerId')
                if player_id == user_id:
                    # Bot's earnings go to the user (update both field name conventions)
                    if 'coins' in player:
                        player['coins'] = player.get('coins', 0.0) + amount
                    if 'coinBalance' in player:
                        player['coinBalance'] = player.get('coinBalance', 0.0) + amount
                    if 'usd' in player:
                        player['usd'] = player.get('usd', 0.0) - cost
                    if 'usdBalance' in player:
                        player['usdBalance'] = player.get('usdBalance', 0.0) - cost
                    break
        
        # Append to interactions
        if 'interactions' not in game_data:
            game_data['interactions'] = []
        
        game_data['interactions'].append({
            'name': f'Bot_{self.bot_id[:8]}',
            'type': 'buy',
            'value': int(amount * 100)  # Store as integer (cents equivalent)
        })
        
        return True
    
    def sell(self, amount: float, price: float, game_data: Dict, user_id: Optional[str] = None) -> bool:
        """
        Execute sell trade
        
        Args:
            amount: Amount of BC to sell
            price: Price per BC
            game_data: Game room data dict (will be modified)
            user_id: Owner user ID (if applicable)
        
        Returns:
            True if successful, False otherwise
        """
        # Check if bot has enough BC
        if self.bc < amount:
            return False
        
        revenue = amount * price
        
        # Update bot wallet
        self.bc -= amount
        self.usd += revenue
        
        # Update game totals (market supplies) - convert from string if needed
        total_bc = float(game_data.get('totalBc', 0.0))
        total_usd = float(game_data.get('totalUsd', 0.0))
        game_data['totalBc'] = total_bc + amount
        game_data['totalUsd'] = total_usd - revenue
        
        # Update user wallet if user_id is provided
        if user_id and 'players' in game_data:
            for player in game_data['players']:
                # Check both userId and playerId for compatibility
                player_id = player.get('userId') or player.get('playerId')
                if player_id == user_id:
                    # Bot's earnings go to the user (update both field name conventions)
                    if 'coins' in player:
                        player['coins'] = player.get('coins', 0.0) - amount
                    if 'coinBalance' in player:
                        player['coinBalance'] = player.get('coinBalance', 0.0) - amount
                    if 'usd' in player:
                        player['usd'] = player.get('usd', 0.0) + revenue
                    if 'usdBalance' in player:
                        player['usdBalance'] = player.get('usdBalance', 0.0) + revenue
                    break
        
        # Append to interactions
        if 'interactions' not in game_data:
            game_data['interactions'] = []
        
        game_data['interactions'].append({
            'name': f'Bot_{self.bot_id[:8]}',
            'type': 'sell',
            'value': int(amount * 100)  # Store as integer (cents equivalent)
        })
        
        return True
    
    def save_to_redis(self, game_id: str):
        """Save bot data to Redis"""
        try:
            r = get_redis_connection()
            
            bot_key = f"bot:{game_id}:{self.bot_id}"
            bot_data = {
                'bot_id': self.bot_id,
                'is_toggled': str(self.is_toggled),
                'usd_given': str(self.usd_given),
                'usd': str(self.usd),
                'bc': str(self.bc),
                'bot_type': self.bot_type,
                'behavior_coefficient': str(self.behavior_coefficient),
                'parameters': json.dumps(self.parameters),
                'user_id': self.user_id or ''
            }
            r.hset(bot_key, mapping=bot_data)
            
            # Add to game's bot set
            bots_set_key = f"bots:{game_id}"
            r.sadd(bots_set_key, self.bot_id)
            
        except Exception as e:
            print(f"Warning: Failed to save bot {self.bot_id} to Redis: {e}")
    
    @classmethod
    def load_from_redis(cls, game_id: str, bot_id: str) -> Optional['Bot']:
        """Load bot from Redis"""
        try:
            r = get_redis_connection()
            
            bot_key = f"bot:{game_id}:{bot_id}"
            if not r.exists(bot_key):
                return None
            
            bot_data = r.hgetall(bot_key)
            if not bot_data:
                return None
            
            is_toggled = bot_data.get('is_toggled', 'True').lower() == 'true'
            
            # Load behavior_coefficient if present, otherwise will be generated
            behavior_coefficient = None
            if 'behavior_coefficient' in bot_data:
                try:
                    behavior_coefficient = float(bot_data['behavior_coefficient'])
                except (ValueError, TypeError):
                    behavior_coefficient = None
            
            parameters = {}
            if 'parameters' in bot_data:
                try:
                    parameters = json.loads(bot_data['parameters'])
                except (json.JSONDecodeError, TypeError):
                    parameters = {}
            
            bot = cls(
                bot_id=bot_data.get('bot_id', bot_id),
                is_toggled=is_toggled,
                usd_given=float(bot_data.get('usd_given', 0)),
                usd=float(bot_data.get('usd', 0)),
                bc=float(bot_data.get('bc', 0)),
                bot_type=bot_data.get('bot_type', 'random'),
                behavior_coefficient=behavior_coefficient,
                user_id=bot_data.get('user_id', '')
            )
            bot.parameters = parameters
            
            return bot
            
        except Exception as e:
            print(f"Error loading bot {bot_id} from Redis: {e}")
            return None
    
    def remove_from_redis(self, game_id: str):
        """Remove bot data from Redis"""
        try:
            r = get_redis_connection()
            
            bot_key = f"bot:{game_id}:{self.bot_id}"
            r.delete(bot_key)
            
            bots_set_key = f"bots:{game_id}"
            r.srem(bots_set_key, self.bot_id)
            
        except Exception as e:
            print(f"Warning: Failed to remove bot {self.bot_id} from Redis: {e}")
    
    def run(self, game_id: str, update_interval: float = 1.0):
        """
        Main bot trading loop. Continuously monitors coin prices, makes trading decisions,
        and updates the bot's wallet. Runs throughout the game until bot is toggled off.
        
        Args:
            game_id: Game ID where the bot operates
            update_interval: Time in seconds between trading decisions (default: 1.0)
        """
        import time
        
        print(f"Bot {self.bot_id} started running in game {game_id}")
        
        while True:
            try:
                # Reload toggle state from Redis every iteration
                r = get_redis_connection()
                bot_key = f"bot:{game_id}:{self.bot_id}"
                if r.exists(bot_key):
                    bot_data = r.hgetall(bot_key)
                    # Python stores True/False, Redis returns as string "True" or "False"
                    is_toggled_str = bot_data.get('is_toggled', 'True')
                    self.is_toggled = (is_toggled_str == 'True' or is_toggled_str == 'true' or is_toggled_str == '1')
                    
                    if not self.is_toggled:
                        # Bot is OFF - sleep and continue checking
                        time.sleep(update_interval)
                        continue
                else:
                    # Bot removed, exit
                    print(f"Bot {self.bot_id} removed, stopping")
                    break
                
                # Get real-time access to coins (price history)
                coins = self._get_coins_from_redis(game_id)
                if not coins:
                    time.sleep(update_interval)
                    continue
                
                current_price = coins[-1] if coins else 1.0
                
                # Make trading decision based on trend
                decision = self.analyze(coins, current_price)
                
                # Execute trade if decision is not 'hold'
                if decision['action'] != 'hold' and decision['amount'] > 0:
                    # Load game data for trade execution
                    game_data = self._get_game_data_from_redis(game_id)
                    if game_data:
                        success = False
                        if decision['action'] == 'buy':
                            success = self.buy(decision['amount'], current_price, game_data, self.user_id)
                        elif decision['action'] == 'sell':
                            success = self.sell(decision['amount'], current_price, game_data, self.user_id)
                        
                        if success:
                            # Save updated bot state to Redis
                            self.save_to_redis(game_id)
                            
                            # Save updated game data back to Redis
                            self._save_game_data_to_redis(game_id, game_data)
                            
                            print(f"Bot {self.bot_id} executed {decision['action']} of {decision['amount']} BC at {current_price}")
                
                # Update coin value (this happens automatically via market updates,
                # but we ensure bot state is saved)
                self.save_to_redis(game_id)
                
                # Sleep before next iteration
                time.sleep(update_interval)
                
            except Exception as e:
                print(f"Error in Bot.run() for {self.bot_id}: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(update_interval)
    
    def _get_coins_from_redis(self, game_id: str) -> List[float]:
        """
        Get current coin price history from Redis.
        Tries to get from market data first, then falls back to game data.
        
        Args:
            game_id: Game ID
            
        Returns:
            List of coin prices (price history)
        """
        try:
            r = get_redis_connection()
            
            # Try to get from market data first
            market_data_key = f"market:{game_id}:data"
            if r.exists(market_data_key):
                market_data = r.hgetall(market_data_key)
                if 'price_history' in market_data:
                    price_history = json.loads(market_data['price_history'])
                    return price_history
            
            # Fall back to game data
            game_key = f"game:{game_id}"
            if r.exists(game_key):
                game_data = r.hgetall(game_key)
                
                # Check for coinPrice (single value) or coins (array)
                if 'coins' in game_data:
                    coins_str = game_data['coins']
                    if isinstance(coins_str, str):
                        coins = json.loads(coins_str)
                    else:
                        coins = coins_str
                    if isinstance(coins, list):
                        return [float(c) for c in coins]
                
                # If only coinPrice exists, return it as a single-item list
                if 'coinPrice' in game_data:
                    coin_price = float(game_data['coinPrice'])
                    return [coin_price]
            
            return []
            
        except Exception as e:
            print(f"Error getting coins from Redis: {e}")
            return []
    
    def _get_game_data_from_redis(self, game_id: str) -> Optional[Dict]:
        """
        Get game data from Redis for trade execution.
        
        Args:
            game_id: Game ID
            
        Returns:
            Game data dictionary or None
        """
        try:
            r = get_redis_connection()
            game_key = f"game:{game_id}"
            
            if not r.exists(game_key):
                return None
            
            game_data = r.hgetall(game_key)
            
            # Parse JSON fields
            if 'players' in game_data:
                game_data['players'] = json.loads(game_data['players'])
            
            if 'interactions' in game_data:
                try:
                    game_data['interactions'] = json.loads(game_data['interactions'])
                except:
                    game_data['interactions'] = []
            else:
                game_data['interactions'] = []
            
            # Ensure totalBc and totalUsd exist
            if 'totalBc' not in game_data:
                game_data['totalBc'] = 0.0
            else:
                game_data['totalBc'] = float(game_data['totalBc'])
            
            if 'totalUsd' not in game_data:
                game_data['totalUsd'] = 0.0
            else:
                game_data['totalUsd'] = float(game_data['totalUsd'])
            
            return game_data
            
        except Exception as e:
            print(f"Error getting game data from Redis: {e}")
            return None
    
    def _save_game_data_to_redis(self, game_id: str, game_data: Dict):
        """
        Save updated game data back to Redis.
        
        Args:
            game_id: Game ID
            game_data: Updated game data dictionary
        """
        try:
            r = get_redis_connection()
            game_key = f"game:{game_id}"
            
            # Serialize JSON fields
            if 'players' in game_data:
                game_data['players'] = json.dumps(game_data['players'])
            
            if 'interactions' in game_data:
                game_data['interactions'] = json.dumps(game_data['interactions'])
            
            # Convert numeric fields to strings for Redis
            update_data = {}
            for key, value in game_data.items():
                if isinstance(value, (int, float)):
                    update_data[key] = str(value)
                elif isinstance(value, (list, dict)):
                    update_data[key] = json.dumps(value) if not isinstance(value, str) else value
                else:
                    update_data[key] = str(value)
            
            r.hset(game_key, mapping=update_data)
            
        except Exception as e:
            print(f"Error saving game data to Redis: {e}")
    
    def to_dict(self) -> Dict:
        """
        Convert bot to dictionary format matching Redis room structure
        
        Returns:
            Dictionary matching the bot structure in the Redis room data:
            {
                'botId': string,
                'botName': string,
                'startingUsdBalance': float,
                'usdBalance': float,
                'coinBalance': float,
                'isActive': boolean
            }
        """
        return {
            'botId': self.bot_id,
            'botName': self.bot_type,
            'startingUsdBalance': self.usd_given,
            'usdBalance': self.usd,
            'coinBalance': self.bc,
            'isActive': self.is_toggled
        }
