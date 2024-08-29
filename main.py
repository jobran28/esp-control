from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List

app = FastAPI()

# CORS settings (allow requests from any origin)
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lists to store connected clients
esp_clients: List[WebSocket] = []
web_clients: List[WebSocket] = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_host = websocket.client.host
    print(f"New connection from {client_host}")

    await websocket.accept()
    print(f"WebSocket connection accepted: {client_host}")
    
    try:
        # Wait for the client to send its identifier
        identifier = await websocket.receive_text()
        print(f"Received identifier from {client_host}: {identifier}")

        if identifier == "ESP32":
            esp_clients.append(websocket)
            print("ESP32 connected")
        else:
            web_clients.append(websocket)
            print("Web client connected")

        while True:
            # Receive a message from the client
            data = await websocket.receive_text()
            print(f"Received message from {client_host}: {data}")
            
            if websocket in web_clients:
                print(f"Forwarding message from web client to ESP32 clients: {data}")
                # Forward control messages from web clients to all ESP32 clients
                for esp_client in esp_clients:
                    await esp_client.send_text(data)
                    print(f"Sent message to ESP32: {data}")
            elif websocket in esp_clients:
                print(f"Broadcasting message from ESP32 to web clients: {data}")
                # Broadcast status messages from ESP32 to all web clients
                for web_client in web_clients:
                    await web_client.send_text(data)
                    print(f"Sent message to web client: {data}")
    
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {client_host}")
        if websocket in esp_clients:
            esp_clients.remove(websocket)
            print("ESP32 disconnected")
        elif websocket in web_clients:
            web_clients.remove(websocket)
            print("Web client disconnected")

    except Exception as e:
        print(f"An error occurred: {e}")
        await websocket.close()
