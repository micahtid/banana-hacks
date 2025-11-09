import redis
from dotenv import load_dotenv
import os

# --- Connection (from your file) ---
load_dotenv()

SERVER_IP = os.getenv("REDIS_IP")
SERVER_PORT = os.getenv("REDIS_PORT")
SERVER_PASSWORD = os.getenv("REDIS_PASSWORD")

def get_redis_connection() -> redis.Redis:
    """Get a Redis connection using environment variables"""
    try:
        r = redis.Redis(
            host=SERVER_IP,
            port=int(SERVER_PORT) if SERVER_PORT else 6379,
            password=SERVER_PASSWORD,
            decode_responses=True
        )
        r.ping()
        print("Connected to Redis successfully!\n")
        return r
    except Exception as e:
        print(f"Error connecting to Redis: {e}")
        exit(1)

# --- Tree Building Logic ---

def scan_all_keys(r: redis.Redis) -> list:
    """
    Safely scan for all keys in the database using SCAN.
    This is non-blocking and safe for production.
    """
    print("Scanning all keys...")
    all_keys = set()
    cursor = 0
    while True:
        cursor, keys_batch = r.scan(cursor, count=500)
        all_keys.update(keys_batch)
        if cursor == 0:
            break
    print(f"Found {len(all_keys)} total keys.\n")
    return list(all_keys)

def build_key_tree(keys: list, delimiter=':') -> dict:
    """
    Builds a nested dictionary (a tree) from a flat list of keys.
    """
    tree = {}
    for key in keys:
        parts = key.split(delimiter)
        current_level = tree
        
        for part in parts:
            # setdefault gets the key, or creates it if it doesn't exist
            current_level = current_level.setdefault(part, {})
        
        # At the end of the branch, store the full key
        # using a special, reserved name.
        current_level['_key_'] = key
    return tree

def get_key_details(r: redis.Redis, full_key: str) -> str:
    """
    Gets the type and a summary of the value for a given key.
    """
    key_type = r.type(full_key)
    ttl = r.ttl(full_key)
    
    ttl_str = f" (TTL: {ttl}s)" if ttl > -1 else ""
    
    try:
        if key_type == "string":
            value = r.get(full_key)
            if value is None:
                return f"(string){ttl_str} = [None]"
            if len(value) > 75:
                value = value[:75] + "..."
            return f"(string){ttl_str} = \"{value}\""
            
        elif key_type == "list":
            length = r.llen(full_key)
            sample = r.lrange(full_key, 0, 4)
            if length > 5:
                sample.append("...")
            return f"(list, len={length}){ttl_str} = {sample}"

        elif key_type == "hash":
            length = r.hlen(full_key)
            
            # --- NEW LOGIC: Check if this is a user hash ---
            # A "user hash" is one whose key path ends in "user:<something>"
            is_user_hash = False
            key_parts = full_key.split(':')
            if len(key_parts) >= 2 and key_parts[-2] == 'user':
                is_user_hash = True
            
            # --- SPECIAL HANDLING FOR USER HASHES ---
            if is_user_hash:
                # For user hashes, show the actual values
                data = r.hgetall(full_key)
                # Convert values to floats/ints for cleaner display
                for k, v in data.items():
                    try:
                        data[k] = round(float(v), 2)
                    except (ValueError, TypeError):
                        pass # Keep as string if not a float
                return f"(hash, fields={length}){ttl_str} = {data}"
            
            # --- Standard handling for all other hashes ---
            fields = r.hkeys(full_key)
            sample = fields[:5]
            if length > 5:
                sample.append("...")
            return f"(hash, fields={length}){ttl_str} = {sample}"

        elif key_type == "set":
            length = r.scard(full_key)
            # sscan is safer for large sets
            sample = r.sscan(full_key, 0, count=5)[1]
            return f"(set, members={length}){ttl_str} = {set(sample)}{'...' if length > 5 else ''}"
            
        elif key_type == "zset":
            length = r.zcard(full_key)
            sample = r.zrange(full_key, 0, 4)
            if length > 5:
                sample.append("...")
            return f"(sorted set, members={length}){ttl_str} = {sample}"

        else:
            return f"({key_type}){ttl_str}"
            
    except Exception as e:
            return f"({key_type}){ttl_str} - Error reading value: {e}"

def print_tree(r: redis.Redis, node: dict, prefix=""):
    """
    Recursively prints the tree with connectors.
    """
    # Separate sub-branches from the special '_key_' leaf
    sub_nodes = {k: v for k, v in node.items() if k != '_key_'}
    
    # Sort for consistent output
    parts = sorted(sub_nodes.keys())
    num_parts = len(parts)

    for i, part in enumerate(parts):
        subtree = sub_nodes[part]
        is_last = (i == num_parts - 1)
        
        # Connector symbols
        connector = "└── " if is_last else "├── "
        
        # Check if this node is *also* a key (e.g., 'user:1')
        # in addition to having children (e.g., 'user:1:wallet')
        key_data = subtree.get('_key_')
        
        print_line = f"{prefix}{connector}{part}"
        
        if key_data:
            details = get_key_details(r, key_data)
            print_line += f" -> {details}"
            
        print(print_line)
        
        # Prepare the prefix for the *next* level
        next_prefix = prefix + ("    " if is_last else "│   ")
        
        # Recurse into the subtree
        print_tree(r, subtree, next_prefix)

# --- Main Execution ---

if __name__ == "__main__":
    r = get_redis_connection()
    
    all_keys = scan_all_keys(r)
    
    if not all_keys:
        print("Database is empty.")
    else:
        key_tree = build_key_tree(all_keys)
        # --- NEW: Add a (root) node ---
        print("(root)")
        print_tree(r, key_tree, prefix="")