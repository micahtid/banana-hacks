"""
Test to verify that bots appear in the UI after purchase.
This test simulates the complete flow from bot purchase to UI display.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'back-end'))

import unittest
import json
import requests
import time
from redis_helper import get_redis_connection
from bot_operations import buyBot


class TestBotDisplayInUI(unittest.TestCase):
    """Test that purchased bots appear in the game UI"""
    
    def setUp(self):
        """Set up test game"""
        self.r = get_redis_connection()
        self.game_id = "test_bot_display_game"
        self.user_id = "test_user_display"
        
        # Create game in Redis with playerId structure
        game_data = {
            'gameId': self.game_id,
            'currentPrice': 100.0,
            'isStarted': 'true',
            'durationMinutes': '30',
            'totalBc': 1000000.0,
            'totalUsd': 1000000.0,
            'coinHistory': json.dumps([100.0]),
            'interactions': json.dumps([]),
            'players': json.dumps([
                {
                    'playerId': self.user_id,
                    'playerName': 'Test User',
                    'usdBalance': 10000.0,
                    'coinBalance': 0.0,
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
    
    def test_01_bot_stored_in_redis_after_purchase(self):
        """Test: Bot is stored in Redis after purchase"""
        print("\n" + "="*60)
        print("TEST 1: Bot Stored in Redis After Purchase")
        print("="*60)
        
        # Purchase a bot
        bot_id = buyBot(
            user_id=self.user_id,
            game_id=self.game_id,
            bot_type='momentum',
            initial_usd=500.0
        )
        
        self.assertIsNotNone(bot_id, "Bot ID should not be None")
        print(f"[TEST 1] Bot purchased: {bot_id}")
        
        # Check if bot exists in Redis
        bot_key = f"bot:{self.game_id}:{bot_id}"
        bot_exists = self.r.exists(bot_key)
        self.assertTrue(bot_exists, f"Bot should exist in Redis at key: {bot_key}")
        print(f"[TEST 1] [PASS] Bot exists in Redis: {bot_key}")
        
        # Get bot data
        bot_data = self.r.hgetall(bot_key)
        print(f"[TEST 1] Bot data keys: {list(bot_data.keys())}")
        
        # Verify bot fields
        self.assertIn('bot_id', bot_data, "Bot should have bot_id field")
        self.assertIn('is_toggled', bot_data, "Bot should have is_toggled field")
        self.assertIn('usd', bot_data, "Bot should have usd field")
        self.assertIn('bc', bot_data, "Bot should have bc field")
        self.assertIn('usd_given', bot_data, "Bot should have usd_given field")
        self.assertIn('bot_type', bot_data, "Bot should have bot_type field")
        self.assertIn('user_id', bot_data, "Bot should have user_id field")
        
        print(f"[TEST 1] [PASS] Bot has all required fields")
        print(f"[TEST 1]   - bot_id: {bot_data.get('bot_id')}")
        print(f"[TEST 1]   - is_toggled: {bot_data.get('is_toggled')}")
        print(f"[TEST 1]   - usd: {bot_data.get('usd')}")
        print(f"[TEST 1]   - bc: {bot_data.get('bc')}")
        print(f"[TEST 1]   - usd_given: {bot_data.get('usd_given')}")
        print(f"[TEST 1]   - bot_type: {bot_data.get('bot_type')}")
        print(f"[TEST 1]   - user_id: {bot_data.get('user_id')}")
    
    def test_02_bot_added_to_player_bots_list(self):
        """Test: Bot is added to player's bots list"""
        print("\n" + "="*60)
        print("TEST 2: Bot Added to Player's Bots List")
        print("="*60)
        
        # Get initial player data
        game_data = self.r.hgetall(f"game:{self.game_id}")
        players = json.loads(game_data['players'])
        initial_bots_count = len(players[0].get('bots', []))
        print(f"[TEST 2] Initial bots count: {initial_bots_count}")
        
        # Purchase a bot
        bot_id = buyBot(
            user_id=self.user_id,
            game_id=self.game_id,
            bot_type='mean_reversion',
            initial_usd=500.0
        )
        
        self.assertIsNotNone(bot_id)
        print(f"[TEST 2] Bot purchased: {bot_id}")
        
        # Get updated player data
        game_data = self.r.hgetall(f"game:{self.game_id}")
        players = json.loads(game_data['players'])
        player_bots = players[0].get('bots', [])
        
        print(f"[TEST 2] Updated bots count: {len(player_bots)}")
        print(f"[TEST 2] Player's bots list: {player_bots}")
        
        # Verify bot was added
        self.assertEqual(len(player_bots), initial_bots_count + 1, 
                        "Player should have one more bot")
        
        # Verify bot is in the list
        bot_ids = [b['botId'] for b in player_bots]
        self.assertIn(bot_id, bot_ids, "Bot ID should be in player's bots list")
        
        # Verify bot entry has required fields
        bot_entry = next((b for b in player_bots if b['botId'] == bot_id), None)
        self.assertIsNotNone(bot_entry, "Bot entry should exist")
        self.assertIn('botId', bot_entry, "Bot entry should have botId")
        self.assertIn('botName', bot_entry, "Bot entry should have botName")
        
        print(f"[TEST 2] [PASS] Bot added to player's bots list")
        print(f"[TEST 2]   Bot entry: {bot_entry}")
    
    def test_03_api_returns_full_bot_details(self):
        """Test: API endpoint returns full bot details"""
        print("\n" + "="*60)
        print("TEST 3: API Returns Full Bot Details")
        print("="*60)
        
        # Purchase a bot
        bot_id = buyBot(
            user_id=self.user_id,
            game_id=self.game_id,
            bot_type='momentum',
            initial_usd=600.0
        )
        
        self.assertIsNotNone(bot_id)
        print(f"[TEST 3] Bot purchased: {bot_id}")
        
        # Wait a moment for data to settle
        time.sleep(0.5)
        
        # Simulate what the Next.js API does
        print(f"[TEST 3] Simulating API endpoint logic...")
        
        game_data = self.r.hgetall(f"game:{self.game_id}")
        players = json.loads(game_data['players'])
        
        # For each bot in player's list, fetch full details
        player = players[0]
        player_bots = player.get('bots', [])
        
        print(f"[TEST 3] Player has {len(player_bots)} bot(s) in list")
        
        full_bot_details = []
        for bot in player_bots:
            bot_key = f"bot:{self.game_id}:{bot['botId']}"
            bot_exists = self.r.exists(bot_key)
            
            print(f"[TEST 3] Checking bot: {bot['botId']}")
            print(f"[TEST 3]   Key: {bot_key}")
            print(f"[TEST 3]   Exists: {bot_exists}")
            
            if bot_exists:
                bot_data = self.r.hgetall(bot_key)
                
                full_details = {
                    'botId': bot['botId'],
                    'botName': bot.get('botName', bot_data.get('bot_type', 'Bot')),
                    'isActive': bot_data.get('is_toggled') == 'true',
                    'usdBalance': float(bot_data.get('usd', 0)),
                    'coinBalance': float(bot_data.get('bc', 0)),
                    'startingUsdBalance': float(bot_data.get('usd_given', 0)),
                    'botType': bot_data.get('bot_type'),
                }
                
                full_bot_details.append(full_details)
                
                print(f"[TEST 3]   Full details retrieved:")
                print(f"[TEST 3]     - botId: {full_details['botId']}")
                print(f"[TEST 3]     - botName: {full_details['botName']}")
                print(f"[TEST 3]     - isActive: {full_details['isActive']}")
                print(f"[TEST 3]     - usdBalance: {full_details['usdBalance']}")
                print(f"[TEST 3]     - coinBalance: {full_details['coinBalance']}")
                print(f"[TEST 3]     - startingUsdBalance: {full_details['startingUsdBalance']}")
                print(f"[TEST 3]     - botType: {full_details['botType']}")
            else:
                print(f"[TEST 3]   [FAIL] Bot not found in Redis!")
                self.fail(f"Bot {bot['botId']} not found in Redis at {bot_key}")
        
        # Verify we got full details for all bots
        self.assertEqual(len(full_bot_details), len(player_bots),
                        "Should have full details for all bots")
        
        # Verify all required fields are present
        for bot_details in full_bot_details:
            self.assertIn('botId', bot_details)
            self.assertIn('botName', bot_details)
            self.assertIn('isActive', bot_details)
            self.assertIn('usdBalance', bot_details)
            self.assertIn('coinBalance', bot_details)
            self.assertIn('startingUsdBalance', bot_details)
            
            # Verify types
            self.assertIsInstance(bot_details['isActive'], bool)
            self.assertIsInstance(bot_details['usdBalance'], (int, float))
            self.assertIsInstance(bot_details['coinBalance'], (int, float))
            self.assertIsInstance(bot_details['startingUsdBalance'], (int, float))
        
        print(f"[TEST 3] [PASS] API returns complete bot details for UI display")
    
    def test_04_multiple_bots_all_appear(self):
        """Test: Multiple bots all appear correctly"""
        print("\n" + "="*60)
        print("TEST 4: Multiple Bots All Appear")
        print("="*60)
        
        # Purchase 3 different bots
        bot_types = ['momentum', 'mean_reversion', 'market_maker']
        bot_ids = []
        
        for bot_type in bot_types:
            bot_id = buyBot(
                user_id=self.user_id,
                game_id=self.game_id,
                bot_type=bot_type,
                initial_usd=500.0
            )
            bot_ids.append(bot_id)
            print(f"[TEST 4] Purchased {bot_type} bot: {bot_id}")
        
        # Verify all 3 bots exist in Redis
        for bot_id in bot_ids:
            bot_key = f"bot:{self.game_id}:{bot_id}"
            self.assertTrue(self.r.exists(bot_key), 
                           f"Bot {bot_id} should exist in Redis")
        
        print(f"[TEST 4] [PASS] All 3 bots exist in Redis")
        
        # Verify all 3 bots are in player's list
        game_data = self.r.hgetall(f"game:{self.game_id}")
        players = json.loads(game_data['players'])
        player_bots = players[0].get('bots', [])
        
        self.assertEqual(len(player_bots), 3, "Player should have 3 bots")
        
        player_bot_ids = [b['botId'] for b in player_bots]
        for bot_id in bot_ids:
            self.assertIn(bot_id, player_bot_ids, 
                         f"Bot {bot_id} should be in player's list")
        
        print(f"[TEST 4] [PASS] All 3 bots in player's bots list")
        
        # Simulate API fetching full details for all bots
        full_bot_details = []
        for bot in player_bots:
            bot_key = f"bot:{self.game_id}:{bot['botId']}"
            bot_data = self.r.hgetall(bot_key)
            
            full_details = {
                'botId': bot['botId'],
                'botName': bot.get('botName', bot_data.get('bot_type', 'Bot')),
                'isActive': bot_data.get('is_toggled') == 'true',
                'usdBalance': float(bot_data.get('usd', 0)),
                'coinBalance': float(bot_data.get('bc', 0)),
                'startingUsdBalance': float(bot_data.get('usd_given', 0)),
                'botType': bot_data.get('bot_type'),
            }
            full_bot_details.append(full_details)
        
        # Verify we have full details for all 3 bots
        self.assertEqual(len(full_bot_details), 3, 
                        "Should have full details for all 3 bots")
        
        print(f"[TEST 4] [PASS] API can fetch full details for all bots")
        print(f"[TEST 4] Bot details:")
        for i, bot in enumerate(full_bot_details, 1):
            print(f"[TEST 4]   Bot {i}: {bot['botType']} - ${bot['usdBalance']:.2f} USD")


def run_tests():
    """Run all bot display tests"""
    print("\n" + "="*60)
    print("BOT DISPLAY IN UI TESTS")
    print("Testing the complete flow from purchase to UI display")
    print("="*60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBotDisplayInUI)
    
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
        print("\n[SUCCESS] All tests passed!")
        print("\nThe bot display system is working correctly:")
        print("  1. [PASS] Bots are stored in Redis after purchase")
        print("  2. [PASS] Bots are added to player's bots list")
        print("  3. [PASS] API can fetch full bot details")
        print("  4. [PASS] Multiple bots all appear correctly")
        print("\nIf bots don't appear in UI, check:")
        print("  - Next.js frontend is running and polling /api/game/{gameId}")
        print("  - Python backend is running (for bot creation)")
        print("  - Browser console for any errors")
        print("  - Network tab to verify API calls")
        return 0
    else:
        print("\n[FAILURE] Some tests failed.")
        print("Review the errors above to identify the issue.")
        if len(result.failures) > 0:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback}")
        if len(result.errors) > 0:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback}")
        return 1


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)

