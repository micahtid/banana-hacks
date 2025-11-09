"""Check specific game that showed players in diagnostic."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'back-end'))

from redis_helper import get_redis_connection
import json

r = get_redis_connection()

# Check the game from earlier diagnostic
game_id = "84c7d5dc-97b3-4ae0-9988-a49a58c64550"
game_key = f"game:{game_id}"

print(f"Checking game: {game_id}\n")

game_data = r.hgetall(game_key)
print(f"Fields in game: {list(game_data.keys())}\n")

if 'players' in game_data:
    players = json.loads(game_data['players'])
    print(f"Number of players: {len(players)}")
    
    if players:
        player = players[0]
        print(f"Player ID: {player.get('playerId') or player.get('userId')}")
        print(f"Player name: {player.get('playerName') or player.get('userName')}")
        print(f"Player bots: {len(player.get('bots', []))}")
        print(f"Bots list: {player.get('bots', [])}")
else:
    print("No 'players' field in game!")

