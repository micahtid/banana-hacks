"""
Test with detailed logging of what's in Redis at each step.
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
game_id = f"test_log_{uuid.uuid4().hex[:8]}"
user_id = f"test_user_{uuid.uuid4().hex[:8]}"

print(f"Game: {game_id}")
print(f"User: {user_id}\n")

# Create game
players_data = [{
    'playerId': user_id,
    'playerName': 'Test',
    'usdBalance': 10000.0,
    'coinBalance': 0.0,
    'bots': []
}]

game_data = {
    'gameId': game_id,
    'isStarted': 'true',
    'players': json.dumps(players_data)
}

r.hset(f"game:{game_id}", mapping=game_data)

print("BEFORE API CALL:")
print(f"  Raw players field: {r.hget(f'game:{game_id}', 'players')}\n")

# Call API
response = requests.post(
    'http://localhost:8000/api/bot/buy',
    json={
        'gameId': game_id,
        'userId': user_id,
        'botType': 'momentum',
        'cost': 500
    }
)

print(f"API Response: {response.status_code}")
if response.status_code == 200:
    print(f"Bot ID: {response.json().get('botId')}\n")

# Wait for async operations
time.sleep(1)

print("AFTER API CALL:")
raw_players = r.hget(f'game:{game_id}', 'players')
print(f"  Raw players field: {raw_players}")

if raw_players:
    players_parsed = json.loads(raw_players)
    print(f"  Parsed players: {json.dumps(players_parsed, indent=4)}")

# Cleanup
r.delete(f"game:{game_id}")
bot_keys = r.keys(f"bot:{game_id}:*")
for bk in bot_keys:
    r.delete(bk)

