"""Check what fields games actually have in Redis."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'back-end'))

from redis_helper import get_redis_connection

r = get_redis_connection()

# Get all game keys
game_keys = r.keys("game:*")
print(f"Found {len(game_keys)} games\n")

for game_key in game_keys[:5]:  # Check first 5
    game_key_str = game_key.decode() if isinstance(game_key, bytes) else game_key
    game_id = game_key_str.replace('game:', '')
    
    if game_id.startswith('test_'):
        continue
    
    print(f"Game: {game_id}")
    game_data = r.hgetall(game_key_str)
    print(f"Fields: {list(game_data.keys())}")
    print()

