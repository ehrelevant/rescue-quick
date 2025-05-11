from picamera2 import Picamera2
import RPi.GPIO as GPIO
import requests
import base64
import json
from time import sleep
import io
from PIL import Image

# Device ID
CAMERA_ID: str = "..."

# Server and endpoints
HOST: str = "..."
PORT: int = 8000

HTTP_TYPE: str = "http" # http or https
DOMAIN_URL: str = f"{HTTP_TYPE}://{HOST}:{PORT}"
GET_PATH = "/api/get-flood-status/"
IMG_POST_PATH = "/api/upload-image/"
HEALTH_POST_PATH = "/api/post-cam-health/"
FULL_GET_PATH = f"{DOMAIN_URL}{GET_PATH}?pair_id={CAMERA_ID}"
FULL_POST_IMG_PATH = f"{DOMAIN_URL}{IMG_POST_PATH}{CAMERA_ID}"
FULL_POST_HEALTH_PATH = f"{DOMAIN_URL}{HEALTH_POST_PATH}{CAMERA_ID}"

# Authentication
AUTH_TOKEN: str = ""

# LED PIN
LED_PIN: int = 23

# Time delays (in seconds)
IMG_DELAY: int = 5
HEALTH_DELAY: int = 10

def get_flood_status() -> bool:
    """Function to send an HTTP GET request to the server to retrieve the current flood status"""
    try:
        print(f"Getting from {FULL_GET_PATH}")

        headers = {
            'Authorization': f'Bearer {AUTH_TOKEN}',
            'Content-Type': 'application/json'
        }

        response = requests.get(FULL_GET_PATH, headers=headers)

        # Convert the response text into json
        response_json = response.json()

        return response.status_code == 200 and str(response_json['indicator']).lower() == "true"
    except Exception as e:
        print(f"GET Error: {e}")
    
    return False

def send_image(picam):
    # Capture the image
    try:
        picam.start() # start camera if stopped
        sleep(1)

        # Capture image
        img_array = picam.capture_array()
        picam.stop()
        print("Image has been captured")

        # Convert to base64 jpeg
        buffer = io.BytesIO()
        image = Image.fromarray(img_array)
        image.save(buffer, format='JPEG')
        img_bytes = buffer.getvalue()
        encodedImage = base64.b64encode(img_bytes).decode("utf-8")
        print("Image has been encoded")
    except Exception as e:
        print(f"Failed to capture image: {e}")
        return
    
    # Send the image
    try:
        payload = {
            "image": encodedImage,
            "content_type": "image/jpeg"
        }

        headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Content-Type": "application/json"
        }

        # Send POST request
        print("POST request ready to be sent")
        response = requests.post(FULL_POST_IMG_PATH, headers=headers, data=json.dumps(payload))
        print(f"POST status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"POST error: {e}")

def send_health():
    try:
        payload = {
            "state": "alive",
            "content_type": "text/plain"
        }

        headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Content-Type": "application/json"
        }

        # Send POST request
        print("POST request ready to be sent")
        response = requests.post(FULL_POST_HEALTH_PATH, headers=headers, data=json.dumps(payload))
        print(f"POST status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"POST error: {e}")

def update_light(indicator: bool = False):
    if indicator:
        GPIO.output(LED_PIN, GPIO.HIGH)
        print("Successfully turned on LED light")
    else:
        GPIO.output(LED_PIN, GPIO.LOW)
        print("Successfully turned off LED light")

def main():
    try:
        print("Program starting...")

        # Camera Settings
        picam = Picamera2()
        config = picam.create_still_configuration()
        picam.configure(config)
        picam.set_controls({"AfMode": 2}) # set to autofocus
        picam.start()
        sleep(2) # ready the camera
        print("Camera successfully initialized")
        picam.stop() # stop the camera's current activity

        # LED Settings
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(LED_PIN, GPIO.OUT)

        print("Starting the loop...")

        while True:
            print()
            # Get the current flood status
            status: bool = get_flood_status()
            print(f"Flood Status (in loop): {status}")

            # Send the photo
            if(status):
                print("--in the if statement--")
                send_image(picam)
                # # Update LED light
                # update_light(status)
                print("--end of if statement")
                sleep(IMG_DELAY)
            # Send the health update
            else:
                print("--sending health update--")
                send_health()
                print("--end of health update")
                sleep(HEALTH_DELAY)
            
    except KeyboardInterrupt:
        print("\nKeyboard Interrupt occurred! Stopping the camera and GPIO pins....")
    except Exception as e:
        print(f"An error occured: {e}")
    finally:
        picam.close()
        print("Camera successfully stopped")
        GPIO.cleanup()
        print("GPIO pins cleaned up")


if __name__ == "__main__":
    main()