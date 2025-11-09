"""
Live test for bot purchase to diagnose the 500 error
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'back-end'))

import json
import uuid
from redis_helper import get_redis_connection
from bot_operations import buyBot
from bot import Bot

def test_bot_purchase():
    """Test the complete bot purchase flow"""
    print("=" * 70)
    print("TESTING BOT PURCHASE FLOW")
    print("=" * 70)
    
    # Setup test game
    game_id = f"test_game_{uuid.uuid4().hex[:8]}"
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    r = get_redis_connection()
    
    print(f"\n1. Creating test game: {game_id}")
    print(f"   User ID: {user_id}")
    
    # Create test game with user
    game_data = {
        'gameId': game_id,
        'isStarted': 'true',
        'players': json.dumps([{
            'userId': user_id,
            'userName': 'Test User',
            'usd': 10000.0,
            'coins': 0.0,
            'bots': []
        }]),
        'totalBc': 100000.0,
        'totalUsd': 100000.0
    }
    r.hset(f"game:{game_id}", mapping=game_data)
    print("   [OK] Game created in Redis")
    
    # Create market data with price history
    market_data = {
        'price_history': json.dumps([1.0, 1.1, 1.2, 1.15, 1.25])
    }
    r.hset(f"market:{game_id}:data", mapping=market_data)
    print("   [OK] Market data created")
    
    # Test bot purchase
    print("\n2. Testing bot purchase (buyBot function)")
    print("   Bot type: momentum")
    print("   Initial USD: $200")
    
    try:
        bot_id = buyBot(
            user_id=user_id,
            game_id=game_id,
            bot_type='momentum',
            initial_usd=200.0
        )
        
        if bot_id:
            print(f"   [OK] Bot created successfully: {bot_id}")
        else:
            print("   [FAIL] Bot creation returned None")
            return False
            
    except Exception as e:
        print(f"   [FAIL] Error creating bot: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Verify bot exists
    print("\n3. Verifying bot in Redis")
    try:
        bot = Bot.load_from_redis(game_id, bot_id)
        if bot:
            print(f"   [OK] Bot loaded from Redis")
            print(f"   - Bot ID: {bot.bot_id}")
            print(f"   - User ID: {bot.user_id}")
            print(f"   - Bot type: {bot.bot_type}")
            print(f"   - USD: ${bot.usd}")
            print(f"   - BC: {bot.bc}")
            print(f"   - Is toggled: {bot.is_toggled}")
        else:
            print("   [FAIL] Bot not found in Redis")
            return False
    except Exception as e:
        print(f"   [FAIL] Error loading bot: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Verify user data updated
    print("\n4. Verifying user data in game")
    try:
        game_data = r.hgetall(f"game:{game_id}")
        players = json.loads(game_data['players'])
        user = players[0]
        
        print(f"   User USD: ${user['usd']}")
        print(f"   User bots: {len(user.get('bots', []))}")
        
        if 'bots' in user and len(user['bots']) > 0:
            print(f"   [OK] Bot added to user's bots list")
            print(f"   - Bot entry: {user['bots'][0]}")
        else:
            print("   [FAIL] Bot not in user's bots list")
            
    except Exception as e:
        print(f"   [FAIL] Error checking user data: {e}")
        import traceback
        traceback.print_exc()
    
    # Test bot serialization
    print("\n5. Testing bot serialization (to_dict)")
    try:
        bot_dict = bot.to_dict()
        print("   [OK] Bot serialized successfully:")
        for key, value in bot_dict.items():
            print(f"   - {key}: {value}")
    except Exception as e:
        print(f"   [FAIL] Error serializing bot: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Cleanup
    print("\n6. Cleaning up test data")
    r.delete(f"game:{game_id}")
    r.delete(f"market:{game_id}:data")
    r.delete(f"bot:{game_id}:{bot_id}")
    r.delete(f"bots:{game_id}")
    print("   [OK] Test data cleaned up")
    
    print("\n" + "=" * 70)
    print("BOT PURCHASE TEST COMPLETED SUCCESSFULLY")
    print("=" * 70)
    return True

if __name__ == '__main__':
    try:
        success = test_bot_purchase()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FAIL] FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

