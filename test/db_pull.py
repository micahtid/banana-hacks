import redis
import dotenv
import os

dotenv.load_dotenv()

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
    r.ping()
    print(f"Connected to {SERVER_IP}...")
    print("--- Pulling Data ---")

    # Get the simple keys
    status = r.get("server:status")
    last_update = r.get("last_update")
    print(f"Server Status: {status}")
    print(f"Last Update:   {last_update}")

    # Get the hash
    sensor_data = r.hgetall("sensor:1")
    print(f"Sensor 1 Data: {sensor_data}")

except Exception as e:
    print(f"An error occurred: {e}")