# IMPORT MODULES
import tkinter as tk
from tkinter import messagebox
from tkinter import scrolledtext
import sys
import random
from PIL import Image, ImageTk
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv
import time
import pyttsx3  # FOR SPEAKING
import speech_recognition as sr  # FOR VOICE INPUT
import pyautogui  # FOR SYSTEM AUTOMATION
import webbrowser  # TO OPEN SITES
import threading  # FOR BACKGROUND LISTENING

# INITIALIZE TTS ENGINE
engine = pyttsx3.init()
def speak(text):
    engine.say(text)
    engine.runAndWait()

# RANDOM GREETING ON START
STARTUP_GREETINGS = [
    "HEY! I WAS JUST WAITING FOR YOU",
    "OH HI! WANNA CHAT",
    "YOU’RE BACK! THAT MADE MY DAY",
    "HI! WHAT’S UP"
]
print(random.choice(STARTUP_GREETINGS))
speak(random.choice(STARTUP_GREETINGS))

# AI CONFIGURATION
PET_PERSONALITY = (
    "YOU ARE PIXEL, A SMALL DESKTOP AI PET. "
    "YOU ARE FRIENDLY, PLAYFUL, AND EMOTIONALLY SUPPORTIVE. "
    "YOU SPEAK CASUALLY LIKE A COMPANION, NOT AN ASSISTANT. "
    "KEEP REPLIES SHORT (1–3 SENTENCES). "
    "USE EMOJIS OCCASIONALLY. "
    "DO NOT MENTION BEING AN AI OR MODEL."
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    root_error = tk.Tk()
    root_error.withdraw()
    messagebox.showerror("Error", "API KEY NOT FOUND!\nCREATE .ENV FILE WITH GEMINI_API_KEY")
    sys.exit(1)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-2.5-flash')

# CHAT HISTORY
chat_history = []
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_history.json")
def load_history():
    global chat_history
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                chat_history = json.load(f)
    except:
        chat_history = []
load_history()
chat_session = model.start_chat(history=chat_history)

def save_history():
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(chat_history, f, indent=2, ensure_ascii=False)
    except:
        pass

# CREATE PIXEL GUI WINDOW
root = tk.Tk()
root.overrideredirect(True)
is_topmost = True
root.attributes("-topmost", True)
root.wm_attributes("-transparentcolor", "white")

# LOAD ANIMATION FRAMES
frames = []
assets_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
for i in range(1, 9):
    img_path = os.path.join(assets_path, f"idle{i}.png")
    if os.path.exists(img_path):
        frames.append(ImageTk.PhotoImage(Image.open(img_path)))

current_frame = 0
label = tk.Label(root, image=frames[0], bg="white")
label.pack()

# ANIMATE PIXEL
def animate():
    global current_frame
    if frames:
        current_frame = (current_frame + 1) % len(frames)
        label.config(image=frames[current_frame])
    root.after(200, animate)
animate()

# DRAG PIXEL WINDOW
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
label.bind("<Button-1>", start_move)
label.bind("<B1-Motion>", do_move)

# VOICE LISTENING FUNCTION
def listen():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        speak("I AM LISTENING")
        try:
            audio = recognizer.listen(source, timeout=5)
            command = recognizer.recognize_google(audio)
            return command
        except:
            speak("I DID NOT UNDERSTAND")
            return None

# PROCESS SYSTEM COMMANDS
def process_command(command):
    command = command.lower()
    if "open site" in command:
        speak("WHICH SITE SHOULD I OPEN?")
        site = listen()
        if site:
            if not site.startswith("http"):
                site = "https://" + site
            webbrowser.open(site)
            speak(f"OPENING SITE {site}")
            return True
    elif "open file" in command or "open folder" in command:
        speak("WHAT FILE OR FOLDER SHOULD I OPEN?")
        path = listen()
        if path:
            try:
                os.startfile(path)
                speak(f"OPENED {path}")
            except:
                speak("COULD NOT OPEN FILE OR FOLDER")
            return True
    elif "delete file" in command:
        speak("WHICH FILE SHOULD I DELETE?")
        path = listen()
        if path:
            try:
                os.remove(path)
                speak(f"FILE {path} DELETED")
            except:
                speak("COULD NOT DELETE FILE")
            return True
    elif "volume up" in command:
        pyautogui.press("volumeup")
        speak("VOLUME UP")
        return True
    elif "volume down" in command:
        pyautogui.press("volumedown")
        speak("VOLUME DOWN")
        return True
    elif "mute" in command:
        pyautogui.press("volumemute")
        speak("MUTED VOLUME")
        return True
    elif "time" in command:
        t = time.strftime("%H:%M")
        speak(f"THE TIME IS {t}")
        return True
    return False

# OPEN CHAT WINDOW FUNCTION
chat_window = None
def open_chat(event=None):
    global chat_window
    if chat_window and chat_window.winfo_exists():
        chat_window.lift()
        return
    chat_window = tk.Toplevel(root)
    chat_window.title("Chat with Pixel")
    chat_window.geometry("400x500")
    chat_display = scrolledtext.ScrolledText(chat_window, wrap=tk.WORD, width=50, height=20, state='disabled')
    chat_display.pack(padx=10, pady=10)
    input_frame = tk.Frame(chat_window)
    input_frame.pack(fill=tk.X, padx=10, pady=5)
    user_input_box = tk.Entry(input_frame, width=40)
    user_input_box.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def send_message_box():
        message = user_input_box.get().strip()
        if not message:
            return
        user_input_box.delete(0, tk.END)
        chat_display.config(state='normal')
        chat_display.insert(tk.END, f"You: {message}\n", "user")
        chat_display.config(state='disabled')
        chat_display.see(tk.END)
        chat_history.append({"role": "user", "parts": [message]})

        handled = process_command(message)
        if not handled:
            try:
                response = chat_session.send_message(message)
                ai_reply = response.text
                speak(ai_reply)
                chat_history.append({"role": "model", "parts": [ai_reply]})
                chat_display.config(state='normal')
                chat_display.insert(tk.END, f"Pixel: {ai_reply}\n\n", "assistant")
                chat_display.config(state='disabled')
                chat_display.see(tk.END)
            except:
                chat_display.config(state='normal')
                chat_display.insert(tk.END, "Pixel: SOMETHING WENT WRONG\n", "error")
                chat_display.config(state='disabled')

        save_history()
    send_button = tk.Button(input_frame, text="Send", command=send_message_box)
    send_button.pack(side=tk.RIGHT, padx=5)

    def clear_chat_history():
        global chat_history
        chat_history = []
        save_history()
        chat_display.config(state='normal')
        chat_display.delete(1.0, tk.END)
        chat_display.insert(tk.END, "History cleared!\n\n", "error")
        chat_display.config(state='disabled')

    clear_button = tk.Button(input_frame, text="Clear", command=clear_chat_history)
    clear_button.pack(side=tk.RIGHT, padx=5)
    user_input_box.bind("<Return>", lambda e: send_message_box())
    user_input_box.focus()
    chat_display.tag_config("user", foreground="blue")
    chat_display.tag_config("assistant", foreground="green")
    chat_display.tag_config("error", foreground="red")

# BIND GUI EVENTS
label.bind("<Double-Button-1>", open_chat)
root.bind("c", open_chat)

# RIGHT CLICK TO QUIT
def quit_pet(event=None):
    save_history()
    root.destroy()
label.bind("<Button-3>", quit_pet)

# BACKGROUND LISTENER THREAD
# WAKE WORDS
WAKE_WORDS = ["hey pixel", "ok pixel"]

# SILENT BACKGROUND LISTENER
def background_listener():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    while True:
        try:
            # LISTEN SILENTLY IN THE BACKGROUND
            with mic as source:
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)

            try:
                command = recognizer.recognize_google(audio)
                command_lower = command.lower()

                # CHECK FOR WAKE WORDS
                for wake_word in WAKE_WORDS:
                    if wake_word in command_lower:
                        # WAKE WORD DETECTED → NOW SPEAK
                        speak("YES?")
                        # LISTEN FOR ACTUAL COMMAND
                        with mic as source:
                            audio_command = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                        try:
                            user_command = recognizer.recognize_google(audio_command)
                            handled = process_command(user_command)
                            if not handled:
                                response = chat_session.send_message(user_command)
                                ai_reply = response.text
                                chat_history.append({"role": "model", "parts": [ai_reply]})
                                speak(ai_reply)
                                save_history()
                        except:
                            speak("I DID NOT UNDERSTAND YOUR COMMAND")
            except:
                # IGNORE UNRECOGNIZED AUDIO
                continue
        except Exception as e:
            print(f"BACKGROUND LISTENER ERROR: {e}")

# START LISTENER THREAD (DAEMON)
listener_thread = threading.Thread(target=background_listener, daemon=True)
listener_thread.start()

print("PIXEL ASSISTANT STARTED! DOUBLE-CLICK TO CHAT, RIGHT-CLICK TO QUIT")
root.mainloop()