# trigger_client.py
# Run: python3 trigger_client.py --server http://localhost:8000 --client-id restaurant_01
import requests
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", required=True, help="Server base URL (e.g. http://localhost:8000)")
    parser.add_argument("--client-id", required=True, help="Client ID to trigger")
    args = parser.parse_args()

    url = f"{args.server.rstrip('/')}/trigger/{args.client_id}"
    print(f"[TRIGGER] Sending trigger to {url} ...")
    resp = requests.get(url, timeout=10)
    print(f"[TRIGGER] Response ({resp.status_code}): {resp.text}")

if __name__ == "__main__":
    main()
