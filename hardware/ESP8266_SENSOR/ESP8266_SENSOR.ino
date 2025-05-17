// Imports for the ESP8266
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>

// ====== WiFi Credentials ===== 
const char* ssid = "cs145";
const char* password = "password";

// ===== Sensor Values =====
const int pair_id = 1;
const int height = 20;

// ===== Server =====
String serverName = "https://rescue-quick.ehrencastillo.tech/api/sensor-data/" + String(pair_id) + "/";

// ===== Authentication =====
const char *token = "...";

// ===== Pins =====
const int trigPin = 12; //D12
const int echoPin = 13; //D11

// ===== WiFi Client =====
//WiFiClientSecure client;

WiFiClient client;

// ===== HTTP Client =====
HTTPClient http;

void setup() {
  // initialize serial communication and set pin modes
  Serial.begin(115200);
  delay(1000);
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("Connected!");
  Serial.println(WiFi.localIP());

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
}

void loop() {
  long duration, distanceReading, waterReading, depth;
  bool isWet;

  // The PING))) is triggered by a HIGH pulse of 2 or more microseconds.
  // Give a short LOW pulse beforehand to ensure a clean HIGH pulse:
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  // The same pin is used to read the signal from the PING))): a HIGH pulse
  // whose duration is the time (in microseconds) from the sending of the ping
  // to the reception of its echo off of an object.
  duration = pulseIn(echoPin, HIGH);

  // convert the time into a distance
  distanceReading = microsecondsToInches(duration);
  Serial.print(distanceReading);
  Serial.println("Reading");
  // print the depth
  depth = height - distanceReading;
  Serial.print(depth);
  Serial.println("Depth");
  
  waterReading = analogRead(A0);

  if (waterReading < 500) {
    isWet = false;
  } else {
    isWet = true; 
  }

  sendData(depth, isWet);
  delay(1000);
}

void sendData(long depth, bool isWet) {
  if (WiFi.status() == WL_CONNECTED) {

    //client.setInsecure();

    http.begin(client, serverName);
    http.addHeader("Authorization", "Bearer " + String(token));
    http.addHeader("Content-Type", "application/json");
    String jsonPayload = "{\"current_depth\":" + String(depth) + ", \"is_wet\":" + String(isWet) + "}";

    int httpResponseCode = http.POST(jsonPayload);
    Serial.println("Sending JSON: " + jsonPayload);

    Serial.print("HTTP Response code: ");
    Serial.println(httpResponseCode);

    String response = http.getString();
    Serial.println(response);

    http.end();
  } else {
    Serial.println("WiFi not connected");
  }
}

long microsecondsToInches(long microseconds) {
  // According to Parallax's datasheet for the PING))), there are 73.746
  // microseconds per inch (i.e. sound travels at 1130 feet per second).
  // This gives the distance travelled by the ping, outbound and return,
  // so we divide by 2 to get the distance of the obstacle.
  // See: https://www.parallax.com/package/ping-ultrasonic-distance-sensor-downloads/
  return microseconds / 74 / 2;
}