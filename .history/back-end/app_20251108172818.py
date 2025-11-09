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

def create_bot(botID, botType, **attributes):
    """Create a bot as a separate entity in Redis"""
    bot_key = f"bot:{botID}"
    bot_data = {
        "botID": botID,
        "botType": botType,
        "isActive": "False"
    }
    # Add any additional attributes passed in
    bot_data.update(attributes)
    try:
        r.hset(bot_key, mapping=bot_data)
        return {"success": True, "botID": botID, "botType": botType, **bot_data}
    except Exception as e:
        return {"error": str(e)}

def get_bot(botID):
    """Get bot data by botID"""
    bot_key = f"bot:{botID}"
    bot_data = r.hgetall(bot_key)
    if not bot_data:
        return {"error": "Bot not found"}
    return bot_data

def attach_bot_to_user(userID, botID):
    """Attach an existing bot to a user"""
    # Check if bot exists
    bot_data = get_bot(botID)
    if "error" in bot_data:
        return bot_data
    
    # Add botID to user's bot list (using a set to avoid duplicates)
    user_bots_key = f"user:{userID}:bots"
    try:
        r.sadd(user_bots_key, botID)
        return {"success": True, "userID": userID, "botID": botID}
    except Exception as e:
        return {"error": str(e)}

def get_user_bots(userID):
    """Get all bot IDs attached to a user"""
    user_bots_key = f"user:{userID}:bots"
    bot_ids = r.smembers(user_bots_key)
    return {"userID": userID, "botIDs": list(bot_ids)}

def detach_bot_from_user(userID, botID):
    """Remove a bot from a user's bot list"""
    user_bots_key = f"user:{userID}:bots"
    try:
        removed = r.srem(user_bots_key, botID)
        if removed:
            return {"success": True, "userID": userID, "botID": botID}
        else:
            return {"error": "Bot not attached to user"}
    except Exception as e:
        return {"error": str(e)}

def toggle_bot(botID):
    """Toggle a bot's active status"""
    bot_key = f"bot:{botID}"
    bot_data = r.hgetall(bot_key)
    if not bot_data:
        return {"error": "Bot not found"}
    bot_data["isActive"] = "True" if bot_data["isActive"] == "False" else "False"
    r.hset(bot_key, mapping=bot_data)
    return {"botID": botID, "isActive": bot_data["isActive"]}

def update_bot_attributes(botID, **attributes):
    """Update bot attributes"""
    bot_key = f"bot:{botID}"
    bot_data = r.hgetall(bot_key)
    if not bot_data:
        return {"error": "Bot not found"}
    # Update with new attributes
    bot_data.update(attributes)
    r.hset(bot_key, mapping=bot_data)
    return {"success": True, "botID": botID, **bot_data}

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
    add_price_to_history(1, float(get_market_total(1,"usd")["total"]) / float(get_market_total(1,"bc")["total"]))
    print(get_market_total(1,"usd")["total"])
    print(get_market_total(1,"bc")["total"])
    ax.clear()
    ax.plot(xs, ys)

ani = animation.FuncAnimation(fig, animate, interval=100)
plt.show()

print(get_user_wallet(123))
print(get_price_history(1))






