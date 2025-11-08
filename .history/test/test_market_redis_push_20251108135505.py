"""
Test script to populate Redis with market data
"""
import sys
import os
import time

# Get the project root directory (works whether script is run from test/ or root/)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
back_end_dir = os.path.join(project_root, 'back-end')

# Add back-end directory to Python path
if back_end_dir not in sys.path:
    sys.path.insert(0, back_end_dir)

# Also add project root in case of relative imports
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now we can import from back-end
from market import Market
from redis_helper import get_redis_connection

def test_market_push():
    """Create a market, add users, update it, and save to Redis"""
    try:
        # Test Redis connection
        r = get_redis_connection()
        r.ping()
        print("[OK] Connected to Redis")
        
        # Create a market with a specific game_id for testing
        game_id = "test-game-001"
        print(f"\n--- Creating Market with game_id: {game_id} ---")
        
        market = Market(initial_price=1.0, game_id=game_id)
        print(f"✓ Market created")
        print(f"  - Initial price: ${market.market_data.current_price:.2f}")
        print(f"  - Current tick: {market.current_tick}")
        print(f"  - Users: {market.users}")
        
        # Add some users
        print(f"\n--- Adding Users ---")
        test_users = ["user1", "user2", "user3"]
        for user_id in test_users:
            market.addUser(user_id)
            print(f"✓ Added user: {user_id}")
        
        print(f"  - Total users: {len(market.users)}")
        print(f"  - Users list: {market.users}")
        
        # Update market several times
        print(f"\n--- Updating Market (5 times) ---")
        for i in range(5):
            market.updateMarket()
            print(f"  Update {i+1}: Price=${market.market_data.current_price:.4f}, "
                  f"Tick={market.current_tick}, Volatility={market.market_data.volatility:.4f}")
            time.sleep(0.5)  # Small delay to see updates
        
        print(f"\n--- Market Data Summary ---")
        print(f"  - Game ID: {market.game_id}")
        print(f"  - Start time: {market.start_time}")
        print(f"  - Current tick: {market.current_tick}")
        print(f"  - Current price: ${market.market_data.current_price:.4f}")
        print(f"  - Volatility: {market.market_data.volatility:.4f}")
        print(f"  - Price history length: {len(market.market_data.price_history)}")
        print(f"  - Users: {market.users}")
        
        print(f"\n✓ Market data saved to Redis!")
        print(f"  - Redis key: market:{game_id}")
        print(f"  - Redis key: market:{game_id}:data")
        
        return game_id
        
    except Exception as e:
        print(f"\n✗ An error occurred: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("Market Redis Push Test")
    print("=" * 60)
    game_id = test_market_push()
    if game_id:
        print(f"\n" + "=" * 60)
        print(f"Test completed successfully!")
        print(f"Run 'python test_market_redis_pull.py {game_id}' to retrieve the data")
        print("=" * 60)

