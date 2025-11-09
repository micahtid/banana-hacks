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

def buy_coins(userID, num_coins, current_price, marketID = 1):
    key = f"user:{userID}"
    wallet_data = r.hgetall(key)
    if not wallet_data:
        return {"error": "User not found"}
    cost = num_coins * current_price
    if float(wallet_data["wallet_usd"]) - cost < 0:
        return {"error": "Insufficient funds"}
    wallet_data["wallet_usd"] = float(wallet_data["wallet_usd"]) - cost
    wallet_data["wallet_coins"] = float(wallet_data["wallet_coins"]) + num_coins
    new_total_usd = float(get_market_total(marketID,"usd")["total"]) - cost
    new_total_coins = float(get_market_total(marketID,"bc")["total"]) + num_coins
    set_market_totals(marketID, new_total_usd, new_total_coins)
    r.hset(key, mapping=wallet_data)
    return {"cost": cost, "new_usd": wallet_data["wallet_usd"], "new_coins": wallet_data["wallet_coins"], "current_price": current_price, "num_coins": num_coins}

def sell_coins(userID, num_coins, current_price, marketID = 1):
    key = f"user:{userID}"
    wallet_data = r.hgetall(key)
    if not wallet_data:
        return {"error": "User not found"}
    revenue = num_coins * current_price
    if float(wallet_data["wallet_coins"]) - num_coins < 0:
        return {"error": "Insufficient coins"}
    wallet_data["wallet_usd"] = float(wallet_data["wallet_usd"]) + revenue
    wallet_data["wallet_coins"] = float(wallet_data["wallet_coins"]) - num_coins
    new_total_usd = float(get_market_total(marketID,"usd")["total"]) + revenue
    new_total_coins = float(get_market_total(marketID,"bc")["total"]) - num_coins
    set_market_totals(marketID, new_total_usd, new_total_coins)

    r.hset(key, mapping=wallet_data)
    return {"revenue": revenue, "new_usd": wallet_data["wallet_usd"], "new_coins": wallet_data["wallet_coins"], "current_price": current_price, "num_coins": num_coins}


print(buy_coins(123, 20, 2))
print(sell_coins(123, 20, 2))
print(set_market_totals(1, 1000000.0, 50000.0))
print(add_price_to_history(1, 2))
print(add_price_to_history(1, 2.1))
print(add_price_to_history(1, 2.5))
print(get_market_total(1, "usd"))
print(get_market_total(1, "bc"))
print(get_price_history(1))
print(get_market_data(1))
print(get_user_wallet(123))