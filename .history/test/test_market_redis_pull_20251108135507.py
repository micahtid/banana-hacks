"""
Test script to pull market data from Redis
"""
import sys
import os
import json

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

def test_market_pull(game_id: str = None):
    """Load market data from Redis and display it"""
    try:
        # Test Redis connection
        r = get_redis_connection()
        r.ping()
        print("[OK] Connected to Redis")
        
        # If no game_id provided, try to find one
        if not game_id:
            print("\n--- Searching for market keys in Redis ---")
            keys = r.keys("market:*")
            market_keys = [k for k in keys if ":data" not in k]
            
            if not market_keys:
                print("✗ No market data found in Redis")
                print("  Run test_market_redis_push.py first to create market data")
                return
            
            # Extract game_id from first key (format: market:game_id)
            game_id = market_keys[0].split(":")[1]
            print(f"  Found market with game_id: {game_id}")
        
        print(f"\n--- Loading Market from Redis (game_id: {game_id}) ---")
        
        # Load market from Redis
        market = Market.load_from_redis(game_id)
        
        if not market:
            print(f"✗ Market with game_id '{game_id}' not found in Redis")
            return
        
        print(f"[OK] Market loaded successfully!")
        
        # Display market information
        print(f"\n--- Market Information ---")
        print(f"  Game ID: {market.game_id}")
        print(f"  Start Time: {market.start_time}")
        print(f"  Current Tick: {market.current_tick}")
        print(f"  Users: {market.users}")
        print(f"  Number of Users: {len(market.users)}")
        
        print(f"\n--- Market Data ---")
        print(f"  Current Price: ${market.market_data.current_price:.4f}")
        print(f"  Current Tick: {market.market_data.current_tick}")
        print(f"  Volatility: {market.market_data.volatility:.4f}")
        print(f"  Price History Length: {len(market.market_data.price_history)}")
        
        # Show recent price history
        print(f"\n--- Recent Price History (last 10) ---")
        recent_prices = market.market_data.price_history[-10:]
        for i, price in enumerate(recent_prices):
            tick = len(market.market_data.price_history) - len(recent_prices) + i
            print(f"  Tick {tick}: ${price:.4f}")
        
        # Verify data in Redis directly
        print(f"\n--- Verifying Redis Data Directly ---")
        market_key = f"market:{game_id}"
        market_data_key = f"market:{game_id}:data"
        
        market_info = r.hgetall(market_key)
        market_data = r.hgetall(market_data_key)
        
        print(f"  Redis Key: {market_key}")
        print(f"    - game_id: {market_info.get('game_id')}")
        print(f"    - start_time: {market_info.get('start_time')}")
        print(f"    - current_tick: {market_info.get('current_tick')}")
        print(f"    - users: {market_info.get('users')}")
        
        print(f"  Redis Key: {market_data_key}")
        print(f"    - current_price: {market_data.get('current_price')}")
        print(f"    - current_tick: {market_data.get('current_tick')}")
        print(f"    - volatility: {market_data.get('volatility')}")
        print(f"    - price_history length: {len(json.loads(market_data.get('price_history', '[]')))}")
        
        print(f"\n[OK] Market data retrieved successfully!")
        
    except Exception as e:
        print(f"\n✗ An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("Market Redis Pull Test")
    print("=" * 60)
    
    # Get game_id from command line argument if provided
    game_id = sys.argv[1] if len(sys.argv) > 1 else None
    
    if game_id:
        print(f"Loading market with game_id: {game_id}")
    else:
        print("No game_id provided, searching for markets in Redis...")
    
    test_market_pull(game_id)
    print("=" * 60)

