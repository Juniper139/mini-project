#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SH110X.h>
#include <ArduinoJson.h>

// ==============================
// WiFi & MQTT CONFIG
// ==============================
const char* ssid        = "Kripa's M34";
const char* password    = "enpkf4js2mgugc4";
const char* mqtt_server = "172.21.40.142";
const int   mqtt_port   = 1883;
const char* mqtt_topic  = "crowd/data";

// ==============================
// OLED CONFIG — SH1106
// SDA=2, SCL=14
// ==============================
#define SDA_PIN 2
#define SCL_PIN 14
Adafruit_SH1106G display = Adafruit_SH1106G(128, 64, &Wire, -1);

// ==============================
// CAMERA PINS (AI Thinker)
// ==============================
#define PWDN_GPIO_NUM   32
#define RESET_GPIO_NUM  -1
#define XCLK_GPIO_NUM    0
#define SIOD_GPIO_NUM   26
#define SIOC_GPIO_NUM   27
#define Y9_GPIO_NUM     35
#define Y8_GPIO_NUM     34
#define Y7_GPIO_NUM     39
#define Y6_GPIO_NUM     36
#define Y5_GPIO_NUM     21
#define Y4_GPIO_NUM     19
#define Y3_GPIO_NUM     18
#define Y2_GPIO_NUM      5
#define VSYNC_GPIO_NUM  25
#define HREF_GPIO_NUM   23
#define PCLK_GPIO_NUM   22

// ==============================
// GLOBALS
// ==============================
WebServer    server(80);
WiFiClient   espClient;
PubSubClient mqttClient(espClient);

int    g_count   = 0;
float  g_density = 0.0;
String g_status  = "WAITING";
bool   g_newData = false;

// ==============================
// OLED UPDATE
// ==============================
void updateOLED() {
  display.clearDisplay();

  // Title
  display.setTextSize(1);
  display.setTextColor(SH110X_WHITE);
  display.setCursor(20, 0);
  display.println("CROWD MONITOR");
  display.drawLine(0, 10, 127, 10, SH110X_WHITE);

  // People count
  display.setTextSize(1);
  display.setCursor(0, 14);
  display.print("People:");
  display.setTextSize(2);
  display.setCursor(60, 12);
  display.println(g_count);

  // Density
  display.setTextSize(1);
  display.setCursor(0, 34);
  display.print("Density: ");
  display.println(g_density, 2);

  // Status
  display.drawLine(0, 44, 127, 44, SH110X_WHITE);
  display.setTextSize(1);
  display.setCursor(0, 48);
  display.print("Status: ");
  display.setTextSize(2);
  display.setCursor(52, 46);
  display.println(g_status);

  display.display();
}

// ==============================
// MQTT CALLBACK
// ==============================
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  char jsonStr[200];
  unsigned int copyLen = (length < sizeof(jsonStr) - 1) ? length : sizeof(jsonStr) - 1;
  memcpy(jsonStr, payload, copyLen);
  jsonStr[copyLen] = '\0';

  Serial.print("MQTT received: ");
  Serial.println(jsonStr);

  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, jsonStr);
  if (error) {
    Serial.print("JSON parse failed: ");
    Serial.println(error.c_str());
    return;
  }

  g_count   = doc["count"]   | 0;
  g_density = doc["density"] | 0.0f;
  const char* s = doc["status"] | "UNKNOWN";
  g_status  = String(s);
  g_newData = true;

  // Print to serial terminal
  Serial.print("People: ");    Serial.print(g_count);
  Serial.print(" | Density: "); Serial.print(g_density, 2);
  Serial.print(" | Status: ");  Serial.println(g_status);
}

// ==============================
// MQTT RECONNECT
// ==============================
void reconnectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Connecting to MQTT...");
    if (mqttClient.connect("ESP32CAM_Display")) {
      Serial.println("connected");
      mqttClient.subscribe(mqtt_topic);
      Serial.print("Subscribed to: ");
      Serial.println(mqtt_topic);
    } else {
      Serial.print("failed rc=");
      Serial.print(mqttClient.state());
      Serial.println(" retrying in 3s");
      delay(3000);
    }
  }
}

// ==============================
// /capture — for test.py
// ==============================
void handleCapture() {
  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) {
    server.send(500, "text/plain", "Capture failed");
    return;
  }
  server.send_P(200, "image/jpeg", (const char*)fb->buf, fb->len);
  esp_camera_fb_return(fb);
}

// ==============================
// /stream — for browser
// ==============================
void handleJPGStream() {
  WiFiClient client = server.client();
  camera_fb_t* fb = NULL;
  client.print("HTTP/1.1 200 OK\r\nContent-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n");
  while (true) {
    fb = esp_camera_fb_get();
    if (!fb) break;
    client.printf("--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n", fb->len);
    client.write(fb->buf, fb->len);
    client.print("\r\n");
    esp_camera_fb_return(fb);
    if (!client.connected()) break;
  }
}

void handleRoot() {
  server.send(200, "text/html",
    "<h2>ESP32-CAM Crowd Monitor</h2>"
    "<a href='/stream'>Live Stream</a><br><br>"
    "<a href='/capture'>Single Capture</a>"
  );
}

// ==============================
// SETUP
// ==============================
void setup() {
  Serial.begin(115200);

  // OLED init
  Wire.begin(SDA_PIN, SCL_PIN);
  if (!display.begin(0x3C, true)) {
    Serial.println("OLED failed — check wiring!");
  }
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SH110X_WHITE);
  display.setCursor(10, 25);
  display.println("Connecting WiFi...");
  display.display();

  // WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting WiFi");
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.println("\nWiFi Connected");
  Serial.print("IP: "); Serial.println(WiFi.localIP());
  Serial.print("URL: http://"); Serial.print(WiFi.localIP()); Serial.println("/capture");

  // Camera
  camera_config_t config;
  config.ledc_channel    = LEDC_CHANNEL_0;
  config.ledc_timer      = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM; config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM; config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM; config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM; config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM; config.pin_pclk  = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM; config.pin_href  = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size   = FRAMESIZE_QVGA;
  config.jpeg_quality = 10;
  config.fb_count     = 1;

  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("Camera init failed!");
    while (1) delay(1000);
  }
  Serial.println("Camera ready");

  // Web server
  server.on("/",        handleRoot);
  server.on("/stream",  HTTP_GET, handleJPGStream);
  server.on("/capture", HTTP_GET, handleCapture);
  server.begin();
  Serial.println("Web server started");

  // MQTT
  mqttClient.setServer(mqtt_server, mqtt_port);
  mqttClient.setCallback(mqttCallback);

  // OLED ready screen
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SH110X_WHITE);
  display.setCursor(10, 15);
  display.println("System Ready!");
  display.setCursor(0, 30);
  display.print("IP: "); display.println(WiFi.localIP());
  display.setCursor(0, 45);
  display.println("Waiting for data...");
  display.display();
  delay(2000);

  updateOLED();
}

// ==============================
// LOOP
// ==============================
void loop() {
  if (!mqttClient.connected()) reconnectMQTT();
  mqttClient.loop();
  server.handleClient();

  if (g_newData) {
    updateOLED();
    g_newData = false;
  }
}