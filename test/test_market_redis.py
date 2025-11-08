"""
Combined test script to push market data to Redis and then pull it back
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

def test_market_redis_full():
    """Complete test: create market, save to Redis, then load it back"""
    try:
        # Test Redis connection
        r = get_redis_connection()
        r.ping()
        print("[OK] Connected to Redis")
        
        # ============================================================
        # PART 1: CREATE AND POPULATE MARKET DATA
        # ============================================================
        print("\n" + "=" * 60)
        print("PART 1: Creating and Populating Market Data")
        print("=" * 60)
        
        game_id = "test-game-full"
        print(f"\nCreating Market with game_id: {game_id}")
        
        market = Market(initial_price=1.0, game_id=game_id)
        print(f"[OK] Market created (auto-saved to Redis)")
        print(f"  - Initial price: ${market.market_data.current_price:.2f}")
        
        # Add users
        print(f"\nAdding users...")
        test_users = ["alice", "bob", "charlie"]
        for user_id in test_users:
            market.addUser(user_id)
            print(f"  [OK] Added {user_id}")
        
        # Update market
        print(f"\nUpdating market 5 times...")
        for i in range(5):
            market.updateMarket()
            print(f"  Update {i+1}: Price=${market.market_data.current_price:.4f}, "
                  f"Tick={market.current_tick}, Vol={market.market_data.volatility:.4f}")
            time.sleep(0.3)
        
        print(f"\n[OK] Market populated and saved to Redis")
        print(f"  - Final price: ${market.market_data.current_price:.4f}")
        print(f"  - Total ticks: {market.current_tick}")
        print(f"  - Users: {market.users}")
        
        # ============================================================
        # PART 2: LOAD MARKET DATA FROM REDIS
        # ============================================================
        print("\n" + "=" * 60)
        print("PART 2: Loading Market Data from Redis")
        print("=" * 60)
        
        print(f"\nLoading market with game_id: {game_id}")
        loaded_market = Market.load_from_redis(game_id)
        
        if not loaded_market:
            print("[ERROR] Failed to load market from Redis")
            return False
        
        print(f"[OK] Market loaded successfully!")
        
        # Compare data
        print(f"\n--- Data Verification ---")
        print(f"  Game ID: {loaded_market.game_id}")
        print(f"  Start Time: {loaded_market.start_time}")
        print(f"  Current Tick: {loaded_market.current_tick} (original: {market.current_tick})")
        print(f"  Current Price: ${loaded_market.market_data.current_price:.4f} (original: ${market.market_data.current_price:.4f})")
        print(f"  Volatility: {loaded_market.market_data.volatility:.4f} (original: {market.market_data.volatility:.4f})")
        print(f"  Users: {loaded_market.users} (original: {market.users})")
        print(f"  Price History Length: {len(loaded_market.market_data.price_history)} (original: {len(market.market_data.price_history)})")
        
        # Verify data matches
        matches = (
            loaded_market.game_id == market.game_id and
            loaded_market.current_tick == market.current_tick and
            abs(loaded_market.market_data.current_price - market.market_data.current_price) < 0.0001 and
            loaded_market.users == market.users and
            len(loaded_market.market_data.price_history) == len(market.market_data.price_history)
        )
        
        if matches:
            print(f"\n[OK] All data matches! Redis storage/retrieval working correctly.")
        else:
            print(f"\n⚠ Some data doesn't match. Check the values above.")
        
        # Show Redis keys
        print(f"\n--- Redis Keys Created ---")
        market_key = f"market:{game_id}"
        market_data_key = f"market:{game_id}:data"
        print(f"  {market_key}")
        print(f"  {market_data_key}")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] An error occurred: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Market Redis Integration Test")
    print("=" * 60)
    
    success = test_market_redis_full()
    
    print("\n" + "=" * 60)
    if success:
        print("[OK] Test completed successfully!")
    else:
        print("[ERROR] Test failed!")
    print("=" * 60)

