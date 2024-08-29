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

# Root path to verify the server is running
@app.get("/")
async def read_root():
    print("Root path accessed")
    return {"message": "WebSocket Server Running"}

# Web interface route
@app.get("/interface", response_class=HTMLResponse)
async def get_interface():
    print("Web interface accessed")
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ESP32 D2 Control</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100vh;
                background-color: #f4f4f4;
            }
            h1 {
                font-size: 2rem;
                color: #333;
            }
            button {
                padding: 15px 30px;
                font-size: 1.2rem;
                color: #fff;
                background-color: #007bff;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                margin-top: 20px;
            }
            button:active {
                background-color: #0056b3;
            }
            p {
                margin-top: 20px;
                font-size: 1.2rem;
                color: #333;
            }
        </style>
    </head>
    <body>
        <h1>ESP32 D2 Pin Control</h1>
        <button onclick="toggleD2()">Toggle D2</button>
        <p id="status">Status: Unknown</p>

        <script>
            const websocket = new WebSocket("ws://esp-control.onrender.com:80/ws");

            websocket.onmessage = function(event) {
                const status = document.getElementById("status");
                if (event.data === "D2_ON") {
                    status.innerText = "Status: D2 is ON";
                } else if (event.data === "D2_OFF") {
                    status.innerText = "Status: D2 is OFF";
                }
            };

            function toggleD2() {
                websocket.send("TOGGLE_D2");
            }

            websocket.onopen = function() {
                websocket.send("GET_STATE");
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
