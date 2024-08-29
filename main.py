#include <WiFi.h>
#include <WebSocketsClient.h>

#define LED_PIN 2  // The built-in LED on the ESP32

// WiFi credentials - Replace with your own WiFi SSID and Password
const char* ssid = "your-ssid";
const char* password = "your-password";

// WebSocket server address and port
const char* websocket_server_url = "your-websocket-server-ip";
const uint16_t websocket_server_port = 8000; // FastAPI default port
const char* websocket_server_path = "/ws";

// WebSocket client instance
WebSocketsClient webSocket;

// Current state of the LED
bool ledState = false;

// Function to handle WebSocket events
void webSocketEvent(WStype_t type, uint8_t* payload, size_t length) {
    switch(type) {
        case WStype_DISCONNECTED:
            Serial.println("WebSocket Disconnected");
            break;
        case WStype_CONNECTED:
            Serial.println("WebSocket Connected");
            // Send identification message
            webSocket.sendTXT("ESP32");
            // Send initial state of LED
            webSocket.sendTXT(ledState ? "LED_ON" : "LED_OFF");
            break;
        case WStype_TEXT:
            // Handle incoming text messages
            Serial.printf("WebSocket received: %s\n", payload);

            // Toggle LED based on received message
            if(strcmp((char*)payload, "TOGGLE_LED") == 0) {
                ledState = !ledState;
                digitalWrite(LED_PIN, ledState ? HIGH : LOW);
                // Send back the updated LED state
                webSocket.sendTXT(ledState ? "LED_ON" : "LED_OFF");
            } else if(strcmp((char*)payload, "GET_STATE") == 0) {
                // Send the current LED state
                webSocket.sendTXT(ledState ? "LED_ON" : "LED_OFF");
            }
            break;
    }
}

void setup() {
    // Initialize serial communication
    Serial.begin(115200);

    // Initialize LED pin
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);

    // Connect to Wi-Fi
    Serial.printf("Connecting to %s ", ssid);
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println(" connected");

    // Initialize WebSocket connection
    webSocket.begin(websocket_server_url, websocket_server_port, websocket_server_path);
    webSocket.onEvent(webSocketEvent);

    // Set reconnect interval (in case of disconnection)
    webSocket.setReconnectInterval(5000);
}

void loop() {
    // Keep WebSocket connection alive
    webSocket.loop();
}
