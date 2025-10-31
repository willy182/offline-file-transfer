# client.py
# Run: python client.py --server http://localhost:8000 --client-id restaurant_01
from websocket import create_connection
import json
import argparse
from pathlib import Path
import requests
import time

DEFAULT_FILE_PATH = Path(__file__).parent / "file_to_download.txt"
DEFAULT_FILE_SIZE_MB = 100

def ensure_dummy_file(file_path: Path, size_mb: int = 100):
    """Generate dummy 100MB file if not exists."""
    if file_path.exists():
        print(f"[INFO] Found existing file: {file_path}")
        return
    print(f"[INFO] Generating dummy file: {file_path} ({size_mb} MB)...")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    chunk = b"A" * 1024 * 1024  # 1 MB
    with open(file_path, "wb") as f:
        for _ in range(size_mb):
            f.write(chunk)
    print("[INFO] File generated successfully.")

def upload_file_chunked(server_base: str, client_id: str, file_path: Path):
    """Upload file via HTTP POST /upload/{client_id}"""
    upload_url = f"{server_base.rstrip('/')}/upload/{client_id}"
    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f)}
        resp = requests.post(upload_url, files=files, timeout=600)
    return resp

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", required=True, help="Server base HTTP URL (e.g. http://localhost:8000)")
    parser.add_argument("--client-id", required=True, help="Unique client id")
    parser.add_argument("--file", default=str(DEFAULT_FILE_PATH), help="File path to upload")
    args = parser.parse_args()

    file_path = Path(args.file)
    ensure_dummy_file(file_path, DEFAULT_FILE_SIZE_MB)

    # Convert HTTP -> WS
    if args.server.startswith("https://"):
        ws_url = args.server.replace("https://", "wss://") + "/ws"
    else:
        ws_url = args.server.replace("http://", "ws://") + "/ws"

    while True:
        try:
            print(f"[WS] Connecting to {ws_url} ...")
            ws = create_connection(ws_url)
            time.sleep(0.5)  # small delay before sending client_id
            ws.send(args.client_id)
            print(f"[WS] Connected as {args.client_id}")

            while True:
                message = ws.recv()
                print(f"[WS recv] {message}")

                try:
                    payload = json.loads(message)
                except Exception:
                    print("[WS] Invalid JSON message, ignored.")
                    continue

                if payload.get("cmd") == "UPLOAD":
                    path = payload.get("path") or str(file_path)
                    fp = Path(path)
                    if not fp.exists():
                        print(f"[UPLOAD] File not found: {fp}")
                        continue

                    print(f"[UPLOAD] Uploading {fp} ...")
                    start = time.time()
                    resp = upload_file_chunked(args.server, args.client_id, fp)
                    duration = time.time() - start
                    if resp.ok:
                        print(f"[UPLOAD] Done in {duration:.1f}s -> {resp.json()}")
                    else:
                        print(f"[UPLOAD] Failed ({resp.status_code}): {resp.text}")
                else:
                    print("[WS] Unknown command:", payload)

        except Exception as e:
            print(f"[WS] Connection error: {e}. Reconnecting in 5s...")
            time.sleep(5)

if __name__ == "__main__":
    main()
