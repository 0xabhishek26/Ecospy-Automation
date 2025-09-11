♻️ EcoSpy Automation

        EcoSpy is a smart waste detection and recycling payout system.
        It uses YOLOv8 + Firebase + Tkinter GUI to detect recyclable waste from a live camera              feed, calculate payouts, and update user balances with EcoPoints.

🚀 Features

     🎥 Live Waste Detection using YOLOv8 + OpenCV
     📸 Capture Mode – press P to capture image and re-run detection
     🧾 Waste Categorization – separates recyclable items from all detected waste
     💰 Automatic Payout Calculation based on item prices stored in Firebase
     🔗 Firebase Integration – manages user accounts and balances
     🖥️ Tkinter GUI – smooth full-screen interface with background images
     🌐 Extensible – easy to add new recyclable items or update prices

📂 Project Structure

         Ecospy-Automation/
         │── main.py               # Core logic (YOLO detection, payout calculation, Firebase updates)
         │── gui.py                # Tkinter GUI (home, camera, results, verification, payout)
         │── ui.py                 # Alternative/simple UI (optional)
         │── waste_mapping.py       # Mapping of items to recyclable/non-recyclable
         │── requirements.txt       # Python dependencies
         │── Ecospy_bg.jpg          # Background for home screen
         │── Ecospy.jpg             # Background for results screen
         │── eco.jpg                # Background for verification & info screens
         │── waste_collected/       # Folder for captured images
         │── serviceAccountKey.json # Firebase service account credentials (not in repo)

⚙️ Installation & Setup

    1. Clone this repository

           git clone https://github.com/your-username/Ecospy-Automation.git
           cd Ecospy-Automation


    2.Create a virtual environment (recommended)

           python -m venv venv
           source venv/bin/activate   # Linux/Mac
           venv\Scripts\activate      # Windows


    3.Install dependencies

           pip install -r requirements.txt


    4.Setup Firebase Service Account

           Go to Firebase Console
           Create a service account key (JSON)
           Save it as serviceAccountKey.json in the project root
           Ensure Firestore has:
                   users collection → fields: name, email, phone/mobile, ecopoints, wastecollected
                   pricing collection → item name & price mapping

▶️ Usage

         Run the GUI:
               python gui.py

Controls:

        Start → Opens camera and starts live detection
        P → Capture image & run detection
        Q → Quit the application
        Cancel → Return to home screen
        Add Items → Open camera again and add more items
        Next → Verify user & proceed to payout
        Add Points → Update user EcoPoints in Firebase

       
📊 Example Workflow

       1. User starts live detection from Home Screen.
       2. Press P → Capture image → System detects recyclable waste.
       3. Firebase pricing is fetched.
       4.Payout is calculated and added to user balance.
       5.User sees final EcoPoints balance and confirmation screen.

🤝 Contributing

Contributions are welcome!

       1. Fork this repo
       2.Create a new branch
               git checkout -b feature-branch
       3.Commit changes
               git commit -m "Added new feature"
       4.Push branch
               git push origin feature-branch
       5.Create a Pull Request

📜 License

This project is licensed under the MIT License.

💚 Made with passion by EcoSpy Team (SIH 2025 Project)
