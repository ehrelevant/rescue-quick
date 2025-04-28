#include "esp_camera.h"
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"
#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include "base64.h"
#include <ArduinoJson.h>

// WiFi credentials
const char *ssid = "...";
const char *password = "...";

// Device ID for database
const char *deviceID = "...";

// Server and endpoints
const String host = "...";
const int httpPort = 8000;
String getPath = "/api/get-flood-status/";
String postPath = "/api/upload-image/";
String fullPostPath = postPath + String(deviceID);

// Authentication
const char *token = "...";

// LED PIN
const int LED_PIN = 2;

// WiFi client
// WiFiClientSecure client;
WiFiClient client;

// HTTP Client
HTTPClient http;

// Camera Settings
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

void setupCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG; //YUV422,GRAYSCALE,RGB565,JPEG

  // Select lower framesize if the camera doesn't support PSRAM
  if(psramFound()){
    config.frame_size = FRAMESIZE_QVGA; // 320x240 // FRAMESIZE_ + QVGA|CIF|VGA|SVGA|XGA|SXGA|UXGA
    // config.frame_size = FRAMESIZE_UXGA; // 1600x1200 // FRAMESIZE_ + QVGA|CIF|VGA|SVGA|XGA|SXGA|UXGA
    // config.frame_size = FRAMESIZE_VGA; // 640x480
    // config.frame_size = FRAMESIZE_XGA; // 1024x768
    // config.frame_size = FRAMESIZE_SXGA; // 1280x1024
    config.jpeg_quality = 10; //10-63 lower number means higher quality
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_SVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }
  
  // Initialize the Camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    delay(1000);
    ESP.restart();
  }
}

bool getFloodStatus() {
  String serverUrl = host + ":" + String(httpPort) + getPath + "?pair_id=" + String(deviceID);
  Serial.print("Getting from ");
  Serial.println(serverUrl);

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Not connected to WiFi");
    return false;
  }

  // client.setInsecure();
  http.begin(client, serverUrl);

  // http.setAuthorization();

  // Send HTTP GET request
  int response = http.GET();
  String payload = "{}";
  StaticJsonDocument<200> doc;
  DeserializationError error;

  if (response > 0) {
    Serial.print("HTTP Response Code: ");
    Serial.println(response);
    payload = http.getString();
    Serial.print("Payload: ");
    Serial.println(payload);

    // Parse the JSON reading
    error = deserializeJson(doc, payload);
  }
  else {
    Serial.print("Error code: ");
    Serial.println(response);
    return false;
  }

  // Free resources
  http.end();

  // Check if parsing of JSON is successful
  if (error) {
    Serial.print("Deserialization of JSON failed: ");
    Serial.println("error.f_str()");
    return "false";
  }

  const char* status = doc["status"];
  
  // Check status of response
  if (strcmp(status, "success") == 0) {
    const char* indicatorStr = doc["indicator"];
    bool indicator = (strcmp(indicatorStr, "true") == 0);

    Serial.print("Flood Indicator: ");
    Serial.println(indicator);

    return indicator;
  }
  else {
    const char* errorMessage = doc["message"];
    Serial.print("An error occured: ");
    Serial.println(errorMessage);
    
    return false;
  }
}

void updateLight(bool indicator) {
  if(indicator == true) {
    digitalWrite(LED_PIN, HIGH);
    Serial.println("Successfully turned on LED light");
  }
  else {
    digitalWrite(LED_PIN, LOW);
    Serial.println("Successfully turned off LED light");
  }
}

void sendImage() {
  // Capture image
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Failed to capture image");
    delay(1000);
    ESP.restart();
  }

  String encodedImage = base64::encode(fb->buf, fb->len);  // Encode image to Base64

  encodedImage.replace("\"", "\\\"");  // Escape double quotes in the Base64 string
  String payload = "{\"image\":\"" + encodedImage + "\"}";  // Create the final payload

  // Send HTTP POST request with the Base64-encoded image
  http.begin(client, host + fullPostPath);
  http.addHeader("Content-Type", "application/json");

  int httpCode = http.POST(payload);  // Send the JSON payload

  if (httpCode > 0) {
    String response = http.getString();
    Serial.println("Response: " + response);
  } else {
    Serial.print("HTTP POST failed, error code: ");
    Serial.println(httpCode);
  }

  // Free resources
  esp_camera_fb_return(fb);
  http.end();
}

void setup() {
  // put your setup code here, to run once:
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);
  Serial.begin(115200);

  // Connect to wifi
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  WiFi.setSleep(false);

  Serial.print("WiFi connecting");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("WiFi IP:");
  Serial.println(WiFi.localIP());

  // Setup the camera
  setupCamera();
  Serial.println("Camera has been initialized");

  // Setup LED light
  pinMode(LED_PIN, OUTPUT);

  Serial.println("Staring ESP32-Cam Loop");
}

void loop() {
  // put your main code here, to run repeatedly:
  Serial.println();
  bool status = getFloodStatus();
  Serial.print("Flood Status (in loop): ");
  Serial.println(status);

  if(status == true) {
    Serial.println("----in the if statement----");
    sendImage();
    Serial.println("----end of if statement----");
  }
  updateLight(status);

  delay(1000); // loop every second
  // delay(5000);
  // delay(30000);
}