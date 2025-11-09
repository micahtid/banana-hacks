"""
Test backward compatibility for transaction history
Ensures that transactions have all required fields for front-end
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'back-end'))

import uuid
from transaction_history import TransactionHistory


def test_transaction_backward_compatibility():
    """Test that transactions have all required fields for front-end"""
    game_id = f"test_backward_compat_{uuid.uuid4()}"
    
    # Add a transaction with new format (actor_name, amount)
    transaction = {
        'type': 'buy',
        'actor': 'user123',
        'actor_name': 'Test User',
        'amount': 10.0,
        'price': 1.5,
        'total_cost': 15.0,
        'is_bot': False
    }
    
    success = TransactionHistory.add_transaction(game_id, transaction)
    assert success, "Adding transaction should succeed"
    
    # Retrieve the transaction
    transactions = TransactionHistory.get_transactions(game_id)
    assert len(transactions) == 1, "Should have 1 transaction"
    
    tx = transactions[0]
    
    # Check that it has BOTH new and old format fields
    print(f"Transaction fields: {tx.keys()}")
    
    # New format fields
    assert 'actor' in tx, "Should have 'actor' field"
    assert 'actor_name' in tx, "Should have 'actor_name' field"
    assert 'amount' in tx, "Should have 'amount' field"
    assert 'price' in tx, "Should have 'price' field"
    assert 'total_cost' in tx, "Should have 'total_cost' field"
    assert 'timestamp' in tx, "Should have 'timestamp' field"
    
    # Old format fields (for backward compatibility)
    assert 'name' in tx, "Should have 'name' field for backward compatibility"
    assert 'value' in tx, "Should have 'value' field for backward compatibility"
    assert 'type' in tx, "Should have 'type' field"
    
    # Check values are correct
    assert tx['name'] == 'Test User', f"'name' should be 'Test User', got {tx.get('name')}"
    assert tx['actor_name'] == 'Test User', "'actor_name' should be 'Test User'"
    assert tx['value'] == 1000, f"'value' should be 1000 (cents), got {tx.get('value')}"
    assert tx['amount'] == 10.0, "'amount' should be 10.0"
    
    # Check that name is not None (the original error)
    assert tx['name'] is not None, "'name' field should not be None"
    assert isinstance(tx['name'], str), "'name' should be a string"
    
    print("[PASS] Transaction has all required fields for front-end compatibility")
    print(f"  - name: {tx['name']}")
    print(f"  - actor_name: {tx['actor_name']}")
    print(f"  - value: {tx['value']}")
    print(f"  - amount: {tx['amount']}")
    
    # Clean up
    TransactionHistory.clear_transactions(game_id)


def test_bot_transaction_backward_compatibility():
    """Test that bot transactions have all required fields"""
    game_id = f"test_bot_compat_{uuid.uuid4()}"
    
    # Add a bot transaction
    transaction = {
        'type': 'sell',
        'actor': 'bot456',
        'actor_name': 'Bot_bot456',
        'amount': 5.0,
        'price': 1.6,
        'total_cost': 8.0,
        'is_bot': True,
        'bot_type': 'momentum',
        'user_id': 'user123'
    }
    
    success = TransactionHistory.add_transaction(game_id, transaction)
    assert success, "Adding bot transaction should succeed"
    
    # Retrieve the transaction
    transactions = TransactionHistory.get_transactions(game_id)
    assert len(transactions) == 1, "Should have 1 transaction"
    
    tx = transactions[0]
    
    # Check backward compatibility fields
    assert 'name' in tx, "Bot transaction should have 'name' field"
    assert tx['name'] == 'Bot_bot456', f"Bot name should be 'Bot_bot456', got {tx.get('name')}"
    assert 'Bot' in tx['name'], "Bot name should contain 'Bot'"
    
    # This is the specific check that was failing in the front-end
    assert tx['name'].startswith('Bot_'), "Bot name should start with 'Bot_'"
    
    print("[PASS] Bot transaction has all required fields")
    print(f"  - name: {tx['name']}")
    print(f"  - is_bot: {tx['is_bot']}")
    
    # Clean up
    TransactionHistory.clear_transactions(game_id)


def test_multiple_transactions_all_have_name():
    """Test that all transactions in a list have the 'name' field"""
    game_id = f"test_multi_{uuid.uuid4()}"
    
    # Add multiple transactions
    transactions_to_add = [
        {'type': 'buy', 'actor': 'user1', 'actor_name': 'Alice', 'amount': 10.0, 'price': 1.5, 'total_cost': 15.0, 'is_bot': False},
        {'type': 'sell', 'actor': 'bot1', 'actor_name': 'Bot_abc', 'amount': 5.0, 'price': 1.6, 'total_cost': 8.0, 'is_bot': True},
        {'type': 'buy', 'actor': 'user2', 'actor_name': 'Bob', 'amount': 8.0, 'price': 1.4, 'total_cost': 11.2, 'is_bot': False},
    ]
    
    for tx in transactions_to_add:
        TransactionHistory.add_transaction(game_id, tx)
    
    # Retrieve all transactions
    retrieved = TransactionHistory.get_transactions(game_id)
    assert len(retrieved) == 3, f"Should have 3 transactions, got {len(retrieved)}"
    
    # Check that ALL transactions have the 'name' field and it's not None
    for i, tx in enumerate(retrieved):
        assert 'name' in tx, f"Transaction {i} missing 'name' field"
        assert tx['name'] is not None, f"Transaction {i} has None for 'name'"
        assert isinstance(tx['name'], str), f"Transaction {i} 'name' is not a string"
        print(f"  Transaction {i}: name='{tx['name']}', type={tx['type']}")
    
    print(f"[PASS] All {len(retrieved)} transactions have valid 'name' field")
    
    # Clean up
    TransactionHistory.clear_transactions(game_id)


if __name__ == "__main__":
    print("=" * 80)
    print("TRANSACTION BACKWARD COMPATIBILITY TESTS")
    print("=" * 80)
    print()
    
    try:
        test_transaction_backward_compatibility()
        print()
        test_bot_transaction_backward_compatibility()
        print()
        test_multiple_transactions_all_have_name()
        print()
        print("=" * 80)
        print("ALL BACKWARD COMPATIBILITY TESTS PASSED!")
        print("=" * 80)
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

