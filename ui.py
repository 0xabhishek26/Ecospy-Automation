import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2
from main import detect_recyclables, model, update_firebase, db, calculate_payout

# ===== Globals =====
cap = None
frame_label = None
camera_running = False
detected_items = []
recyclable_items = {}
filename = None
current_user_ref = None
current_user_data = None
status_label = None  # For interactive feedback
thumb_label = None   # For thumbnail preview

# ===== Utility Functions =====
def clear_screen():
    global status_label, thumb_label
    for widget in root.winfo_children():
        widget.destroy()
    status_label = tk.Label(root, text="", font=("Arial", 14), bg="white")
    status_label.pack(side="bottom", pady=5)
    thumb_label = None

def reset_session():
    global detected_items, recyclable_items, filename, thumb_label, status_label
    detected_items = []
    recyclable_items = {}
    filename = None
    if thumb_label:
        thumb_label.destroy()
        thumb_label = None
    if status_label:
        status_label.config(text="")

def on_enter(e):
    e.widget['background'] = 'lightblue'

def on_leave(e):
    e.widget['background'] = 'SystemButtonFace'

# ===== Camera Handling =====
def open_camera():
    global cap, camera_running, frame_label
    clear_screen()
    frame_label = tk.Label(root)
    frame_label.place(x=0, y=0, relwidth=1, relheight=0.75)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror("Error", "Cannot open camera")
        return

    camera_running = True
    if status_label:
        status_label.config(text="Camera Started...")
    show_camera_frame()

def show_camera_frame():
    global cap, frame_label, camera_running
    if not camera_running:
        return

    ret, frame = cap.read()
    if ret:
        frame_small = cv2.resize(frame, (640, 480))
        results = model(frame_small, verbose=False)
        annotated = results[0].plot()
        rgb_frame = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb_frame)
        imgtk = ImageTk.PhotoImage(img)
        frame_label.imgtk = imgtk
        frame_label.configure(image=imgtk)

    frame_label.after(30, show_camera_frame)

def capture_image(event=None):
    global cap, filename, detected_items, recyclable_items, thumb_label
    if not cap:
        return
    ret, frame = cap.read()
    if not ret:
        messagebox.showerror("Error", "Failed to capture image")
        return

    filename = "captured.jpg"
    cv2.imwrite(filename, frame)

    all_items, recyclable = detect_recyclables(model, filename)
    if not all_items:
        messagebox.showinfo("Info", "No items detected in the image.")
        return

    detected_items.extend(all_items)
    for k, v in recyclable.items():
        if k in recyclable_items:
            recyclable_items[k] += v
        else:
            recyclable_items[k] = v

    # Thumbnail preview
    thumb = cv2.resize(frame, (150, 100))
    img = Image.fromarray(cv2.cvtColor(thumb, cv2.COLOR_BGR2RGB))
    imgtk = ImageTk.PhotoImage(img)
    global thumb_label
    thumb_label = tk.Label(root, image=imgtk)
    thumb_label.image = imgtk
    thumb_label.pack(side="bottom", pady=5)

    if status_label:
        status_label.config(text="Image Captured!")
    close_camera()
    show_results()

def close_camera():
    global cap, camera_running
    camera_running = False
    if cap:
        cap.release()
        cap = None

# ===== Screens =====
def show_home():
    reset_session()
    clear_screen()
    try:
        bg_img = Image.open("Ecospy_bg.jpg").resize((screen_width, screen_height))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(root, image=bg_photo)
        bg_label.image = bg_photo
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    except:
        root.configure(bg="white")

    start_btn = tk.Button(root, text="Start", font=("Arial", 30), width=15, height=2, command=open_camera)
    start_btn.pack(expand=True)
    start_btn.bind("<Enter>", on_enter)
    start_btn.bind("<Leave>", on_leave)

def show_results():
    clear_screen()
    root.configure(bg="white")

    container = tk.Frame(root, bg="white")
    container.pack(expand=True, fill="both", padx=50, pady=50)

    left_frame = tk.Frame(container, bg="white")
    left_frame.pack(side="left", expand=True, fill="both", padx=90, pady=120)
    tk.Label(left_frame, text=f"Detected Items ({len(detected_items)})", font=("Arial", 20, "bold"), bg="white").pack(pady=10)
    tk.Label(left_frame, text="\n".join(detected_items) or "None", font=("Arial", 16), bg="white", justify="left").pack(pady=10)

    right_frame = tk.Frame(container, bg="white")
    right_frame.pack(side="right", expand=True, fill="both", padx=90, pady=120)
    tk.Label(right_frame, text=f"Recyclable Items ({len(recyclable_items)})", font=("Arial", 20, "bold"), bg="white").pack(pady=10)
    recyclable_text = "\n".join([f"{k}: {v}" for k, v in recyclable_items.items()]) or "None"
    tk.Label(right_frame, text=recyclable_text, font=("Arial", 16), bg="white", justify="left").pack(pady=10)

    btn_frame = tk.Frame(root, bg="white")
    btn_frame.pack(side="bottom", pady=50, padx=100)

    cancel_btn = tk.Button(btn_frame, text="Cancel", command=lambda:[reset_session(), show_home()], font=("Arial", 16), width=12)
    cancel_btn.pack(side="left", padx=90, pady=30)
    cancel_btn.bind("<Enter>", on_enter)
    cancel_btn.bind("<Leave>", on_leave)

    add_btn = tk.Button(btn_frame, text="Add Items", command=open_camera, font=("Arial", 16), width=12)
    add_btn.pack(side="left", padx=90, pady=30)
    add_btn.bind("<Enter>", on_enter)
    add_btn.bind("<Leave>", on_leave)

    next_btn = tk.Button(btn_frame, text="Next", command=show_verification_screen, font=("Arial", 16), width=12)
    next_btn.pack(side="left", padx=90, pady=30)
    next_btn.bind("<Enter>", on_enter)
    next_btn.bind("<Leave>", on_leave)

# ===== Verification Screen =====
def show_verification_screen():
    clear_screen()
    root.configure(bg="white")
    frame = tk.Frame(root, bg="white")
    frame.pack(expand=True)

    tk.Label(frame, text="Enter Registered Email / Mobile", font=("Arial", 20), bg="white").pack(pady=10)
    user_entry = tk.Entry(frame, font=("Arial", 18), width=30)
    user_entry.pack(pady=10)

    def submit_user():
        global current_user_ref, current_user_data
        user_input = user_entry.get().strip()
        if not user_input:
            tk.messagebox.showerror("Error", "Please enter Email or Mobile")
            return

        users_ref = db.collection("users")
        query = users_ref.where("email", "==", user_input).limit(1).get()
        if not query:
            query = users_ref.where("phone", "==", user_input).limit(1).get()
        if not query:
            query = users_ref.where("mobile", "==", user_input).limit(1).get()

        if query:
            user_doc = query[0]
            current_user_ref = user_doc.reference
            current_user_data = {k: v for k, v in user_doc.to_dict().items() if k in ["name","email","phone","mobile","ecopoints","wastecollected"]}
            show_user_info()
        else:
            tk.messagebox.showerror("Error", "User not found. Try again.")

    submit_btn = tk.Button(frame, text="Submit", font=("Arial", 16), width=15, command=submit_user)
    submit_btn.pack(pady=10)
    submit_btn.bind("<Enter>", on_enter)
    submit_btn.bind("<Leave>", on_leave)

    cancel_btn = tk.Button(frame, text="Cancel", font=("Arial", 16), width=15, command=lambda:[reset_session(), show_home()])
    cancel_btn.pack(pady=10)
    cancel_btn.bind("<Enter>", on_enter)
    cancel_btn.bind("<Leave>", on_leave)

# ===== User Info Screen =====
def show_user_info():
    clear_screen()
    root.configure(bg="white")

    frame = tk.Frame(root, bg="white")
    frame.pack(expand=True)

    balance_label = tk.Label(root, text=str(current_user_data.get("ecopoints", 0)), font=("Arial", 24, "bold"), bg="white", fg="green")
    balance_label.place(relx=0.95, rely=0.05, anchor="ne")

    tk.Label(frame, text=f"Name: {current_user_data.get('name', 'N/A')}", font=("Arial", 18), bg="white").pack(pady=5)
    tk.Label(frame, text=f"Email: {current_user_data.get('email', 'N/A')}", font=("Arial", 16), bg="white").pack(pady=5)
    total_points = sum(recyclable_items.values())
    tk.Label(frame, text=f"Total Points Earned: {total_points}", font=("Arial", 16), bg="white").pack(pady=5)

    def add_points():
        total_payout, total_weight, _ = calculate_payout(db, recyclable_items)
        update_firebase(current_user_ref, total_payout, total_weight, "Mixed")
        current_user_data["ecopoints"] += total_payout
        show_added_points(total_payout)

    add_btn = tk.Button(frame, text="Add Points", font=("Arial", 16), width=15, command=add_points)
    add_btn.pack(pady=10)
    add_btn.bind("<Enter>", on_enter)
    add_btn.bind("<Leave>", on_leave)

    cancel_btn = tk.Button(frame, text="Cancel", font=("Arial", 16), width=15, command=lambda:[reset_session(), show_home()])
    cancel_btn.pack(pady=10)
    cancel_btn.bind("<Enter>", on_enter)
    cancel_btn.bind("<Leave>", on_leave)

# ===== Added Points Screen with 10s auto-return =====
def show_added_points(total_payout):
    clear_screen()
    root.configure(bg="white")
    frame = tk.Frame(root, bg="white")
    frame.pack(expand=True)

    tk.Label(frame, text=f"✅ Added {total_payout} points to {current_user_data.get('name')}", font=("Arial", 20), bg="white", fg="green").pack(pady=20)
    tk.Label(frame, text=f"New EcoPoints: {current_user_data.get('ecopoints', 0)}", font=("Arial", 18), bg="white").pack(pady=10)

    # Countdown timer label
    countdown_label = tk.Label(frame, text="", font=("Arial", 16), bg="white", fg="blue")
    countdown_label.pack(pady=10)

    def countdown(seconds):
        if seconds > 0:
            countdown_label.config(text=f"Returning to Home in {seconds} seconds...")
            root.after(1000, countdown, seconds-1)
        else:
            show_home()

    countdown(10)  # start 10-second countdown


# ===== Main App =====
root = tk.Tk()
root.attributes('-fullscreen', True)

# Screen dimensions
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Key bindings
root.bind("p", capture_image)
root.bind("q", lambda e: root.destroy())

# Start app
show_home()
root.mainloop()
