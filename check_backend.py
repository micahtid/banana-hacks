"""
Quick script to check if Python backend is running
"""

import requests
import sys

BACKEND_URL = "http://localhost:8000"

print("=" * 70)
print("CHECKING PYTHON BACKEND STATUS")
print("=" * 70)

try:
    print(f"\nAttempting to connect to: {BACKEND_URL}/health")
    response = requests.get(f"{BACKEND_URL}/health", timeout=3)
    
    if response.status_code == 200:
        data = response.json()
        print("\n[OK] Python backend is RUNNING!")
        print(f"\nBackend Status:")
        print(f"  - Status: {data.get('status', 'unknown')}")
        print(f"  - Timestamp: {data.get('timestamp', 'unknown')}")
        print(f"  - Active Games: {data.get('activeGames', 0)}")
        print(f"  - Running Tasks: {data.get('runningTasks', 0)}")
        print(f"\nBackend URL: {BACKEND_URL}")
        print("Backend Docs: {}/docs".format(BACKEND_URL))
        print("\n" + "=" * 70)
        print("READY TO USE!")
        print("=" * 70)
        sys.exit(0)
    else:
        print(f"\n[WARN] Backend responded with status: {response.status_code}")
        sys.exit(1)
        
except requests.exceptions.ConnectionError:
    print("\n[FAIL] Cannot connect to Python backend!")
    print("\nThe Python backend server is NOT running.")
    print("\nTo start it:")
    print("  1. Open a terminal")
    print("  2. cd back-end")
    print("  3. python api_server.py")
    print("\nOr use the run script:")
    print("  - Windows: back-end\\run_server.bat")
    print("  - Linux/Mac: back-end/run_server.sh")
    print("\n" + "=" * 70)
    sys.exit(1)
    
except requests.exceptions.Timeout:
    print("\n[FAIL] Connection timeout!")
    print("Backend may be starting up or experiencing issues.")
    sys.exit(1)
    
except Exception as e:
    print(f"\n[FAIL] Unexpected error: {e}")
    sys.exit(1)

