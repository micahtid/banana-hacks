"""
Test that verifies the EXACT front-end scenario works:
1. Game data is loaded from Redis
2. Interactions are parsed
3. interaction.name exists for all interactions
4. interaction.name.includes("Bot") works
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'back-end'))

import uuid
import json
from redis_helper import get_redis_connection
from transaction_history import TransactionHistory


def test_frontend_api_flow():
    """
    Test the EXACT flow that the front-end uses:
    1. Create a game with interactions
    2. Load game data from Redis (as the API does)
    3. Parse interactions
    4. Verify interaction.name exists and works
    """
    game_id = f"test_frontend_api_{uuid.uuid4()}"
    
    print("=" * 80)
    print("FRONTEND API INTEGRATION TEST")
    print("=" * 80)
    print()
    print("Simulating EXACT front-end data flow...")
    print()
    
    # Step 1: Create a game in Redis with interactions
    r = get_redis_connection()
    game_key = f"game:{game_id}"
    
    # Add some transactions using our TransactionHistory
    print("Step 1: Adding transactions...")
    TransactionHistory.add_transaction(game_id, {
        'type': 'buy',
        'actor': 'user123',
        'actor_name': 'Alice',
        'amount': 10.0,
        'price': 1.5,
        'total_cost': 15.0,
        'is_bot': False
    })
    
    TransactionHistory.add_transaction(game_id, {
        'type': 'sell',
        'actor': 'bot456',
        'actor_name': 'Bot_momentum_abc',
        'amount': 5.0,
        'price': 1.6,
        'total_cost': 8.0,
        'is_bot': True,
        'bot_type': 'momentum'
    })
    print("  Added 2 transactions")
    print()
    
    # Step 2: Simulate what the API route does
    # This is from front-end/app/api/game/[gameId]/route.ts line 33
    print("Step 2: Loading game data from Redis (as API does)...")
    
    if not r.exists(game_key):
        print("  Creating game data structure...")
        r.hset(game_key, mapping={
            'gameId': game_id,
            'isStarted': 'true',
            'interactions': '[]'
        })
    
    game_data = r.hgetall(game_key)
    print("  Loaded game data from Redis")
    print()
    
    # Step 3: Parse interactions (as the API does)
    print("Step 3: Parsing interactions from JSON...")
    interactions_json = game_data.get('interactions', '[]')
    if isinstance(interactions_json, bytes):
        interactions_json = interactions_json.decode('utf-8')
    
    interactions = json.loads(interactions_json)
    print(f"  Parsed {len(interactions)} interactions")
    print()
    
    # Step 4: Simulate what the Transactions component does
    print("Step 4: Simulating Transactions.tsx code...")
    print()
    print("  // Line 18: const interactions = game.interactions || [];")
    print(f"  interactions.length = {len(interactions)}")
    print()
    
    if len(interactions) == 0:
        print("  WARNING: No interactions found!")
        print("  This might be because interactions aren't being saved to the legacy format")
        print()
        # Clean up and return
        r.delete(game_key)
        TransactionHistory.clear_transactions(game_id)
        raise AssertionError("No interactions found in game data!")
    
    errors = []
    
    for index, interaction in enumerate(interactions):
        print(f"  Interaction {index + 1}:")
        print(f"    Data: {interaction}")
        
        # Line 133: const isCurrentUser = interaction.name === currentUser.userName;
        try:
            name = interaction.get('name')
            print(f"    interaction.name = '{name}'")
            
            if name is None:
                errors.append(f"Interaction {index}: 'name' is None")
                print(f"    [FAIL] 'name' is None - THIS CAUSES THE ERROR!")
                continue
            
            if not isinstance(name, str):
                errors.append(f"Interaction {index}: 'name' is not a string")
                print(f"    [FAIL] 'name' is not a string: {type(name)}")
                continue
            
        except KeyError:
            errors.append(f"Interaction {index}: 'name' field missing")
            print(f"    [FAIL] 'name' field missing - THIS CAUSES THE ERROR!")
            continue
        
        # Line 134: const isBot = interaction.name.includes("Bot");
        try:
            is_bot = "Bot" in name
            print(f"    interaction.name.includes('Bot') = {is_bot}")
            print(f"    [PASS]")
        except Exception as e:
            errors.append(f"Interaction {index}: Cannot check 'Bot' in name: {e}")
            print(f"    [FAIL] Cannot check 'Bot' in name: {e}")
        
        print()
    
    # Clean up
    r.delete(game_key)
    TransactionHistory.clear_transactions(game_id)
    
    if errors:
        print("=" * 80)
        print("[FAIL] FRONTEND API INTEGRATION TEST FAILED")
        print("=" * 80)
        for error in errors:
            print(f"  {error}")
        print()
        raise AssertionError(f"Found {len(errors)} errors in front-end API flow")
    else:
        print("=" * 80)
        print("[PASS] Frontend API integration works correctly!")
        print("=" * 80)
        print()


def test_migration_script_effectiveness():
    """
    Test that the migration script actually fixes the problem
    """
    game_id = f"test_migration_{uuid.uuid4()}"
    
    print("=" * 80)
    print("MIGRATION SCRIPT EFFECTIVENESS TEST")
    print("=" * 80)
    print()
    
    r = get_redis_connection()
    game_key = f"game:{game_id}"
    
    # Create a game with OLD format interactions (missing 'name' field)
    print("Creating game with OLD format interactions (missing 'name')...")
    old_interactions = [
        {
            'interactionName': 'Alice',
            'type': 'buy',
            'value': 1000
            # NOTE: NO 'name' field!
        },
        {
            'interactionName': 'Bot_test',
            'type': 'sell',
            'value': 500
            # NOTE: NO 'name' field!
        }
    ]
    
    r.hset(game_key, mapping={
        'gameId': game_id,
        'interactions': json.dumps(old_interactions)
    })
    print(f"  Created game with {len(old_interactions)} old-format interactions")
    print()
    
    # Verify they don't have 'name' field
    print("Verifying interactions are missing 'name' field...")
    game_data = r.hgetall(game_key)
    interactions = json.loads(game_data['interactions'])
    
    for i, interaction in enumerate(interactions):
        if 'name' in interaction:
            print(f"  [UNEXPECTED] Interaction {i} already has 'name' field")
        else:
            print(f"  [OK] Interaction {i} missing 'name' field (as expected)")
    print()
    
    # Run migration
    print("Running migration...")
    from migrate_interactions import migrate_game_interactions
    fixed_count = migrate_game_interactions(game_id)
    print(f"  Migration fixed {fixed_count} interaction(s)")
    print()
    
    # Verify they now have 'name' field
    print("Verifying interactions now have 'name' field...")
    game_data = r.hgetall(game_key)
    interactions = json.loads(game_data['interactions'])
    
    errors = []
    for i, interaction in enumerate(interactions):
        if 'name' not in interaction:
            errors.append(f"Interaction {i} still missing 'name' field after migration!")
            print(f"  [FAIL] Interaction {i} still missing 'name'")
        elif interaction['name'] is None:
            errors.append(f"Interaction {i} has 'name' = None after migration!")
            print(f"  [FAIL] Interaction {i} has 'name' = None")
        else:
            print(f"  [PASS] Interaction {i} has 'name' = '{interaction['name']}'")
            
            # Test the .includes() check
            try:
                is_bot = "Bot" in interaction['name']
                print(f"    'Bot' in name = {is_bot}")
            except Exception as e:
                errors.append(f"Interaction {i}: Cannot check 'Bot' in name: {e}")
                print(f"    [FAIL] Cannot check 'Bot' in name: {e}")
    
    # Clean up
    r.delete(game_key)
    
    if errors:
        print()
        print("[FAIL] Migration didn't fix all interactions!")
        for error in errors:
            print(f"  {error}")
        raise AssertionError("Migration script didn't work correctly")
    else:
        print()
        print("[PASS] Migration successfully fixed all interactions!")
        print()


if __name__ == "__main__":
    print("\n")
    
    tests = [
        ("Frontend API integration flow", test_frontend_api_flow),
        ("Migration script effectiveness", test_migration_script_effectiveness)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"\n[FAIL] {test_name}")
            print(f"Error: {e}\n")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("FRONTEND API INTEGRATION TEST SUMMARY")
    print("=" * 80)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    print()
    
    if failed == 0:
        print("*** ALL TESTS PASSED! ***")
        print()
        print("The error 'interaction.name is undefined' should be FIXED")
        print()
        print("What was fixed:")
        print("  1. TransactionHistory adds 'name' field on retrieval")
        print("  2. TransactionHistory adds 'name' field when storing")
        print("  3. Migration script fixed existing interactions in Redis")
        print("  4. All interactions now have 'name' field")
        print()
        exit(0)
    else:
        print(f"WARNING: {failed} test(s) failed")
        exit(1)

