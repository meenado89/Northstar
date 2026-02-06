# PIXEL PET - NO API VERSION (FOR TESTING)
import tkinter as tk
from tkinter import scrolledtext
import sys
import random
from PIL import Image, ImageTk
import os
import time
import pyttsx3
import speech_recognition as sr
import pyautogui
import webbrowser
import threading

# GET APPLICATION PATH
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

print("="*50)
print("PIXEL PET - NO API TEST VERSION")
print("="*50)
print("This version works WITHOUT Gemini API")
print("It only does voice commands, no AI chat")
print("="*50 + "\n")

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

# RANDOM GREETING
STARTUP_GREETINGS = [
    "HEY! I WAS JUST WAITING FOR YOU",
    "OH HI! WANNA CHAT",
    "YOU'RE BACK! THAT MADE MY DAY",
    "HI! WHAT'S UP"
]
startup_greeting = random.choice(STARTUP_GREETINGS)
print(startup_greeting)
speak(startup_greeting)

# CREATE GUI WINDOW
root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
root.wm_attributes("-transparentcolor", "white")

# LOAD ANIMATION FRAMES
frames = []
assets_path = os.path.join(application_path, "assets")
print(f"\nLooking for images in: {assets_path}")

try:
    for i in range(1, 9):
        img_path = os.path.join(assets_path, f"Bidle{i}.png")
        if os.path.exists(img_path):
            frames.append(ImageTk.PhotoImage(Image.open(img_path)))
            print(f"  ✓ Loaded idle{i}.png")
        else:
            print(f"  ⚠️  idle{i}.png not found")
    
    if len(frames) == 0:
        raise Exception("No animation frames found in assets folder!")
        
    print(f"\n✓ Loaded {len(frames)} frames successfully\n")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("Make sure you have an 'assets' folder with idle1.png to idle8.png")
    root.destroy()
    sys.exit(1)

current_frame = 0
label = tk.Label(root, image=frames[0], bg="white")
label.pack()

# SPAWN AT BOTTOM RIGHT
root.update_idletasks()
x = root.winfo_screenwidth() - root.winfo_width() - 10
y = root.winfo_screenheight() - root.winfo_height() - 45
root.geometry(f"+{x}+{y}")

print(f"Window position: x={x}, y={y}")
print(f"Window size: {root.winfo_width()}x{root.winfo_height()}\n")

# ANIMATE
def animate():
    global current_frame
    if frames:
        current_frame = (current_frame + 1) % len(frames)
        label.config(image=frames[current_frame])
    root.after(62000, animate)
animate()

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

label.bind("<Button-1>", start_move)
label.bind("<B1-Motion>", do_move)

# VOICE LISTENING
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
                print("⏱️  Timeout")
                speak("I DID NOT HEAR ANYTHING")
                return None
            except sr.UnknownValueError:
                print("❌ Could not understand")
                speak("I DID NOT UNDERSTAND")
                return None
    except Exception as e:
        print(f"❌ Listen error: {e}")
        return None

# PROCESS COMMANDS
def process_command(command):
    command_lower = command.lower()
    
    # Common websites
    common_sites = {
        "youtube": "https://youtube.com",
        "google": "https://google.com",
        "gmail": "https://gmail.com",
        "chat gpt": "https://chat.openai.com",
        "facebook": "https://facebook.com",
        "twitter": "https://twitter.com",
        "instagram": "https://instagram.com",
        "reddit": "https://reddit.com",
        "amazon": "https://amazon.com"
    }
    
    for site_name, url in common_sites.items():
        if site_name in command_lower and ("open" in command_lower or command_lower.strip() == site_name):
            webbrowser.open(url)
            speak(f"OPENING {site_name.upper()}")
            print(f"✓ Opening {url}")
            return True
    
    if "open site" in command_lower or "open website" in command_lower:
        speak("WHICH SITE?")
        site = listen()
        if site:
            if not site.startswith("http"):
                site = "https://" + site
            webbrowser.open(site)
            speak(f"OPENING {site}")
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
        speak("MUTED")
        return True
    elif "time" in command_lower or "what time" in command_lower:
        t = time.strftime("%I:%M %p")
        speak(f"THE TIME IS {t}")
        print(f"Time: {t}")
        return True
    
    # If command not recognized
    speak("I CAN ONLY DO SYSTEM COMMANDS. NO AI CHAT IN THIS VERSION")
    return True

# SIMPLE INFO WINDOW (NO AI)
chat_window = None
def open_chat(event=None):
    global chat_window
    if chat_window and chat_window.winfo_exists():
        chat_window.lift()
        return
    chat_window = tk.Toplevel(root)
    chat_window.title("Pixel - Test Version")
    chat_window.geometry("400x300")
    
    info_text = scrolledtext.ScrolledText(chat_window, wrap=tk.WORD, width=50, height=15)
    info_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    info_text.insert(tk.END, "PIXEL PET - TEST VERSION\n\n", "title")
    info_text.insert(tk.END, "This version has NO AI chat.\n\n", "normal")
    info_text.insert(tk.END, "Voice commands that work:\n", "normal")
    info_text.insert(tk.END, "• 'Hey pixel open YouTube'\n", "cmd")
    info_text.insert(tk.END, "• 'Hey pixel what time is it'\n", "cmd")
    info_text.insert(tk.END, "• 'Hey pixel volume up'\n", "cmd")
    info_text.insert(tk.END, "• 'Hey pixel mute'\n\n", "cmd")
    info_text.insert(tk.END, "To enable AI chat, you need:\n", "normal")
    info_text.insert(tk.END, "1. Valid Gemini API key\n", "normal")
    info_text.insert(tk.END, "2. .env file with GEMINI_API_KEY\n", "normal")
    info_text.insert(tk.END, "3. Use the full version script\n", "normal")
    
    info_text.tag_config("title", foreground="blue", font=("Arial", 14, "bold"))
    info_text.tag_config("cmd", foreground="green")
    info_text.config(state='disabled')

label.bind("<Double-Button-1>", open_chat)
root.bind("c", open_chat)

def quit_pet(event=None):
    root.destroy()
label.bind("<Button-3>", quit_pet)

# BACKGROUND LISTENER
WAKE_WORDS = ["hey pixel", "okay pixel", "ok pixel", "pixel"]
listening_active = False

def background_listener():
    global listening_active
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8
    
    print("🎧 Background listener started")
    print(f"Wake words: {', '.join(WAKE_WORDS)}\n")
    
    while True:
        if listening_active:
            time.sleep(0.1)
            continue
            
        try:
            with sr.Microphone() as mic:
                recognizer.adjust_for_ambient_noise(mic, duration=0.3)
                audio = recognizer.listen(mic, timeout=2, phrase_time_limit=3)

            try:
                command = recognizer.recognize_google(audio).lower()
                print(f"🎤 Heard: '{command}'")
                
                wake_detected = False
                detected_word = None
                extracted_command = None
                
                for wake_word in WAKE_WORDS:
                    if wake_word in command:
                        wake_detected = True
                        detected_word = wake_word
                        parts = command.split(wake_word, 1)
                        if len(parts) > 1 and parts[1].strip():
                            extracted_command = parts[1].strip()
                        break
                
                if not wake_detected and command.startswith("pixel"):
                    wake_detected = True
                    detected_word = "pixel"
                    extracted_command = command.replace("pixel", "", 1).strip()
                
                if wake_detected:
                    print(f"✓ Wake word: '{detected_word}'")
                    listening_active = True
                    
                    if extracted_command:
                        print(f"📝 Command: '{extracted_command}'")
                        user_command = extracted_command
                    else:
                        speak("YES?")
                        try:
                            with sr.Microphone() as mic:
                                recognizer.adjust_for_ambient_noise(mic, duration=0.3)
                                print("🎤 Listening for command...")
                                audio_command = recognizer.listen(mic, timeout=5, phrase_time_limit=10)
                            
                            user_command = recognizer.recognize_google(audio_command)
                            print(f"✓ Command: '{user_command}'")
                        except (sr.WaitTimeoutError, sr.UnknownValueError):
                            speak("I DID NOT UNDERSTAND")
                            listening_active = False
                            continue
                    
                    try:
                        process_command(user_command)
                    except Exception as e:
                        print(f"❌ Error: {e}")
                        speak("SORRY SOMETHING WENT WRONG")
                    finally:
                        listening_active = False
                        
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                print(f"❌ Google API error: {e}")
                time.sleep(5)
                
        except sr.WaitTimeoutError:
            pass
        except Exception as e:
            print(f"❌ Listener error: {e}")
            time.sleep(2)

listener_thread = threading.Thread(target=background_listener, daemon=True)
listener_thread.start()

print("="*50)
print("✓ PIXEL STARTED!")
print("="*50)
print("  Double-click → Info")
print("  Press 'c' → Info")
print("  Right-click → Quit")
print("  Say wake word → Voice command")
print("="*50 + "\n")

root.mainloop()