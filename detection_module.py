# detection_module.py

from ultralytics import YOLO
from waste_mapping import check_recyclability

model = YOLO("yolov8n.pt")

def detect_items(image_path):
    results = model(image_path, verbose=False)

    all_items = []
    recyclable_items = {}

    for box in results[0].boxes:
        cls = int(box.cls[0])
        label = results[0].names[cls].lower()
        all_items.append(label)

        status = check_recyclability(label)
        if status == "Recyclable":
            recyclable_items[label] = recyclable_items.get(label, 0) + 1

    return all_items, recyclable_items
