import cv2
import time
import sys
import os
import pyttsx3

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ultralytics import YOLO
from firebase.firebase_logger import log_to_firebase, log_ppe_photo_to_firebase
from utils.serial_comm import send_to_arduino, read_from_arduino, check_rfid_card

# ============== TEXT TO SPEECH SETUP ==============
tts = pyttsx3.init()
tts.setProperty('rate', 150)
tts.setProperty('volume', 0.9)

def speak(text):
    """Text to speech function"""
    print(f"[SPEAK] {text}")
    tts.say(text)
    tts.runAndWait()

# ============== SYSTEM STATES ==============
STATE_WAITING_FOR_RFID = 0      # Waiting for card tap
STATE_CHECKING_CARD = 1          # Validating card with Firebase
STATE_WAITING_FOR_PERSON = 2     # Card valid, waiting for person
STATE_REPOSITION_DELAY = 3       # Person detected, repositioning
STATE_CHECK_FOR_PPE = 4          # Checking PPE

# ============== LOAD MODEL ==============
model_path = os.path.join(os.path.dirname(__file__), 'model', 'best.pt')
if not os.path.exists(model_path):
    print(f"❌ Model not found at: {model_path}")
    exit(1)

print(f"[INFO] Loading model from: {model_path}")
model = YOLO(model_path)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Camera error! Check webcam connection.")
    exit(1)

# ============== PPE CONFIGURATION ==============
REQUIRED_PPE = ['Safety Vest']  # Only Safety Vest required

# ============== SYSTEM VARIABLES ==============
state = STATE_WAITING_FOR_RFID
reposition_start = None
ppe_check_start = None
current_card_uid = None
current_user_name = None
ppe_check_passed = False
ppe_retry_count = 0  # Track PPE retry attempts (max 2 chances)

window_duration = 9      # seconds to verify PPE
reposition_delay = 6     # seconds to reposition

font = cv2.FONT_HERSHEY_SIMPLEX

def check_ppe_compliance(detected):
    """Check if all required PPE is detected"""
    missing = [item for item in REQUIRED_PPE if item not in detected]
    return len(missing) == 0, missing

print("="*60)
print("PPE Detection System Started (RFID Triggered Mode)")
print("Required PPE: Safety Vest Only")
print("PPE Chances: 2 attempts allowed")
print("Press 'q' to quit")
print("="*60)

# Initial voice greeting
speak("PPE detection system activated. Please tap your card.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Frame capture failed.")
        break

    # Run YOLO detection on every frame
    pred = model.predict(frame, verbose=False)[0]
    detected = [model.names[int(c)] for c in pred.boxes.cls]
    
    # ============== STATE MACHINE ==============
    
    if state == STATE_WAITING_FOR_RFID:
        display_text = "Tap your RFID card"
        cv2.putText(frame, display_text, (30, 30), font, 0.8, (0, 255, 0), 2, cv2.LINE_AA)
        
        # Check for RFID card
        rfid_uid = read_from_arduino()
        if rfid_uid:
            current_card_uid = rfid_uid
            state = STATE_CHECKING_CARD
            speak("Card detected. Validating...")
            continue

    elif state == STATE_CHECKING_CARD:
        display_text = "Validating card..."
        cv2.putText(frame, display_text, (30, 30), font, 0.8, (255, 255, 0), 2, cv2.LINE_AA)
        
        # Check card in Firebase
        is_valid, user_name, message = check_rfid_card(current_card_uid)
        
        if is_valid:
            current_user_name = user_name
            ppe_retry_count = 0  # Reset retry counter for new user
            # Log card acceptance
            log_to_firebase('CARD_ACCEPTED', f"Card accepted for {user_name}", current_card_uid, user_name)
            speak(f"Card accepted. Welcome {user_name}. Please step in front of the camera.")
            print(f"✅ Card VALID - User: {user_name}")
            state = STATE_WAITING_FOR_PERSON
            send_to_arduino('1')  # Send temporary acceptance signal (maybe beep)
        else:
            # Log card rejection
            log_to_firebase('CARD_REJECTED', message, current_card_uid, None)
            speak(message)
            print(f"❌ Card INVALID - {message}")
            send_to_arduino('0')  # Send denial signal
            
            # Wait 3 seconds, then reset to wait for next card
            time.sleep(3)
            state = STATE_WAITING_FOR_RFID
            current_card_uid = None
            continue

    elif state == STATE_WAITING_FOR_PERSON:
        display_text = "Waiting for person to appear..."
        cv2.putText(frame, display_text, (30, 30), font, 0.8, (255, 255, 0), 2, cv2.LINE_AA)
        
        # Show detected items
        if detected:
            y_offset = 70
            cv2.putText(frame, "Detected:", (30, y_offset), font, 0.5, (255, 255, 255), 1)
            for i, item in enumerate(detected[:5]):
                cv2.putText(frame, f"- {item}", (30, y_offset + (i+1)*25), font, 0.5, (0, 255, 0), 1)
        
        # Check if person is detected
        if 'Person' in detected:
            print("👤 Person detected!")
            reposition_start = time.time()
            state = STATE_REPOSITION_DELAY
            speak("Please position yourself at about one meter for PPE check.")

    elif state == STATE_REPOSITION_DELAY:
        remaining = reposition_delay - (time.time() - reposition_start)
        display_text = f"Please position yourself at 1 meter... ({int(remaining)}s)"
        cv2.putText(frame, display_text, (30, 30), font, 0.7, (255, 255, 0), 2, cv2.LINE_AA)
        
        # Show detected items
        if detected:
            y_offset = 70
            cv2.putText(frame, "Detected:", (30, y_offset), font, 0.5, (255, 255, 255), 1)
            for i, item in enumerate(detected[:5]):
                cv2.putText(frame, f"- {item}", (30, y_offset + (i+1)*25), font, 0.5, (0, 255, 0), 1)
        
        if time.time() - reposition_start >= reposition_delay:
            print("⏳ Starting PPE detection process...")
            state = STATE_CHECK_FOR_PPE
            ppe_check_start = None  # Will be set immediately when entering state
            speak("Checking your equipment. Please stay still. Required: Safety Vest.")

    elif state == STATE_CHECK_FOR_PPE:
        display_text = f"Checking for required PPE: {', '.join(REQUIRED_PPE)} (Attempt {ppe_retry_count + 1}/2)"
        cv2.putText(frame, display_text, (30, 30), font, 0.6, (255, 255, 0), 2, cv2.LINE_AA)
        
        # Check if person is still present
        if 'Person' not in detected:
            print("⚠️ Person lost! Resetting...")
            speak("Please step back in front of the camera.")
            state = STATE_WAITING_FOR_PERSON
            ppe_check_start = None
            continue
        
        # Check PPE compliance
        ppe_ok, missing_ppe = check_ppe_compliance(detected)
        
        # FIX: Start timer immediately when entering this state
        if ppe_check_start is None:
            print("⏳ Starting PPE verification timer (5 seconds)...")
            ppe_check_start = time.time()
            speak("You have 5 seconds to show your safety vest.")
        
        # Calculate elapsed time
        elapsed = time.time() - ppe_check_start
        
        # Show missing items
        if missing_ppe:
            y_offset = 70
            cv2.putText(frame, "Missing PPE:", (30, y_offset), font, 0.5, (0, 0, 255), 1)
            for i, item in enumerate(missing_ppe):
                cv2.putText(frame, f"⚠️ {item}", (30, y_offset + (i+1)*25), font, 0.5, (0, 0, 255), 1)
        
        # Show detected items
        if detected:
            y_offset = 70 + (len(missing_ppe) + 1) * 25 if missing_ppe else 70
            cv2.putText(frame, "Detected:", (30, y_offset), font, 0.5, (255, 255, 255), 1)
            for i, item in enumerate(detected[:5]):
                cv2.putText(frame, f"- {item}", (30, y_offset + (i+1)*25), font, 0.5, (0, 255, 0), 1)
        
        # Show timer (always show, regardless of PPE status)
        remaining = window_duration - elapsed
        cv2.putText(frame, f"Time remaining: {remaining:.1f}s", (30, 110), 
                   font, 0.6, (255, 255, 0), 2, cv2.LINE_AA)
        
        # Show success message if PPE is detected before time expires
        if ppe_ok and elapsed < window_duration:
            cv2.putText(frame, "✅ PPE Detected! Holding...", (30, 150), 
                       font, 0.6, (0, 255, 0), 2, cv2.LINE_AA)
        
        # Check if time is up
        if elapsed >= window_duration:
            if ppe_ok:
                # SUCCESS: All PPE detected within time window
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                log_dir = os.path.join(os.path.dirname(__file__), 'logs')
                os.makedirs(log_dir, exist_ok=True)
                filename = os.path.join(log_dir, f'ppe_success_{current_card_uid}_{timestamp}.jpg')
                cv2.imwrite(filename, frame)
                print(f"[📸] Image saved: {filename}")
                
                # Log PPE success to Firebase
                log_to_firebase('PPE_APPROVED', 
                               f"PPE Complete - Detected: {detected}", 
                               current_card_uid, 
                               current_user_name)
                
                # Log photo path to Firebase
                log_ppe_photo_to_firebase(filename, current_card_uid, current_user_name, 'PPE_APPROVED')
                
                # Send signal to Arduino to grant access
                send_to_arduino('1')
                
                # Voice confirmation
                speak(f"PPE check successful. Access granted. Thank you, {current_user_name}.")
                print(f"✅ ACCESS GRANTED - {current_user_name} - PPE Compliance OK")
                
                # Wait 3 seconds, then reset for next user
                time.sleep(3)
                
                # Reset everything
                state = STATE_WAITING_FOR_RFID
                current_card_uid = None
                current_user_name = None
                ppe_check_start = None
                ppe_retry_count = 0
                speak("System ready. Please tap your card for next user.")
                
            else:
                # FAILURE: Time's up but PPE not detected
                ppe_retry_count += 1
                print(f"❌ PPE CHECK FAILED - Attempt {ppe_retry_count}/2 - Missing: {missing_ppe}")
                
                if ppe_retry_count < 2:
                    # GIVE SECOND CHANCE
                    print(f"⚠️ SECOND CHANCE - {current_user_name}")
                    speak(f"PPE check failed on attempt {ppe_retry_count}. You have one more chance. Please reposition and try again.")
                    
                    # Wait 2 seconds, then go back to reposition
                    time.sleep(2)
                    state = STATE_WAITING_FOR_PERSON
                    ppe_check_start = None
                    
                else:
                    # FINAL REJECTION - Both chances used
                    print(f"❌ ACCESS DENIED - {current_user_name} - Missing: {missing_ppe} (All attempts exhausted)")
                    
                    # Log final PPE rejection to Firebase
                    log_to_firebase('PPE_REJECTED', 
                                   f"PPE Rejected (Both attempts failed) - Missing: {missing_ppe}", 
                                   current_card_uid, 
                                   current_user_name)
                    
                    # Send signal to Arduino to deny access
                    send_to_arduino('0')
                    
                    # Voice warning
                    speak("PPE check failed on final attempt. Access denied. Please ensure you have your safety vest.")
                    
                    # Wait 3 seconds, then reset for next user
                    time.sleep(3)
                    
                    # Reset everything
                    state = STATE_WAITING_FOR_RFID
                    current_card_uid = None
                    current_user_name = None
                    ppe_check_start = None
                    ppe_retry_count = 0
                    speak("System ready. Please tap your card for next user.")

    # Show YOLO detection overlay
    pred_plot = pred.plot()
    cv2.imshow('PPE Compliance - Telecom Access System', pred_plot)

    # Exit on 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        speak("System shutting down. Goodbye.")
        print("\n👋 System shutdown by user")
        break

# ============== CLEANUP ==============
cap.release()
cv2.destroyAllWindows()
print("System stopped.")