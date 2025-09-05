# waste_mapping.py

def check_recyclability(item_name: str) -> str:
    recyclable_items = ["bottle", "cup", "can", "paper", "cardboard", "plastic"]
    
    if item_name.lower() in recyclable_items:
        return "Recyclable"
    else:
        return "Non-Recyclable"
