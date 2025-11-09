"""
Test bot purchase flow with a real game to find where it fails.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'back-end'))

from redis_helper import get_redis_connection
import json
import requests

def test_live_bot_purchase():
    r = get_redis_connection()
    
    print("\n" + "="*70)
    print("LIVE BOT PURCHASE TEST")
    print("="*70)
    
    # Find a real game
    game_keys = r.keys("game:*")
    real_games = []
    for k in game_keys:
        key_str = k.decode() if isinstance(k, bytes) else k
        if not key_str.startswith('game:test_'):
            real_games.append(key_str)
    
    if not real_games:
        print("\n[ERROR] No games found! Create a game first.")
        return
    
    # Use the most recent game
    game_key = real_games[-1]
    game_id = game_key.replace('game:', '')
    
    print(f"\n[TEST] Using game: {game_id}")
    
    # Get game data
    game_data = r.hgetall(game_key)
    
    if 'players' not in game_data:
        print(f"[ERROR] Game has no 'players' field. Trying next game...")
        # Try another game
        if len(real_games) > 1:
            game_key = real_games[-2]
            game_id = game_key.replace('game:', '')
            print(f"[TEST] Using game: {game_id}")
            game_data = r.hgetall(game_key)
        
        if 'players' not in game_data:
            print("[ERROR] No valid games with players found!")
            return
    
    players = json.loads(game_data['players'])
    
    if not players:
        print("[ERROR] No players in game!")
        return
    
    player = players[0]
    player_id = player.get('playerId') or player.get('userId')
    player_name = player.get('playerName') or player.get('userName')
    
    print(f"[TEST] Player: {player_name} ({player_id})")
    print(f"[TEST] Initial bots: {len(player.get('bots', []))}")
    
    # Test purchase via API
    print("\n[TEST] Attempting to purchase bot via API...")
    
    try:
        response = requests.post(
            'http://localhost:3000/api/bot/buy',
            json={
                'gameId': game_id,
                'userId': player_id,
                'botType': 'momentum',
                'cost': 500,
                'customPrompt': 'Test Bot'
            },
            timeout=10
        )
        
        print(f"[TEST] API Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"[TEST] API Response: {json.dumps(result, indent=2)}")
            
            # Check if bot was added to player's list
            game_data = r.hgetall(game_key)
            players = json.loads(game_data['players'])
            player = players[0]
            bots = player.get('bots', [])
            
            print(f"\n[TEST] After purchase:")
            print(f"  - Player bots count: {len(bots)}")
            print(f"  - Player bots list: {bots}")
            
            if len(bots) > 0:
                bot_id = bots[-1].get('botId')
                print(f"\n[TEST] Checking if bot exists in Redis...")
                bot_key = f"bot:{game_id}:{bot_id}"
                bot_exists = r.exists(bot_key)
                print(f"  - Bot key: {bot_key}")
                print(f"  - Exists: {bot_exists}")
                
                if bot_exists:
                    bot_data = r.hgetall(bot_key)
                    print(f"  - Bot data: {dict(bot_data)}")
                    print(f"\n[SUCCESS] Bot purchase completed successfully!")
                else:
                    print(f"\n[ERROR] Bot not found in Redis!")
            else:
                print(f"\n[ERROR] Bot was not added to player's bots list!")
        else:
            error_text = response.text
            print(f"[ERROR] API returned error: {error_text}")
            
    except requests.exceptions.ConnectionError:
        print("[ERROR] Could not connect to Next.js server!")
        print("Make sure Next.js is running: npm run dev")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_live_bot_purchase()

