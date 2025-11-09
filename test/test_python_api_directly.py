"""
Test Python backend API directly to see debug output.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'back-end'))

from redis_helper import get_redis_connection
import json
import requests
import uuid
import time

r = get_redis_connection()

# Create test game
game_id = f"test_direct_{uuid.uuid4().hex[:8]}"
user_id = f"test_user_{uuid.uuid4().hex[:8]}"

print(f"Creating game: {game_id}")
print(f"User: {user_id}\n")

game_data = {
    'gameId': game_id,
    'isStarted': 'true',
    'currentPrice': '100.0',
    'totalBc': '1000000.0',
    'totalUsd': '1000000.0',
    'coinHistory': json.dumps([100.0]),
    'interactions': json.dumps([]),
    'players': json.dumps([
        {
            'playerId': user_id,
            'playerName': 'Test',
            'usdBalance': 10000.0,
            'coinBalance': 0.0,
            'bots': []
        }
    ])
}

r.hset(f"game:{game_id}", mapping=game_data)

# Check initial state
initial_game = r.hgetall(f"game:{game_id}")
initial_players = json.loads(initial_game['players'])
print(f"Initial state:")
print(f"  Player bots: {initial_players[0].get('bots', [])}")
print(f"  Player USD: {initial_players[0].get('usdBalance')}\n")

# Purchase bot
print("Calling Python API to purchase bot...")
response = requests.post(
    'http://localhost:8000/api/bot/buy',
    json={
        'gameId': game_id,
        'userId': user_id,
        'botType': 'momentum',
        'cost': 500
    }
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"Bot ID: {result.get('botId')}\n")
else:
    print(f"Error: {response.text}\n")

# Wait a moment for writes to complete
time.sleep(0.5)

# Check final state
final_game = r.hgetall(f"game:{game_id}")
final_players = json.loads(final_game['players'])
print(f"Final state:")
print(f"  Player bots: {final_players[0].get('bots', [])}")
print(f"  Player USD: {final_players[0].get('usdBalance')}\n")

# Cleanup
print("Cleaning up...")
r.delete(f"game:{game_id}")
bot_keys = r.keys(f"bot:{game_id}:*")
for bk in bot_keys:
    r.delete(bk)
print("Done")

