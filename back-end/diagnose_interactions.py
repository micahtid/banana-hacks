"""
Emergency diagnostic script to find ALL interactions missing 'name' field
"""

import json
from redis_helper import get_redis_connection


def diagnose_all_games():
    """Find all interactions missing 'name' field"""
    r = get_redis_connection()
    
    print("=" * 80)
    print("DIAGNOSING ALL GAMES FOR MISSING 'name' FIELD")
    print("=" * 80)
    print()
    
    game_keys = r.keys('game:*')
    print(f"Found {len(game_keys)} games")
    print()
    
    total_issues = 0
    games_with_issues = []
    
    for game_key_bytes in game_keys:
        game_key = game_key_bytes.decode('utf-8') if isinstance(game_key_bytes, bytes) else game_key_bytes
        
        # Skip non-game keys (like game:id:bot)
        if game_key.count(':') > 1:
            continue
        
        game_id = game_key[5:]  # Remove 'game:' prefix
        
        # Get interactions
        interactions_json = r.hget(game_key, 'interactions')
        if not interactions_json:
            continue
        
        try:
            if isinstance(interactions_json, bytes):
                interactions_json = interactions_json.decode('utf-8')
            interactions = json.loads(interactions_json)
        except:
            continue
        
        # Check each interaction
        issues = []
        for i, interaction in enumerate(interactions):
            if not isinstance(interaction, dict):
                continue
            
            if 'name' not in interaction or interaction['name'] is None:
                issues.append({
                    'index': i,
                    'type': interaction.get('type', 'UNKNOWN'),
                    'has_interactionName': 'interactionName' in interaction,
                    'has_actor_name': 'actor_name' in interaction,
                    'keys': list(interaction.keys())
                })
        
        if issues:
            games_with_issues.append({
                'game_id': game_id,
                'total_interactions': len(interactions),
                'issues': issues
            })
            total_issues += len(issues)
    
    # Report results
    print("=" * 80)
    print("DIAGNOSIS RESULTS")
    print("=" * 80)
    print(f"Total games with issues: {len(games_with_issues)}")
    print(f"Total interactions with missing 'name': {total_issues}")
    print()
    
    if games_with_issues:
        print("GAMES WITH ISSUES:")
        print()
        for game_info in games_with_issues:
            print(f"Game ID: {game_info['game_id']}")
            print(f"  Total interactions: {game_info['total_interactions']}")
            print(f"  Interactions missing 'name': {len(game_info['issues'])}")
            
            for issue in game_info['issues'][:3]:  # Show first 3
                print(f"    - Index {issue['index']}: type={issue['type']}, keys={issue['keys']}")
            
            if len(game_info['issues']) > 3:
                print(f"    ... and {len(game_info['issues']) - 3} more")
            print()
    else:
        print("[OK] No issues found!")
    
    return games_with_issues


def fix_specific_game(game_id: str):
    """Fix a specific game's interactions"""
    from migrate_interactions import migrate_game_interactions
    
    print(f"\nFixing game: {game_id}")
    fixed = migrate_game_interactions(game_id)
    print(f"Fixed {fixed} interactions")
    
    # Verify
    r = get_redis_connection()
    game_key = f"game:{game_id}"
    interactions_json = r.hget(game_key, 'interactions')
    
    if interactions_json:
        if isinstance(interactions_json, bytes):
            interactions_json = interactions_json.decode('utf-8')
        interactions = json.loads(interactions_json)
        
        still_broken = []
        for i, interaction in enumerate(interactions):
            if 'name' not in interaction or interaction['name'] is None:
                still_broken.append(i)
        
        if still_broken:
            print(f"WARNING: {len(still_broken)} interactions still missing 'name'!")
            return False
        else:
            print(f"[OK] All {len(interactions)} interactions now have 'name' field")
            return True
    
    return True


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "fix":
        if len(sys.argv) > 2:
            # Fix specific game
            game_id = sys.argv[2]
            fix_specific_game(game_id)
        else:
            # Fix all games with issues
            games_with_issues = diagnose_all_games()
            
            if games_with_issues:
                print("\nFixing all games with issues...")
                for game_info in games_with_issues:
                    fix_specific_game(game_info['game_id'])
    else:
        # Just diagnose
        diagnose_all_games()

