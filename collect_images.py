import uuid  # To create Unique identifier for each images we take
import os  # To use filepath to store images
import time  # To get some break between taking images
import cv2

IMAGES_PATH = os.path.join("datas", "new_images")
labels = ["awake", "drowsy"]
number_imgs = 50

cap = cv2.VideoCapture(1)

# Loop through labels
for label in labels:
    print(f"Collecting images for {label}")
    time.sleep(5)

    # Loop through image range
    for img_num in range(number_imgs):
        print(f"Collecting images for {label}, image number {img_num}")

        # Now will access our Webcam, take pictures and save it to our path
        # Webcam feed
        ret, frame = cap.read()

        # Naming our images path
        imgname = os.path.join(IMAGES_PATH, label + "." + str(uuid.uuid1()) + ".jpg")

        # Write out image to file
        cv2.imwrite(imgname, frame)

        # Render to the screen
        cv2.imshow("Image Collection", frame)

        # 5 sec delay between image captures
        time.sleep(2)

        if cv2.waitKey(10) & 0xFF == ord("q"):
            break
cap.release()
cv2.destroyAllWindows()
