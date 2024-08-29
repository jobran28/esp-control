from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List

app = FastAPI()

# CORS settings (allow requests from any origin)
origins = [
    "*",
]

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

# WebSocket route to handle connections
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # Wait for the client to send its identifier
        identifier = await websocket.receive_text()
        
        if identifier == "ESP32":
            esp_clients.append(websocket)
            print("ESP32 connected")
        else:
            web_clients.append(websocket)
            print("Web client connected")
        
        while True:
            data = await websocket.receive_text()
            
            if websocket in web_clients:
                # Forward control messages to all ESP32 clients
                for esp_client in esp_clients:
                    await esp_client.send_text(data)
            elif websocket in esp_clients:
                # Broadcast messages from ESP32 to all web clients
                for web_client in web_clients:
                    await web_client.send_text(data)
    
    except WebSocketDisconnect:
        if websocket in esp_clients:
            esp_clients.remove(websocket)
            print("ESP32 disconnected")
        elif websocket in web_clients:
            web_clients.remove(websocket)
            print("Web client disconnected")

# Root path to verify the server is running
@app.get("/")
async def read_root():
    return {"message": "WebSocket Server Running"}

# Web interface route
@app.get("/interface", response_class=HTMLResponse)
async def get_interface():
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
            const websocket = new WebSocket("ws://your-websocket-server-ip:80/ws");

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
