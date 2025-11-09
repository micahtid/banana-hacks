"""
Diagnostic script to check why bots don't appear in UI.
Run this after purchasing a bot to see what's in Redis.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'back-end'))

from redis_helper import get_redis_connection
import json

def diagnose_bot_display():
    r = get_redis_connection()
    
    print("\n" + "="*70)
    print("BOT DISPLAY DIAGNOSTICS")
    print("="*70)
    
    # Find all games
    game_keys = r.keys("game:*")
    
    # Handle both bytes and strings
    real_games = []
    for k in game_keys:
        key_str = k.decode() if isinstance(k, bytes) else k
        if not key_str.startswith('game:test_'):
            real_games.append(key_str)
    
    print(f"\nFound {len(real_games)} real game(s) (excluding test games)")
    
    if not real_games:
        print("\n[ERROR] No games found! Create a game first.")
        return
    
    # Check each game
    for game_key in real_games:
        game_key_str = game_key if isinstance(game_key, str) else game_key.decode()
        game_id = game_key_str.replace('game:', '')
        
        print(f"\n" + "-"*70)
        print(f"GAME: {game_id}")
        print("-"*70)
        
        game_data = r.hgetall(game_key)
        
        if 'players' not in game_data:
            print("[ERROR] No 'players' field in game data!")
            continue
        
        players = json.loads(game_data['players'])
        print(f"Number of players: {len(players)}")
        
        for i, player in enumerate(players):
            print(f"\n  Player {i + 1}:")
            
            # Show player ID (both possible field names)
            player_id = player.get('playerId') or player.get('userId')
            player_name = player.get('playerName') or player.get('userName')
            print(f"    ID: {player_id}")
            print(f"    Name: {player_name}")
            
            # Check bots
            bots = player.get('bots', [])
            print(f"    Bots in list: {len(bots)}")
            
            if not bots:
                print("    [INFO] No bots purchased yet")
                continue
            
            # Check each bot
            for j, bot_entry in enumerate(bots):
                print(f"\n    Bot {j + 1} in player's list:")
                print(f"      botId: {bot_entry.get('botId')}")
                print(f"      botName: {bot_entry.get('botName')}")
                
                # Check if bot exists in Redis
                bot_id = bot_entry.get('botId')
                if not bot_id:
                    print("      [ERROR] Bot entry has no botId!")
                    continue
                
                bot_key = f"bot:{game_id}:{bot_id}"
                bot_exists = r.exists(bot_key)
                
                if not bot_exists:
                    print(f"      [ERROR] Bot NOT found in Redis!")
                    print(f"      Expected key: {bot_key}")
                    
                    # Search for bot keys that might match
                    all_bot_keys = r.keys(f"bot:{game_id}:*")
                    print(f"      Available bot keys for this game: {len(all_bot_keys)}")
                    for bk in all_bot_keys:
                        bk_str = bk.decode() if isinstance(bk, bytes) else bk
                        print(f"        - {bk_str}")
                else:
                    print(f"      [OK] Bot found in Redis at: {bot_key}")
                    
                    # Get bot details
                    bot_data = r.hgetall(bot_key)
                    print(f"      Bot details:")
                    print(f"        - is_toggled: {bot_data.get('is_toggled')}")
                    print(f"        - usd: {bot_data.get('usd')}")
                    print(f"        - bc: {bot_data.get('bc')}")
                    print(f"        - usd_given: {bot_data.get('usd_given')}")
                    print(f"        - bot_type: {bot_data.get('bot_type')}")
                    print(f"        - user_id: {bot_data.get('user_id')}")
                    
                    # Check if details are complete for UI display
                    required_fields = ['is_toggled', 'usd', 'bc', 'usd_given', 'bot_type']
                    missing = [f for f in required_fields if not bot_data.get(f)]
                    
                    if missing:
                        print(f"      [WARNING] Missing fields: {missing}")
                    else:
                        print(f"      [OK] All required fields present")
                        
                        # Simulate what Next.js API will return
                        is_active = (bot_data.get('is_toggled') == 'True' or 
                                   bot_data.get('is_toggled') == 'true' or
                                   bot_data.get('is_toggled') == True)
                        
                        api_response = {
                            'botId': bot_id,
                            'botName': bot_entry.get('botName', bot_data.get('bot_type', 'Bot')),
                            'isActive': is_active,
                            'usdBalance': float(bot_data.get('usd', 0)),
                            'coinBalance': float(bot_data.get('bc', 0)),
                            'startingUsdBalance': float(bot_data.get('usd_given', 0)),
                            'botType': bot_data.get('bot_type'),
                        }
                        
                        print(f"      [OK] API would return:")
                        print(f"        {json.dumps(api_response, indent=10)}")
    
    print("\n" + "="*70)
    print("DIAGNOSIS COMPLETE")
    print("="*70)
    print("\nWhat to check:")
    print("  1. If bot is NOT in player's bots list → Backend issue (bot_operations.py)")
    print("  2. If bot is in list but NOT in Redis → Bot creation failed")
    print("  3. If bot is in Redis but missing fields → Bot.save_to_redis() issue")
    print("  4. If all checks pass → Frontend display issue")
    print("\nNext steps:")
    print("  - Check Next.js terminal for [API Game] logs")
    print("  - Check browser console for bot data")
    print("  - Verify frontend is polling /api/game/{gameId}")
    print("")

if __name__ == '__main__':
    diagnose_bot_display()

