"""
Test bot toggle functionality.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'back-end'))

from redis_helper import get_redis_connection
from bot import Bot
from bot_operations import buyBot, toggleBot
import json
import uuid

r = get_redis_connection()

# Create test game
game_id = f"test_toggle_{uuid.uuid4().hex[:8]}"
user_id = f"test_user_{uuid.uuid4().hex[:8]}"

print(f"Creating test game: {game_id}")

game_data = {
    'gameId': game_id,
    'isStarted': 'true',
    'players': json.dumps([{
        'playerId': user_id,
        'playerName': 'Test',
        'usdBalance': 10000.0,
        'coinBalance': 0.0,
        'bots': []
    }])
}

r.hset(f"game:{game_id}", mapping=game_data)

# Create a bot
print("\n1. Creating bot...")
bot_id = buyBot(user_id, game_id, 'momentum', 500.0)
print(f"   Bot ID: {bot_id}")

# Check initial state
bot = Bot.load_from_redis(game_id, bot_id)
print(f"   Initial state: is_toggled = {bot.is_toggled}")

# Toggle OFF
print("\n2. Toggling bot OFF...")
success = toggleBot(bot_id, game_id)
print(f"   Toggle success: {success}")

# Check state after toggle
bot = Bot.load_from_redis(game_id, bot_id)
print(f"   After toggle: is_toggled = {bot.is_toggled}")
assert bot.is_toggled == False, "Bot should be OFF"

# Toggle ON
print("\n3. Toggling bot ON...")
success = toggleBot(bot_id, game_id)
print(f"   Toggle success: {success}")

# Check state after toggle
bot = Bot.load_from_redis(game_id, bot_id)
print(f"   After toggle: is_toggled = {bot.is_toggled}")
assert bot.is_toggled == True, "Bot should be ON"

# Check what's stored in Redis
print("\n4. Checking Redis storage...")
bot_key = f"bot:{game_id}:{bot_id}"
bot_data = r.hgetall(bot_key)
print(f"   Redis is_toggled field: {bot_data.get('is_toggled')}")
print(f"   Type: {type(bot_data.get('is_toggled'))}")

# Cleanup
print("\n5. Cleaning up...")
r.delete(f"game:{game_id}")
r.delete(bot_key)

print("\n✓ Toggle test PASSED!")
print("\nBot toggle is working correctly in Python backend.")
print("If the UI doesn't update, check:")
print("  - Browser console for toggle logs")
print("  - Next.js terminal for [Bot Toggle] logs")
print("  - Network tab to see API responses")

