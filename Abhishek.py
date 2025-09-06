import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2
from main import detect_recyclables, model

# ===== Globals =====
cap = None
frame_label = None
camera_running = False
detected_items = []
recyclable_items = []
filename = None

# ===== Camera Handling =====
def open_camera():
    global cap, camera_running, frame_label
    clear_screen()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror("Error", "Cannot open camera")
        return

    frame_label = tk.Label(root, bg="black")
    frame_label.place(x=0, y=0, relwidth=1, relheight=1)

    camera_running = True
    show_camera_frame()

def show_camera_frame():
    global cap, frame_label, camera_running
    if not camera_running:
        return

    ret, frame = cap.read()
    if ret:
        results = model(frame, verbose=False)
        annotated = results[0].plot()
        rgb_frame = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb_frame)
        imgtk = ImageTk.PhotoImage(img)
        frame_label.imgtk = imgtk
        frame_label.configure(image=imgtk)

    frame_label.after(30, show_camera_frame)

def capture_image(event=None):
    global cap, filename, detected_items, recyclable_items
    if not cap:
        return
    ret, frame = cap.read()
    if not ret:
        messagebox.showerror("Error", "Failed to capture image")
        return

    filename = "captured.jpg"
    cv2.imwrite(filename, frame)

    all_items, recyclable = detect_recyclables(model, filename)
    detected_items = all_items
    recyclable_items = recyclable

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
    clear_screen()

    # Background
    try:
        bg_img = Image.open("Ecospy_bg.jpg").resize((screen_width, screen_height))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(root, image=bg_photo)
        bg_label.image = bg_photo
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    except:
        root.configure(bg="black")

    # Start Button
    tk.Button(root, text="Start", font=("Arial", 30), width=15, height=2, command=open_camera).pack(expand=True)

def show_results():
    clear_screen()
    root.configure(bg="white")

    tk.Label(root, text="Detected Items", font=("Arial", 20), bg="white").place(x=100, y=50)
    tk.Label(root, text="\n".join(detected_items), font=("Arial", 16), bg="white", justify="left").place(x=100, y=100)

    tk.Label(root, text="Recyclable Items", font=("Arial", 20), bg="white").place(x=500, y=50)
    recyclable_text = "\n".join([f"{k}: {v}" for k, v in recyclable_items.items()])
    tk.Label(root, text=recyclable_text, font=("Arial", 16), bg="white", justify="left").place(x=500, y=100)

    # Buttons
    tk.Button(root, text="Cancel", command=show_home, font=("Arial", 16), width=10).place(x=100, y=500)
    tk.Button(root, text="Add Items", command=open_camera, font=("Arial", 16), width=10).place(x=300, y=500)
    tk.Button(root, text="Next", command=lambda: messagebox.showinfo("Next", "Firebase integration pending..."),
              font=("Arial", 16), width=10).place(x=500, y=500)

def clear_screen():
    for widget in root.winfo_children():
        widget.destroy()

# ===== Main App =====
root = tk.Tk()
root.attributes('-fullscreen', True)
screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()

root.bind("p", capture_image)   # P to capture
root.bind("q", lambda e: root.destroy())  # Q to quit

show_home()
root.mainloop()
