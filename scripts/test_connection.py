import sys
from waapi import WaapiClient

def test_conn():
    try:
        client = WaapiClient(url="ws://localhost:8080/waapi")
        print("SUCCESS: Connected to WAAPI server.")
        client.disconnect()
        sys.exit(0)
    except Exception as e:
        print(f"FAILED: Connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_conn()
