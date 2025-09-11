import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2
from main import detect_recyclables, model, update_firebase, db, calculate_payout, get_next_filename


ALLOWED_CLASSES = {"bottle", "cup", "can","person","cellphone"} 



cap = None
frame_label = None
camera_running = False
detected_items = []
recyclable_items = {}
filename = None
current_user_ref = None
current_user_data = None
status_label = None
thumb_label = None



def clear_screen():
    global status_label, thumb_label
    for widget in root.winfo_children():
        widget.destroy()
    status_label = tk.Label(root, text="", font=("Arial", 14), bg="#66bb66")
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
    e.widget['background'] = '#3aec72'

def on_leave(e):
    e.widget['background'] = 'darkgreen'



import time 

camera_start_time = None  

def open_camera():
    global cap, camera_running, frame_label, camera_start_time
    clear_screen()
    frame_label = tk.Label(root)
    frame_label.place(x=0, y=0, relwidth=1, relheight=1)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror("Error", "Cannot open camera")
        return

    camera_running = True
    camera_start_time = time.time()  
    show_camera_frame()


def show_camera_frame():
    global cap, frame_label, camera_running, camera_start_time
    if not camera_running:
        return

    ret, frame = cap.read()
    if ret:
        frame_full = cv2.resize(frame, (screen_width, screen_height))
        results = model(frame_full, verbose=False)

        

        allowed_mask = [i for i, cls_id in enumerate(results[0].boxes.cls)
                        if results[0].names[int(cls_id)] in ALLOWED_CLASSES]

        if allowed_mask:
            filtered_boxes = results[0].boxes[allowed_mask]
            temp = results[0].new()
            temp.boxes = filtered_boxes
            annotated = temp.plot()
        else:
            annotated = frame_full

        rgb_frame = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb_frame)
        imgtk = ImageTk.PhotoImage(img)

        frame_label.configure(image=imgtk)
        frame_label.imgtk = imgtk



    if time.time() - camera_start_time > 30:
        close_camera()
        show_home()  
        return


    frame_label.after(20, show_camera_frame)



def capture_image(event=None):
    global cap, filename, detected_items, recyclable_items, thumb_label
    if not cap:
        return
    ret, frame = cap.read()
    if not ret:
        messagebox.showerror("Error", "Failed to capture image")
        return

    filename = get_next_filename()
    cv2.imwrite(filename, frame)

    

    all_items, recyclable = detect_recyclables(model, filename)
    all_items = [i for i in all_items if i in ALLOWED_CLASSES]
    recyclable = {k: v for k, v in recyclable.items() if k in ALLOWED_CLASSES}

    
    

    detected_items.extend(all_items)
    for k, v in recyclable.items():
        recyclable_items[k] = recyclable_items.get(k, 0) + v

    thumb = cv2.resize(frame, (150, 100))
    img = Image.fromarray(cv2.cvtColor(thumb, cv2.COLOR_BGR2RGB))
    imgtk = ImageTk.PhotoImage(img)
    global thumb_label
    thumb_label = tk.Label(root, image=imgtk)
    thumb_label.image = imgtk
    thumb_label.pack(side="bottom", pady=5)

    close_camera()
    show_results()  


def close_camera():
    global cap, camera_running
    camera_running = False
    if cap:
        cap.release()
        cap = None




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
        root.configure(bg="#66bb66")

    start_btn = tk.Button(root, text="Start", font=("Arial", 30), width=15, height=2,
                          bg='darkgreen', fg='white', activebackground="#7deba0", command=open_camera)
    start_btn.pack(expand=True)
    start_btn.bind("<Enter>", on_enter)
    start_btn.bind("<Leave>", on_leave)

def show_results():
    clear_screen()

    
    bg_image = Image.open("Ecospy.jpg")   
    bg_image = bg_image.resize((root.winfo_screenwidth(), root.winfo_screenheight()))
    bg_photo = ImageTk.PhotoImage(bg_image)

    bg_label = tk.Label(root, image=bg_photo)
    bg_label.image = bg_photo
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)

    
    container = tk.Frame(root, bg="", bd=0)
    container.pack(expand=True, fill="both", padx=50, pady=(120, 0))  

    
    
    left_frame = tk.Frame(container, bg="#64b864", bd=3, relief="ridge")
    left_frame.pack(side="left", expand=True, fill="both", padx=80, pady=20)

    tk.Label(left_frame, text=f"Detected Items ({len(detected_items)})",
             font=("Arial", 20, "bold"), bg="#64b864", fg="black").pack(pady=10)

    items_frame = tk.Frame(left_frame, bg="#64b864")
    items_frame.pack(expand=True, fill="both", padx=10, pady=(0,10), anchor="n")

    tk.Label(items_frame, text="\n".join(detected_items) or "None",
             font=("Arial", 16), bg="#64b864", fg="black", justify="center", anchor="n").pack(fill="x", pady=10)

    

    right_frame = tk.Frame(container, bg="#64b864", bd=3, relief="ridge")
    right_frame.pack(side="right", expand=True, fill="both", padx=80, pady=20)

    tk.Label(right_frame, text=f"Recyclable Items ({len(recyclable_items)})",
             font=("Arial", 20, "bold"), bg="#64b864", fg="black").pack(pady=10)

    recycle_frame = tk.Frame(right_frame, bg="#64b864")
    recycle_frame.pack(expand=True, fill="both", padx=10, pady=(0,10), anchor="n")

    recyclable_text = "\n".join([f"{k}: {v}" for k, v in recyclable_items.items()]) or "None"
    tk.Label(recycle_frame, text=recyclable_text,
             font=("Arial", 16), bg="#64b864", fg="black", justify="center", anchor="n").pack(fill="x", pady=10)

    
    
    btn_frame = tk.Frame(root, bg="")
    btn_frame.pack(side="bottom", pady=40)

    cancel_btn = tk.Button(btn_frame, text="Cancel", command=lambda:[reset_session(), show_home()],
                           font=("Arial", 16), width=12, bg='darkgreen', fg='white', activebackground='#3aec72')
    cancel_btn.pack(side="left", padx=50)
    cancel_btn.bind("<Enter>", on_enter)
    cancel_btn.bind("<Leave>", on_leave)

    add_btn = tk.Button(btn_frame, text="Add Items", command=open_camera,
                        font=("Arial", 16), width=12, bg='darkgreen', fg='white', activebackground='#3aec72')
    add_btn.pack(side="left", padx=50)
    add_btn.bind("<Enter>", on_enter)
    add_btn.bind("<Leave>", on_leave)

    

    def handle_next():
        if not recyclable_items:  
            reset_session()
            show_home()
        else:
            show_verification_screen()

    next_btn = tk.Button(btn_frame, text="Next", command=handle_next,
                         font=("Arial", 16), width=12, bg='darkgreen', fg='white', activebackground='#3aec72')
    next_btn.pack(side="left", padx=50)
    next_btn.bind("<Enter>", on_enter)
    next_btn.bind("<Leave>", on_leave)




import os

def show_verification_screen():
    clear_screen()

    
    if os.path.exists("eco.jpg"):
        bg_img = Image.open("eco.jpg").resize((screen_width, screen_height))
        bg_photo = ImageTk.PhotoImage(bg_img)

        global bg_label_verification
        bg_label_verification = tk.Label(root, image=bg_photo)
        bg_label_verification.image = bg_photo
        bg_label_verification.place(x=0, y=0, relwidth=1, relheight=1)
        bg_label_verification.lower()  # send to back
    else:
        root.configure(bg="#64b864")

    
    frame_width = 800
    frame_height = 500
    frame = tk.Frame(root, bg="#64b864", bd=5, relief="ridge", width=frame_width, height=frame_height)
    frame.place(relx=0.5, rely=0.5, anchor="center")

    
    tk.Label(frame, text="Enter Registered Email / Mobile",
             font=("Arial", 30, "bold"), bg="#64b864", fg='black').pack(pady=30)

    
    user_entry = tk.Entry(frame, font=("Arial", 26), bg="#a9eea9", width=40)
    user_entry.pack(pady=25, padx=30)

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
            current_user_data = {k: v for k, v in user_doc.to_dict().items()
                                 if k in ["name","email","phone","mobile","ecopoints","wastecollected"]}
            show_user_info()
        else:
            tk.messagebox.showerror("Error", "User not found. Try again.")

    
    submit_btn = tk.Button(frame, text="Submit", font=("Arial", 22), width=20,
                           bg='darkgreen', fg='white', activebackground='#3aec72', command=submit_user)
    submit_btn.pack(pady=20)
    submit_btn.bind("<Enter>", on_enter)
    submit_btn.bind("<Leave>", on_leave)

    cancel_btn = tk.Button(frame, text="Cancel", font=("Arial", 22), width=20,
                           bg='darkgreen', fg='white', activebackground='#3aec72',
                           command=lambda: [reset_session(), show_home()])
    cancel_btn.pack(pady=20)
    cancel_btn.bind("<Enter>", on_enter)
    cancel_btn.bind("<Leave>", on_leave)





def show_user_info():
    clear_screen()

    
    if os.path.exists("eco.jpg"):
        bg_img = Image.open("eco.jpg").resize((screen_width, screen_height))
        bg_photo = ImageTk.PhotoImage(bg_img)

        global bg_label_userinfo
        bg_label_userinfo = tk.Label(root, image=bg_photo)
        bg_label_userinfo.image = bg_photo
        bg_label_userinfo.place(x=0, y=0, relwidth=1, relheight=1)
        bg_label_userinfo.lower()  
    else:
        root.configure(bg="#9ff49f")

    
    balance_label = tk.Label(root, text=f"Ecopoints: {current_user_data.get('ecopoints', 0)}",
                             font=("Arial", 24, "bold"), bg="#9ff49f", fg="black", bd=3, relief="ridge", padx=15, pady=8)
    balance_label.place(relx=0.95, rely=0.05, anchor="ne")

   
    box_frame = tk.Frame(root, bg="#9ff49f", bd=5, relief="ridge")
    box_frame.place(relx=0.5, rely=0.5, anchor="center",y=-30)

    inner_frame = tk.Frame(box_frame, bg="#9ff49f", padx=50, pady=40)
    inner_frame.pack()

    
    tk.Label(inner_frame, text="USER", font=("Arial", 28, "bold"), bg="#9ff49f", fg='black').pack(pady=(0, 30))

    
    name_frame = tk.Frame(inner_frame, bg="#9ff49f")
    name_frame.pack(fill="x", pady=10)
    tk.Label(name_frame, text="Name:", font=("Arial", 22, "bold"), bg="#9ff49f", fg='black').pack(side="left")
    tk.Label(name_frame, text=f"{current_user_data.get('name', 'N/A')}", font=("Arial", 22), bg="#9ff49f", fg='black').pack(side="left", padx=20)

    
    email_frame = tk.Frame(inner_frame, bg="#9ff49f")
    email_frame.pack(fill="x", pady=10)
    tk.Label(email_frame, text="Email:", font=("Arial", 22, "bold"), bg="#9ff49f", fg='black').pack(side="left")
    tk.Label(email_frame, text=f"{current_user_data.get('email', 'N/A')}", font=("Arial", 22), bg="#9ff49f", fg='black').pack(side="left", padx=20)

    
    mobile_number = current_user_data.get('phone') or current_user_data.get('mobile') or "-"
    mobile_frame = tk.Frame(inner_frame, bg="#9ff49f")
    mobile_frame.pack(fill="x", pady=10)
    tk.Label(mobile_frame, text="Mobile:", font=("Arial", 22, "bold"), bg="#9ff49f", fg='black').pack(side="left")
    tk.Label(mobile_frame, text=f"{mobile_number}", font=("Arial", 22), bg="#9ff49f", fg='black').pack(side="left", padx=20)

    
    def add_points():
        total_payout, total_weight, waste_type_final = calculate_payout(db, recyclable_items)
        update_firebase(current_user_ref, total_payout, total_weight, waste_type_final)
        current_user_data["ecopoints"] += total_payout
        show_added_points(total_payout, waste_type_final)

    add_btn = tk.Button(inner_frame, text="Add Points", font=("Arial", 22), width=20,
                        bg='darkgreen', fg='white', activebackground="#3aec72", command=add_points)
    add_btn.pack(pady=25)
    add_btn.bind("<Enter>", on_enter)
    add_btn.bind("<Leave>", on_leave)

    cancel_btn = tk.Button(inner_frame, text="Cancel", font=("Arial", 22), width=20,
                           bg='darkgreen', fg='white', activebackground="#3aec72",
                           command=lambda:[reset_session(), show_home()])
    cancel_btn.pack(pady=10)
    cancel_btn.bind("<Enter>", on_enter)
    cancel_btn.bind("<Leave>", on_leave)



def show_added_points(total_payout, waste_type):
    clear_screen()

   
    if os.path.exists("eco.jpg"):
        bg_img = Image.open("eco.jpg").resize((screen_width, screen_height))
        bg_photo = ImageTk.PhotoImage(bg_img)

        global bg_label_added
        bg_label_added = tk.Label(root, image=bg_photo)
        bg_label_added.image = bg_photo
        bg_label_added.place(x=0, y=0, relwidth=1, relheight=1)
        bg_label_added.lower()
    else:
        root.configure(bg="white")

   
    tk.Label(root, text=f"{current_user_data.get('name', 'N/A')}", 
             font=("Arial", 36, "bold"), fg="#ffffff", bg="#048406", bd=2, relief="ridge", padx=25, pady=12)\
        .place(relx=0.95, rely=0.05, anchor="ne")

    
    box_frame = tk.Frame(root, bg="#8FF791", bd=5, relief="ridge", padx=60, pady=60)
    box_frame.place(relx=0.5, rely=0.5, anchor="center")

    
    tk.Label(box_frame, text=f"Waste Type: {waste_type}", font=("Arial", 26, "bold"),
             bg="#8FF791", fg="black").pack(pady=15, anchor="w")

    tk.Label(box_frame, text=f"Earned Points: {total_payout}", font=("Arial", 26, "bold"),
             bg="#8FF791", fg="black").pack(pady=15, anchor="w")

    tk.Label(box_frame, text=f"Final EcoPoints: {current_user_data.get('ecopoints', 0)}", font=("Arial", 26, "bold"),
             bg="#8FF791", fg="black").pack(pady=15, anchor="w")

    
    countdown_label = tk.Label(root, text="", font=("Arial", 20, "bold"), fg="#00008B")
    countdown_label.place(relx=0.5, rely=0.85, anchor="center")

    
    def countdown(seconds):
        if seconds > 0:
            countdown_label.config(text=f"Returning to Home in {seconds} seconds...")
            root.after(1000, countdown, seconds-1)
        else:
            show_home()

    countdown(10)




root = tk.Tk()
root.attributes('-fullscreen', True)

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

root.bind("p", capture_image)
root.bind("q", lambda e: root.destroy())

show_home()
root.mainloop()
