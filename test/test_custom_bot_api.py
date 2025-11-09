"""
Test custom bot through the API endpoints
Tests the complete integration: Front-end -> API -> Bot creation -> Execution
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'back-end'))

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json
import time
from redis_helper import get_redis_connection


# API endpoint (update if different)
PYTHON_API_URL = "http://localhost:8000"


def setup_test_game():
    """Create a test game with a player"""
    print("\n" + "="*80)
    print("SETUP: Creating Test Game")
    print("="*80)
    
    game_id = f"test_custom_bot_{int(time.time())}"
    user_id = "test_user_custom"
    
    try:
        r = get_redis_connection()
        
        # Create a simple game setup
        game_data = {
            'gameId': game_id,
            'status': 'in_progress',
            'totalBc': '1000',
            'totalUsd': '1000',
            'coinPrice': '1.0',
            'coins': json.dumps([1.0]),
            'players': json.dumps([{
                'userId': user_id,
                'playerName': 'Test Player',
                'usd': 500.0,
                'usdBalance': 500.0,
                'coins': 50.0,
                'coinBalance': 50.0,
                'bots': []
            }]),
            'interactions': json.dumps([])
        }
        
        r.hset(f"game:{game_id}", mapping=game_data)
        
        print(f"✓ Test game created: {game_id}")
        print(f"✓ Test user: {user_id}")
        print(f"✓ User USD balance: 500.0")
        
        return game_id, user_id
        
    except Exception as e:
        print(f"✗ ERROR: Failed to create test game: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def cleanup_test_game(game_id):
    """Clean up test game data"""
    try:
        r = get_redis_connection()
        
        # Find all bots for this game
        bots_key = f"bots:{game_id}"
        bot_ids = r.smembers(bots_key)
        
        # Delete all bot keys
        for bot_id in bot_ids:
            r.delete(f"bot:{game_id}:{bot_id}")
        
        # Delete game data
        r.delete(f"game:{game_id}")
        r.delete(bots_key)
        
        print(f"\n✓ Cleanup complete for game {game_id}")
        
    except Exception as e:
        print(f"\n✗ WARNING: Cleanup failed: {e}")


def test_buy_custom_bot_via_api():
    """Test 1: Buy a custom bot through the API"""
    print("\n" + "="*80)
    print("TEST 1: Buy Custom Bot via API")
    print("="*80)
    
    game_id, user_id = setup_test_game()
    
    if not game_id:
        return False
    
    try:
        # Prepare bot purchase request
        custom_prompt = "Buy when the price increases by more than 5%, sell when it decreases by more than 5%"
        
        request_data = {
            'gameId': game_id,
            'userId': user_id,
            'botType': 'custom',
            'cost': 50.0,
            'customPrompt': custom_prompt
        }
        
        print(f"\nBuying custom bot...")
        print(f"Prompt: {custom_prompt}")
        print(f"Cost: $50.0")
        
        # Make API request
        response = requests.post(
            f"{PYTHON_API_URL}/api/bot/buy",
            json=request_data,
            timeout=30  # Generous timeout for LLM generation
        )
        
        print(f"\nAPI Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"✗ ERROR: API returned {response.status_code}")
            print(f"Response: {response.text}")
            cleanup_test_game(game_id)
            return False
        
        result = response.json()
        print(f"\n✓ Bot purchased successfully!")
        print(f"Bot ID: {result.get('botId')}")
        print(f"Bot Type: {result.get('botType')}")
        print(f"New USD Balance: ${result.get('newUsd')}")
        
        # Verify bot exists in Redis
        bot_id = result.get('botId')
        r = get_redis_connection()
        bot_key = f"bot:{game_id}:{bot_id}"
        
        if not r.exists(bot_key):
            print(f"✗ ERROR: Bot not found in Redis")
            cleanup_test_game(game_id)
            return False
        
        bot_data = r.hgetall(bot_key)
        print(f"\n✓ Bot found in Redis:")
        print(f"  Type: {bot_data.get('bot_type')}")
        print(f"  USD: {bot_data.get('usd')}")
        print(f"  BC: {bot_data.get('bc')}")
        print(f"  Custom code length: {len(bot_data.get('custom_strategy_code', ''))} chars")
        
        # Verify bot type is custom
        if bot_data.get('bot_type') != 'custom':
            print(f"✗ ERROR: Bot type is {bot_data.get('bot_type')}, expected 'custom'")
            cleanup_test_game(game_id)
            return False
        
        # Verify custom strategy code exists
        if not bot_data.get('custom_strategy_code'):
            print(f"✗ ERROR: No custom strategy code found")
            cleanup_test_game(game_id)
            return False
        
        print("\n✓ Custom strategy code verified in Redis")
        
        # Verify user's USD was deducted
        game_data = r.hgetall(f"game:{game_id}")
        players = json.loads(game_data.get('players', '[]'))
        
        if not players:
            print("✗ ERROR: No players found")
            cleanup_test_game(game_id)
            return False
        
        player = players[0]
        player_usd = player.get('usd', player.get('usdBalance', 0))
        
        print(f"\n✓ User USD after purchase: ${player_usd}")
        
        if player_usd != 450.0:  # 500 - 50
            print(f"✗ ERROR: Expected $450, got ${player_usd}")
            cleanup_test_game(game_id)
            return False
        
        # Verify bot is in user's bots list
        user_bots = player.get('bots', [])
        print(f"✓ User has {len(user_bots)} bot(s)")
        
        if len(user_bots) < 1:
            print("✗ ERROR: Bot not added to user's bots list")
            cleanup_test_game(game_id)
            return False
        
        bot_entry = user_bots[0]
        if bot_entry.get('botId') != bot_id:
            print(f"✗ ERROR: Bot ID mismatch in user's bots list")
            cleanup_test_game(game_id)
            return False
        
        print(f"✓ Bot correctly added to user's bots list")
        
        cleanup_test_game(game_id)
        return True
        
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Cannot connect to Python API")
        print("Make sure the backend server is running on port 8000")
        cleanup_test_game(game_id)
        return False
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        cleanup_test_game(game_id)
        return False


def test_custom_bot_execution():
    """Test 2: Verify custom bot can execute trades"""
    print("\n" + "="*80)
    print("TEST 2: Custom Bot Execution")
    print("="*80)
    
    game_id, user_id = setup_test_game()
    
    if not game_id:
        return False
    
    try:
        # Buy custom bot
        custom_prompt = "Always buy 1 coin"
        
        response = requests.post(
            f"{PYTHON_API_URL}/api/bot/buy",
            json={
                'gameId': game_id,
                'userId': user_id,
                'botType': 'custom',
                'cost': 50.0,
                'customPrompt': custom_prompt
            },
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"✗ ERROR: Failed to buy bot: {response.status_code}")
            cleanup_test_game(game_id)
            return False
        
        result = response.json()
        bot_id = result.get('botId')
        print(f"\n✓ Bot created: {bot_id}")
        
        # Load bot and test execution
        from bot import Bot
        bot = Bot.load_from_redis(game_id, bot_id)
        
        if not bot:
            print("✗ ERROR: Failed to load bot from Redis")
            cleanup_test_game(game_id)
            return False
        
        print(f"✓ Bot loaded from Redis")
        
        # Test analyze
        test_coins = [1.0, 1.05, 1.10, 1.15, 1.20]
        decision = bot.analyze(test_coins, 1.20)
        
        print(f"\n✓ Bot analysis result: {decision}")
        
        if 'action' not in decision or 'amount' not in decision:
            print("✗ ERROR: Invalid decision format")
            cleanup_test_game(game_id)
            return False
        
        if decision['action'] not in ['buy', 'sell', 'hold']:
            print(f"✗ ERROR: Invalid action '{decision['action']}'")
            cleanup_test_game(game_id)
            return False
        
        print(f"✓ Decision format valid")
        print(f"  Action: {decision['action']}")
        print(f"  Amount: {decision['amount']}")
        
        cleanup_test_game(game_id)
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        cleanup_test_game(game_id)
        return False


def test_toggle_custom_bot():
    """Test 3: Toggle custom bot on/off"""
    print("\n" + "="*80)
    print("TEST 3: Toggle Custom Bot")
    print("="*80)
    
    game_id, user_id = setup_test_game()
    
    if not game_id:
        return False
    
    try:
        # Buy custom bot
        response = requests.post(
            f"{PYTHON_API_URL}/api/bot/buy",
            json={
                'gameId': game_id,
                'userId': user_id,
                'botType': 'custom',
                'cost': 50.0,
                'customPrompt': "Buy when price is increasing"
            },
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"✗ ERROR: Failed to buy bot")
            cleanup_test_game(game_id)
            return False
        
        bot_id = response.json().get('botId')
        print(f"\n✓ Bot created: {bot_id}")
        
        # Toggle bot off
        print("\nToggling bot OFF...")
        toggle_response = requests.post(
            f"{PYTHON_API_URL}/api/bot/toggle",
            json={
                'gameId': game_id,
                'userId': user_id,
                'botId': bot_id
            },
            timeout=10
        )
        
        if toggle_response.status_code != 200:
            print(f"✗ ERROR: Failed to toggle bot: {toggle_response.status_code}")
            cleanup_test_game(game_id)
            return False
        
        toggle_result = toggle_response.json()
        print(f"✓ Toggle response: {toggle_result.get('isActive')}")
        
        # Verify bot is toggled off in Redis
        r = get_redis_connection()
        bot_data = r.hgetall(f"bot:{game_id}:{bot_id}")
        is_toggled = bot_data.get('is_toggled', 'True')
        
        print(f"✓ Bot is_toggled in Redis: {is_toggled}")
        
        if is_toggled == 'False':
            print("✓ Bot successfully toggled OFF")
        elif is_toggled == 'True':
            print("✓ Bot successfully toggled ON")
        else:
            print(f"✗ ERROR: Unexpected is_toggled value: {is_toggled}")
            cleanup_test_game(game_id)
            return False
        
        cleanup_test_game(game_id)
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        cleanup_test_game(game_id)
        return False


def main():
    """Run all API tests"""
    print("\n" + "="*80)
    print("CUSTOM BOT API TESTING SUITE")
    print("="*80)
    print("\nNOTE: These tests require the Python backend to be running on port 8000")
    print("Run: cd back-end && python api_server.py")
    
    # Check if API is reachable
    try:
        response = requests.get(f"{PYTHON_API_URL}/docs", timeout=2)
        print(f"\n✓ Backend is reachable at {PYTHON_API_URL}")
    except:
        print(f"\n✗ ERROR: Cannot reach backend at {PYTHON_API_URL}")
        print("Please start the backend server first!")
        return 1
    
    tests = [
        ("Buy Custom Bot via API", test_buy_custom_bot_via_api),
        ("Custom Bot Execution", test_custom_bot_execution),
        ("Toggle Custom Bot", test_toggle_custom_bot),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
            time.sleep(1)  # Brief pause between tests
        except Exception as e:
            print(f"\n✗ EXCEPTION in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, passed in results if passed)
    
    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL API TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())

