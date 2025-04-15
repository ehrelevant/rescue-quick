import cv2
import torch

# Load YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)

# Define allowed classes (YOLOv5 COCO class names)
ALLOWED_CLASSES = ['person', 'dog', 'cat']

# Initialize webcam
cap = cv2.VideoCapture(0)

# Check if the webcam is opened correctly
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

# Get webcam properties (width, height, fps)
width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps    = cap.get(cv2.CAP_PROP_FPS)

# Set up video writer
output_path = 'output_cam.mp4'
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Inference
    results = model(frame)

    # Filter detections to only allowed classes
    filtered_results = results.pandas().xyxy[0]
    filtered_results = filtered_results[filtered_results['name'].isin(ALLOWED_CLASSES)]

    # Draw boxes around detected objects
    for _, row in filtered_results.iterrows():
        xmin, ymin, xmax, ymax = map(int, [row['xmin'], row['ymin'], row['xmax'], row['ymax']])
        label = row['name']
        confidence = row['confidence']

        cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
        cv2.putText(frame, f'{label} {confidence:.2f}', (xmin, ymin - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

    # Display the frame with detections
    cv2.imshow('Webcam Detection', frame)

    # Write frame to output video (optional)
    out.write(frame)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture and writer
cap.release()
out.release()

# Close all OpenCV windows
cv2.destroyAllWindows()
