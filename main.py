import cv2
import os
from ultralytics import YOLO
from waste_mapping import check_recyclability

# ===== Firebase imports =====
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# ===== Firebase setup =====
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()
print("✅ Firebase setup complete!")

# ===== YOLO & Camera =====
model = YOLO("yolov8n.pt")
cap = cv2.VideoCapture(0)

print("📷 Press 'P' to capture with detection, 'Q' to quit")
folder = "waste_collected"
os.makedirs(folder, exist_ok=True)

def get_next_filename():
    existing = [int(f.split(".")[0]) for f in os.listdir(folder) if f.endswith(".jpg")]
    next_index = max(existing, default=0) + 1
    return os.path.join(folder, f"{next_index}.jpg")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, verbose=False)
    annotated_frame = results[0].plot()
    cv2.imshow("EcoSpy Camera", annotated_frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('p'):
        filename = get_next_filename()
        cv2.imwrite(filename, frame)
        print(f"✅ Captured & saved {filename}")
        break
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# ===== YOLO detection on captured image =====
results = model(filename)
all_detected_items = []
recyclable_items = {}

for box in results[0].boxes:
    cls = int(box.cls[0])
    conf = float(box.conf[0])
    label = results[0].names[cls].lower()
    all_detected_items.append(label)

    status = check_recyclability(label)
    if status == "Recyclable":
        recyclable_items[label] = recyclable_items.get(label, 0) + 1

print("\n♻️ Final Detection on Captured Image")
print("All Detected Items:", all_detected_items)
print("Recyclable Items:", recyclable_items if recyclable_items else "None found")

# ===== Firebase User Flow =====
if recyclable_items:
    account_no = input("\nEnter Account Number: ").strip()
    
    user_ref = db.collection("users").document(account_no)
    user_doc = user_ref.get()

    if user_doc.exists:
        user_data = user_doc.to_dict()
        print(f"✅ User found: {user_data['name']} (Balance: {user_data['balance']})")

        # Calculate total payout
        total_payout = 0
        for item, qty in recyclable_items.items():
            price_doc = db.collection("recyclable_items").document(item).get()
            if price_doc.exists:
                total_payout += price_doc.to_dict().get("price", 0) * qty

        print(f"💰 Total Payout: {total_payout} points")

        confirm = input("Do you want to add this amount to user balance? (y/n): ").strip().lower()
        if confirm == "y":
            user_ref.update({
                "balance": firestore.Increment(total_payout)
            })

            # Save transaction record
            db.collection("transactions").add({
                "account_no": account_no,
                "items": recyclable_items,
                "payout": total_payout,
                "timestamp": datetime.utcnow()
            })

            print(f"✅ Balance updated! {user_data['name']} received {total_payout} points.")
        else:
            print("❌ Transaction cancelled.")
    else:
        print(f"❌ User not found for Account Number: {account_no}")
