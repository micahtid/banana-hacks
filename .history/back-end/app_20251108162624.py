import redis
from dotenv import load_dotenv
import os

load_dotenv()

SERVER_IP = os.getenv("REDIS_IP")
SERVER_PORT = os.getenv("REDIS_PORT")
SERVER_PASSWORD = os.getenv("REDIS_PASSWORD")

def set_market_totals(total_usd, total_bc):
    with r.pipeline() as pipe:
        pipe.set("market:total_usd", total_usd)
        pipe.set("market:total_bc", total_bc)
        pipe.execute()
    print(f"Set market totals to {total_usd} USD and {total_bc} BC")

def get_market_total(currency_type):
    key = f"market:total_{currency_type}"
    if key not in ["market:total_usd", "market:total_bc"]:
        return {"error": "Invalid currency type"}
    return {"success": True, "currency_type": currency_type, "total": r.get(key)}

def get_redis_connection() -> redis.Redis:
    """Get a Redis connection using environment variables"""
    return redis.Redis(
        host=SERVER_IP,
        port=int(SERVER_PORT) if SERVER_PORT else 6379,
        password=SERVER_PASSWORD,
        decode_responses=True
    )

def add_price_to_history(price):
    key = f"price_history"
    r.rpush(key, price)
    print(f"Added price {price} to history")

def get_price_history(count=10):
    key = f"price_history"
    return r.lrange(key, 0, count-1)



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
    return {"success": True, "userID": wallet_data["userID"], "wallet_usd": wallet_data["wallet_usd"], "wallet_coins": wallet_data["wallet_coins"]}

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
    return {"success": True, "cost": cost, "new_usd": wallet_data["wallet_usd"], "new_coins": wallet_data["wallet_coins"], "current_price": current_price, "num_coins": num_coins}

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
    return {"success": True, "revenue": revenue, "new_usd": wallet_data["wallet_usd"], "new_coins": wallet_data["wallet_coins"], "current_price": current_price, "num_coins": num_coins}


for i in range(10):
    add_price_to_history(i)
print(int(get_price_history()[0]))







    


    

