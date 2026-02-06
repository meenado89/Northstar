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

# LOAD ENVIRONMENT VARIABLES FIRST
load_dotenv()

# INITIALIZE TTS ENGINE
engine = pyttsx3.init()
def speak(text):
    """Thread-safe speaking function"""
    def _speak():
        try:
            engine.say(text)
            engine.runAndWait()
        except:
            pass
    threading.Thread(target=_speak, daemon=True).start()

# RANDOM GREETING ON START
STARTUP_GREETINGS = [
    "HEY! I WAS JUST WAITING FOR YOU",
    "OH HI! WANNA CHAT",
    "YOU'RE BACK! THAT MADE MY DAY",
    "HI! WHAT'S UP"
]
startup_greeting = random.choice(STARTUP_GREETINGS)
print(startup_greeting)
speak(startup_greeting)

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
model = genai.GenerativeModel('gemini-2.0-flash-exp')

# CHAT HISTORY
chat_history = []
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_history.json")

def load_history():
    global chat_history
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                chat_history = json.load(f)
    except Exception as e:
        print(f"Could not load history: {e}")
        chat_history = []

load_history()
chat_session = model.start_chat(history=chat_history)

def save_history():
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(chat_history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Could not save history: {e}")

# CREATE PIXEL GUI WINDOW - FIX #1: Better window setup
root = tk.Tk()
root.title("Pixel Pet")  # Add title first for debugging
root.overrideredirect(True)  # Remove borders
root.attributes("-topmost", True)  # Always on top

# FIX #2: Set window size and position before making transparent
root.geometry("150x150+100+100")  # width x height + x_position + y_position

# FIX #3: Transparent background (do this AFTER geometry)
try:
    root.wm_attributes("-transparentcolor", "white")
except:
    print("Transparency not supported on this system")

# LOAD ANIMATION FRAMES
frames = []
assets_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
print(f"Looking for frames in: {assets_path}")

for i in range(1, 9):
    img_path = os.path.join(assets_path, f"idle{i}.png")
    print(f"Checking: {img_path} - Exists: {os.path.exists(img_path)}")
    if os.path.exists(img_path):
        try:
            img = Image.open(img_path)
            # FIX #4: Resize images to consistent size
            img = img.resize((80, 80), Image.Resampling.LANCZOS)
            frames.append(ImageTk.PhotoImage(img))
            print(f"Loaded frame {i}")
        except Exception as e:
            print(f"Error loading frame {i}: {e}")

# FIX #5: Create a simple placeholder if no frames found
if not frames:
    print("⚠️ WARNING: No animation frames found!")
    print("Creating placeholder. Make sure your 'assets' folder contains idle1.png to idle8.png")
    # Create a simple colored square as placeholder
    from PIL import ImageDraw
    placeholder = Image.new('RGBA', (150, 150), (255, 255, 255, 0))
    draw = ImageDraw.Draw(placeholder)
    draw.ellipse([25, 25, 125, 125], fill=(100, 200, 255, 255))
    draw.ellipse([50, 60, 70, 80], fill=(0, 0, 0, 255))  # Left eye
    draw.ellipse([80, 60, 100, 80], fill=(0, 0, 0, 255))  # Right eye
    draw.arc([50, 85, 100, 110], 0, 180, fill=(0, 0, 0, 255), width=3)  # Smile
    frames.append(ImageTk.PhotoImage(placeholder))
else:
    print(f"✓ Loaded {len(frames)} animation frames")

current_frame = 0
label = tk.Label(root, image=frames[0], bg="white", borderwidth=0)
label.pack(fill=tk.BOTH, expand=True)

# ANIMATE PIXEL
def animate():
    global current_frame
    if len(frames) > 1:  # Only animate if we have multiple frames
        current_frame = (current_frame + 1) % len(frames)
        label.config(image=frames[current_frame])
    root.after(200, animate)

# FIX #6: Start animation after window is ready
root.after(100, animate)

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
    try:
        with sr.Microphone() as mic:
            recognizer.adjust_for_ambient_noise(mic, duration=0.5)
            speak("I AM LISTENING")
            print("🎤 Listening...")
            try:
                audio = recognizer.listen(mic, timeout=5, phrase_time_limit=10)
                command = recognizer.recognize_google(audio)
                print(f"✓ Heard: {command}")
                return command
            except sr.WaitTimeoutError:
                print("⏱️ Timeout - no speech detected")
                speak("I DID NOT HEAR ANYTHING")
                return None
            except sr.UnknownValueError:
                print("❌ Could not understand audio")
                speak("I DID NOT UNDERSTAND")
                return None
    except Exception as e:
        print(f"❌ Listen error: {e}")
        return None

# PROCESS SYSTEM COMMANDS
def process_command(command):
    command_lower = command.lower()
    
    # Common websites - just say "youtube", "google", etc.
    common_sites = {
        "youtube": "https://youtube.com",
        "google": "https://google.com",
        "gmail": "https://gmail.com",
        "facebook": "https://facebook.com",
        "twitter": "https://twitter.com",
        "instagram": "https://instagram.com",
        "reddit": "https://reddit.com",
        "amazon": "https://amazon.com"
    }
    
    # Check for direct site mentions
    for site_name, url in common_sites.items():
        if site_name in command_lower and ("open" in command_lower or command_lower.strip() == site_name):
            webbrowser.open(url)
            speak(f"OPENING {site_name}")
            print(f"✓ Opening {url}")
            return True
    
    if "open site" in command_lower or "open website" in command_lower:
     if "open site" in command_lower or "open website" in command_lower:
        speak("WHICH SITE SHOULD I OPEN?")
        site = listen()
        if site:
            if not site.startswith("http"):
                site = "https://" + site
            webbrowser.open(site)
            speak(f"OPENING {site}")
            return True
    elif "open file" in command_lower or "open folder" in command_lower:
        speak("WHAT FILE OR FOLDER SHOULD I OPEN?")
        path = listen()
        if path:
            try:
                os.startfile(path)
                speak(f"OPENED {path}")
            except Exception as e:
                speak("COULD NOT OPEN FILE OR FOLDER")
                print(f"File open error: {e}")
            return True
    elif "delete file" in command_lower:
        speak("WHICH FILE SHOULD I DELETE?")
        path = listen()
        if path:
            try:
                os.remove(path)
                speak(f"FILE DELETED")
            except Exception as e:
                speak("COULD NOT DELETE FILE")
                print(f"Delete error: {e}")
            return True
    elif "volume up" in command_lower:
        pyautogui.press("volumeup")
        speak("VOLUME UP")
        return True
    elif "volume down" in command_lower:
        pyautogui.press("volumedown")
        speak("VOLUME DOWN")
        return True
    elif "mute" in command_lower:
        pyautogui.press("volumemute")
        speak("MUTED VOLUME")
        return True
    elif "time" in command_lower or "what time" in command_lower:
        t = time.strftime("%I:%M %p")
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
        
        # Prepend personality to first user message
        if len(chat_history) == 0:
            full_message = PET_PERSONALITY + "\n\n" + message
        else:
            full_message = message
            
        chat_history.append({"role": "user", "parts": [full_message]})

        handled = process_command(message)
        if not handled:
            try:
                response = chat_session.send_message(full_message)
                ai_reply = response.text
                speak(ai_reply)
                chat_history.append({"role": "model", "parts": [ai_reply]})
                chat_display.config(state='normal')
                chat_display.insert(tk.END, f"Pixel: {ai_reply}\n\n", "assistant")
                chat_display.config(state='disabled')
                chat_display.see(tk.END)
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                print(error_msg)
                chat_display.config(state='normal')
                chat_display.insert(tk.END, f"Pixel: SOMETHING WENT WRONG\n", "error")
                chat_display.config(state='disabled')

        save_history()
        
    send_button = tk.Button(input_frame, text="Send", command=send_message_box)
    send_button.pack(side=tk.RIGHT, padx=5)

    def clear_chat_history():
        global chat_history, chat_session
        chat_history = []
        chat_session = model.start_chat(history=[])
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

# FIX #7: IMPROVED BACKGROUND LISTENER WITH DEBUGGING
WAKE_WORDS = ["hey pixel", "okay pixel", "ok pixel", "pixel"]
listening_active = False

def background_listener():
    global listening_active
    recognizer = sr.Recognizer()
    
    # FIX #8: Adjust these settings for better wake word detection
    recognizer.energy_threshold = 300  # Lower = more sensitive
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8  # How long to wait for pause
    
    print("🎧 Background listener started")
    print(f"Wake words: {', '.join(WAKE_WORDS)}")
    print("Say 'hey pixel' or 'ok pixel' to activate!")
    
    while True:
        if listening_active:
            time.sleep(0.1)  # Don't interfere with active listening
            continue
            
        try:
            with sr.Microphone() as mic:
                recognizer.adjust_for_ambient_noise(mic, duration=0.3)
                
                # FIX #9: Listen in shorter bursts for better wake word detection
                audio = recognizer.listen(mic, timeout=2, phrase_time_limit=3)

            try:
                command = recognizer.recognize_google(audio).lower()
                print(f"🎤 Background heard: '{command}'")
                
                # CHECK FOR WAKE WORDS AND EXTRACT COMMAND
                wake_detected = False
                detected_word = None
                extracted_command = None
                
                for wake_word in WAKE_WORDS:
                    if wake_word in command:
                        wake_detected = True
                        detected_word = wake_word
                        # Extract command after wake word
                        if wake_word in command:
                            parts = command.split(wake_word, 1)
                            if len(parts) > 1 and parts[1].strip():
                                extracted_command = parts[1].strip()
                        break
                
                # Also check if command starts with "pixel"
                if not wake_detected and command.startswith("pixel"):
                    wake_detected = True
                    detected_word = "pixel"
                    extracted_command = command.replace("pixel", "", 1).strip()
                
                if wake_detected:
                    print(f"✓✓✓ WAKE WORD DETECTED: '{detected_word}' ✓✓✓")
                    listening_active = True
                    
                    # If command was in same phrase, use it
                    if extracted_command:
                        print(f"📝 Command extracted: '{extracted_command}'")
                        user_command = extracted_command
                    else:
                        # Otherwise, ask for command
                        speak("YES?")
                        try:
                            with sr.Microphone() as mic:
                                recognizer.adjust_for_ambient_noise(mic, duration=0.3)
                                print("🎤 Listening for command...")
                                audio_command = recognizer.listen(mic, timeout=5, phrase_time_limit=10)
                            
                            user_command = recognizer.recognize_google(audio_command)
                            print(f"✓ Command received: '{user_command}'")
                        except sr.WaitTimeoutError:
                            speak("I DID NOT HEAR ANYTHING")
                            print("⏱️ Command timeout")
                            listening_active = False
                            continue
                        except sr.UnknownValueError:
                            speak("I DID NOT UNDERSTAND YOUR COMMAND")
                            print("❌ Could not understand command")
                            listening_active = False
                            continue
                    
                    # Process the command
                    try:
                        handled = process_command(user_command)
                        
                        if not handled:
                            # Send to AI
                            print(f"🤖 Sending to AI: '{user_command}'")
                            response = chat_session.send_message(user_command)
                            ai_reply = response.text
                            print(f"💬 AI Reply: '{ai_reply}'")
                            chat_history.append({"role": "user", "parts": [user_command]})
                            chat_history.append({"role": "model", "parts": [ai_reply]})
                            speak(ai_reply)
                            save_history()
                    except Exception as e:
                        print(f"❌ Processing error: {e}")
                        speak("SORRY, SOMETHING WENT WRONG")
                    finally:
                        listening_active = False
                        
            except sr.UnknownValueError:
                # Normal - just background noise
                pass
            except sr.RequestError as e:
                print(f"❌ Google Speech API error: {e}")
                time.sleep(5)
                
        except sr.WaitTimeoutError:
            # Normal - no speech detected in timeout period
            pass
        except Exception as e:
            print(f"❌ Background listener error: {e}")
            time.sleep(2)

# START LISTENER THREAD
listener_thread = threading.Thread(target=background_listener, daemon=True)
listener_thread.start()

print("\n" + "="*50)
print("✓ PIXEL ASSISTANT STARTED!")
print("="*50)
print("Controls:")
print("  • Double-click Pixel → Open chat")
print("  • Press 'c' → Open chat")
print("  • Right-click Pixel → Quit")
print("  • Say 'hey pixel' → Voice command")
print("="*50 + "\n")

# FIX #10: Make sure window appears
root.lift()
root.focus_force()
root.mainloop()