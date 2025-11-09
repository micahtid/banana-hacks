import redis
from dotenv import load_dotenv
import os
import matplotlib
matplotlib.rcParams['keymap.save'] = []
import matplotlib.pyplot as plt
import matplotlib.animation as animation

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

def set_market_totals(marketID, totalUsd, totalBC):
    with r.pipeline() as pipe:
        pipe.set(f"market:{marketID}:totalUsd", totalUsd)
        pipe.set(f"market:{marketID}:totalBC", totalBC)
        pipe.execute()
    result = {"marketID": marketID, "totalUsd": totalUsd, "totalBC": totalBC}
    print(f"Set market {marketID} totals to {totalUsd} USD and {totalBC} BC")
    return result

def get_market_total(marketID, currency_type):
    currency_type = currency_type.lower()
    if currency_type not in ["usd", "bc"]:
        return {"error": "Invalid currency type"}
    # Map to camelCase keys to match set_market_totals
    key_mapping = {"usd": "totalUsd", "bc": "totalBC"}
    key = f"market:{marketID}:{key_mapping[currency_type]}"
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



def set_user_wallet(userID, num_dollars=1000, num_coins=0):
    key = f"user:{userID}"
    wallet_data = {
        "userID": userID,
        "walletUsd": num_dollars,
        "walletCoins": num_coins
    }
    r.hset(key, mapping=wallet_data)
    print(f"Set wallet for {key}")

def get_user_wallet(userID):
    key = f"user:{userID}"
    wallet_data = r.hgetall(key)
    return {"userID": wallet_data["userID"], "walletUsd": wallet_data["walletUsd"], "walletCoins": wallet_data["walletCoins"]}

def buy_coins(userID, num_coins, current_price, marketID = 1):
    key = f"user:{userID}"
    wallet_data = r.hgetall(key)
    if not wallet_data:
        return {"error": "User not found"}
    cost = num_coins * current_price
    if float(wallet_data["walletUsd"]) - cost < 0:
        return {"error": "Insufficient funds"}
    wallet_data["walletUsd"] = float(wallet_data["walletUsd"]) - cost
    wallet_data["walletCoins"] = float(wallet_data["walletCoins"]) + num_coins
    new_totalUsd = float(get_market_total(marketID,"usd")["total"]) - cost
    new_total_coins = float(get_market_total(marketID,"bc")["total"]) + num_coins
    set_market_totals(marketID, new_totalUsd, new_total_coins)
    r.hset(key, mapping=wallet_data)
    return {"cost": cost, "new_usd": wallet_data["walletUsd"], "new_coins": wallet_data["walletCoins"], "current_price": current_price, "num_coins": num_coins}

def sell_coins(userID, num_coins, current_price, marketID = 1):
    key = f"user:{userID}"
    wallet_data = r.hgetall(key)
    if not wallet_data:
        return {"error": "User not found"}
    revenue = num_coins * current_price
    if float(wallet_data["walletCoins"]) - num_coins < 0:
        return {"error": "Insufficient coins"}
    wallet_data["walletUsd"] = float(wallet_data["walletUsd"]) + revenue
    wallet_data["walletCoins"] = float(wallet_data["walletCoins"]) - num_coins
    new_totalUsd = float(get_market_total(marketID,"usd")["total"]) + revenue
    new_total_coins = float(get_market_total(marketID,"bc")["total"]) - num_coins
    set_market_totals(marketID, new_totalUsd, new_total_coins)

    r.hset(key, mapping=wallet_data)
    return {"revenue": revenue, "new_usd": wallet_data["walletUsd"], "new_coins": wallet_data["walletCoins"], "current_price": current_price, "num_coins": num_coins}

def attach_bot_to_user(userID, botType, botID):
    key = f"user:{userID}"
    bot_data = {
        "userID": userID,
        "botType": botType,
        "botID": botID,
        "isActive": "False"
    }
    try:
        r.hset(key, mapping=bot_data)
        return {"userID": userID, "botType": botType, "botID": botID}
    except Exception as e:
        return {"error": str(e)}

def toggle_bot(userID, botID):
    key = f"user:{userID}"
    bot_data = r.hgetall(key)
    if not bot_data:
        return {"error": "Bot not found"}
    bot_data["isActive"] = "True" if bot_data["isActive"] == "False" else "False" 
    r.hset(key, mapping=bot_data)
    return {"userID": userID, "botID": botID, "isActive": bot_data["isActive"]}

fig, ax = plt.subplots()
xs, ys = [], []


set_user_wallet(123, 1000, 0)
def on_key(event):
    if event.key == 'b':
        price_history = get_price_history(1)
        if price_history:
            print(buy_coins(123, 1, float(price_history[-1]), 1))
    elif event.key == 's':
        price_history = get_price_history(1)
        if price_history:
            print(sell_coins(123, 1, float(price_history[-1]), 1))

# Connect the key press event handler to the figure
fig.canvas.mpl_connect('key_press_event', on_key)

def animate(i):
    xs.append(i)
    ys.append(float(get_price_history(1)[-1]))
    print(buy_coins(123, 1, float(get_price_history(1)[-1]), 1))
    add_price_to_history(1, float(get_market_total(1,"usd")["total"]) / float(get_market_total(1,"bc")["total"]))
    print(get_market_total(1,"usd")["total"])
    print(get_market_total(1,"bc")["total"])
    ax.clear()
    ax.plot(xs, ys)

ani = animation.FuncAnimation(fig, animate, interval=100)
plt.show()

print(get_user_wallet(123))
print(get_price_history(1))






