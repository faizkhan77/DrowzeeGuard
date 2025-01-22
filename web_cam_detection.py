import cv2
from ultralytics import YOLO
import threading

# Load your YOLO model
model = YOLO("best.pt")  # Replace "best.pt" with the path to your model if needed

# Global variables for threading
frame = None
processing = False
results_frame = None


# Function to capture frames
def capture_frames():
    global frame
    while True:
        ret, new_frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(new_frame, (640, 480))  # Resize to speed up detection


# Function to process frames with YOLO
def process_frames():
    global frame, processing, results_frame
    while True:
        if frame is not None and not processing:
            processing = True

            # Run YOLO detection
            results = model.predict(
                source=frame, imgsz=640, conf=0.5, device="cpu", verbose=False
            )

            # Annotate the frame with detections
            annotated_frame = results[0].plot()
            results_frame = annotated_frame
            processing = False


# Start video capture
cap = cv2.VideoCapture(1)

# Start threading
capture_thread = threading.Thread(target=capture_frames)
process_thread = threading.Thread(target=process_frames)
capture_thread.daemon = True
process_thread.daemon = True
capture_thread.start()
process_thread.start()

# Display frames
while True:
    if results_frame is not None:
        cv2.imshow("Webcam", results_frame)

    # Break on pressing 'q'
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Release the webcam and close OpenCV windows
cap.release()
cv2.destroyAllWindows()
