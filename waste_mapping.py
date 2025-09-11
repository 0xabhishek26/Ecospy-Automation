# waste_mapping.py

def check_recyclability(item_name: str) -> str:
    recyclable_items = ["bottle", "cup", "paper", "book", "plastic"]
    
    if item_name.lower() in recyclable_items:
        return "Recyclable"
    else:
        return "Non-Recyclable"
