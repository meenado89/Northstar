import tkinter as tk
from tkinter import messagebox
from tkinter import scrolledtext
import sys
import random
from tkinter import scrolledtext
from PIL import Image, ImageTk

import google.generativeai as genai
import os
import json
from dotenv import load_dotenv
import time

chat_session = None

# LOAD ENVIRONMENT VARIABLES
# Check if running as .exe or script
if getattr(sys, 'frozen', False):
    # Running as .exe - look in exe directory
    application_path = os.path.dirname(sys.executable)
else:
    # Running as script
    application_path = os.path.dirname(os.path.abspath(__file__))

# Load .env from exe directory
dotenv_path = os.path.join(application_path, '.env')
load_dotenv(dotenv_path)

# AI CONFIGURATION 

STARTUP_GREETINGS = [
    "Hey!  I was just waiting for you.",
    "Oh hi!  Wanna chat?",
    "You’re back! That made my day ",
    "Hi hi!  What’s up?"
]

print(random.choice(STARTUP_GREETINGS))


PET_PERSONALITY = (
    "You are Pixel, a small desktop AI pet. "
    "You are friendly, playful, and emotionally supportive. "
    "You speak casually like a companion, not an assistant. "
    "Keep replies short (1–3 sentences). "
    "Use emojis occasionally. "
    "Do not mention being an AI or model."
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("ERROR: API key not found! Create a .env file with your key.")
    # Don't exit immediately in .exe, show error window
    root_error = tk.Tk()
    root_error.withdraw()
    messagebox.showerror("Error", "API key not found!\nCreate .env file with GEMINI_API_KEY")
    sys.exit(1)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-2.5-flash')

# def ask_gemini(user_input):
#     try:
#         prompt = f"{PET_PERSONALITY}\nUser: {user_input}\nPixel:"
#         response = model.generate_content(prompt)
#         return response.text.strip()
#     except Exception as e:
#         return "😿 Something went wrong… try again?"



# CHAT HISTORY FOR MEMORY
chat_history = []
HISTORY_FILE = os.path.join(application_path, "chat_history.json")

# LOAD SAVED HISTORY
def load_history():
    global chat_history
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                chat_history = json.load(f)
                print(f"Loaded {len(chat_history)} messages")
    except Exception as e:
        print(f"Could not load history: {e}")
        chat_history = []

load_history()
def init_chat_session():
    global chat_session
    chat_session = model.start_chat(history=chat_history)

init_chat_session()

# SAVE HISTORY
def save_history():
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(chat_history, f, indent=2, ensure_ascii=False)
        print("History saved!")
    except Exception as e:
        print(f"Could not save: {e}")

# CREATES WINDOW
root = tk.Tk()
root.overrideredirect(True)
is_topmost = True
root.attributes("-topmost", is_topmost)
root.wm_attributes("-transparentcolor", "white")

# QUIT WITH SAVE FUNCTION
def quit_with_save(event=None):
    print("Quitting and saving...")
    save_history()
    root.destroy()

root.bind("<Escape>", quit_with_save)

# TOGGLE FUNCTIONS
def toggle_topmost(event=None):
    global is_topmost
    is_topmost = not is_topmost
    root.attributes("-topmost", is_topmost)
    print(f"Always on top: {is_topmost}")

def send_to_back(event=None):
    global is_topmost
    is_topmost = False
    root.attributes("-topmost", False)
    print("Sent to back")

def bring_to_front(event=None):
    global is_topmost
    is_topmost = True
    root.attributes("-topmost", True)
    print("Brought to front")

root.bind("t", toggle_topmost)
root.bind("b", send_to_back)
root.bind("f", bring_to_front)

# LOAD IMAGES WITH ERROR HANDLING
frames = []
assets_path = os.path.join(application_path, "assets")
#img loop
try:
    for i in range(1, 9):
        img_path = os.path.join(assets_path, f"idle{i}.png")
        if os.path.exists(img_path):
            frames.append(ImageTk.PhotoImage(Image.open(img_path)))
        else:
            print(f"Warning: {img_path} not found")
    
    if len(frames) == 0:
        raise Exception("No animation frames found!")
        
except Exception as e:
    print(f"Error loading images: {e}")
    root_error = tk.Tk()
    root_error.withdraw()
    messagebox.showerror("Error", f"Could not load images!\n{e}")
    sys.exit(1)

current_frame = 0
label = tk.Label(root, image=frames[0], bg="white")
label.pack()

# SPAWN AT BOTTOM RIGHT
root.update_idletasks()
x = root.winfo_screenwidth() - root.winfo_width() - 14
y = root.winfo_screenheight() - root.winfo_height() - 46
root.geometry(f"+{x}+{y}")

# DRAG VARIABLES
x_offset = 0
y_offset = 0

def start_move(event):
    global x_offset, y_offset
    x_offset = event.x
    y_offset = event.y

def do_move(event):
    x = event.x_root - x_offset
    y = event.y_root - y_offset
    root.geometry(f"+{x}+{y}")

# IMPORTANT: Bind to label, not root
label.bind("<Button-1>", start_move)
label.bind("<B1-Motion>", do_move)

# CHAT WINDOW
chat_window = None

def open_chat(event=None):
    global chat_window

    print("Opening chat window...")

    try:
        if chat_window is not None and chat_window.winfo_exists():
            chat_window.lift()
            return

        chat_window = tk.Toplevel(root)
        chat_window.title("Chat with Cat Assistant")
        chat_window.geometry("400x500")

        chat_display = scrolledtext.ScrolledText(
            chat_window,
            wrap=tk.WORD,
            width=50,
            height=20,
            state='disabled'
        )
        chat_display.pack(padx=10, pady=10)

        # Load history
        chat_display.config(state='normal')
        for msg in chat_history:
            if msg["role"] == "user":
                chat_display.insert(tk.END, f"You: {msg['parts'][0]}\n", "user")
            elif msg["role"] == "model":
                chat_display.insert(tk.END, f"Cat: {msg['parts'][0]}\n\n", "assistant")
        chat_display.config(state='disabled')
        chat_display.see(tk.END)

        input_frame = tk.Frame(chat_window)
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        user_input = tk.Entry(input_frame)
        user_input.pack(side=tk.LEFT, fill=tk.X, expand=True)

        def send_message():
            message = user_input.get().strip()
            if not message:
                return

            user_input.delete(0, tk.END)

            chat_display.config(state='normal')
            chat_display.insert(tk.END, f"You: {message}\n", "user")
            chat_display.config(state='disabled')

            chat_history.append({"role": "user", "parts": [message]})

            try:
                response = chat_session.send_message(message)
                ai_reply = response.text

                chat_history.append({"role": "model", "parts": [ai_reply]})

                chat_display.config(state='normal')
                chat_display.insert(tk.END, f"Cat: {ai_reply}\n\n", "assistant")
                chat_display.config(state='disabled')
                chat_display.see(tk.END)

                save_history()

            except Exception as e:
                chat_display.config(state='normal')
                chat_display.insert(tk.END, f"Error: {e}\n", "error")
                chat_display.config(state='disabled')

        def clear_chat_history():
            global chat_history
            chat_history = []
            save_history()
            chat_display.config(state='normal')
            chat_display.delete(1.0, tk.END)
            chat_display.insert(tk.END, "History cleared!\n\n", "error")
            chat_display.config(state='disabled')

        send_button = tk.Button(input_frame, text="Send", command=send_message)
        send_button.pack(side=tk.RIGHT, padx=5)

        clear_button = tk.Button(input_frame, text="Clear", command=clear_chat_history)
        clear_button.pack(side=tk.RIGHT, padx=5)

        user_input.bind("<Return>", lambda e: send_message())
        user_input.focus()

        chat_display.tag_config("user", foreground="blue")
        chat_display.tag_config("assistant", foreground="green")
        chat_display.tag_config("error", foreground="red")

        print("Chat window opened successfully!")

    except Exception as e:
        print(f"Error opening chat: {e}")
        import traceback
        traceback.print_exc()

# BIND DOUBLE-CLICK TO LABEL
label.bind("<Double-Button-1>", open_chat)

# ADD KEYBOARD SHORTCUT TOO
root.bind("c", open_chat)

# QUIT WITH SAVE
def quit_pet(event=None):
    print("Right-click quit triggered")
    save_history()
    root.destroy()

# BIND RIGHT-CLICK TO LABEL
label.bind("<Button-3>", quit_pet)

# ANIMATION
def animate():
    global current_frame
    if len(frames) > 0:
        current_frame = (current_frame + 1) % len(frames)
        label.config(image=frames[current_frame])
    root.after(200, animate)

animate()

print("Cat assistant started! Double-click to chat, Right-click to quit")

root.mainloop()