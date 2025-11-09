"""
Comprehensive test for bot purchase and operation with playerId/usdBalance field names.
This test verifies that the bot system works with the actual Redis data structure.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'back-end'))

import unittest
import json
import time
from redis_helper import get_redis_connection
from bot import Bot
from bot_operations import buyBot, toggleBot


class TestBotWithPlayerIdFields(unittest.TestCase):
    """Test bot operations with playerId, usdBalance, and coinBalance field names"""
    
    def setUp(self):
        """Set up test game with correct field names"""
        self.r = get_redis_connection()
        self.game_id = "test_game_playerid_123"
        self.user_id = "test_user_abc"
        
        # Create game with playerId, usdBalance, coinBalance (actual structure)
        game_data = {
            'gameId': self.game_id,
            'currentPrice': 100.0,
            'totalBc': 1000000.0,
            'totalUsd': 1000000.0,
            'interactions': json.dumps([]),
            'players': json.dumps([
                {
                    'playerId': self.user_id,  # Using playerId, not userId
                    'playerName': 'Test Player',
                    'usdBalance': 10000.0,  # Using usdBalance, not usd
                    'coinBalance': 0.0,  # Using coinBalance, not coins
                    'bots': []
                }
            ])
        }
        
        self.r.hset(f"game:{self.game_id}", mapping=game_data)
        print(f"\n[SETUP] Created test game: {self.game_id}")
        print(f"[SETUP] Test user: {self.user_id}")
        
    def tearDown(self):
        """Clean up test data"""
        # Delete test game
        self.r.delete(f"game:{self.game_id}")
        
        # Delete any bot keys
        bot_keys = self.r.keys(f"bot:{self.game_id}:*")
        if bot_keys:
            self.r.delete(*bot_keys)
        
        print(f"[TEARDOWN] Cleaned up test data")
    
    def test_01_buy_bot_with_playerid(self):
        """Test buying a bot with playerId field"""
        print("\n" + "="*60)
        print("TEST 1: Buy Bot with playerId Field")
        print("="*60)
        
        # Buy a bot
        bot_id = buyBot(
            user_id=self.user_id,
            game_id=self.game_id,
            bot_type='momentum',
            initial_usd=500.0
        )
        
        print(f"[TEST 1] Bot ID returned: {bot_id}")
        self.assertIsNotNone(bot_id, "Bot ID should not be None")
        
        # Verify bot was created in Redis
        bot = Bot.load_from_redis(self.game_id, bot_id)
        self.assertIsNotNone(bot, "Bot should be loadable from Redis")
        self.assertEqual(bot.usd, 500.0, "Bot should have correct USD")
        self.assertEqual(bot.bc, 0.0, "Bot should start with 0 BC")
        self.assertEqual(bot.user_id, self.user_id, "Bot should have correct user_id")
        print(f"[TEST 1] [PASS] Bot created successfully in Redis")
        
        # Verify bot was added to user's bots list
        game_data = self.r.hgetall(f"game:{self.game_id}")
        players = json.loads(game_data['players'])
        user = players[0]
        
        self.assertIn('bots', user, "User should have bots list")
        self.assertEqual(len(user['bots']), 1, "User should have 1 bot")
        self.assertEqual(user['bots'][0]['botId'], bot_id, "Bot ID should match")
        print(f"[TEST 1] [PASS] Bot added to user's bots list")
        
        print(f"[TEST 1] [PASS] All checks passed!")
    
    def test_02_bot_trading_updates_user_balance(self):
        """Test that bot trading updates user's usdBalance and coinBalance"""
        print("\n" + "="*60)
        print("TEST 2: Bot Trading Updates User Balance")
        print("="*60)
        
        # Buy a bot
        bot_id = buyBot(
            user_id=self.user_id,
            game_id=self.game_id,
            bot_type='random',
            initial_usd=1000.0
        )
        self.assertIsNotNone(bot_id)
        print(f"[TEST 2] Bot created: {bot_id}")
        
        # Load bot
        bot = Bot.load_from_redis(self.game_id, bot_id)
        self.assertIsNotNone(bot)
        
        # Get initial user balance
        game_data_dict = self.r.hgetall(f"game:{self.game_id}")
        game_data = {k: json.loads(v) if k in ['players', 'interactions'] else v 
                     for k, v in game_data_dict.items()}
        
        initial_user_usd = game_data['players'][0].get('usdBalance', 0)
        initial_user_coins = game_data['players'][0].get('coinBalance', 0)
        print(f"[TEST 2] Initial user balance: ${initial_user_usd:.2f} USD, {initial_user_coins:.2f} BC")
        
        # Execute a buy trade
        trade_amount = 10.0
        trade_price = 100.0
        success = bot.buy(trade_amount, trade_price, game_data, user_id=self.user_id)
        self.assertTrue(success, "Trade should succeed")
        print(f"[TEST 2] Bot executed buy: {trade_amount} BC at ${trade_price} = ${trade_amount * trade_price}")
        
        # Check user balance was updated
        final_user_usd = game_data['players'][0].get('usdBalance', 
                         game_data['players'][0].get('usd', 0))
        final_user_coins = game_data['players'][0].get('coinBalance',
                           game_data['players'][0].get('coins', 0))
        
        print(f"[TEST 2] Final user balance: ${final_user_usd:.2f} USD, {final_user_coins:.2f} BC")
        
        expected_usd = initial_user_usd - (trade_amount * trade_price)
        expected_coins = initial_user_coins + trade_amount
        
        self.assertAlmostEqual(final_user_usd, expected_usd, places=2, 
                              msg="User USD should decrease by trade cost")
        self.assertAlmostEqual(final_user_coins, expected_coins, places=2,
                              msg="User coins should increase by trade amount")
        
        print(f"[TEST 2] [PASS] User balance updated correctly!")
        print(f"[TEST 2]   USD change: ${initial_user_usd:.2f} -> ${final_user_usd:.2f}")
        print(f"[TEST 2]   BC change: {initial_user_coins:.2f} -> {final_user_coins:.2f}")
    
    def test_03_toggle_bot(self):
        """Test toggling bot on/off"""
        print("\n" + "="*60)
        print("TEST 3: Toggle Bot On/Off")
        print("="*60)
        
        # Buy a bot
        bot_id = buyBot(
            user_id=self.user_id,
            game_id=self.game_id,
            bot_type='momentum',
            initial_usd=500.0
        )
        self.assertIsNotNone(bot_id)
        print(f"[TEST 3] Bot created: {bot_id}")
        
        # Load bot and check initial state
        bot = Bot.load_from_redis(self.game_id, bot_id)
        self.assertTrue(bot.is_toggled, "Bot should start toggled ON")
        print(f"[TEST 3] Initial state: ON")
        
        # Toggle bot OFF
        success = toggleBot(bot_id, self.game_id)
        self.assertTrue(success, "Toggle should succeed")
        
        # Reload and check state
        bot = Bot.load_from_redis(self.game_id, bot_id)
        self.assertFalse(bot.is_toggled, "Bot should be toggled OFF")
        print(f"[TEST 3] After toggle: OFF")
        
        # Toggle bot ON
        success = toggleBot(bot_id, self.game_id)
        self.assertTrue(success, "Toggle should succeed")
        
        # Reload and check state
        bot = Bot.load_from_redis(self.game_id, bot_id)
        self.assertTrue(bot.is_toggled, "Bot should be toggled ON")
        print(f"[TEST 3] After toggle: ON")
        
        print(f"[TEST 3] [PASS] Toggle functionality works!")
    
    def test_04_api_server_bot_buy_logic(self):
        """Test the same logic as api_server.py bot buy endpoint"""
        print("\n" + "="*60)
        print("TEST 4: API Server Bot Buy Logic")
        print("="*60)
        
        # Simulate API server logic
        game_data = self.r.hgetall(f"game:{self.game_id}")
        self.assertTrue(game_data, "Game should exist")
        
        players = json.loads(game_data.get('players', '[]'))
        print(f"[TEST 4] Found {len(players)} player(s)")
        
        # Find user (same logic as api_server.py)
        user_data = None
        user_index = None
        for i, player in enumerate(players):
            player_id = player.get('userId') or player.get('playerId')
            print(f"[TEST 4] Checking player {i}: playerId={player.get('playerId')}, userId={player.get('userId')}")
            if player_id == self.user_id:
                user_data = player
                user_index = i
                break
        
        self.assertIsNotNone(user_data, "User should be found")
        print(f"[TEST 4] [PASS] User found at index {user_index}")
        
        # Check USD balance
        user_usd = user_data.get('usd', user_data.get('usdBalance', 0))
        print(f"[TEST 4] User USD: ${user_usd:.2f}")
        self.assertGreaterEqual(user_usd, 500, "User should have enough USD")
        print(f"[TEST 4] [PASS] User has sufficient funds")
        
        # Deduct cost (simulating API server logic)
        bot_cost = 500.0
        original_usd = user_usd
        if 'usd' in user_data:
            user_data['usd'] -= bot_cost
        if 'usdBalance' in user_data:
            user_data['usdBalance'] -= bot_cost
        
        # Update Redis FIRST (like API server does)
        players[user_index] = user_data
        self.r.hset(f"game:{self.game_id}", "players", json.dumps(players))
        
        # Buy bot (this will add bot to user's list)
        bot_initial_usd = bot_cost * 0.2
        bot_id = buyBot(
            self.user_id,
            self.game_id,
            'momentum',
            bot_initial_usd
        )
        
        self.assertIsNotNone(bot_id, "Bot should be created")
        print(f"[TEST 4] [PASS] Bot created: {bot_id}")
        
        # Verify final state
        final_game_data = self.r.hgetall(f"game:{self.game_id}")
        final_players = json.loads(final_game_data['players'])
        final_user = final_players[user_index]
        
        final_usd = final_user.get('usd', final_user.get('usdBalance', 0))
        expected_usd = original_usd - bot_cost
        
        self.assertAlmostEqual(final_usd, expected_usd, places=2,
                              msg="User USD should be deducted")
        print(f"[TEST 4] [PASS] User USD deducted: ${original_usd:.2f} -> ${final_usd:.2f}")
        
        # Verify bot in user's list
        self.assertIn('bots', final_user)
        self.assertTrue(any(b['botId'] == bot_id for b in final_user['bots']),
                       "Bot should be in user's bots list")
        print(f"[TEST 4] [PASS] Bot added to user's bots list")
        
        print(f"[TEST 4] [PASS] Complete API flow successful!")
    
    def test_05_bot_sell_updates_user_balance(self):
        """Test that bot selling updates user's balance correctly"""
        print("\n" + "="*60)
        print("TEST 5: Bot Sell Updates User Balance")
        print("="*60)
        
        # Buy a bot
        bot_id = buyBot(
            user_id=self.user_id,
            game_id=self.game_id,
            bot_type='random',
            initial_usd=1000.0
        )
        self.assertIsNotNone(bot_id)
        
        # Load bot and give it some BC
        bot = Bot.load_from_redis(self.game_id, bot_id)
        bot.bc = 50.0  # Give bot some coins to sell
        bot.save_to_redis(self.game_id)
        
        # Get game data
        game_data_dict = self.r.hgetall(f"game:{self.game_id}")
        game_data = {k: json.loads(v) if k in ['players', 'interactions'] else v 
                     for k, v in game_data_dict.items()}
        
        initial_user_usd = game_data['players'][0].get('usdBalance', 0)
        initial_user_coins = game_data['players'][0].get('coinBalance', 0)
        print(f"[TEST 5] Initial: ${initial_user_usd:.2f} USD, {initial_user_coins:.2f} BC")
        
        # Execute sell trade
        trade_amount = 20.0
        trade_price = 100.0
        success = bot.sell(trade_amount, trade_price, game_data, user_id=self.user_id)
        self.assertTrue(success, "Sell trade should succeed")
        print(f"[TEST 5] Bot sold: {trade_amount} BC at ${trade_price}")
        
        # Check balances
        final_user_usd = game_data['players'][0].get('usdBalance',
                         game_data['players'][0].get('usd', 0))
        final_user_coins = game_data['players'][0].get('coinBalance',
                           game_data['players'][0].get('coins', 0))
        
        print(f"[TEST 5] Final: ${final_user_usd:.2f} USD, {final_user_coins:.2f} BC")
        
        expected_usd = initial_user_usd + (trade_amount * trade_price)
        expected_coins = initial_user_coins - trade_amount
        
        self.assertAlmostEqual(final_user_usd, expected_usd, places=2)
        self.assertAlmostEqual(final_user_coins, expected_coins, places=2)
        
        print(f"[TEST 5] [PASS] Sell updated user balance correctly!")


def run_tests():
    """Run all tests with detailed output"""
    print("\n" + "="*60)
    print("COMPREHENSIVE BOT PURCHASE & OPERATION TESTS")
    print("Testing with playerId, usdBalance, coinBalance fields")
    print("="*60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBotWithPlayerIdFields)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n[SUCCESS] All tests passed! Bot system is working correctly.")
        print("The system properly handles:")
        print("  - playerId field (instead of userId)")
        print("  - usdBalance field (instead of usd)")
        print("  - coinBalance field (instead of coins)")
        print("  - Bot purchase and creation")
        print("  - Bot trading and user balance updates")
        print("  - Bot toggling on/off")
        return 0
    else:
        print("\n[FAILURE] Some tests failed. Please review the errors above.")
        return 1


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)

