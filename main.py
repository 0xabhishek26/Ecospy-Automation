import cv2
import os
from collections import Counter
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

# ===== Capture image =====
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
        cap.release()
        cv2.destroyAllWindows()
        exit()

cap.release()
cv2.destroyAllWindows()

# ===== YOLO detection on captured image =====
results = model(filename)
all_detected_items = []
recyclable_items = {}

for box in results[0].boxes:
    cls = int(box.cls[0])
    label = results[0].names[cls].lower()
    all_detected_items.append(label)

    if check_recyclability(label) == "Recyclable":
        recyclable_items[label] = recyclable_items.get(label, 0) + 1

print("\n♻️ Final Detection on Captured Image")
print("All Detected Items:", all_detected_items)
if not recyclable_items:
    print("❌ No recyclable items detected. Exiting program.")
    exit()
print("Recyclable Items:", recyclable_items)

# ===== Firebase User Flow (via email OR phone) =====
while True:
    user_input = input("\nEnter registered Email or Mobile (or 'q' to quit): ").strip()
    if user_input.lower() == 'q':
        print("❌ Exiting program.")
        exit()

    users_ref = db.collection("users")
    
    # Query: check email OR phone
    query = users_ref.where("email", "==", user_input).limit(1).get()
    if not query:
        query = users_ref.where("phone", "==", user_input).limit(1).get()

    if query:
        user_doc = query[0]
        user_ref = user_doc.reference
        user_data = user_doc.to_dict()
        break
    else:
        print("❌ User not found. Please try again or press 'q' to quit.")

print(f"✅ Logged in as: {user_data['name']} (Current EcoPoints: {user_data['ecopoints']})")

# ===== Calculate total payout and weight =====
total_payout = 0
total_weight = 0.0
item_types = []

for item, qty in recyclable_items.items():
    doc = db.collection("recyclable_items").document(item).get()
    if doc.exists:
        data = doc.to_dict()
        price = data.get("price", 0)
        weight = data.get("weight", 0.0)
        waste_type = data.get("type", "Mixed")  # fetch waste type from Firebase

        total_payout += (price * weight * qty)  # ecopoints + weight contribution
        total_weight += weight * qty
        item_types.extend([waste_type] * qty)

print(f"💰 Total Payout: {total_payout} points")
print(f"⚖️ Total Weight: {total_weight} kg")

# Determine most frequent waste type
if item_types:
    waste_type_final = Counter(item_types).most_common(1)[0][0]
else:
    waste_type_final = "Mixed"

confirm = input("Do you want to add this amount to user EcoPoints? (y/n): ").strip().lower()
if confirm != 'y':
    print("❌ Transaction cancelled.")
    exit()

# ===== Sequential DOC ID for wasteHistory =====
waste_history_ref = user_ref.collection("wasteHistory")
docs = waste_history_ref.stream()
max_doc_no = 0
for doc in docs:
    try:
        num = int(doc.id.replace("DOC", ""))
        if num > max_doc_no:
            max_doc_no = num
    except:
        continue
next_doc_id = f"DOC{str(max_doc_no + 1).zfill(3)}"

# Example location (replace with GPS if available)
location = [28.61, 77.20]

# Timestamp UTC
collection_date = datetime.utcnow().isoformat()

# ===== Update Firebase =====
existing_weight = user_data.get("wastecollected", 0)
new_total_weight = existing_weight + total_weight

user_ref.update({
    "ecopoints": firestore.Increment(total_payout),
    "wastecollected": new_total_weight
})

# ===== Update wasteHistory =====
waste_history_ref.document(next_doc_id).set({
    "collectionDate": collection_date,
    "location": location,
    "pointsEarned": total_payout,
    "status": "Recycled",
    "wasteType": waste_type_final,
    "weightKg": total_weight
})

# ===== Save transaction record =====
db.collection("transactions").add({
    "email_or_phone": user_input,
    "items": recyclable_items,
    "payout": total_payout,
    "weightKg": total_weight,
    "timestamp": datetime.utcnow()
})

print(f"✅ EcoPoints updated! {user_data['name']} received {total_payout} points.")
print(f"💰 New EcoPoints: {user_data['ecopoints'] + total_payout}")
print(f"⚖️ Total Waste Collected (all time): {new_total_weight} kg")
