# offline-file-transfer
a project file transfer from offline client to server

## How to Run
```sh
pip3 install -r requirements.txt
```

### Server
1. run `uvicorn server:app --host 0.0.0.0 --port 8000` in terminal
2. Visit: http://localhost:8000/trigger/{client_id} to trigger file request or run file `python3 trigger_client.py --server http://localhost:8000 --client-id {client_id}`

### Client
1. run `python3 client.py --server http://localhost:8000 --client-id {client_id}` in terminal
