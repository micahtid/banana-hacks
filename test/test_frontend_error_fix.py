"""
Test to verify the exact front-end error is fixed:
"can't access property 'includes', interaction.name is undefined"

This test simulates the exact conditions that caused the front-end crash.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'back-end'))

import uuid
from transaction_history import TransactionHistory


def test_interaction_name_is_never_undefined():
    """
    Test the EXACT error condition from the front-end:
    interaction.name must NEVER be undefined
    
    Front-end code at line 134:
    const isBot = interaction.name.includes("Bot");
    
    This was failing because interaction.name was undefined.
    """
    game_id = f"test_frontend_fix_{uuid.uuid4()}"
    
    print("Testing the exact front-end error condition...")
    print("Front-end code: const isBot = interaction.name.includes('Bot');")
    print()
    
    # Add various types of transactions (user and bot)
    test_transactions = [
        {
            'type': 'buy',
            'actor': 'user123',
            'actor_name': 'Alice',
            'amount': 10.0,
            'price': 1.5,
            'total_cost': 15.0,
            'is_bot': False
        },
        {
            'type': 'sell',
            'actor': 'bot456',
            'actor_name': 'Bot_momentum_123',
            'amount': 5.0,
            'price': 1.6,
            'total_cost': 8.0,
            'is_bot': True,
            'bot_type': 'momentum'
        },
        {
            'type': 'buy',
            'actor': 'bot789',
            'actor_name': 'Bot_abc',
            'amount': 3.0,
            'price': 1.4,
            'total_cost': 4.2,
            'is_bot': True,
            'bot_type': 'random'
        },
        {
            'type': 'sell',
            'actor': 'user456',
            'actor_name': 'Bob',
            'amount': 8.0,
            'price': 1.55,
            'total_cost': 12.4,
            'is_bot': False
        }
    ]
    
    # Add all transactions
    for tx in test_transactions:
        success = TransactionHistory.add_transaction(game_id, tx)
        assert success, f"Failed to add transaction: {tx}"
    
    # Retrieve transactions (as the front-end would)
    interactions = TransactionHistory.get_transactions(game_id)
    
    print(f"Retrieved {len(interactions)} transactions")
    print()
    
    # Test EACH transaction (simulating front-end code)
    for index, interaction in enumerate(interactions):
        print(f"Testing transaction {index + 1}/{len(interactions)}:")
        print(f"  Type: {interaction.get('type', 'MISSING')}")
        print(f"  Actor: {interaction.get('actor', 'MISSING')}")
        
        # This is the EXACT line that was failing in the front-end
        # Line 133: const isCurrentUser = interaction.name === currentUser.userName;
        interaction_name = interaction.get('name')
        print(f"  interaction.name: '{interaction_name}'")
        
        # CRITICAL TEST: name must NOT be undefined/None
        assert interaction_name is not None, \
            f"ERROR: interaction.name is None/undefined at index {index}! This would cause the front-end error."
        
        # CRITICAL TEST: name must be a string so we can call .includes()
        assert isinstance(interaction_name, str), \
            f"ERROR: interaction.name is not a string (type: {type(interaction_name)}). Cannot call .includes()."
        
        # This is the EXACT line that was crashing (line 134)
        # const isBot = interaction.name.includes("Bot");
        try:
            is_bot = "Bot" in interaction_name  # Python equivalent of JavaScript's .includes()
            print(f"  interaction.name.includes('Bot'): {is_bot} [SUCCESS]")
        except Exception as e:
            raise AssertionError(
                f"ERROR: Cannot call .includes() on interaction.name! "
                f"This is the exact front-end error. Exception: {e}"
            )
        
        # Verify is_bot detection works correctly
        if interaction.get('is_bot'):
            assert is_bot, f"Bot transaction should have 'Bot' in name, got: {interaction_name}"
            print(f"  [OK] Bot transaction correctly identified")
        else:
            assert not is_bot, f"User transaction should NOT have 'Bot' in name, got: {interaction_name}"
            print(f"  [OK] User transaction correctly identified")
        
        print()
    
    print("=" * 80)
    print("[PASS] Front-end error is FIXED!")
    print("=" * 80)
    print("[OK] All transactions have valid 'name' field")
    print("[OK] interaction.name is NEVER undefined")
    print("[OK] interaction.name.includes('Bot') works correctly")
    print("[OK] No TypeError will occur in the front-end")
    print()
    
    # Clean up
    TransactionHistory.clear_transactions(game_id)


def test_edge_cases_for_name_field():
    """Test edge cases that could cause interaction.name to be undefined"""
    game_id = f"test_edge_cases_{uuid.uuid4()}"
    
    print("Testing edge cases...")
    
    # Edge case 1: Transaction with empty actor_name
    tx1 = {
        'type': 'buy',
        'actor': 'user1',
        'actor_name': '',  # Empty string
        'amount': 1.0,
        'price': 1.0,
        'total_cost': 1.0,
        'is_bot': False
    }
    TransactionHistory.add_transaction(game_id, tx1)
    
    # Edge case 2: Transaction with very long name
    tx2 = {
        'type': 'sell',
        'actor': 'bot1',
        'actor_name': 'Bot_' + 'x' * 100,
        'amount': 1.0,
        'price': 1.0,
        'total_cost': 1.0,
        'is_bot': True
    }
    TransactionHistory.add_transaction(game_id, tx2)
    
    # Edge case 3: Transaction with special characters in name
    tx3 = {
        'type': 'buy',
        'actor': 'user2',
        'actor_name': 'User@#$%^&*()',
        'amount': 1.0,
        'price': 1.0,
        'total_cost': 1.0,
        'is_bot': False
    }
    TransactionHistory.add_transaction(game_id, tx3)
    
    # Retrieve and test all edge cases
    interactions = TransactionHistory.get_transactions(game_id)
    
    for i, interaction in enumerate(interactions):
        name = interaction.get('name')
        
        # Must not be None
        assert name is not None, f"Edge case {i}: name is None"
        
        # Must be a string
        assert isinstance(name, str), f"Edge case {i}: name is not a string"
        
        # .includes() must work (even with empty string or special chars)
        try:
            _ = "Bot" in name
        except Exception as e:
            raise AssertionError(f"Edge case {i}: Cannot check 'Bot' in name: {e}")
        
        print(f"  Edge case {i + 1}: name='{name[:50]}...' [PASS]")
    
    print("[PASS] All edge cases handled correctly")
    print()
    
    # Clean up
    TransactionHistory.clear_transactions(game_id)


def test_simulated_frontend_code():
    """
    Simulate the EXACT front-end code that was failing
    """
    game_id = f"test_frontend_sim_{uuid.uuid4()}"
    
    print("Simulating exact front-end code...")
    print()
    
    # Add test data
    TransactionHistory.add_transaction(game_id, {
        'type': 'buy',
        'actor': 'user1',
        'actor_name': 'TestUser',
        'amount': 10.0,
        'price': 1.5,
        'total_cost': 15.0,
        'is_bot': False
    })
    
    TransactionHistory.add_transaction(game_id, {
        'type': 'sell',
        'actor': 'bot1',
        'actor_name': 'Bot_test123',
        'amount': 5.0,
        'price': 1.6,
        'total_cost': 8.0,
        'is_bot': True
    })
    
    # Simulate front-end code
    game = {'interactions': TransactionHistory.get_transactions(game_id)}
    currentUser = {'userName': 'TestUser'}
    
    print("// Simulating Transactions.tsx lines 132-134:")
    print("sortedInteractions.map((interaction, index) => {")
    
    for index, interaction in enumerate(game['interactions']):
        print(f"\n  // Processing interaction {index}:")
        
        # Line 133: const isCurrentUser = interaction.name === currentUser.userName;
        try:
            isCurrentUser = interaction['name'] == currentUser['userName']
            print(f"  const isCurrentUser = {isCurrentUser}  // [OK] No error")
        except KeyError:
            raise AssertionError("ERROR: interaction['name'] is missing!")
        except TypeError as e:
            raise AssertionError(f"ERROR: Cannot compare interaction.name: {e}")
        
        # Line 134: const isBot = interaction.name.includes("Bot");
        try:
            # JavaScript: interaction.name.includes("Bot")
            # Python equivalent: "Bot" in interaction['name']
            isBot = "Bot" in interaction['name']
            print(f"  const isBot = {isBot}  // [OK] No error")
        except KeyError:
            raise AssertionError("ERROR: interaction['name'] is missing!")
        except AttributeError:
            raise AssertionError("ERROR: interaction.name is undefined/None!")
        except TypeError as e:
            raise AssertionError(f"ERROR: Cannot call .includes() on interaction.name: {e}")
        
        print(f"  // Transaction processed successfully!")
    
    print("\n})")
    print()
    print("[PASS] Front-end code simulation completed without errors!")
    print()
    
    # Clean up
    TransactionHistory.clear_transactions(game_id)


def run_all_tests():
    """Run all front-end error fix tests"""
    print("=" * 80)
    print("FRONT-END ERROR FIX VERIFICATION TESTS")
    print("=" * 80)
    print()
    print("Testing fix for:")
    print("  TypeError: can't access property 'includes', interaction.name is undefined")
    print("  at components/game/Transactions.tsx:134:29")
    print()
    print("=" * 80)
    print()
    
    tests = [
        ("Verify interaction.name is never undefined", test_interaction_name_is_never_undefined),
        ("Test edge cases", test_edge_cases_for_name_field),
        ("Simulate exact front-end code", test_simulated_frontend_code)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"Running: {test_name}")
        print("-" * 80)
        try:
            test_func()
            passed += 1
            print(f"[PASS] {test_name}")
        except Exception as e:
            failed += 1
            print(f"[FAIL] {test_name}")
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
        print()
    
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print()
    
    if failed == 0:
        print("*** ALL TESTS PASSED! ***")
        print()
        print("The front-end error is COMPLETELY FIXED:")
        print("  [OK] interaction.name is never undefined")
        print("  [OK] interaction.name.includes('Bot') works correctly")
        print("  [OK] Front-end Transactions component will work without errors")
        print()
        return True
    else:
        print(f"WARNING: {failed} test(s) failed")
        print()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

