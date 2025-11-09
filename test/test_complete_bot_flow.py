"""
Complete end-to-end test: Create game, purchase bot, verify it appears.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'back-end'))

from redis_helper import get_redis_connection
import json
import requests
import uuid

def test_complete_flow():
    r = get_redis_connection()
    
    print("\n" + "="*70)
    print("COMPLETE BOT PURCHASE FLOW TEST")
    print("="*70)
    
    # Step 1: Create a test game with proper structure
    game_id = f"test_flow_{uuid.uuid4().hex[:8]}"
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    
    print(f"\n[STEP 1] Creating test game")
    print(f"  Game ID: {game_id}")
    print(f"  User ID: {user_id}")
    
    game_data = {
        'gameId': game_id,
        'isStarted': 'true',
        'isEnded': 'false',
        'durationMinutes': '30',
        'maxPlayers': '4',
        'currentPrice': '100.0',
        'totalBc': '1000000.0',
        'totalUsd': '1000000.0',
        'coinHistory': json.dumps([100.0]),
        'interactions': json.dumps([]),
        'players': json.dumps([
            {
                'playerId': user_id,
                'playerName': 'Test Player',
                'usdBalance': 10000.0,
                'coinBalance': 0.0,
                'bots': []
            }
        ])
    }
    
    r.hset(f"game:{game_id}", mapping=game_data)
    print("[STEP 1] [OK] Game created in Redis")
    
    # Step 2: Verify game creation
    print(f"\n[STEP 2] Verifying game in Redis")
    game_check = r.hgetall(f"game:{game_id}")
    if 'players' in game_check:
        players = json.loads(game_check['players'])
        print(f"  Players: {len(players)}")
        print(f"  Player bots: {players[0].get('bots', [])}")
        print("[STEP 2] [OK] Game structure verified")
    else:
        print("[STEP 2] [FAIL] No players field!")
        return
    
    # Step 3: Purchase bot via Python backend
    print(f"\n[STEP 3] Purchasing bot via Python backend API")
    
    try:
        response = requests.post(
            'http://localhost:8000/api/bot/buy',
            json={
                'gameId': game_id,
                'userId': user_id,
                'botType': 'momentum',
                'cost': 500
            },
            timeout=10
        )
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            bot_id = result.get('botId')
            print(f"  Bot ID: {bot_id}")
            print("[STEP 3] [OK] API returned success")
            
            # Step 4: Check if bot was added to player's list
            print(f"\n[STEP 4] Checking player's bots list in Redis")
            game_check = r.hgetall(f"game:{game_id}")
            players = json.loads(game_check['players'])
            player_bots = players[0].get('bots', [])
            
            print(f"  Bots count: {len(player_bots)}")
            print(f"  Bots list: {player_bots}")
            
            if len(player_bots) > 0:
                print("[STEP 4] [OK] Bot added to player's list!")
                
                # Step 5: Check if bot exists in Redis
                print(f"\n[STEP 5] Checking bot in Redis")
                bot_key = f"bot:{game_id}:{bot_id}"
                bot_exists = r.exists(bot_key)
                
                if bot_exists:
                    bot_data = r.hgetall(bot_key)
                    print(f"  Bot key: {bot_key}")
                    print(f"  Bot type: {bot_data.get('bot_type')}")
                    print(f"  Bot USD: {bot_data.get('usd')}")
                    print(f"  Bot is_toggled: {bot_data.get('is_toggled')}")
                    print("[STEP 5] [OK] Bot exists in Redis!")
                    
                    # Step 6: Check USD deduction
                    print(f"\n[STEP 6] Checking USD deduction")
                    final_usd = players[0].get('usdBalance', 0)
                    expected_usd = 10000 - 500
                    
                    print(f"  Initial USD: 10000")
                    print(f"  Final USD: {final_usd}")
                    print(f"  Expected USD: {expected_usd}")
                    
                    if abs(final_usd - expected_usd) < 0.01:
                        print("[STEP 6] [OK] USD deducted correctly!")
                        print("\n" + "="*70)
                        print("[SUCCESS] COMPLETE FLOW WORKS!")
                        print("="*70)
                    else:
                        print("[STEP 6] [FAIL] USD not deducted correctly!")
                else:
                    print("[STEP 5] [FAIL] Bot NOT found in Redis!")
            else:
                print("[STEP 4] [FAIL] Bot NOT added to player's list!")
        else:
            error_text = response.text
            print(f"  Error: {error_text}")
            print("[STEP 3] [FAIL] API returned error")
            
    except Exception as e:
        print(f"[STEP 3] [FAIL] Exception: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        print(f"\n[CLEANUP] Removing test game")
        r.delete(f"game:{game_id}")
        bot_keys = r.keys(f"bot:{game_id}:*")
        if bot_keys:
            for bk in bot_keys:
                r.delete(bk)
        print("[CLEANUP] Done")

if __name__ == '__main__':
    test_complete_flow()

