# server.py
# Run: uvicorn server:app --host 0.0.0.0 --port 8000
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, Request
from fastapi.responses import JSONResponse
from pathlib import Path
import asyncio
import json
import os

app = FastAPI(title="Silentmode File Transfer Server")

clients = {}  # {client_id: websocket connection}
downloads_dir = Path("downloads")
downloads_dir.mkdir(exist_ok=True)

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """Handle websocket connection from clients."""
    await ws.accept()  # handshake

    try:
        # Client sends ID first
        client_id = await ws.receive_text()
        clients[client_id] = ws
        print(f"[WS] Client connected: {client_id}")

        # Keep listening for messages (PING, logs, etc.)
        while True:
            msg = await ws.receive_text()
            print(f"[WS recv] from {client_id}: {msg}")

    except WebSocketDisconnect:
        print(f"[WS] Client disconnected: {client_id}")
        clients.pop(client_id, None)

    except Exception as e:
        print(f"[WS] Error ({client_id}): {e}")
        clients.pop(client_id, None)


@app.post("/upload/{client_id}")
async def upload_file(client_id: str, request: Request):
    """Receive file upload from client."""
    form = await request.form()
    upload: UploadFile = form.get("file")
    if not upload:
        return JSONResponse({"error": "no file field"}, status_code=400)

    save_dir = downloads_dir / client_id
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / upload.filename

    print(f"[UPLOAD] Receiving file from {client_id} -> {save_path}")
    with open(save_path, "wb") as f:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)

    print(f"[UPLOAD] Completed: {save_path}")
    return {"status": "ok", "path": str(save_path)}


@app.get("/trigger/{client_id}")
async def trigger_download(client_id: str):
    """Send instruction to client to upload its file."""
    if client_id not in clients:
        return JSONResponse({"error": "client not connected"}, status_code=400)

    message = json.dumps({
        "cmd": "UPLOAD",
        "path": "file_to_download.txt",
        "timeout_seconds": 120
    })

    try:
        await clients[client_id].send_text(message)
        print(f"[TRIGGER] Sent upload command to {client_id}")
        return JSONResponse({"status": "trigger_sent", "client": client_id}, status_code=200)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/clients")
async def list_clients():
    """List all connected clients."""
    return JSONResponse({"active_clients": list(clients.keys())}, status_code=200)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
