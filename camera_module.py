# camera_module.py

import cv2
import os
from ultralytics import YOLO
from waste_mapping import check_recyclability

# Load YOLO model
model = YOLO("yolov8n.pt")

# Save folder for captured images
folder = "waste_collected"
os.makedirs(folder, exist_ok=True)

def get_next_filename():
    existing = [int(f.split(".")[0]) for f in os.listdir(folder) if f.endswith(".jpg")]
    next_index = max(existing, default=0) + 1
    return os.path.join(folder, f"{next_index}.jpg")

def capture_with_live_detection():
    cap = cv2.VideoCapture(0)
    print("📷 Press 'P' to capture with detection, 'Q' to quit")

    filename = None
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 🔹 Live YOLO detection on each frame
        results = model(frame, verbose=False)
        annotated = results[0].plot()

        cv2.imshow("EcoSpy Live Detection", annotated)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('p'):
            filename = get_next_filename()
            cv2.imwrite(filename, frame)
            print(f"✅ Captured & saved {filename}")

            # 🔹 Run detection again on saved frame
            results = model(filename, verbose=False)
            all_items, recyclable_items = [], {}

            for box in results[0].boxes:
                cls = int(box.cls[0])
                label = results[0].names[cls].lower()
                all_items.append(label)

                status = check_recyclability(label)
                if status == "Recyclable":
                    recyclable_items[label] = recyclable_items.get(label, 0) + 1

            print("\n♻️ Final Detection on Captured Image")
            print("All Detected Items:", all_items)
            print("Recyclable Items:", recyclable_items if recyclable_items else "None")

            break

        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return filename
