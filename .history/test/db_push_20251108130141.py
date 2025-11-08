import redis
from dotenv import load_dotenv
import os
import time

load_dotenv()

SERVER_IP = os.getenv("REDIS_IP")
SERVER_PORT = os.getenv("REDIS_PORT")
SERVER_PASSWORD = os.getenv("REDIS_PASSWORD")

try:
    r = redis.Redis(
        host=SERVER_IP,
        port=SERVER_PORT,
        password=SERVER_PASSWORD,
        decode_responses=True
    )

    # Test the connection
    r.ping()
    print(f"Connected to {SERVER_IP}...")

    # --- This is where you do your work ---
    # Example: Pushing data once per second
    for i in range(5):
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")

        # Set a simple key-value pair
        r.set("server:status", "active")
        r.set("last_update", current_time)

        # Set a hash (like a Python dictionary)
        r.hset("game:1", mapping={"duration": 10, "userIDs": ["user1", "user2", "user3"]})

        print(f"Pushed update {i+1}/5 at {current_time}")
        time.sleep(1)

    print("--- Push complete ---")

except redis.exceptions.ConnectionError as e:
    print(f"Error: Could not connect. Check IP, port, and firewall.")
    print(f"Details: {e}")
except redis.exceptions.AuthenticationError:
    print("Error: Authentication failed. Check your password.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")