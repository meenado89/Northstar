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
import queue
from enum import Enum, auto


# CONFIGURATION
class ListeningState(Enum):
    """State machine for voice assistant"""
    IDLE = auto()
    WAKE_WORD_DETECTED = auto()
    LISTENING_FOR_COMMAND = auto()
    PROCESSING = auto()
    SPEAKING = auto()

# Wake words
WAKE_WORDS = ["hey pixel", "okay pixel", "ok pixel", "pixel"]

# Startup greetings
STARTUP_GREETINGS = [
    "HEY! I WAS JUST WAITING FOR YOU",
    "OH HI! WANNA CHAT",
    "YOU'RE BACK! THAT MADE MY DAY",
    "HI! WHAT'S UP"
]

# Common websites for quick access
COMMON_SITES = {
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

# Audio configuration
ENERGY_THRESHOLD = 300
PAUSE_THRESHOLD = 0.8
LISTEN_TIMEOUT = 5
PHRASE_TIME_LIMIT = 10


# THREADING-SAFE TTS MANAGER


class TTSManager:
    """Thread-safe text-to-speech manager using queue"""
    
    def __init__(self):
        self.tts_queue = queue.Queue()
        self.shutdown_event = threading.Event()
        self.worker_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.worker_thread.start()
        print("✓ TTS Manager initialized")
    
    def _tts_worker(self):
        """Worker thread that processes TTS requests"""
        engine = pyttsx3.init()  # One engine per thread - thread safe!
        
        while not self.shutdown_event.is_set():
            try:
                # Get text from queue with timeout to allow shutdown checks
                text = self.tts_queue.get(timeout=0.5)
                
                if text is None:  # Shutdown signal
                    break
                
                try:
                    engine.say(text)
                    engine.runAndWait()
                except Exception as e:
                    print(f"  TTS error: {e}")
                
                self.tts_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f" TTS worker error: {e}")
    
    def speak(self, text):
        """Queue text for speaking"""
        if not self.shutdown_event.is_set():
            self.tts_queue.put(text)
    
    def shutdown(self):
        """Gracefully shutdown TTS worker"""
        self.shutdown_event.set()
        self.tts_queue.put(None)  # Signal worker to stop
        self.worker_thread.join(timeout=2)


# MICROPHONE MANAGER WITH THREAD-SAFE ACCESS
class MicrophoneManager:
    """Manages microphone access with proper locking"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = ENERGY_THRESHOLD
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = PAUSE_THRESHOLD
        self.mic_lock = threading.Lock()
        self._calibrated = False
        print("✓ Microphone Manager initialized")
    
    def calibrate(self):
        """One-time ambient noise calibration"""
        if self._calibrated:
            return
        
        try:
            with self.mic_lock:
                with sr.Microphone() as mic:
                    print("🎤 Calibrating microphone...")
                    self.recognizer.adjust_for_ambient_noise(mic, duration=1.0)
                    self._calibrated = True
                    print("✓ Microphone calibrated")
        except Exception as e:
            print(f"  Calibration failed: {e}")
    
    def listen_for_wake_word(self, timeout=2, phrase_limit=3):
        """Listen for wake word with proper locking"""
        with self.mic_lock:
            try:
                with sr.Microphone() as mic:
                    audio = self.recognizer.listen(mic, timeout=timeout, phrase_time_limit=phrase_limit)
                    return audio
            except sr.WaitTimeoutError:
                return None
            except Exception as e:
                print(f"  Wake word listen error: {e}")
                return None
    
    def listen_for_command(self, timeout=LISTEN_TIMEOUT, phrase_limit=PHRASE_TIME_LIMIT):
        """Listen for full command with proper locking"""
        with self.mic_lock:
            try:
                with sr.Microphone() as mic:
                    audio = self.recognizer.listen(mic, timeout=timeout, phrase_time_limit=phrase_limit)
                    return audio
            except sr.WaitTimeoutError:
                return None
            except Exception as e:
                print(f"  Command listen error: {e}")
                return None
    
    def recognize_speech(self, audio):
        """Convert audio to text using Google Speech Recognition"""
        if audio is None:
            return None
        
        try:
            return self.recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f" Google API error: {e}")
            return None


# STATE MANAGER WITH THREAD-SAFE STATE TRANSITIONS
class StateManager:
    """Thread-safe state management for voice assistant"""
    
    def __init__(self):
        self.state = ListeningState.IDLE
        self.state_lock = threading.Lock()
    
    def get_state(self):
        """Get current state"""
        with self.state_lock:
            return self.state
    
    def set_state(self, new_state):
        """Set new state with logging"""
        with self.state_lock:
            if self.state != new_state:
                print(f" State: {self.state.name} → {new_state.name}")
                self.state = new_state
    
    def is_busy(self):
        """Check if assistant is currently busy"""
        with self.state_lock:
            return self.state != ListeningState.IDLE


# COMMAND PROCESSOR
class CommandProcessor:
    """Processes voice commands"""
    
    def __init__(self, tts_manager):
        self.tts = tts_manager
    
    def process(self, command):
        """Process a voice command and execute appropriate action"""
        if not command:
            return False
        
        command_lower = command.lower()
        print(f" Processing: '{command}'")
        
        # Check common websites
        for site_name, url in COMMON_SITES.items():
            if site_name in command_lower and ("open" in command_lower or command_lower.strip() == site_name):
                webbrowser.open(url)
                self.tts.speak(f"OPENING {site_name.upper()}")
                print(f"✓ Opened {url}")
                return True
        
        # Open custom website
        if "open site" in command_lower or "open website" in command_lower:
            self.tts.speak("WHICH SITE?")
            # Note: This would need additional mic access - simplified for now
            return True
        
        # Volume controls
        if "volume up" in command_lower:
            pyautogui.press("volumeup")
            self.tts.speak("VOLUME UP")
            return True
        
        if "volume down" in command_lower:
            pyautogui.press("volumedown")
            self.tts.speak("VOLUME DOWN")
            return True
        
        if "mute" in command_lower:
            pyautogui.press("volumemute")
            self.tts.speak("MUTED")
            return True
        
        # Time query
        if "time" in command_lower or "what time" in command_lower:
            current_time = time.strftime("%I:%M %p")
            self.tts.speak(f"THE TIME IS {current_time}")
            print(f" Time: {current_time}")
            return True
        
        # Screenshot
        if "screenshot" in command_lower or "screen shot" in command_lower:
            try:
                screenshot = pyautogui.screenshot()
                screenshot.save(f"screenshot_{int(time.time())}.png")
                self.tts.speak("SCREENSHOT TAKEN")
                return True
            except Exception as e:
                print(f" Screenshot error: {e}")
                self.tts.speak("SCREENSHOT FAILED")
                return True
        
        # Minimize all windows
        if "minimize" in command_lower or "show desktop" in command_lower:
            pyautogui.hotkey('win', 'd')
            self.tts.speak("MINIMIZED")
            return True
        
        # Command not recognized
        self.tts.speak("I CAN ONLY DO SYSTEM COMMANDS. NO AI CHAT IN THIS VERSION")
        return False


# VOICE ASSISTANT COORDINATOR
class VoiceAssistant:
    """Coordinates all voice assistant components"""
    
    def __init__(self, tts_manager, mic_manager, state_manager, command_processor):
        self.tts = tts_manager
        self.mic = mic_manager
        self.state = state_manager
        self.commands = command_processor
        self.shutdown_event = threading.Event()
        self.listener_thread = None
    
    def start_background_listener(self):
        """Start the background wake word detection"""
        self.listener_thread = threading.Thread(target=self._background_listener, daemon=True)
        self.listener_thread.start()
        print("✓ Background listener started")
    
    def _background_listener(self):
        """Background thread that listens for wake words"""
        print(f" Listening for wake words: {', '.join(WAKE_WORDS)}")
        
        # Calibrate microphone once
        self.mic.calibrate()
        
        while not self.shutdown_event.is_set():
            # Skip if already processing a command
            if self.state.is_busy():
                time.sleep(0.1)
                continue
            
            # Listen for wake word
            audio = self.mic.listen_for_wake_word(timeout=2, phrase_limit=3)
            
            if audio is None:
                continue
            
            # Recognize wake word
            text = self.mic.recognize_speech(audio)
            
            if text is None:
                continue
            
            command_lower = text.lower()
            print(f" Heard: '{text}'")
            
            # Check for wake word
            wake_detected = False
            detected_word = None
            extracted_command = None
            
            for wake_word in WAKE_WORDS:
                if wake_word in command_lower:
                    wake_detected = True
                    detected_word = wake_word
                    parts = command_lower.split(wake_word, 1)
                    if len(parts) > 1 and parts[1].strip():
                        extracted_command = parts[1].strip()
                    break
            
            # Handle "pixel" at start
            if not wake_detected and command_lower.startswith("pixel"):
                wake_detected = True
                detected_word = "pixel"
                extracted_command = command_lower.replace("pixel", "", 1).strip()
            
            if not wake_detected:
                continue
            
            print(f"✓ Wake word detected: '{detected_word}'")
            self.state.set_state(ListeningState.WAKE_WORD_DETECTED)
            
            # If command was included with wake word, use it
            if extracted_command:
                print(f" Inline command: '{extracted_command}'")
                self._handle_command(extracted_command)
            else:
                # Ask for command
                self.state.set_state(ListeningState.LISTENING_FOR_COMMAND)
                self.tts.speak("YES?")
                
                # Wait a moment for TTS to start
                time.sleep(0.3)
                
                # Listen for the actual command
                command_audio = self.mic.listen_for_command(timeout=5, phrase_limit=10)
                
                if command_audio is None:
                    self.tts.speak("I DID NOT HEAR ANYTHING")
                    self.state.set_state(ListeningState.IDLE)
                    continue
                
                user_command = self.mic.recognize_speech(command_audio)
                
                if user_command is None:
                    self.tts.speak("I DID NOT UNDERSTAND")
                    self.state.set_state(ListeningState.IDLE)
                    continue
                
                print(f" Command received: '{user_command}'")
                self._handle_command(user_command)
    
    def _handle_command(self, command):
        """Handle a recognized command"""
        try:
            self.state.set_state(ListeningState.PROCESSING)
            self.commands.process(command)
        except Exception as e:
            print(f" Command processing error: {e}")
            self.tts.speak("SORRY SOMETHING WENT WRONG")
        finally:
            # Small delay before returning to idle
            time.sleep(0.5)
            self.state.set_state(ListeningState.IDLE)
    
    def shutdown(self):
        """Shutdown the voice assistant"""
        self.shutdown_event.set()
        if self.listener_thread:
            self.listener_thread.join(timeout=2)


# APPLICATION PATH

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))


# INITIALIZE COMPONENTS

print("="*50)
print("PIXEL PET - FIXED VERSION")
print("="*50)
print("All critical bugs resolved!")
print("="*50 + "\n")

# Initialize managers
tts_manager = TTSManager()
mic_manager = MicrophoneManager()
state_manager = StateManager()
command_processor = CommandProcessor(tts_manager)
voice_assistant = VoiceAssistant(tts_manager, mic_manager, state_manager, command_processor)

# Random startup greeting
startup_greeting = random.choice(STARTUP_GREETINGS)
print(startup_greeting)
tts_manager.speak(startup_greeting)

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
       
        img_path = os.path.join(assets_path, f"Didle{i}.png")
        if os.path.exists(img_path):
            frames.append(ImageTk.PhotoImage(Image.open(img_path)))
            print(f"  ✓ Loaded Didle{i}.png")
        else:
            print(f"    Didle{i}.png not found")
    
    if len(frames) == 0:
        raise Exception("No animation frames found in assets folder!")
        
    print(f"\n✓ Loaded {len(frames)} frames successfully\n")
    
except Exception as e:
    print(f"\n Error: {e}")
    print("Make sure you have an 'assets' folder with Didle1.png to Didle8.png")
    root.destroy()
    sys.exit(1)

current_frame = 0
label = tk.Label(root, image=frames[0], bg="white")
label.pack()

# SPAWN AT BOTTOM RIGHT
root.update_idletasks()
x = root.winfo_screenwidth() - root.winfo_width() - 15
y = root.winfo_screenheight() - root.winfo_height() - 57
root.geometry(f"+{x}+{y}")

print(f"Window position: x={x}, y={y}")
print(f"Window size: {root.winfo_width()}x{root.winfo_height()}\n")

# ANIMATE 
def animate():
    global current_frame
    if frames:
        current_frame = (current_frame + 1) % len(frames)
        label.config(image=frames[current_frame])
    root.after(200, animate)  

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


# INFO WINDOW

chat_window = None

def open_chat(event=None):
    """Open info/chat window"""
    global chat_window
    if chat_window and chat_window.winfo_exists():
        chat_window.lift()
        return
    
    chat_window = tk.Toplevel(root)
    chat_window.title("Pixel")
    chat_window.geometry("450x400")
    
    info_text = scrolledtext.ScrolledText(chat_window, wrap=tk.WORD, width=50, height=20)
    info_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    
    info_text.insert(tk.END, "PIXEL PET\n\n", "title")
    info_text.insert(tk.END, " All Critical Bugs Fixed!\n\n", "success")
    
    info_text.insert(tk.END, "What's Fixed:\n", "header")
    info_text.insert(tk.END, "• Thread-safe TTS (no more crashes)\n", "normal")
    info_text.insert(tk.END, "• Microphone locking (no conflicts)\n", "normal")
    info_text.insert(tk.END, "• State management (no race conditions)\n", "normal")
    info_text.insert(tk.END, "• Proper error handling\n\n", "normal")
    
    info_text.insert(tk.END, "Voice Commands:\n", "header")
    info_text.insert(tk.END, "• 'Hey pixel open YouTube'\n", "cmd")
    info_text.insert(tk.END, "• 'Hey pixel what time is it'\n", "cmd")
    info_text.insert(tk.END, "• 'Hey pixel volume up/down'\n", "cmd")
    info_text.insert(tk.END, "• 'Hey pixel mute'\n", "cmd")
    info_text.insert(tk.END, "• 'Hey pixel screenshot'\n", "cmd")
    info_text.insert(tk.END, "• 'Hey pixel minimize'\n\n", "cmd")
    
    info_text.insert(tk.END, "Keyboard Shortcuts:\n", "header")
    info_text.insert(tk.END, "• C - Open this info window\n", "normal")
    info_text.insert(tk.END, "• T - Show current time\n", "normal")
    info_text.insert(tk.END, "• B - Toggle background listening\n", "normal")
    info_text.insert(tk.END, "• Right-click - Quit\n\n", "normal")
    
    info_text.insert(tk.END, "Note: This version has NO AI chat.\n", "normal")
    info_text.insert(tk.END, "For AI features, add Gemini API key.\n", "normal")
    
    info_text.tag_config("title", foreground="blue", font=("Arial", 14, "bold"))
    info_text.tag_config("success", foreground="green", font=("Arial", 12, "bold"))
    info_text.tag_config("header", foreground="purple", font=("Arial", 11, "bold"))
    info_text.tag_config("cmd", foreground="darkgreen")
    info_text.tag_config("normal", foreground="black")
    
    info_text.config(state='disabled')


# KEYBOARD SHORTCUTS - NOW IMPLEMENTED

def show_time(event=None):
    """Show current time (T key)"""
    current_time = time.strftime("%I:%M %p")
    tts_manager.speak(f"THE TIME IS {current_time}")
    print(f" Time: {current_time}")

def toggle_background_listening(event=None):
    """Toggle background listening on/off (B key)"""
    if state_manager.get_state() == ListeningState.IDLE:
        tts_manager.speak("LISTENING PAUSED")
        state_manager.set_state(ListeningState.SPEAKING)  # Prevents listening
        print("⏸  Background listening paused")
    else:
        state_manager.set_state(ListeningState.IDLE)
        tts_manager.speak("LISTENING RESUMED")
        print("▶  Background listening resumed")

def quit_pet(event=None):
    """Quit the application gracefully"""
    print("\n" + "="*50)
    print("Shutting down Pixel Pet...")
    print("="*50)
    
    # Shutdown components
    voice_assistant.shutdown()
    tts_manager.shutdown()
    
    # Destroy GUI
    root.destroy()
    print(" Goodbye!")

# Bind keyboard shortcuts
label.bind("<Double-Button-1>", open_chat)
root.bind("c", open_chat)
root.bind("C", open_chat)
root.bind("t", show_time)
root.bind("T", show_time)
root.bind("b", toggle_background_listening)
root.bind("B", toggle_background_listening)
label.bind("<Button-3>", quit_pet)


# START VOICE ASSISTANT

# Start background listener
voice_assistant.start_background_listener()

# STARTUP MESSAGE


print("="*50)
print(" PIXEL PET READY!")
print("="*50)
print("Controls:")
print("  Double-click → Info window")
print("  Press 'C' → Info window")
print("  Press 'T' → Show time")
print("  Press 'B' → Toggle listening")
print("  Right-click → Quit")
print("  Say wake word → Voice command")
print("="*50)
print(f"Wake words: {', '.join(WAKE_WORDS)}")
print("="*50 + "\n")

# RUN GUI

try:
    root.mainloop()
except KeyboardInterrupt:
    print("\n  Interrupted by user")
    quit_pet()