"""
Test Bot Ownership System
Tests that bots are properly owned by users and that trades affect the correct user's wallet.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'back-end'))

import unittest
import json


from bot import Bot
from bot_operations import buyBot, toggleBot
from redis_helper import get_redis_connection
import uuid


class TestBotOwnership(unittest.TestCase):
    """Test bot ownership functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.game_id = f"test_game_{uuid.uuid4().hex[:8]}"
        self.user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        self.r = get_redis_connection()
        
        # Create test game with user
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
            'price_history': json.dumps([1.0, 1.1, 1.2, 1.15, 1.25])
        }
        self.r.hset(f"market:{self.game_id}:data", mapping=market_data)
    
    def tearDown(self):
        """Clean up test data"""
        # Delete game data
        self.r.delete(f"game:{self.game_id}")
        self.r.delete(f"market:{self.game_id}:data")
        
        # Delete all bots for this game
        bots_set_key = f"bots:{self.game_id}"
        bot_ids = self.r.smembers(bots_set_key)
        for bot_id_bytes in bot_ids:
            bot_id = bot_id_bytes.decode('utf-8') if isinstance(bot_id_bytes, bytes) else bot_id_bytes
            self.r.delete(f"bot:{self.game_id}:{bot_id}")
        self.r.delete(bots_set_key)
    
    def test_bot_creation_with_owner(self):
        """Test that bot is created with correct owner"""
        bot = Bot(
            bot_id=None,
            is_toggled=True,
            usd_given=100.0,
            usd=100.0,
            bc=0.0,
            bot_type='random',
            user_id=self.user_id
        )
        
        self.assertEqual(bot.user_id, self.user_id)
        print(f"[PASS] Bot created with user_id: {bot.user_id}")
    
    def test_bot_saved_with_owner(self):
        """Test that bot owner is saved to Redis"""
        bot = Bot(
            bot_id=None,
            is_toggled=True,
            usd_given=100.0,
            usd=100.0,
            bc=0.0,
            bot_type='random',
            user_id=self.user_id
        )
        
        bot.save_to_redis(self.game_id)
        
        # Load bot from Redis
        loaded_bot = Bot.load_from_redis(self.game_id, bot.bot_id)
        
        self.assertIsNotNone(loaded_bot)
        self.assertEqual(loaded_bot.user_id, self.user_id)
        print(f"[PASS] Bot owner persisted to Redis: {loaded_bot.user_id}")
    
    def test_buy_bot_assigns_owner(self):
        """Test that buyBot function assigns correct owner"""
        bot_id = buyBot(
            user_id=self.user_id,
            game_id=self.game_id,
            bot_type='momentum',
            initial_usd=200.0
        )
        
        self.assertIsNotNone(bot_id)
        
        # Load bot and verify owner
        bot = Bot.load_from_redis(self.game_id, bot_id)
        self.assertIsNotNone(bot)
        self.assertEqual(bot.user_id, self.user_id)
        print(f"[PASS] buyBot assigned owner correctly: {bot.user_id}")
    
    def test_bot_trade_affects_owner_wallet(self):
        """Test that bot trades affect the owner's wallet"""
        # Create bot with owner
        bot = Bot(
            bot_id=None,
            is_toggled=True,
            usd_given=1000.0,
            usd=1000.0,
            bc=0.0,
            bot_type='random',
            user_id=self.user_id
        )
        
        # Get initial user balance
        game_data = self.r.hgetall(f"game:{self.game_id}")
        players = json.loads(game_data['players'])
        initial_user_usd = players[0]['usd']
        initial_user_coins = players[0]['coins']
        
        # Prepare game data for trade
        trade_game_data = {
            'totalBc': 100000.0,
            'totalUsd': 100000.0,
            'players': players,
            'interactions': []
        }
        
        # Execute a buy trade
        current_price = 1.0
        buy_amount = 10.0
        success = bot.buy(buy_amount, current_price, trade_game_data, bot.user_id)
        
        self.assertTrue(success)
        
        # Check that user's wallet was updated
        updated_players = trade_game_data['players']
        updated_user = updated_players[0]
        
        expected_user_usd = initial_user_usd - (buy_amount * current_price)
        expected_user_coins = initial_user_coins + buy_amount
        
        self.assertAlmostEqual(updated_user['usd'], expected_user_usd, places=2)
        self.assertAlmostEqual(updated_user['coins'], expected_user_coins, places=2)
        print(f"[PASS] Bot buy trade updated owner wallet: USD {initial_user_usd} -> {updated_user['usd']}, BC {initial_user_coins} -> {updated_user['coins']}")
    
    def test_bot_sell_affects_owner_wallet(self):
        """Test that bot sell trades affect the owner's wallet"""
        # Create bot with BC balance
        bot = Bot(
            bot_id=None,
            is_toggled=True,
            usd_given=1000.0,
            usd=500.0,
            bc=50.0,
            bot_type='random',
            user_id=self.user_id
        )
        
        # Get initial user balance
        game_data = self.r.hgetall(f"game:{self.game_id}")
        players = json.loads(game_data['players'])
        initial_user_usd = players[0]['usd']
        initial_user_coins = players[0]['coins']
        
        # Prepare game data for trade
        trade_game_data = {
            'totalBc': 100000.0,
            'totalUsd': 100000.0,
            'players': players,
            'interactions': []
        }
        
        # Execute a sell trade
        current_price = 1.2
        sell_amount = 10.0
        success = bot.sell(sell_amount, current_price, trade_game_data, bot.user_id)
        
        self.assertTrue(success)
        
        # Check that user's wallet was updated
        updated_players = trade_game_data['players']
        updated_user = updated_players[0]
        
        expected_user_usd = initial_user_usd + (sell_amount * current_price)
        expected_user_coins = initial_user_coins - sell_amount
        
        self.assertAlmostEqual(updated_user['usd'], expected_user_usd, places=2)
        self.assertAlmostEqual(updated_user['coins'], expected_user_coins, places=2)
        print(f"[PASS] Bot sell trade updated owner wallet: USD {initial_user_usd} -> {updated_user['usd']}, BC {initial_user_coins} -> {updated_user['coins']}")
    
    def test_multiple_bots_different_owners(self):
        """Test that multiple bots can have different owners"""
        user2_id = f"test_user_2_{uuid.uuid4().hex[:8]}"
        
        # Add second user to game
        game_data = self.r.hgetall(f"game:{self.game_id}")
        players = json.loads(game_data['players'])
        players.append({
            'userId': user2_id,
            'userName': 'Test User 2',
            'usd': 10000.0,
            'coins': 0.0,
            'bots': []
        })
        self.r.hset(f"game:{self.game_id}", 'players', json.dumps(players))
        
        # Create bot for user 1
        bot1_id = buyBot(user2_id, self.game_id, 'momentum', 200.0)
        
        # Create bot for user 2
        bot2_id = buyBot(user2_id, self.game_id, 'random', 150.0)
        
        # Verify both bots have correct owners
        bot1 = Bot.load_from_redis(self.game_id, bot1_id)
        bot2 = Bot.load_from_redis(self.game_id, bot2_id)
        
        self.assertEqual(bot1.user_id, user2_id)
        self.assertEqual(bot2.user_id, user2_id)
        print(f"[PASS] Multiple bots can have different owners")


if __name__ == '__main__':
    print("=" * 70)
    print("TESTING BOT OWNERSHIP SYSTEM")
    print("=" * 70)
    unittest.main(verbosity=2)

