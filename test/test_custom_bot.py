"""
Test custom bot functionality with Gemini-generated strategies.
Tests the complete flow: prompt -> LLM generation -> execution -> trading
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'back-end'))

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import time
from bot import Bot, generate_custom_bot_strategy
from redis_helper import get_redis_connection


def test_generate_custom_strategy():
    """Test 1: Generate custom strategy code from a prompt"""
    print("\n" + "="*80)
    print("TEST 1: Generate Custom Strategy Code")
    print("="*80)
    
    prompt = "Buy when the price goes up by 5%, sell when it goes down by 5%"
    
    print(f"\nUser Prompt: {prompt}")
    print("\nGenerating strategy with Gemini...")
    
    try:
        code = generate_custom_bot_strategy(prompt)
        print(f"\n✓ Strategy generated successfully ({len(code)} characters)")
        print("\nGenerated Code:")
        print("-" * 80)
        print(code)
        print("-" * 80)
        
        # Validate the code
        if "def custom_strategy" not in code:
            print("\n✗ ERROR: No custom_strategy function found in generated code")
            return False
        
        print("\n✓ Code contains custom_strategy function")
        return True
    
    except Exception as e:
        print(f"\n✗ ERROR: Failed to generate strategy: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_execute_custom_strategy():
    """Test 2: Execute a custom strategy with sample data"""
    print("\n" + "="*80)
    print("TEST 2: Execute Custom Strategy")
    print("="*80)
    
    # Simple custom strategy code (no imports - math and random are pre-available)
    strategy_code = """
def custom_strategy(coins, current_price):
    if len(coins) < 5:
        return {'action': 'hold', 'amount': 0.0}
    
    # Calculate 5-period moving average
    recent = coins[-5:]
    ma = sum(recent) / len(recent)
    
    # Buy if price is 5% above MA, sell if 5% below MA
    if current_price > ma * 1.05:
        return {'action': 'buy', 'amount': 2.0}
    elif current_price < ma * 0.95:
        return {'action': 'sell', 'amount': 2.0}
    else:
        return {'action': 'hold', 'amount': 0.0}
"""
    
    print("\nTest Strategy Code:")
    print("-" * 80)
    print(strategy_code)
    print("-" * 80)
    
    # Create a bot with custom strategy
    bot = Bot(
        bot_id="test_custom_bot",
        is_toggled=True,
        usd_given=100.0,
        usd=100.0,
        bc=10.0,
        bot_type='custom',
        user_id='test_user',
        custom_strategy_code=strategy_code
    )
    
    # Test with different price patterns
    test_cases = [
        {
            "name": "Uptrend (should buy)",
            "coins": [1.0, 1.05, 1.10, 1.15, 1.20],
            "current_price": 1.25,
            "expected_action": "buy"
        },
        {
            "name": "Downtrend (should sell)",
            "coins": [1.20, 1.15, 1.10, 1.05, 1.00],
            "current_price": 0.95,
            "expected_action": "sell"
        },
        {
            "name": "Stable (should hold)",
            "coins": [1.0, 1.01, 1.02, 1.01, 1.0],
            "current_price": 1.01,
            "expected_action": "hold"
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"\n{test_case['name']}:")
        print(f"  Coins: {test_case['coins']}")
        print(f"  Current Price: {test_case['current_price']}")
        
        result = bot.analyze(test_case['coins'], test_case['current_price'])
        
        print(f"  Result: {result}")
        print(f"  Expected: {test_case['expected_action']}")
        
        if result['action'] == test_case['expected_action']:
            print("  ✓ PASS")
        else:
            print("  ✗ FAIL")
            all_passed = False
    
    return all_passed


def test_custom_bot_with_gemini():
    """Test 3: Full flow with Gemini-generated strategy"""
    print("\n" + "="*80)
    print("TEST 3: Full Custom Bot with Gemini")
    print("="*80)
    
    prompts = [
        "Buy when price increases by more than 3%, sell when it decreases by more than 3%",
        "Always buy 1 coin if we have less than 5 coins, otherwise hold",
        "Buy when the last 3 prices are all increasing, sell when they're all decreasing"
    ]
    
    all_passed = True
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\n--- Prompt {i} ---")
        print(f"Prompt: {prompt}")
        
        try:
            # Generate strategy
            code = generate_custom_bot_strategy(prompt)
            print(f"✓ Generated code ({len(code)} chars)")
            
            # Create bot with generated code
            bot = Bot(
                bot_id=f"test_gemini_bot_{i}",
                is_toggled=True,
                usd_given=100.0,
                usd=100.0,
                bc=5.0,
                bot_type='custom',
                user_id='test_user',
                custom_strategy_code=code
            )
            
            # Test with sample data
            test_data = [1.0, 1.05, 1.10, 1.15, 1.20]
            result = bot.analyze(test_data, 1.20)
            
            print(f"✓ Executed successfully: {result}")
            
            # Validate result format
            if 'action' not in result or 'amount' not in result:
                print("✗ ERROR: Invalid result format")
                all_passed = False
                continue
            
            if result['action'] not in ['buy', 'sell', 'hold']:
                print(f"✗ ERROR: Invalid action '{result['action']}'")
                all_passed = False
                continue
            
            if not isinstance(result['amount'], (int, float)) or result['amount'] < 0:
                print(f"✗ ERROR: Invalid amount '{result['amount']}'")
                all_passed = False
                continue
            
            print("✓ Result format valid")
            
        except Exception as e:
            print(f"✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    return all_passed


def test_custom_bot_redis_persistence():
    """Test 4: Save and load custom bot from Redis"""
    print("\n" + "="*80)
    print("TEST 4: Redis Persistence for Custom Bot")
    print("="*80)
    
    strategy_code = """
def custom_strategy(coins, current_price):
    if len(coins) < 2:
        return {'action': 'hold', 'amount': 0.0}
    
    if current_price > coins[-2]:
        return {'action': 'buy', 'amount': 1.5}
    else:
        return {'action': 'sell', 'amount': 1.5}
"""
    
    game_id = "test_game_custom_redis"
    bot_id = "test_custom_redis_bot"
    
    try:
        r = get_redis_connection()
        
        # Clean up any existing data
        r.delete(f"bot:{game_id}:{bot_id}")
        r.delete(f"bots:{game_id}")
        
        # Create custom bot
        print("\nCreating custom bot...")
        bot = Bot(
            bot_id=bot_id,
            is_toggled=True,
            usd_given=100.0,
            usd=100.0,
            bc=5.0,
            bot_type='custom',
            user_id='test_user',
            custom_strategy_code=strategy_code
        )
        
        print(f"✓ Bot created: {bot.bot_id}")
        print(f"  Bot type: {bot.bot_type}")
        print(f"  Custom code: {len(bot.custom_strategy_code)} chars")
        
        # Save to Redis
        print("\nSaving to Redis...")
        bot.save_to_redis(game_id)
        print("✓ Saved to Redis")
        
        # Verify data exists
        bot_key = f"bot:{game_id}:{bot_id}"
        if not r.exists(bot_key):
            print("✗ ERROR: Bot key not found in Redis")
            return False
        
        redis_data = r.hgetall(bot_key)
        print(f"✓ Redis data exists: {len(redis_data)} fields")
        
        # Verify custom_strategy_code is saved
        if 'custom_strategy_code' not in redis_data:
            print("✗ ERROR: custom_strategy_code not in Redis")
            return False
        
        saved_code = redis_data['custom_strategy_code']
        print(f"✓ custom_strategy_code saved: {len(saved_code)} chars")
        
        # Load bot from Redis
        print("\nLoading from Redis...")
        loaded_bot = Bot.load_from_redis(game_id, bot_id)
        
        if not loaded_bot:
            print("✗ ERROR: Failed to load bot from Redis")
            return False
        
        print(f"✓ Bot loaded: {loaded_bot.bot_id}")
        print(f"  Bot type: {loaded_bot.bot_type}")
        print(f"  Custom code: {len(loaded_bot.custom_strategy_code) if loaded_bot.custom_strategy_code else 0} chars")
        
        # Verify loaded bot has same data
        if loaded_bot.bot_type != 'custom':
            print(f"✗ ERROR: Wrong bot type: {loaded_bot.bot_type}")
            return False
        
        if not loaded_bot.custom_strategy_code:
            print("✗ ERROR: Custom strategy code not loaded")
            return False
        
        if loaded_bot.custom_strategy_code != strategy_code:
            print("✗ ERROR: Custom strategy code doesn't match")
            return False
        
        print("✓ Loaded bot matches original")
        
        # Test that loaded bot can execute strategy
        print("\nTesting loaded bot execution...")
        test_coins = [1.0, 1.05, 1.10, 1.15, 1.20]
        result = loaded_bot.analyze(test_coins, 1.25)
        
        print(f"✓ Loaded bot executed: {result}")
        
        if 'action' not in result or 'amount' not in result:
            print("✗ ERROR: Invalid result format")
            return False
        
        print("✓ Result format valid")
        
        # Clean up
        r.delete(f"bot:{game_id}:{bot_id}")
        r.delete(f"bots:{game_id}")
        print("\n✓ Cleanup complete")
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_custom_bot_error_handling():
    """Test 5: Error handling for malformed strategies"""
    print("\n" + "="*80)
    print("TEST 5: Error Handling")
    print("="*80)
    
    test_cases = [
        {
            "name": "Missing function",
            "code": "x = 1 + 1",
            "should_fail": True
        },
        {
            "name": "Wrong function name",
            "code": "def wrong_name(coins, current_price):\n    return {'action': 'buy', 'amount': 1.0}",
            "should_fail": True
        },
        {
            "name": "Invalid return format",
            "code": "def custom_strategy(coins, current_price):\n    return 'buy'",
            "should_fail": True
        },
        {
            "name": "Valid strategy",
            "code": "def custom_strategy(coins, current_price):\n    return {'action': 'hold', 'amount': 0.0}",
            "should_fail": False
        }
    ]
    
    all_passed = True
    
    for test in test_cases:
        print(f"\n{test['name']}:")
        
        bot = Bot(
            bot_id="test_error_bot",
            bot_type='custom',
            usd=100.0,
            bc=5.0,
            custom_strategy_code=test['code']
        )
        
        result = bot.analyze([1.0, 1.1, 1.2], 1.2)
        
        # Should always return valid format (even on error, defaults to hold)
        if result['action'] not in ['buy', 'sell', 'hold']:
            print(f"✗ FAIL: Invalid action {result['action']}")
            all_passed = False
            continue
        
        if test['should_fail'] and result['action'] == 'hold' and result['amount'] == 0.0:
            print(f"✓ PASS: Correctly handled error, returned hold")
        elif not test['should_fail']:
            print(f"✓ PASS: Valid strategy executed")
        else:
            print(f"✗ FAIL: Expected error handling, got {result}")
            all_passed = False
    
    return all_passed


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("CUSTOM BOT TESTING SUITE")
    print("="*80)
    
    tests = [
        ("Generate Custom Strategy", test_generate_custom_strategy),
        ("Execute Custom Strategy", test_execute_custom_strategy),
        ("Full Flow with Gemini", test_custom_bot_with_gemini),
        ("Redis Persistence", test_custom_bot_redis_persistence),
        ("Error Handling", test_custom_bot_error_handling),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
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
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())

