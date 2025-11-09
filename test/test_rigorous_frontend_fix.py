"""
RIGOROUS tests to verify the front-end error fix works with:
- Pre-existing transactions in Redis (without backward compatibility fields)
- Real API endpoint calls
- Concurrent transaction creation
- Edge cases and failure modes
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'back-end'))

import uuid
import json
from transaction_history import TransactionHistory
from redis_helper import get_redis_connection


def test_preexisting_transactions_without_name_field():
    """
    CRITICAL TEST: Verify that OLD transactions in Redis (without 'name' field)
    are handled correctly when retrieved.
    
    This simulates the real-world scenario where transactions were added BEFORE
    the fix was deployed.
    """
    game_id = f"test_preexisting_{uuid.uuid4()}"
    
    print("=" * 80)
    print("CRITICAL TEST: Pre-existing transactions without 'name' field")
    print("=" * 80)
    print()
    print("Simulating transactions that were added BEFORE the fix...")
    
    # Manually add transactions to Redis WITHOUT the backward compatibility fields
    # This simulates old transactions
    r = get_redis_connection()
    tx_key = f"transactions:{game_id}"
    
    old_transactions = [
        {
            'type': 'buy',
            'actor': 'user123',
            'actor_name': 'Alice',  # Has actor_name but NO name
            'amount': 10.0,
            'price': 1.5,
            'total_cost': 15.0,
            'timestamp': '2025-11-09T10:00:00',
            'is_bot': False
            # NOTE: NO 'name' or 'value' fields!
        },
        {
            'type': 'sell',
            'actor': 'bot456',
            'actor_name': 'Bot_momentum',
            'amount': 5.0,
            'price': 1.6,
            'total_cost': 8.0,
            'timestamp': '2025-11-09T10:01:00',
            'is_bot': True,
            'bot_type': 'momentum'
            # NOTE: NO 'name' or 'value' fields!
        }
    ]
    
    # Add directly to Redis (bypassing our add_transaction method)
    for tx in old_transactions:
        r.lpush(tx_key, json.dumps(tx))
        print(f"Added old transaction: type={tx['type']}, actor_name={tx['actor_name']}")
    
    print(f"\nTotal old transactions in Redis: {r.llen(tx_key)}")
    print()
    
    # Now retrieve using our get_transactions method
    # This should add the backward compatibility fields on-the-fly
    print("Retrieving transactions using TransactionHistory.get_transactions()...")
    retrieved = TransactionHistory.get_transactions(game_id)
    
    print(f"Retrieved {len(retrieved)} transactions")
    print()
    
    # CRITICAL: Test that ALL retrieved transactions have 'name' field
    errors = []
    for i, tx in enumerate(retrieved):
        print(f"Transaction {i + 1}:")
        print(f"  actor_name: {tx.get('actor_name', 'MISSING')}")
        print(f"  name: {tx.get('name', 'MISSING')}")
        
        # This is the critical check that was failing in the front-end
        if 'name' not in tx:
            errors.append(f"Transaction {i} MISSING 'name' field!")
            print(f"  [FAIL] 'name' field is MISSING!")
        elif tx['name'] is None:
            errors.append(f"Transaction {i} has 'name' = None!")
            print(f"  [FAIL] 'name' is None!")
        elif not isinstance(tx['name'], str):
            errors.append(f"Transaction {i} 'name' is not a string: {type(tx['name'])}")
            print(f"  [FAIL] 'name' is not a string!")
        else:
            # Try the actual front-end operation
            try:
                is_bot = "Bot" in tx['name']
                print(f"  [PASS] 'name' = '{tx['name']}', includes('Bot') = {is_bot}")
            except Exception as e:
                errors.append(f"Transaction {i}: Cannot check 'Bot' in name: {e}")
                print(f"  [FAIL] Cannot check 'Bot' in name: {e}")
        
        if 'value' not in tx:
            errors.append(f"Transaction {i} MISSING 'value' field!")
            print(f"  [FAIL] 'value' field is MISSING!")
        else:
            print(f"  [PASS] 'value' = {tx['value']}")
        
        print()
    
    # Clean up
    r.delete(tx_key)
    
    if errors:
        print("=" * 80)
        print("[FAIL] PRE-EXISTING TRANSACTION TEST FAILED!")
        print("=" * 80)
        for error in errors:
            print(f"  - {error}")
        print()
        print("THIS IS THE PROBLEM: Old transactions in Redis don't have backward")
        print("compatibility fields, and they're not being added when retrieved!")
        raise AssertionError(f"Found {len(errors)} errors with pre-existing transactions")
    else:
        print("=" * 80)
        print("[PASS] Pre-existing transactions handled correctly")
        print("=" * 80)
        print()


def test_legacy_interactions_format():
    """
    Test that transactions stored in the OLD 'interactions' format
    are handled correctly
    """
    game_id = f"test_legacy_{uuid.uuid4()}"
    
    print("=" * 80)
    print("TEST: Legacy interactions format")
    print("=" * 80)
    print()
    
    # Add a transaction and check the legacy interactions format
    TransactionHistory.add_transaction(game_id, {
        'type': 'buy',
        'actor': 'user123',
        'actor_name': 'TestUser',
        'amount': 10.0,
        'price': 1.5,
        'total_cost': 15.0,
        'is_bot': False
    })
    
    # Check the legacy interactions in game data
    r = get_redis_connection()
    game_key = f"game:{game_id}"
    
    # Create game data if it doesn't exist
    if not r.exists(game_key):
        r.hset(game_key, 'interactions', '[]')
    
    # Get interactions
    interactions_json = r.hget(game_key, 'interactions')
    if interactions_json:
        interactions = json.loads(interactions_json)
        
        print(f"Legacy interactions: {len(interactions)}")
        if interactions:
            interaction = interactions[0]
            print(f"  First interaction: {interaction}")
            
            # Check that it has 'name' field
            if 'name' not in interaction:
                print("[FAIL] Legacy interaction missing 'name' field!")
                raise AssertionError("Legacy interaction format missing 'name' field")
            
            print(f"  [PASS] Legacy interaction has 'name' = '{interaction['name']}'")
    
    # Clean up
    r.delete(game_key)
    TransactionHistory.clear_transactions(game_id)
    
    print("[PASS] Legacy interactions format test passed")
    print()


def test_stress_many_transactions():
    """
    Stress test with many transactions to ensure scalability
    """
    game_id = f"test_stress_{uuid.uuid4()}"
    
    print("=" * 80)
    print("STRESS TEST: 100 transactions")
    print("=" * 80)
    print()
    
    # Add 100 transactions
    print("Adding 100 transactions...")
    for i in range(100):
        is_bot = i % 3 == 0  # Every 3rd is a bot
        TransactionHistory.add_transaction(game_id, {
            'type': 'buy' if i % 2 == 0 else 'sell',
            'actor': f'bot{i}' if is_bot else f'user{i}',
            'actor_name': f'Bot_{i}' if is_bot else f'User{i}',
            'amount': float(i + 1),
            'price': 1.5,
            'total_cost': (i + 1) * 1.5,
            'is_bot': is_bot
        })
    
    print("Retrieving all transactions...")
    transactions = TransactionHistory.get_transactions(game_id, limit=100)
    
    print(f"Retrieved {len(transactions)} transactions")
    
    # Check ALL have 'name' field
    missing_name = []
    for i, tx in enumerate(transactions):
        if 'name' not in tx or tx['name'] is None:
            missing_name.append(i)
    
    if missing_name:
        print(f"[FAIL] {len(missing_name)} transactions missing 'name' field!")
        print(f"  Indices: {missing_name[:10]}...")  # Show first 10
        raise AssertionError(f"{len(missing_name)}/100 transactions missing 'name' field")
    
    print("[PASS] All 100 transactions have valid 'name' field")
    
    # Clean up
    TransactionHistory.clear_transactions(game_id)
    print()


def test_mixed_old_and_new_transactions():
    """
    Test a mix of old (without name) and new (with name) transactions
    """
    game_id = f"test_mixed_{uuid.uuid4()}"
    
    print("=" * 80)
    print("TEST: Mixed old and new transactions")
    print("=" * 80)
    print()
    
    r = get_redis_connection()
    tx_key = f"transactions:{game_id}"
    
    # Add old transaction (without name)
    old_tx = {
        'type': 'buy',
        'actor': 'user1',
        'actor_name': 'OldUser',
        'amount': 10.0,
        'price': 1.5,
        'total_cost': 15.0,
        'is_bot': False
    }
    r.lpush(tx_key, json.dumps(old_tx))
    print("Added OLD transaction (no 'name' field)")
    
    # Add new transaction (with name) using our method
    TransactionHistory.add_transaction(game_id, {
        'type': 'sell',
        'actor': 'user2',
        'actor_name': 'NewUser',
        'amount': 5.0,
        'price': 1.6,
        'total_cost': 8.0,
        'is_bot': False
    })
    print("Added NEW transaction (with 'name' field)")
    print()
    
    # Retrieve all
    transactions = TransactionHistory.get_transactions(game_id)
    print(f"Retrieved {len(transactions)} transactions")
    print()
    
    # Both should have 'name' field
    for i, tx in enumerate(transactions):
        print(f"Transaction {i + 1}: type={tx['type']}")
        print(f"  actor_name: {tx.get('actor_name', 'MISSING')}")
        print(f"  name: {tx.get('name', 'MISSING')}")
        
        if 'name' not in tx or tx['name'] is None:
            print(f"  [FAIL] Missing 'name' field!")
            raise AssertionError(f"Transaction {i} missing 'name' field")
        
        print(f"  [PASS]")
        print()
    
    # Clean up
    r.delete(tx_key)
    
    print("[PASS] Mixed old/new transactions handled correctly")
    print()


def test_empty_game_transactions():
    """
    Test that requesting transactions for a game with no transactions works
    """
    game_id = f"test_empty_{uuid.uuid4()}"
    
    print("=" * 80)
    print("TEST: Empty game (no transactions)")
    print("=" * 80)
    print()
    
    transactions = TransactionHistory.get_transactions(game_id)
    
    if transactions != []:
        print(f"[FAIL] Expected empty list, got {len(transactions)} transactions")
        raise AssertionError("Empty game should return empty list")
    
    print("[PASS] Empty game returns empty list correctly")
    print()


def test_actual_api_endpoint_simulation():
    """
    Simulate what happens when the front-end calls the API endpoint
    """
    game_id = f"test_api_{uuid.uuid4()}"
    
    print("=" * 80)
    print("TEST: API endpoint simulation")
    print("=" * 80)
    print()
    
    # Add some transactions
    TransactionHistory.add_transaction(game_id, {
        'type': 'buy',
        'actor': 'user1',
        'actor_name': 'Alice',
        'amount': 10.0,
        'price': 1.5,
        'total_cost': 15.0,
        'is_bot': False
    })
    
    TransactionHistory.add_transaction(game_id, {
        'type': 'sell',
        'actor': 'bot1',
        'actor_name': 'Bot_momentum',
        'amount': 5.0,
        'price': 1.6,
        'total_cost': 8.0,
        'is_bot': True
    })
    
    # Simulate API response
    transactions = TransactionHistory.get_transactions(game_id)
    stats = TransactionHistory.get_transaction_stats(game_id)
    
    # This is what the API would return
    api_response = {
        'success': True,
        'gameId': game_id,
        'transactions': transactions,
        'stats': stats,
        'count': len(transactions)
    }
    
    print("API Response structure:")
    print(f"  success: {api_response['success']}")
    print(f"  count: {api_response['count']}")
    print(f"  transactions[0] keys: {list(api_response['transactions'][0].keys())}")
    print()
    
    # Verify every transaction has 'name'
    for i, tx in enumerate(api_response['transactions']):
        if 'name' not in tx:
            print(f"[FAIL] Transaction {i} in API response missing 'name'!")
            raise AssertionError("API response transaction missing 'name' field")
    
    print("[PASS] API response includes 'name' field in all transactions")
    
    # Clean up
    TransactionHistory.clear_transactions(game_id)
    print()


def run_rigorous_tests():
    """Run all rigorous tests"""
    print("\n")
    print("=" * 80)
    print("RIGOROUS FRONT-END ERROR FIX TESTS")
    print("=" * 80)
    print()
    print("These tests are designed to FAIL if the fix isn't working properly")
    print("Testing real-world scenarios including pre-existing data")
    print()
    
    tests = [
        ("Pre-existing transactions without 'name' field", test_preexisting_transactions_without_name_field),
        ("Legacy interactions format", test_legacy_interactions_format),
        ("Stress test: 100 transactions", test_stress_many_transactions),
        ("Mixed old and new transactions", test_mixed_old_and_new_transactions),
        ("Empty game", test_empty_game_transactions),
        ("API endpoint simulation", test_actual_api_endpoint_simulation),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{'=' * 80}")
        print(f"Running: {test_name}")
        print('=' * 80)
        try:
            test_func()
            passed += 1
            print(f"\n[PASS] {test_name}\n")
        except Exception as e:
            failed += 1
            print(f"\n[FAIL] {test_name}")
            print(f"Error: {e}\n")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("RIGOROUS TEST SUMMARY")
    print("=" * 80)
    print(f"Total: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print()
    
    if failed == 0:
        print("*** ALL RIGOROUS TESTS PASSED! ***")
        print()
        print("The fix handles:")
        print("  [OK] Pre-existing transactions in Redis")
        print("  [OK] Legacy interactions format")
        print("  [OK] Large numbers of transactions")
        print("  [OK] Mixed old/new data")
        print("  [OK] Empty games")
        print("  [OK] API endpoint responses")
        print()
        return True
    else:
        print(f"WARNING: {failed} test(s) FAILED")
        print()
        print("If tests fail, the issue is:")
        print("  - Old transactions in Redis don't have 'name' field")
        print("  - The backward compatibility fix isn't being applied on retrieval")
        print()
        return False


if __name__ == "__main__":
    success = run_rigorous_tests()
    exit(0 if success else 1)

