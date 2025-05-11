"""
Code to delete old photos stored in s3 after a certain amount of time has passed. This ensures that the s3 continues to have available storage space.
"""

# IMPORTS
import os
from dotenv import load_dotenv
from pathlib import Path
import boto3
import time
from datetime import datetime, timezone, timedelta
import typing

# Load env file
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# CONSTANTS
BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION')
CHECK_INTERVAL = 1800  # check every 30 minutes
TIME_INTERVAL = {'hours': 2, 'minutes': 0, 'seconds': 0}
CAMERA_OBJ = 'camera'
PROCESSED_OBJ = 'processed'

# S3
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION,
)


def delete_photos(
    prefix: str = 'camera',
    interval: dict[str, int] = {'hours': 1, 'minutes': 0, 'seconds': 0},
) -> int:
    """
    Function to delete the old photos in a certain object if a certain interval has passed.

    args:
    - prefix: str -> the object (folder) in the s3 bucket
    - interval: dict[str, int] -> time passed in hours, minutes, and seconds

    return: bool (true if success, false if not)
    """
    time_passed = datetime.now(timezone.utc) - timedelta(
        hours=interval.get('hours', 0),
        minutes=interval.get('minutes', 0),
        seconds=interval.get('seconds', 0),
    )
    response: dict[str, typing.Any] = s3.list_objects_v2(
        Bucket=BUCKET_NAME, Prefix=prefix
    )

    # If folder is empty (contains no files), return false
    if 'Contents' not in response:
        print('\tNo objects found.')
        return 0

    num_imgs = 0

    # Go through each object
    for img in response['Contents']:
        # Get the key and the time the image was last modified
        key = img.get('Key', '')
        last_modified = img.get('LastModified', datetime.now())

        # If time at which image was uploaded exceeds the time, delete it
        if last_modified <= time_passed:
            print(f'\tDeleting {key} (uploaded at {last_modified})')
            try:
                s3.delete_object(Bucket=BUCKET_NAME, Key=key)
                num_imgs += 1
            except Exception as e:
                print(f'\tError when attempting to delete {key}: ', e)

    return num_imgs


def main():
    while True:
        print(f'\n[{datetime.now()}] Checking for old photos in bucket: {BUCKET_NAME}')
        cam_deleted = 0
        processed_deleted = 0

        try:
            print(f'Attempting to delete in folder {CAMERA_OBJ}')
            cam_deleted = delete_photos(prefix=CAMERA_OBJ, interval=TIME_INTERVAL)
        except Exception as e:
            print(f'Error: {e}')

        try:
            print(f'Attempting to delete in folder {PROCESSED_OBJ}')
            processed_deleted = delete_photos(
                prefix=PROCESSED_OBJ, interval=TIME_INTERVAL
            )
        except Exception as e:
            print(f'Error: {e}')

        print(f'\n{cam_deleted} photos deleted in {CAMERA_OBJ}')
        print(f'{processed_deleted} photos deleted in {PROCESSED_OBJ}')

        # Delete again after interval
        time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    main()
