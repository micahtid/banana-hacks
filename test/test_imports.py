"""
Simple test to verify imports work
"""
import sys
import os

# Get the project root directory (works whether script is run from test/ or root/)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
back_end_dir = os.path.join(project_root, 'back-end')

print(f"Script directory: {script_dir}")
print(f"Project root: {project_root}")
print(f"Back-end directory: {back_end_dir}")
print(f"Back-end exists: {os.path.exists(back_end_dir)}")

# Add back-end directory to Python path
if back_end_dir not in sys.path:
    sys.path.insert(0, back_end_dir)
    print(f"[OK] Added {back_end_dir} to sys.path")

# Also add project root in case of relative imports
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"[OK] Added {project_root} to sys.path")

# Try importing
try:
    from market import Market
    print("[OK] Successfully imported Market")
except ImportError as e:
    print(f"[ERROR] Failed to import Market: {e}")
    sys.exit(1)

try:
    from redis_helper import get_redis_connection
    print("[OK] Successfully imported redis_helper")
except ImportError as e:
    print(f"[ERROR] Failed to import redis_helper: {e}")
    sys.exit(1)

print("\n[SUCCESS] All imports successful!")

