import redis
from dotenv import load_dotenv
import os

load_dotenv()

SERVER_IP = os.getenv("REDIS_IP")
SERVER_PORT = os.getenv("REDIS_PORT")
SERVER_PASSWORD = os.getenv("REDIS_PASSWORD")

def set_market_totals(marketID, total_usd, total_bc):
    with r.pipeline() as pipe:
        pipe.set(f"market:{marketID}:total_usd", total_usd)
        pipe.set(f"market:{marketID}:total_bc", total_bc)
        pipe.execute()
    result = {"marketID": marketID, "total_usd": total_usd, "total_bc": total_bc}
    print(f"Set market {marketID} totals to {total_usd} USD and {total_bc} BC")
    return result

def get_market_total(marketID, currency_type):
    if currency_type not in ["usd", "bc"]:
        return {"error": "Invalid currency type"}
    key = f"market:{marketID}:total_{currency_type}"
    return {"marketID": marketID, "currency_type": currency_type, "total": r.get(key)}

def get_redis_connection() -> redis.Redis:
    """Get a Redis connection using environment variables"""
    return redis.Redis(
        host=SERVER_IP,
        port=int(SERVER_PORT) if SERVER_PORT else 6379,
        password=SERVER_PASSWORD,
        decode_responses=True
    )

def add_price_to_history(marketID, price):
    key = f"market:{marketID}:price_history"
    r.rpush(key, price)
    result = {"marketID": marketID, "price": price}
    print(f"Added price {price} to market {marketID} price history")
    return result

def get_price_history(marketID):
    key = f"market:{marketID}:price_history"
    return r.lrange(key, 0, -1)

def get_market_data(marketID):
    key = f"market:{marketID}"
    return r.hgetall(key)



try:
    r = get_redis_connection()
    r.ping()
    print("Connected to Redis")
except Exception as e:
    print(f"Error connecting to Redis: {e}")

def set_user_wallet(userID, num_dollars=1000, num_coins=0):
    key = f"user:{userID}"
    wallet_data = {
        "userID": userID,
        "wallet_usd": num_dollars,
        "wallet_coins": num_coins
    }
    r.hset(key, mapping=wallet_data)
    print(f"Set wallet for {key}")

def get_user_wallet(userID):
    key = f"user:{userID}"
    wallet_data = r.hgetall(key)
    return {"userID": wallet_data["userID"], "wallet_usd": wallet_data["wallet_usd"], "wallet_coins": wallet_data["wallet_coins"]}

def buy_coins(userID, num_coins, current_price):
    key = f"user:{userID}"
    wallet_data = r.hgetall(key)
    if not wallet_data:
        return {"error": "User not found"}
    cost = num_coins * current_price
    if int(wallet_data["wallet_usd"]) - cost < 0:
        return {"error": "Insufficient funds"}
    wallet_data["wallet_usd"] = int(wallet_data["wallet_usd"]) - cost
    wallet_data["wallet_coins"] = int(wallet_data["wallet_coins"]) + num_coins

    r.hset(key, mapping=wallet_data)
    return {"cost": cost, "new_usd": wallet_data["wallet_usd"], "new_coins": wallet_data["wallet_coins"], "current_price": current_price, "num_coins": num_coins}

def sell_coins(userID, num_coins, current_price):
    key = f"user:{userID}"
    wallet_data = r.hgetall(key)
    if not wallet_data:
        return {"error": "User not found"}
    revenue = num_coins * current_price
    if int(wallet_data["wallet_coins"]) - num_coins < 0:
        return {"error": "Insufficient coins"}
    wallet_data["wallet_usd"] = int(wallet_data["wallet_usd"]) + revenue
    wallet_data["wallet_coins"] = int(wallet_data["wallet_coins"]) - num_coins
    r.hset(key, mapping=wallet_data)
    return {"revenue": revenue, "new_usd": wallet_data["wallet_usd"], "new_coins": wallet_data["wallet_coins"], "current_price": current_price, "num_coins": num_coins}


# --- Example Usage ---
print("\n--- Running Example ---")

# Set up initial state
set_user_wallet(123)
set_user_wallet(456)
set_market_totals("1", 1000000.0, 50000.0)

# Simulate a trade: User 123 buys 20 bananacoins for 40 USD
print("\nSimulating Trade:")
# 1. Debit user 123 USD
print(buy_coins(123, 20, 2))
# 2. Credit user 123 bananacoins
print(sell_coins(123, 20, 2))
# 3. Update market totals
print(set_market_totals("1", 1000000.0, 50000.0))

# Add some prices to the history
print("\nUpdating Price History:")
print(add_price_to_history("1",2))
print(add_price_to_history("1",2.1))
print(add_price_to_history("1",2.5))

# Get final state
print("\n--- Final State ---")
print("User 123 Wallet:", get_user_wallet(123))
print("Market Totals:", get_market_total("1","usd"))
print("Market Prices:", get_price_history("1"))





    


    

