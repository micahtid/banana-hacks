import redis
from dotenv import load_dotenv
import os

load_dotenv()

SERVER_IP = os.getenv("REDIS_IP")
SERVER_PORT = os.getenv("REDIS_PORT")
SERVER_PASSWORD = os.getenv("REDIS_PASSWORD")

def get_redis_connection() -> redis.Redis:
    """Get a Redis connection using environment variables"""
    return redis.Redis(
        host=SERVER_IP,
        port=int(SERVER_PORT) if SERVER_PORT else 6379,
        password=SERVER_PASSWORD,
        decode_responses=True
    )

try:
    r = get_redis_connection()
    r.ping()
    print("Connected to Redis")
except Exception as e:
    print(f"Error connecting to Redis: {e}")

def set_user_wallet(userID, num_coins=0, num_dollars=1000):
    key = f"user:{userID}"
    wallet_data = {
        "wallet_usd": num_dollars,
        "wallet_coins": num_coins
    }
    r.hset(key, mapping=wallet_data)
    print(f"Set wallet for {key}")

def get_user_wallet(userID):
    key = f"user:{userID}"
    wallet_data = r.hgetall(key)
    return wallet_data

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

set_user_wallet(123, 1000, 1000)
print(get_user_wallet(123))
buy_coins(123, 10, 23)
print(get_user_wallet(123))







    


    

