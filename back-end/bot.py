import random
import math
from typing import List, Dict, Optional
from dataclasses import dataclass
import uuid
import json
import re
import os
from redis_helper import get_redis_connection
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# ============================================================================
# GEMINI STRATEGY GENERATOR
# ============================================================================

def generate_custom_bot_strategy(user_prompt: str) -> str:
    """
    Use Gemini 2.5 Pro to generate a custom trading strategy function based on user's prompt.
    
    Args:
        user_prompt: User's description of the trading strategy they want
        
    Returns:
        String containing executable Python code that implements the strategy.
        The code should define a function that takes coins (list of prices) and 
        current_price (float) as parameters and returns {'action': action, 'amount': amount}
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    
    client = genai.Client(api_key=api_key)
    
    system_prompt = """You are an expert Python developer creating trading bot strategies.
Generate ONLY executable Python code with NO explanations, NO markdown formatting, NO code fences.

The code must:
1. Define a function named 'custom_strategy' that takes two parameters:
   - coins: List[float] - historical price data
   - current_price: float - current coin price
2. Return a dictionary with two keys:
   - 'action': str - must be 'buy', 'sell', or 'hold'
   - 'amount': float - amount of coins to trade (0 for hold)
3. DO NOT include import statements - math and random modules are already available
4. Be safe to execute (no file I/O, no network calls, no system commands)
5. Handle edge cases (empty list, single price, etc.)
6. Use reasonable trading amounts (100.0 to 600.0 coins) - bots have significant capital and trade in large volumes
7. ALWAYS return a valid dictionary - never return None

Example structure:
def custom_strategy(coins, current_price):
    if len(coins) < 2:
        return {'action': 'hold', 'amount': 0.0}
    # Use math.sqrt(), random.random(), etc. directly - no imports needed
    avg = sum(coins) / len(coins)
    if current_price > avg * 1.05:
        return {'action': 'buy', 'amount': 200.0}
    return {'action': 'hold', 'amount': 0.0}
"""
    
    user_request = f"""Create a trading bot strategy based on this description:
{user_prompt}

Remember: Output ONLY the Python code, nothing else."""
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=user_request,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7,
                max_output_tokens=1000,
            )
        )
        
        code = response.text.strip()
        
        # Remove markdown code fences if present
        if code.startswith("```python"):
            code = code[9:]
        elif code.startswith("```"):
            code = code[3:]
        if code.endswith("```"):
            code = code[:-3]
        
        code = code.strip()
        
        # Validate the code has the required function
        if "def custom_strategy" not in code:
            raise ValueError("Generated code does not contain 'custom_strategy' function")
        
        # Test the generated code to ensure it returns valid results
        try:
            test_globals = {
                '__builtins__': {
                    'len': len, 'sum': sum, 'abs': abs, 'min': min, 'max': max,
                    'range': range, 'float': float, 'int': int, 'str': str,
                    'bool': bool, 'list': list, 'dict': dict, 'enumerate': enumerate,
                    'zip': zip, 'True': True, 'False': False, 'None': None,
                },
                'math': math,
                'random': random,
            }
            exec(code, test_globals)
            
            if 'custom_strategy' not in test_globals:
                raise ValueError("Function not defined after execution")
            
            # Test with sample data
            test_result = test_globals['custom_strategy']([1.0, 1.1, 1.05], 1.08)
            
            # Validate the result
            if not isinstance(test_result, dict):
                raise ValueError(f"Strategy returned {type(test_result)}, expected dict")
            
            if 'action' not in test_result or 'amount' not in test_result:
                raise ValueError(f"Strategy missing required keys. Got: {test_result.keys()}")
            
            if test_result['action'] not in ['buy', 'sell', 'hold']:
                raise ValueError(f"Invalid action: {test_result['action']}")
            
            if test_result is None:
                raise ValueError("Strategy returned None")
            
            print(f"Custom strategy validated successfully. Test result: {test_result}")
            
        except Exception as e:
            print(f"Generated code failed validation: {e}")
            raise ValueError(f"Generated code failed validation: {e}")
        
        return code
        
    except Exception as e:
        print(f"Error generating custom bot strategy: {e}")
        # Return a safe default strategy
        return """def custom_strategy(coins, current_price):
    if len(coins) < 2:
        return {'action': 'hold', 'amount': 0.0}
    if random.random() > 0.5:
        return {'action': 'buy', 'amount': 200.0}
    else:
        return {'action': 'sell', 'amount': 200.0}
"""


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
                 behavior_coefficient: Optional[float] = None, user_id: Optional[str] = None,
                 custom_strategy_code: Optional[str] = None, bot_name: Optional[str] = None):
        """
        Initialize a bot
        
        Args:
            bot_id: Unique bot identifier (generated if not provided)
            is_toggled: Boolean indicating if bot is on/off
            usd_given: Initial USD capital given to the bot (startingBalance in Redis)
            usd: Current USD balance in bot's wallet (balance in Redis)
            bc: Current BC (Banana Coin) balance in bot's wallet (not in Redis structure, but needed for trading)
            bot_type: Type of bot strategy (random, momentum, mean_reversion, market_maker, hedger, custom)
            behavior_coefficient: Bot's behavior coefficient (0.8-1.2). If None, generated from bot_id
            user_id: Owner user ID
            custom_strategy_code: Python code for custom strategy (only used when bot_type='custom')
            bot_name: Display name for the bot (e.g., 'HODL Master')
        """
        self.bot_id = bot_id or str(uuid.uuid4())
        self.is_toggled = is_toggled
        self.usd_given = usd_given
        self.usd = usd
        self.bc = bc
        self.bot_type = bot_type or 'random'
        self.user_id = user_id
        self.custom_strategy_code = custom_strategy_code
        self.bot_name = bot_name or f'Bot_{self.bot_id[:8]}'  # Use provided name or generate default
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
                'min_trade': 2.0,  # 20x increase (was 2.0)
                'max_trade': 60.0,  # 20x increase (was 10.0)
                'trade_probability': 0.3
            },
            'momentum': {
                'short_window': 5,
                'long_window': 20,
                'trade_size': 40.0,  # 20x increase (was 8.0)
                'aggressiveness': 1.0
            },
            'mean_reversion': {
                'lookback_window': 20,
                'std_threshold': 1.5,
                'trade_size': 50.0  # 20x increase (was 10.0)
            },
            'market_maker': {
                'target_bc_ratio': 0.5,
                'rebalance_threshold': 0.1,
                'trade_size': 30.0  # 20x increase (was 6.0)
            },
            'hedger': {
                'volatility_threshold': 0.05,
                'low_vol_ratio': 0.7,
                'high_vol_ratio': 0.3,
                'trade_size': 40.0  # 20x increase (was 8.0)
            }
        }
        return defaults.get(self.bot_type, defaults['random'])
    
    def _scale_trade_amount(self, base_amount: float, current_price: float, action: str) -> float:
        """
        Scale trade amount based on bot's available capital.
        For buys: scale based on available USD (use up to 20% of USD per trade)
        For sells: scale based on available BC (use up to 20% of BC per trade)
        
        Args:
            base_amount: Base trade amount from strategy
            current_price: Current coin price
            action: 'buy' or 'sell'
        
        Returns:
            Scaled trade amount
        """
        if action == 'buy':
            # For buys, scale based on available USD
            # Use up to 20% of available USD per trade
            max_usd_to_use = self.usd * 0.2
            max_bc_from_usd = max_usd_to_use / current_price if current_price > 0 else 0
            # Use the larger of base_amount or scaled amount, but cap at what we can afford
            scaled_amount = max(base_amount, max_bc_from_usd)
            # Cap at what we can actually afford
            max_affordable = self.usd / current_price if current_price > 0 else 0
            return min(scaled_amount, max_affordable)
        elif action == 'sell':
            # For sells, scale based on available BC
            # Use up to 20% of available BC per trade
            max_bc_to_use = self.bc * 0.2
            # Use the larger of base_amount or scaled amount, but cap at what we have
            scaled_amount = max(base_amount, max_bc_to_use)
            return min(scaled_amount, self.bc)
        else:
            return base_amount
    
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
        elif self.bot_type == 'custom':
            return self._analyze_custom(coins, current_price)
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
        
        # Scale amount based on available capital (need current_price, estimate from coins if available)
        # For random bot, we'll use a simple scaling without price since we don't have it in this method
        # The scaling will happen in the run loop when we have the price
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
            # Scale buy amount based on available capital
            scaled_amount = self._scale_trade_amount(amount, current_price, 'buy')
            return {'action': 'buy', 'amount': scaled_amount}
        elif short_ma < long_ma * (1.0 - threshold):
            # Scale sell amount based on available capital
            scaled_amount = self._scale_trade_amount(amount, current_price, 'sell')
            return {'action': 'sell', 'amount': scaled_amount}
        
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
            # Scale sell amount based on available capital
            scaled_amount = self._scale_trade_amount(amount, current_price, 'sell')
            return {'action': 'sell', 'amount': scaled_amount}
        elif z_score < -threshold:
            # Scale buy amount based on available capital
            scaled_amount = self._scale_trade_amount(amount, current_price, 'buy')
            return {'action': 'buy', 'amount': scaled_amount}
        
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
            # Scale buy amount based on available capital
            scaled_amount = self._scale_trade_amount(amount, current_price, 'buy')
            return {'action': 'buy', 'amount': scaled_amount}
        elif current_ratio > target_ratio + threshold:
            # Scale sell amount based on available capital
            scaled_amount = self._scale_trade_amount(amount, current_price, 'sell')
            return {'action': 'sell', 'amount': scaled_amount}
        
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
            # Scale buy amount based on available capital
            scaled_amount = self._scale_trade_amount(amount, current_price, 'buy')
            return {'action': 'buy', 'amount': scaled_amount}
        elif current_ratio > target_ratio + rebalance_threshold:
            # Scale sell amount based on available capital
            scaled_amount = self._scale_trade_amount(amount, current_price, 'sell')
            return {'action': 'sell', 'amount': scaled_amount}
        
        return {'action': 'hold', 'amount': 0.0}
    
    def _analyze_custom(self, coins: List[float], current_price: float) -> Dict:
        """
        Execute custom strategy generated by Gemini LLM.
        
        Args:
            coins: List of historical coin prices
            current_price: Current coin price
            
        Returns:
            Dict with 'action' and 'amount' keys
        """
        if not self.custom_strategy_code:
            print(f"Warning: Bot {self.bot_id} has no custom strategy code, defaulting to hold")
            return {'action': 'hold', 'amount': 0.0}
        
        try:
            # Create a safe execution environment with pre-imported modules
            # This avoids the need for __import__ in user code
            safe_globals = {
                '__builtins__': {
                    'len': len,
                    'sum': sum,
                    'abs': abs,
                    'min': min,
                    'max': max,
                    'range': range,
                    'float': float,
                    'int': int,
                    'str': str,
                    'bool': bool,
                    'list': list,
                    'dict': dict,
                    'enumerate': enumerate,
                    'zip': zip,
                    'True': True,
                    'False': False,
                    'None': None,
                },
                'math': math,
                'random': random,
            }
            
            # Execute the custom strategy code to define the function
            exec(self.custom_strategy_code, safe_globals)
            
            # Check if the custom_strategy function was defined
            if 'custom_strategy' not in safe_globals:
                print(f"Error: custom_strategy function not found in generated code")
                return {'action': 'hold', 'amount': 0.0}
            
            # Call the custom strategy function
            result = safe_globals['custom_strategy'](coins, current_price)
            
            # Validate result format
            if not isinstance(result, dict):
                print(f"Error: custom_strategy returned non-dict: {type(result)}")
                return {'action': 'hold', 'amount': 0.0}
            
            if 'action' not in result or 'amount' not in result:
                print(f"Error: custom_strategy missing required keys: {result.keys()}")
                return {'action': 'hold', 'amount': 0.0}
            
            # Validate action
            action = result['action']
            if action not in ['buy', 'sell', 'hold']:
                print(f"Error: invalid action '{action}', defaulting to hold")
                return {'action': 'hold', 'amount': 0.0}
            
            # Validate and clamp amount
            try:
                amount = float(result['amount'])
                if amount < 0:
                    amount = 0.0
                # Clamp to reasonable range (increased to allow larger trades - 20x scale)
                amount = min(max(amount, 0.0), 1000.0)
            except (ValueError, TypeError):
                print(f"Error: invalid amount '{result['amount']}'")
                return {'action': 'hold', 'amount': 0.0}
            
            return {'action': action, 'amount': amount}
            
        except Exception as e:
            print(f"Error executing custom strategy for bot {self.bot_id}: {e}")
            import traceback
            traceback.print_exc()
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
        from transaction_history import TransactionHistory
        from datetime import datetime
        
        cost = amount * price
        
        # Check if bot has enough USD
        if self.usd < cost:
            return False
        
        # Update bot wallet - prevent negative balances
        self.usd = max(0.0, self.usd - cost)
        self.bc = max(0.0, self.bc + amount)
        
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
                    # Prevent negative balances
                    if 'coins' in player:
                        player['coins'] = max(0.0, player.get('coins', 0.0) + amount)
                    if 'coinBalance' in player:
                        player['coinBalance'] = max(0.0, player.get('coinBalance', 0.0) + amount)
                    if 'usd' in player:
                        player['usd'] = max(0.0, player.get('usd', 0.0) - cost)
                    if 'usdBalance' in player:
                        player['usdBalance'] = max(0.0, player.get('usdBalance', 0.0) - cost)
                    break
        
        # Get game_id from game_data (need to extract it)
        game_id = game_data.get('gameId', '')
        if not game_id and hasattr(self, '_current_game_id'):
            game_id = self._current_game_id
        
        # Record transaction in history
        if game_id:
            TransactionHistory.add_transaction(game_id, {
                'type': 'buy',
                'actor': self.bot_id,
                'actor_name': self.bot_name,
                'amount': amount,
                'price': price,
                'total_cost': cost,
                'timestamp': datetime.now().isoformat(),
                'is_bot': True,
                'bot_type': self.bot_type,
                'user_id': user_id
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
        from transaction_history import TransactionHistory
        from datetime import datetime
        
        # Check if bot has enough BC
        if self.bc < amount:
            return False
        
        revenue = amount * price
        
        # Update bot wallet - prevent negative balances
        self.bc = max(0.0, self.bc - amount)
        self.usd = max(0.0, self.usd + revenue)
        
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
                    # Prevent negative balances
                    if 'coins' in player:
                        player['coins'] = max(0.0, player.get('coins', 0.0) - amount)
                    if 'coinBalance' in player:
                        player['coinBalance'] = max(0.0, player.get('coinBalance', 0.0) - amount)
                    if 'usd' in player:
                        player['usd'] = max(0.0, player.get('usd', 0.0) + revenue)
                    if 'usdBalance' in player:
                        player['usdBalance'] = max(0.0, player.get('usdBalance', 0.0) + revenue)
                    break
        
        # Get game_id from game_data (need to extract it)
        game_id = game_data.get('gameId', '')
        if not game_id and hasattr(self, '_current_game_id'):
            game_id = self._current_game_id
        
        # Record transaction in history
        if game_id:
            TransactionHistory.add_transaction(game_id, {
                'type': 'sell',
                'actor': self.bot_id,
                'actor_name': self.bot_name,
                'amount': amount,
                'price': price,
                'total_cost': revenue,
                'timestamp': datetime.now().isoformat(),
                'is_bot': True,
                'bot_type': self.bot_type,
                'user_id': user_id
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
                'bot_name': self.bot_name,
                'behavior_coefficient': str(self.behavior_coefficient),
                'parameters': json.dumps(self.parameters),
                'user_id': self.user_id or '',
                'custom_strategy_code': self.custom_strategy_code or ''
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
            
            custom_strategy_code = bot_data.get('custom_strategy_code', '')
            if not custom_strategy_code:
                custom_strategy_code = None
            
            bot = cls(
                bot_id=bot_data.get('bot_id', bot_id),
                is_toggled=is_toggled,
                usd_given=float(bot_data.get('usd_given', 0)),
                usd=float(bot_data.get('usd', 0)),
                bc=float(bot_data.get('bc', 0)),
                bot_type=bot_data.get('bot_type', 'random'),
                behavior_coefficient=behavior_coefficient,
                user_id=bot_data.get('user_id', ''),
                custom_strategy_code=custom_strategy_code,
                bot_name=bot_data.get('bot_name')
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
        last_trade_time = 0
        iteration_count = 0
        
        while True:
            try:
                current_time = time.time()
                
                # Only check every update_interval seconds
                if current_time - last_trade_time < update_interval:
                    time.sleep(0.1)  # Short sleep to avoid busy waiting
                    continue
                
                last_trade_time = current_time
                iteration_count += 1
                
                # Reload toggle state from Redis
                r = get_redis_connection()
                bot_key = f"bot:{game_id}:{self.bot_id}"
                if not r.exists(bot_key):
                    # Bot removed, exit
                    print(f"Bot {self.bot_id} removed, stopping")
                    break
                
                bot_data = r.hgetall(bot_key)
                # Python stores True/False, Redis returns as string "True" or "False"
                is_toggled_str = bot_data.get('is_toggled', 'True')
                self.is_toggled = (is_toggled_str == 'True' or is_toggled_str == 'true' or is_toggled_str == '1')
                
                if not self.is_toggled:
                    # Bot is OFF - continue checking without trading
                    continue
                
                # Get real-time access to coins (price history)
                coins = self._get_coins_from_redis(game_id)
                if not coins:
                    continue
                
                current_price = coins[-1] if coins else 1.0
                
                # Make trading decision based on trend
                decision = self.analyze(coins, current_price)
                
                # Execute trade if decision is not 'hold'
                if decision['action'] != 'hold' and decision['amount'] > 0:
                    # Scale trade amount for random bot (other bots already scaled in their analyze methods)
                    if self.bot_type == 'random':
                        scaled_amount = self._scale_trade_amount(decision['amount'], current_price, decision['action'])
                        decision['amount'] = scaled_amount
                    
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
                
                # Periodically save bot state (every 5 iterations to reduce Redis writes)
                if iteration_count % 5 == 0:
                    self.save_to_redis(game_id)
                
            except Exception as e:
                print(f"Error in Bot.run() for {self.bot_id}: {e}")
                import traceback
                traceback.print_exc()
                # Short sleep on error to avoid rapid error loops
                time.sleep(0.5)
    
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
            'botName': self.bot_name,
            'startingUsdBalance': self.usd_given,
            'usdBalance': self.usd,
            'coinBalance': self.bc,
            'isActive': self.is_toggled
        }
