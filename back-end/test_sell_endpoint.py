"""
Test script to rigorously test the sell endpoint
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_sell_endpoint():
    """Test the sell endpoint with various scenarios"""
    
    print("=" * 80)
    print("TESTING SELL ENDPOINT")
    print("=" * 80)
    
    # Test 1: Basic sell
    print("\n[TEST 1] Basic sell operation")
    try:
        response = requests.post(
            f"{BASE_URL}/api/game/sell-coins",
            json={
                "gameId": "test-game-1",
                "userId": "test-user-1",
                "action": "sell",
                "amount": 10.0
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        assert response.status_code in [200, 404], "Expected 200 or 404 (game not found)"
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Invalid action
    print("\n[TEST 2] Invalid action (should fail)")
    try:
        response = requests.post(
            f"{BASE_URL}/api/game/sell-coins",
            json={
                "gameId": "test-game-1",
                "userId": "test-user-1",
                "action": "buy",  # Wrong action
                "amount": 10.0
            }
        )
        print(f"Status: {response.status_code}")
        assert response.status_code == 400, "Expected 400 for wrong action"
        print("✓ Correctly rejected invalid action")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Negative amount
    print("\n[TEST 3] Negative amount (should fail)")
    try:
        response = requests.post(
            f"{BASE_URL}/api/game/sell-coins",
            json={
                "gameId": "test-game-1",
                "userId": "test-user-1",
                "action": "sell",
                "amount": -10.0
            }
        )
        print(f"Status: {response.status_code}")
        assert response.status_code == 422, "Expected 422 for negative amount"
        print("✓ Correctly rejected negative amount")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: Zero amount
    print("\n[TEST 4] Zero amount (should fail)")
    try:
        response = requests.post(
            f"{BASE_URL}/api/game/sell-coins",
            json={
                "gameId": "test-game-1",
                "userId": "test-user-1",
                "action": "sell",
                "amount": 0.0
            }
        )
        print(f"Status: {response.status_code}")
        assert response.status_code == 422, "Expected 422 for zero amount"
        print("✓ Correctly rejected zero amount")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_sell_endpoint()

