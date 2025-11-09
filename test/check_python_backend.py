"""Check if Python backend is running."""
import requests

print("Checking if Python backend is running...\n")

try:
    response = requests.get('http://localhost:8000/', timeout=2)
    print(f"[OK] Python backend is running!")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}")
except requests.exceptions.ConnectionError:
    print("[ERROR] Python backend is NOT running!")
    print("\nTo start it:")
    print("  cd back-end")
    print("  python api_server.py")
except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")

