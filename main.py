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
folder = "waste_collected"
os.makedirs(folder, exist_ok=True)

def get_next_filename():
    existing = [int(f.split(".")[0]) for f in os.listdir(folder) if f.endswith(".jpg")]
    next_index = max(existing, default=0) + 1
    return os.path.join(folder, f"{next_index}.jpg")

# ===== Core functions =====

def detect_recyclables(model, filename):
    """Return all detected items and recyclable items dictionary"""
    results = model(filename)
    all_detected_items = []
    recyclable_items = {}
    for box in results[0].boxes:
        cls = int(box.cls[0])
        label = results[0].names[cls].lower()
        all_detected_items.append(label)
        if check_recyclability(label) == "Recyclable":
            recyclable_items[label] = recyclable_items.get(label, 0) + 1
    return all_detected_items, recyclable_items

def calculate_payout(db, recyclable_items):
    """Return total payout, total weight, and most frequent waste type"""
    total_payout = 0
    total_weight = 0.0
    item_types = []

    for item, qty in recyclable_items.items():
        doc = db.collection("recyclable_items").document(item).get()
        if doc.exists:
            data = doc.to_dict()
            price = data.get("price", 0)
            weight = data.get("weight", 0.0)
            waste_type = data.get("type", "Mixed")
            total_payout += price * weight * qty
            total_weight += weight * qty
            item_types.extend([waste_type] * qty)

    if item_types:
        waste_type_final = Counter(item_types).most_common(1)[0][0]
    else:
        waste_type_final = "Mixed"

    return total_payout, total_weight, waste_type_final

def update_firebase(user_ref, total_payout, total_weight, waste_type):
    """Update user EcoPoints, waste collected, and add wasteHistory record"""
    existing_weight = user_ref.get().to_dict().get("wastecollected", 0)
    new_total_weight = existing_weight + total_weight

    # Update user document
    user_ref.update({
        "ecopoints": firestore.Increment(total_payout),
        "wastecollected": new_total_weight
    })

    # Add wasteHistory
    waste_history_ref = user_ref.collection("wasteHistory")
    docs = list(waste_history_ref.stream())
    next_doc_id = f"DOC{len(docs)+1:03}"
    waste_history_ref.document(next_doc_id).set({
        "collectionDate": datetime.utcnow().isoformat(),
        "location": [28.61, 77.20],  # Dummy location
        "pointsEarned": total_payout,
        "status": "Recycled",
        "wasteType": waste_type,
        "weightKg": total_weight
    })

    return new_total_weight

# ===== Main workflow =====
if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    print("📷 Press 'P' to capture with detection, 'Q' to quit")

    filename = None
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

    if not filename:
        print("❌ No image captured. Exiting.")
        exit()

    # ===== YOLO detection on captured image =====
    all_detected_items, recyclable_items = detect_recyclables(model, filename)

    print("\n♻️ Final Detection on Captured Image")
    print("All Detected Items:", all_detected_items)
    if not recyclable_items:
        print("❌ No recyclable items detected. Exiting program.")
        exit()
    print("Recyclable Items:", recyclable_items)

    # ===== Firebase User Flow =====
    while True:
        user_input = input("\nEnter registered Email or Mobile (or 'q' to quit): ").strip()
        if user_input.lower() == 'q':
            print("❌ Exiting program.")
            exit()

        users_ref = db.collection("users")
        query = users_ref.where("email", "==", user_input).limit(1).get()
        if not query:
            query = users_ref.where("phone", "==", user_input).limit(1).get()
        if not query:
            query = users_ref.where("mobile", "==", user_input).limit(1).get()

        if query:
            user_doc = query[0]
            user_ref = user_doc.reference
            user_data = user_doc.to_dict()

            # fix duplicate mobile field
            if "mobilemobile" in user_data:
                user_data["mobile"] = user_data.pop("mobilemobile")

            allowed_fields = ["name", "email", "phone", "mobile", "ecopoints", "wastecollected"]
            user_data = {k: v for k, v in user_data.items() if k in allowed_fields}

            # ✅ Verification step
            print("\n🔎 User Found!")
            print(f"👤 Name: {user_data.get('name', 'N/A')}")
            print(f"📧 Email: {user_data.get('email', 'N/A')}")
            print(f"📱 Mobile: {user_data.get('mobile', user_data.get('phone', 'N/A'))}")
            print(f"💰 Current EcoPoints: {user_data.get('ecopoints', 0)}")
            print(f"⚖️ Waste Collected: {user_data.get('wastecollected', 0)} kg")

            confirm_user = input("\nIs this the correct user? (y/n): ").strip().lower()
            if confirm_user == 'y':
                break
            else:
                print("❌ Try again with another email or mobile.")
                continue
        else:
            print("❌ User not found. Please try again or press 'q' to quit.")

    # ===== Payout calculation =====
    total_payout, total_weight, waste_type_final = calculate_payout(db, recyclable_items)

    print(f"\n💰 Total Payout: {total_payout} points")
    print(f"⚖️ Total Weight: {total_weight} kg")
    print(f"🗑️ Waste Type: {waste_type_final}")

    confirm = input("Do you want to add this amount to user EcoPoints? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Transaction cancelled.")
        exit()

    updated_weight = update_firebase(user_ref, total_payout, total_weight, waste_type_final)

    print(f"\n✅ EcoPoints updated! {user_data['name']} received {total_payout} points.")
    print(f"💰 New EcoPoints: {user_data['ecopoints'] + total_payout}")
    print(f"⚖️ Total Waste Collected (all time): {updated_weight} kg")
