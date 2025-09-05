# transaction_module.py

from firebase_admin import firestore

def process_transaction(db, recyclable_items, account_no):
    # Find user by account number
    users_ref = db.collection("users")
    query = users_ref.where("account_no", "==", account_no).get()

    if not query:
        print("❌ User not found for account number:", account_no)
        return

    user_doc = query[0]
    user_data = user_doc.to_dict()
    user_name = user_data.get("name", "Unknown")

    # Calculate total payout
    total_payout = 0
    for item, qty in recyclable_items.items():
        price_doc = db.collection("recyclable_items").document(item).get()
        if price_doc.exists:
            price = price_doc.to_dict().get("price", 0)
            total_payout += price * qty

    print(f"\n👤 User: {user_name} (Acc No: {account_no})")
    print(f"🗑️ Items given: {recyclable_items}")
    print(f"💰 Total Amount: {total_payout}")

    confirm = input("Confirm transaction? (y/n): ").lower()
    if confirm == "y":
        user_doc.reference.update({
            "balance": firestore.Increment(total_payout)
        })
        print("✅ Balance updated successfully!")
    else:
        print("❌ Transaction cancelled.")
