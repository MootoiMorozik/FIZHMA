from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
import json
from typing import Dict, Set

app = FastAPI()

clients: Dict[WebSocket, str] = {}  # {websocket: token}
stream_subscribers: Set[WebSocket] = set()  # Client WS connections
stream_producers: Dict[str, WebSocket] = {}  # {streamer_name: websocket}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        message = await websocket.receive_text()
        clients[websocket] = message

        if message.startswith("STREAMER:"):
            streamer_name = message.split(":")[1]
            stream_producers[streamer_name] = websocket
            print(f"Stream producer connected: {streamer_name}")
            
            await broadcast_pc_list()
            
            try:
                while True:
                    data = await websocket.receive_bytes()
                    for client_ws in stream_subscribers:
                        try:
                            await client_ws.send_bytes(data)
                        except Exception:
                            pass
            except WebSocketDisconnect:
                pass

        elif message == "CLIENT":
            stream_subscribers.add(websocket)
            print("Client connected")
            await send_pc_list(websocket)
            
            try:
                while True:
                    msg = await websocket.receive_text()
                    if msg == "get_pcs":
                        await send_pc_list(websocket)
            except WebSocketDisconnect:
                pass

    except WebSocketDisconnect:
        token = clients.get(websocket, "UNKNOWN")
        print(f"{token} disconnected")
        
        if token.startswith("STREAMER:"):
            streamer_name = token.split(":")[1]
            if streamer_name in stream_producers:
                del stream_producers[streamer_name]
                await broadcast_pc_list()
        
        clients.pop(websocket, None)
        if token == "CLIENT":
            stream_subscribers.discard(websocket)

async def broadcast_pc_list():
    if not stream_subscribers:
        return
    message = json.dumps({
        "type": "pc_list",
        "pcs": list(stream_producers.keys())
    })
    for client in list(stream_subscribers):
        try:
            await client.send_text(message)
        except Exception:
            pass

async def send_pc_list(websocket: WebSocket):
    message = json.dumps({
        "type": "pc_list",
        "pcs": list(stream_producers.keys())
    })
    try:
        await websocket.send_text(message)
    except Exception:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)