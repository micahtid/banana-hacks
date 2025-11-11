"""
Redis Helper Module

Provides Redis connection management and datetime serialization utilities.
"""

# Standard library imports
import os
from datetime import datetime

# Third-party imports
import redis
from dotenv import load_dotenv

# Load .env file from project root (parent directory of back-end)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
env_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=env_path)

SERVER_IP = os.getenv("REDIS_IP")
SERVER_PORT = os.getenv("REDIS_PORT")
SERVER_PASSWORD = os.getenv("REDIS_PASSWORD")


def get_redis_connection() -> redis.Redis:
    """
    Get a Redis connection using environment variables.

    Returns:
        Redis connection instance with decode_responses enabled

    Raises:
        redis.ConnectionError: If connection fails
    """
    return redis.Redis(
        host=SERVER_IP,
        port=int(SERVER_PORT) if SERVER_PORT else 6379,
        password=SERVER_PASSWORD,
        decode_responses=True
    )


def serialize_datetime(dt: datetime) -> str:
    """
    Serialize datetime to ISO format string for Redis storage.

    Args:
        dt: Datetime object to serialize

    Returns:
        ISO format datetime string
    """
    return dt.isoformat()


def deserialize_datetime(dt_str: str) -> datetime:
    """
    Deserialize ISO format string to datetime object.

    Args:
        dt_str: ISO format datetime string

    Returns:
        Datetime object

    Raises:
        ValueError: If string is not valid ISO format
    """
    return datetime.fromisoformat(dt_str)

