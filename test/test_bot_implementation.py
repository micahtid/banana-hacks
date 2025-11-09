"""
Test Bot Implementation
Tests bot trading strategies, execution, and market interaction.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'back-end'))

import unittest
import json
from bot import Bot
from redis_helper import get_redis_connection
import uuid


class TestBotImplementation(unittest.TestCase):
    """Test bot implementation and trading logic"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.game_id = f"test_game_{uuid.uuid4().hex[:8]}"
        self.user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        self.r = get_redis_connection()
        
        # Create test game
        game_data = {
            'gameId': self.game_id,
            'isStarted': 'true',
            'players': json.dumps([{
                'userId': self.user_id,
                'userName': 'Test User',
                'usd': 10000.0,
                'coins': 0.0,
                'bots': []
            }]),
            'totalBc': 100000.0,
            'totalUsd': 100000.0
        }
        self.r.hset(f"game:{self.game_id}", mapping=game_data)
        
        # Create market data with price history
        market_data = {
            'price_history': json.dumps([1.0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3])
        }
        self.r.hset(f"market:{self.game_id}:data", mapping=market_data)
    
    def tearDown(self):
        """Clean up test data"""
        self.r.delete(f"game:{self.game_id}")
        self.r.delete(f"market:{self.game_id}:data")
        
        bots_set_key = f"bots:{self.game_id}"
        bot_ids = self.r.smembers(bots_set_key)
        for bot_id_bytes in bot_ids:
            bot_id = bot_id_bytes.decode('utf-8') if isinstance(bot_id_bytes, bytes) else bot_id_bytes
            self.r.delete(f"bot:{self.game_id}:{bot_id}")
        self.r.delete(bots_set_key)
    
    def test_bot_initialization(self):
        """Test bot initializes with correct parameters"""
        bot = Bot(
            bot_id=None,
            is_toggled=True,
            usd_given=1000.0,
            usd=1000.0,
            bc=0.0,
            bot_type='momentum',
            user_id=self.user_id
        )
        
        self.assertIsNotNone(bot.bot_id)
        self.assertTrue(bot.is_toggled)
        self.assertEqual(bot.usd, 1000.0)
        self.assertEqual(bot.bc, 0.0)
        self.assertEqual(bot.bot_type, 'momentum')
        self.assertEqual(bot.user_id, self.user_id)
        print(f"[PASS] Bot initialized correctly with type: {bot.bot_type}")
    
    def test_bot_strategies_exist(self):
        """Test all bot strategies are implemented"""
        strategies = ['random', 'momentum', 'mean_reversion', 'market_maker', 'hedger']
        
        for strategy in strategies:
            bot = Bot(bot_type=strategy, usd=1000.0, bc=50.0, user_id=self.user_id)
            
            # Test that analyze returns valid decision
            price_history = [1.0, 1.1, 1.05, 1.15, 1.2]
            decision = bot.analyze(price_history, 1.2)
            
            self.assertIn('action', decision)
            self.assertIn('amount', decision)
            self.assertIn(decision['action'], ['buy', 'sell', 'hold'])
            self.assertGreaterEqual(decision['amount'], 0.0)
            
        print(f"[PASS] All {len(strategies)} bot strategies implemented correctly")
    
    def test_bot_buy_trade(self):
        """Test bot can execute buy trades"""
        bot = Bot(
            bot_id=None,
            is_toggled=True,
            usd_given=1000.0,
            usd=1000.0,
            bc=0.0,
            bot_type='random',
            user_id=self.user_id
        )
        
        game_data = self.r.hgetall(f"game:{self.game_id}")
        players = json.loads(game_data['players'])
        
        trade_data = {
            'totalBc': 100000.0,
            'totalUsd': 100000.0,
            'players': players,
            'interactions': []
        }
        
        initial_bot_usd = bot.usd
        initial_bot_bc = bot.bc
        
        amount = 10.0
        price = 1.5
        success = bot.buy(amount, price, trade_data, bot.user_id)
        
        self.assertTrue(success)
        self.assertEqual(bot.usd, initial_bot_usd - (amount * price))
        self.assertEqual(bot.bc, initial_bot_bc + amount)
        self.assertEqual(trade_data['totalBc'], 100000.0 - amount)
        self.assertEqual(trade_data['totalUsd'], 100000.0 + (amount * price))
        print(f"[PASS] Bot buy trade executed: {amount} BC @ ${price} = ${amount * price}")
    
    def test_bot_sell_trade(self):
        """Test bot can execute sell trades"""
        bot = Bot(
            bot_id=None,
            is_toggled=True,
            usd_given=1000.0,
            usd=500.0,
            bc=50.0,
            bot_type='random',
            user_id=self.user_id
        )
        
        game_data = self.r.hgetall(f"game:{self.game_id}")
        players = json.loads(game_data['players'])
        
        trade_data = {
            'totalBc': 100000.0,
            'totalUsd': 100000.0,
            'players': players,
            'interactions': []
        }
        
        initial_bot_usd = bot.usd
        initial_bot_bc = bot.bc
        
        amount = 10.0
        price = 1.8
        success = bot.sell(amount, price, trade_data, bot.user_id)
        
        self.assertTrue(success)
        self.assertEqual(bot.usd, initial_bot_usd + (amount * price))
        self.assertEqual(bot.bc, initial_bot_bc - amount)
        self.assertEqual(trade_data['totalBc'], 100000.0 + amount)
        self.assertEqual(trade_data['totalUsd'], 100000.0 - (amount * price))
        print(f"[PASS] Bot sell trade executed: {amount} BC @ ${price} = ${amount * price}")
    
    def test_bot_insufficient_funds(self):
        """Test bot cannot trade with insufficient funds"""
        bot = Bot(
            bot_id=None,
            is_toggled=True,
            usd_given=100.0,
            usd=10.0,  # Only $10
            bc=0.0,
            bot_type='random',
            user_id=self.user_id
        )
        
        game_data = self.r.hgetall(f"game:{self.game_id}")
        players = json.loads(game_data['players'])
        
        trade_data = {
            'totalBc': 100000.0,
            'totalUsd': 100000.0,
            'players': players,
            'interactions': []
        }
        
        # Try to buy more than bot can afford
        amount = 100.0  # Would cost $150 at $1.5
        price = 1.5
        success = bot.buy(amount, price, trade_data, bot.user_id)
        
        self.assertFalse(success)
        self.assertEqual(bot.usd, 10.0)  # Unchanged
        self.assertEqual(bot.bc, 0.0)  # Unchanged
        print(f"[PASS] Bot correctly rejected trade with insufficient funds")
    
    def test_bot_insufficient_bc(self):
        """Test bot cannot sell BC it doesn't have"""
        bot = Bot(
            bot_id=None,
            is_toggled=True,
            usd_given=1000.0,
            usd=1000.0,
            bc=5.0,  # Only 5 BC
            bot_type='random',
            user_id=self.user_id
        )
        
        game_data = self.r.hgetall(f"game:{self.game_id}")
        players = json.loads(game_data['players'])
        
        trade_data = {
            'totalBc': 100000.0,
            'totalUsd': 100000.0,
            'players': players,
            'interactions': []
        }
        
        # Try to sell more BC than bot has
        amount = 10.0
        price = 1.5
        success = bot.sell(amount, price, trade_data, bot.user_id)
        
        self.assertFalse(success)
        self.assertEqual(bot.bc, 5.0)  # Unchanged
        print(f"[PASS] Bot correctly rejected sell with insufficient BC")
    
    def test_bot_saves_to_redis(self):
        """Test bot can save state to Redis"""
        bot = Bot(
            bot_id=None,
            is_toggled=True,
            usd_given=1000.0,
            usd=800.0,
            bc=25.0,
            bot_type='momentum',
            user_id=self.user_id
        )
        
        bot.save_to_redis(self.game_id)
        
        # Load bot from Redis
        loaded_bot = Bot.load_from_redis(self.game_id, bot.bot_id)
        
        self.assertIsNotNone(loaded_bot)
        self.assertEqual(loaded_bot.bot_id, bot.bot_id)
        self.assertEqual(loaded_bot.usd, bot.usd)
        self.assertEqual(loaded_bot.bc, bot.bc)
        self.assertEqual(loaded_bot.bot_type, bot.bot_type)
        self.assertEqual(loaded_bot.user_id, bot.user_id)
        print(f"[PASS] Bot state persisted to Redis and loaded correctly")
    
    def test_bot_to_dict(self):
        """Test bot serialization to dict"""
        bot = Bot(
            bot_id='test_bot_123',
            is_toggled=True,
            usd_given=1000.0,
            usd=800.0,
            bc=25.0,
            bot_type='momentum',
            user_id=self.user_id
        )
        
        bot_dict = bot.to_dict()
        
        self.assertEqual(bot_dict['botId'], 'test_bot_123')
        self.assertEqual(bot_dict['botName'], 'momentum')
        self.assertEqual(bot_dict['startingUsdBalance'], 1000.0)
        self.assertEqual(bot_dict['usdBalance'], 800.0)
        self.assertEqual(bot_dict['coinBalance'], 25.0)
        self.assertTrue(bot_dict['isActive'])
        print(f"[PASS] Bot serialized to dict correctly")
    
    def test_momentum_strategy_analysis(self):
        """Test momentum strategy produces valid decisions"""
        bot = Bot(bot_type='momentum', usd=1000.0, bc=50.0, user_id=self.user_id)
        
        # Upward trend
        upward_trend = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
        decision = bot.analyze(upward_trend, 1.5)
        
        self.assertIn(decision['action'], ['buy', 'sell', 'hold'])
        print(f"[PASS] Momentum strategy on upward trend: {decision['action']}")
        
        # Downward trend
        downward_trend = [1.5, 1.4, 1.3, 1.2, 1.1, 1.0]
        decision = bot.analyze(downward_trend, 1.0)
        
        self.assertIn(decision['action'], ['buy', 'sell', 'hold'])
        print(f"[PASS] Momentum strategy on downward trend: {decision['action']}")
    
    def test_mean_reversion_strategy_analysis(self):
        """Test mean reversion strategy produces valid decisions"""
        bot = Bot(bot_type='mean_reversion', usd=1000.0, bc=50.0, user_id=self.user_id)
        
        # Price history with mean around 1.0
        price_history = [1.0, 0.95, 1.05, 1.0, 0.98, 1.02]
        
        # Test high price (should tend to sell)
        decision_high = bot.analyze(price_history, 1.5)
        self.assertIn(decision_high['action'], ['buy', 'sell', 'hold'])
        
        # Test low price (should tend to buy)
        decision_low = bot.analyze(price_history, 0.5)
        self.assertIn(decision_low['action'], ['buy', 'sell', 'hold'])
        
        print(f"[PASS] Mean reversion strategy: high price -> {decision_high['action']}, low price -> {decision_low['action']}")
    
    def test_market_maker_strategy_analysis(self):
        """Test market maker strategy produces valid decisions"""
        bot = Bot(bot_type='market_maker', usd=1000.0, bc=50.0, user_id=self.user_id)
        
        price_history = [1.0, 1.1, 1.2]
        decision = bot.analyze(price_history, 1.2)
        
        self.assertIn(decision['action'], ['buy', 'sell', 'hold'])
        self.assertGreaterEqual(decision['amount'], 0.0)
        print(f"[PASS] Market maker strategy: {decision['action']}")
    
    def test_bot_behavior_coefficient_uniqueness(self):
        """Test that bots have unique behavior coefficients"""
        bot1 = Bot(bot_type='random', usd=1000.0, bc=0.0, user_id=self.user_id)
        bot2 = Bot(bot_type='random', usd=1000.0, bc=0.0, user_id=self.user_id)
        
        # Different bots should have different behavior coefficients
        self.assertNotEqual(bot1.behavior_coefficient, bot2.behavior_coefficient)
        
        # Coefficients should be in valid range (0.8 to 1.2)
        self.assertGreaterEqual(bot1.behavior_coefficient, 0.8)
        self.assertLessEqual(bot1.behavior_coefficient, 1.2)
        self.assertGreaterEqual(bot2.behavior_coefficient, 0.8)
        self.assertLessEqual(bot2.behavior_coefficient, 1.2)
        
        print(f"[PASS] Bots have unique behavior coefficients: {bot1.behavior_coefficient:.3f}, {bot2.behavior_coefficient:.3f}")


if __name__ == '__main__':
    print("=" * 70)
    print("TESTING BOT IMPLEMENTATION")
    print("=" * 70)
    unittest.main(verbosity=2)

