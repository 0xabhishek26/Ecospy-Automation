# ♻️ EcoSpy Automation

EcoSpy is a smart waste detection and recycling payout system.  
It uses **YOLOv8 + Firebase** to automatically detect recyclable waste from live camera feed, calculate payouts, and update user balances.

---

## 🚀 Features
- 🎥 **Live Waste Detection** using YOLOv8 and OpenCV  
- 📸 **Capture Mode** – press `P` to capture image and re-run detection  
- 🧾 **Waste Categorization** – separates recyclable items from all detected waste  
- 💰 **Automatic Payout Calculation** based on item prices stored in Firebase  
- 🔗 **Firebase Integration** – manages user accounts and balances  
- 🌐 **Extensible** – easy to add new recyclable items or price updates  

---

## 📂 Project Structure
Ecospy-Automation/
│── main.py # Main entry point
│── camera_module.py # Live detection + capture logic
│── waste_mapping.py # Mapping of items to recyclable/non-recyclable
│── firebase_module.py # Firebase setup + queries
│── requirements.txt # Python dependencies
│── waste_collected/ # Captured images folder


---

## ⚙️ Installation & Setup

1. Clone this repository:
 
       git clone https://github.com/your-username/Ecospy-Automation.git
       cd Ecospy-Automation



2. Create virtual environment (optional but recommended)

       python -m venv venv
       source venv/bin/activate   # for Linux/Mac
       venv\Scripts\activate      # for Windows


3. Install dependencies

       pip install -r requirements.txt


4. Setup Firebase Service Account

       Go to Firebase Console

       Create a service account key (JSON)

       Save it as serviceAccountKey.json in project root

▶️ Usage

       Run the main program:

       python main.py


Controls:

       P → Capture and detect waste on saved image

       Q → Quit the application

📊 Example Workflow

      1. User starts live detection.

      2. Press P → system captures and detects recyclable waste.

      3. Firebase pricing is fetched.

      4. Payout is calculated and balance is updated.

🤝 Contributing

    Contributions are welcome!

        Fork this repo
        Create a new branch (git checkout -b feature-branch)
        Commit your changes (git commit -m 'Added new feature')
        Push to branch (git push origin feature-branch)
        Create a Pull Request

📜 License

This project is licensed under the MIT License.

Made with ❤️ by EcoSpy Team
