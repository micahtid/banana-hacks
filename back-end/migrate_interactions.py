"""
Migration script to fix interactions in Redis that are missing the 'name' field

This adds backward compatibility fields to existing interactions in all games.
"""

import json
from redis_helper import get_redis_connection


def migrate_game_interactions(game_id: str) -> int:
    """
    Migrate interactions for a single game
    
    Returns:
        Number of interactions fixed
    """
    r = get_redis_connection()
    game_key = f"game:{game_id}"
    
    if not r.exists(game_key):
        return 0
    
    # Get current interactions
    interactions_json = r.hget(game_key, 'interactions')
    if not interactions_json:
        return 0
    
    try:
        interactions = json.loads(interactions_json)
    except:
        return 0
    
    if not isinstance(interactions, list):
        return 0
    
    fixed_count = 0
    
    # Fix each interaction
    for interaction in interactions:
        if not isinstance(interaction, dict):
            continue
        
        # Add 'name' field if missing (from interactionName or name)
        if 'name' not in interaction or interaction['name'] is None:
            # Try to get from interactionName
            if 'interactionName' in interaction:
                interaction['name'] = interaction['interactionName']
                fixed_count += 1
            # Try to construct from actor_name
            elif 'actor_name' in interaction:
                interaction['name'] = interaction['actor_name']
                fixed_count += 1
            # Last resort: use a default
            else:
                interaction['name'] = 'Unknown'
                fixed_count += 1
        
        # Add 'value' field if missing (from amount or value)
        if 'value' not in interaction:
            if 'amount' in interaction:
                # Convert to cents
                interaction['value'] = int(float(interaction['amount']) * 100)
            else:
                interaction['value'] = 0
    
    # Save back to Redis
    r.hset(game_key, 'interactions', json.dumps(interactions))
    
    return fixed_count


def migrate_all_games():
    """
    Migrate interactions for all games in Redis
    """
    r = get_redis_connection()
    
    print("=" * 80)
    print("MIGRATING INTERACTIONS IN REDIS")
    print("=" * 80)
    print()
    
    # Get all game keys
    game_keys = r.keys('game:*')
    
    if not game_keys:
        print("No games found in Redis")
        return
    
    print(f"Found {len(game_keys)} game(s)")
    print()
    
    total_fixed = 0
    games_fixed = 0
    
    for game_key_bytes in game_keys:
        game_key = game_key_bytes.decode('utf-8') if isinstance(game_key_bytes, bytes) else game_key_bytes
        
        # Extract game_id from key (game:GAME_ID)
        if game_key.startswith('game:') and ':' not in game_key[5:]:
            game_id = game_key[5:]
            
            print(f"Migrating game: {game_id}")
            fixed_count = migrate_game_interactions(game_id)
            
            if fixed_count > 0:
                print(f"  Fixed {fixed_count} interaction(s)")
                total_fixed += fixed_count
                games_fixed += 1
            else:
                print(f"  No interactions to fix")
    
    print()
    print("=" * 80)
    print("MIGRATION COMPLETE")
    print("=" * 80)
    print(f"Games processed: {len(game_keys)}")
    print(f"Games with fixes: {games_fixed}")
    print(f"Total interactions fixed: {total_fixed}")
    print()


def verify_game_interactions(game_id: str):
    """
    Verify that all interactions in a game have the required fields
    """
    r = get_redis_connection()
    game_key = f"game:{game_id}"
    
    if not r.exists(game_key):
        print(f"Game {game_id} not found")
        return
    
    interactions_json = r.hget(game_key, 'interactions')
    if not interactions_json:
        print(f"Game {game_id} has no interactions")
        return
    
    interactions = json.loads(interactions_json)
    
    print(f"Verifying {len(interactions)} interactions in game {game_id}:")
    print()
    
    errors = []
    for i, interaction in enumerate(interactions):
        print(f"Interaction {i + 1}:")
        
        # Check 'name' field
        if 'name' not in interaction:
            errors.append(f"  Interaction {i} missing 'name' field")
            print(f"  name: MISSING")
        elif interaction['name'] is None:
            errors.append(f"  Interaction {i} has 'name' = None")
            print(f"  name: None")
        else:
            print(f"  name: '{interaction['name']}'")
        
        # Check 'type' field
        if 'type' in interaction:
            print(f"  type: {interaction['type']}")
        else:
            print(f"  type: MISSING")
        
        # Check 'value' field
        if 'value' in interaction:
            print(f"  value: {interaction['value']}")
        else:
            print(f"  value: MISSING")
        
        print()
    
    if errors:
        print("ERRORS FOUND:")
        for error in errors:
            print(f"  {error}")
        return False
    else:
        print("All interactions have required fields!")
        return True


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "verify":
            if len(sys.argv) > 2:
                verify_game_interactions(sys.argv[2])
            else:
                print("Usage: python migrate_interactions.py verify GAME_ID")
        else:
            print("Usage:")
            print("  python migrate_interactions.py              # Migrate all games")
            print("  python migrate_interactions.py verify GAME_ID  # Verify a specific game")
    else:
        migrate_all_games()

