import redis
from dotenv import load_dotenv
import os
import json
from datetime import datetime
from typing import Optional

# Load .env file from project root (parent directory of back-end)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
env_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=env_path)

SERVER_IP = os.getenv("REDIS_IP")
SERVER_PORT = os.getenv("REDIS_PORT")
SERVER_PASSWORD = os.getenv("REDIS_PASSWORD")

# Use a connection pool to avoid creating a new connection on every call
_pool = redis.ConnectionPool(
    host=SERVER_IP or "localhost",
    port=int(SERVER_PORT) if SERVER_PORT else 6379,
    password=SERVER_PASSWORD,
    decode_responses=True
)


def get_redis_connection() -> redis.Redis:
    """Get a Redis connection from the shared connection pool"""
    return redis.Redis(connection_pool=_pool)


def serialize_datetime(dt: datetime) -> str:
    """Serialize datetime to ISO format string"""
    return dt.isoformat()


def deserialize_datetime(dt_str: str) -> datetime:
    """Deserialize ISO format string to datetime"""
    return datetime.fromisoformat(dt_str)

