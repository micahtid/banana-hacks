"""
Test the actual /api/bot/buy endpoint to see what error occurs
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'back-end'))

import requests
import json
import uuid
from redis_helper import get_redis_connection

# Create test game
game_id = f"test_endpoint_{uuid.uuid4().hex[:8]}"
user_id = f"user_{uuid.uuid4().hex[:8]}"

print("=" * 70)
print("TESTING /api/bot/buy ENDPOINT")
print("=" * 70)

# Setup test game in Redis
print(f"\n1. Setting up test game: {game_id}")
r = get_redis_connection()

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

market_data = {
    'price_history': json.dumps([1.0, 1.1, 1.2])
}
r.hset(f"market:{game_id}:data", mapping=market_data)

print("   [OK] Test game created")

# Test the endpoint
print("\n2. Calling POST /api/bot/buy")

payload = {
    'gameId': game_id,
    'userId': user_id,
    'botType': 'momentum',
    'cost': 800.0
}

print(f"   Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(
        'http://localhost:8000/api/bot/buy',
        json=payload,
        timeout=10
    )
    
    print(f"\n3. Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("   [OK] SUCCESS!")
        print(f"\n   Response:")
        print(f"   {json.dumps(data, indent=2)}")
    else:
        print(f"   [FAIL] Error occurred")
        try:
            error_data = response.json()
            print(f"\n   Error Response:")
            print(f"   {json.dumps(error_data, indent=2)}")
        except:
            print(f"\n   Raw Response:")
            print(f"   {response.text}")
            
except Exception as e:
    print(f"\n   [FAIL] Exception: {e}")
    import traceback
    traceback.print_exc()

# Cleanup
print("\n4. Cleaning up")
r.delete(f"game:{game_id}")
r.delete(f"market:{game_id}:data")

# Clean up any bots created
bots_key = f"bots:{game_id}"
bot_ids = r.smembers(bots_key)
for bot_id_bytes in bot_ids:
    bot_id = bot_id_bytes.decode('utf-8') if isinstance(bot_id_bytes, bytes) else bot_id_bytes
    r.delete(f"bot:{game_id}:{bot_id}")
r.delete(bots_key)

print("   [OK] Cleanup complete")

print("\n" + "=" * 70)

