import sys
import os
import time
import cv2
import pyttsx3
from ultralytics import YOLO

# Custom module paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.serial_comm import send_to_arduino
from sms_alerts.send_sms import send_sms_alert

# Initialize TTS
tts = pyttsx3.init()
def speak(text):
    tts.say(text)
    tts.runAndWait()

# PPE configuration
required_ppe = ['Safety Vest']
full_detection_keywords = ['Person', 'Safety Vest', 'Helmet', 'NO-Hardhat', 'Face Mask', 'NO-Mask']

# Load model
model = YOLO('computer_vision/model/best.pt')
vid = cv2.VideoCapture(0)

# System states
STATE_WAIT_FOR_PERSON = 0
STATE_REPOSITION_DELAY = 1
STATE_CHECK_FOR_PPE = 2

state = STATE_WAIT_FOR_PERSON
reposition_start = None
ppe_check_start = None
frame_with_required_ppe = None

window_duration = 5  # seconds
reposition_delay = 6  # seconds

font = cv2.FONT_HERSHEY_SIMPLEX

def should_take_picture(detected):
    return ('Person' in detected and
            any(x in detected for x in ['Helmet', 'NO-Hardhat']) and
            any(x in detected for x in ['Face Mask', 'NO-Mask']) and
            'Safety Vest' in detected)

print("System started...")

while True:
    ret, frame = vid.read()
    if not ret:
        print("❌ Frame capture failed.")
        break

    pred = model.predict(frame)[0]
    detected = [model.names[int(c)] for c in pred.boxes.cls]
    print(f"[DETECTED] {detected}")

    # Overlay state text
    if state == STATE_WAIT_FOR_PERSON:
        display_text = "Waiting for person to appear..."
        if 'Person' in detected:
            print("👤 Person detected! Ask to reposition...")
            reposition_start = time.time()
            state = STATE_REPOSITION_DELAY
            speak("Please position yourself at about one meter for PPE check.")

    elif state == STATE_REPOSITION_DELAY:
        display_text = "Please position yourself at 1 meter..."
        if time.time() - reposition_start >= reposition_delay:
            print("⏳ Starting PPE detection process...")
            state = STATE_CHECK_FOR_PPE
            ppe_check_start = None
            speak("Checking your equipment, please stay still.")

    elif state == STATE_CHECK_FOR_PPE:
        display_text = "Checking for required PPE..."
        if ppe_check_start is None and all(item in detected for item in required_ppe):
            print("🟡 Required PPE detected. Checking for full visibility...")
            ppe_check_start = time.time()
            frame_with_required_ppe = frame.copy()

        elif ppe_check_start:
            elapsed = time.time() - ppe_check_start
            if should_take_picture(detected):
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"computer_vision/logs/{timestamp}.jpg"
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                cv2.imwrite(filename, frame)
                print(f"[📸] Image saved: {filename}")

                try:
                    send_to_arduino('1')
                except Exception as e:
                    print(f"[Serial Error] {e}")

                send_sms_alert()
                speak("PPE check successful. Thank you.")
                print("✅ Alert sent. System will pause for 5 seconds...")
                time.sleep(5)
                state = STATE_WAIT_FOR_PERSON
                ppe_check_start = None
            elif elapsed >= window_duration:
                print("❌ Could not get full visibility. Please try again.")
                speak("Please try again and ensure your full body is visible.")
                state = STATE_WAIT_FOR_PERSON
                ppe_check_start = None

    else:
        display_text = "System initializing..."

    # Draw overlay text on frame
    cv2.putText(frame, display_text, (30, 30), font, 0.8, (0, 255, 0), 2, cv2.LINE_AA)

    # Show predictions overlayed from YOLO
    pred_plot = pred.plot()
    cv2.imshow('PPE Compliance Detection', pred_plot)

    # Exit on key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

vid.release()
cv2.destroyAllWindows()
