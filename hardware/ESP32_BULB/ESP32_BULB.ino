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

const char *ssid = "cs145";
const char *password = "password";

// Device ID for database
const char *deviceID = "...";

// Server and endpoints
const String host = "...";
const int httpPort = 80;
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
  http.addHeader("Authorization", "Bearer " + String(token));
  
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

  // Setup LED light
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);

  Serial.println("Staring ESP32-Cam Loop");
}

void loop() {
  // put your main code here, to run repeatedly:
  Serial.println();
  bool status = getFloodStatus();
  Serial.print("Flood Status (in loop): ");
  Serial.println(status);

  if(status == true) {
    digitalWrite(LED_PIN, LOW);
    Serial.println("Successfully turned on LED light");
  } else {
    digitalWrite(LED_PIN, HIGH);
    Serial.println("Successfully turned off LED light");
  }

  delay(1000); 
}