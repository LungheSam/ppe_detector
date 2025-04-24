# import sys
# import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# import time
# import cv2
# from ultralytics import YOLO
# from utils.serial_comm import send_to_arduino
# from sms_alerts.send_sms import send_sms_alert


# print("System started...")

# # Classes that show PPE is present
# required_ppe = ['Safety Vest']

# # Load YOLO model
# model = YOLO('computer_vision/model/best.pt')


# def checkfun(img):
#     pred = model.predict(img)[0]
#     detected_classes = [model.names[int(c)] for c in pred.boxes.cls]
#     print(f"Detected classes: {detected_classes}")

#     # Check if both PPE items are present
#     if all(req in detected_classes for req in required_ppe):
#         print("[✅] Worker is wearing full PPE.")
#         cv2.imwrite('computer_vision/out.jpg', img)  # Save image
#         send_to_arduino      # Trigger Arduino (green LED, buzzer beep, etc.)
#         send_sms_alert()   # Notify via SMS
#         time.sleep(4)

#     pred_plotted = pred.plot()
#     return pred_plotted

# # Webcam input
# vid = cv2.VideoCapture(0)

# while True:
#     ret, frame = vid.read()
#     if not ret:
#         print("❌ Failed to capture frame.")
#         break

#     processed_frame = checkfun(frame)
#     cv2.imshow('PPE Compliance Detection', processed_frame)

#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# vid.release()
# cv2.destroyAllWindows()

# import sys
# import os
# import time
# import cv2
# from collections import Counter, defaultdict
# from ultralytics import YOLO

# # Path fixes
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# from utils.serial_comm import send_to_arduino
# from sms_alerts.send_sms import send_sms_alert

# print("System started...")

# # Classes to watch
# required_ppe = ['Safety Vest']
# all_ppe_items = ['Person', 'Helmet', 'Face Mask', 'Safety Vest']  # Update with your actual model class names

# # Load YOLO model
# model = YOLO('computer_vision/model/best.pt')

# # Detection tracker
# detections_log = []
# start_time = time.time()
# window_duration = 5  # seconds

# # Webcam
# vid = cv2.VideoCapture(0)


# def log_detections(pred):
#     detected = [model.names[int(c)] for c in pred.boxes.cls]
#     detections_log.extend(detected)
#     print(f"[FRAME] Detected: {detected}")


# def analyze_window_and_act(frame):
#     if not detections_log:
#         print("[INFO] No detections in the last window.")
#         return

#     # Frequency count
#     counts = Counter(detections_log)
#     print(f"[SUMMARY - Last 5 seconds] {dict(counts)}")

#     # Save image
#     timestamp = time.strftime("%Y%m%d_%H%M%S")
#     filename = f"computer_vision/logs/{timestamp}.jpg"
#     os.makedirs(os.path.dirname(filename), exist_ok=True)
#     cv2.imwrite(filename, frame)
#     print(f"[📸] Frame saved: {filename}")

#     # Decide on action
#     if all(ppe in counts for ppe in required_ppe):
#         print("[✅] PPE Compliance detected.")
#         try:
#             send_to_arduino('1')  # or any signal
#             send_sms_alert()
#         except Exception as e:
#             print(f"[Serial Error] {e}")
#     else:
#         print("[⚠️] Missing PPE detected.")
        


# while True:
#     ret, frame = vid.read()
#     if not ret:
#         print("❌ Failed to capture frame.")
#         break

#     pred = model.predict(frame)[0]
#     log_detections(pred)

#     current_time = time.time()
#     if current_time - start_time >= window_duration:
#         analyze_window_and_act(frame)
#         detections_log.clear()
#         start_time = current_time

#     pred_plotted = pred.plot()
#     cv2.imshow('PPE Compliance Detection', pred_plotted)

#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# vid.release()
# cv2.destroyAllWindows()


# import sys
# import os
# import time
# import cv2
# from ultralytics import YOLO
# from collections import Counter

# # Path fixes
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# from utils.serial_comm import send_to_arduino
# from sms_alerts.send_sms import send_sms_alert

# print("System started...")

# required_ppe = ['Safety Vest']
# full_detection_keywords = ['Person', 'Safety Vest', 'Helmet', 'NO-Hardhat', 'Face Mask', 'NO-Mask']

# model = YOLO('computer_vision/model/best.pt')
# vid = cv2.VideoCapture(0)

# # State variables
# detection_state = {
#     'awaiting_full_view': False,
#     'start_time': None,
#     'frame_with_required_ppe': None
# }

# window_duration = 5  # seconds


# def should_take_picture(detected):
#     return ('Person' in detected and
#             any(x in detected for x in ['Helmet', 'NO-Hardhat']) and
#             any(x in detected for x in ['Face Mask', 'NO-Mask']) and
#             'Safety Vest' in detected)


# while True:
#     ret, frame = vid.read()
#     if not ret:
#         print("❌ Failed to capture frame.")
#         break

#     pred = model.predict(frame)[0]
#     detected = [model.names[int(c)] for c in pred.boxes.cls]
#     print(f"[DETECTED] {detected}")

#     # If we haven't triggered detection yet
#     if not detection_state['awaiting_full_view']:
#         if all(item in detected for item in required_ppe):
#             print("🟡 Required PPE detected! Monitoring for full view...")
#             detection_state['awaiting_full_view'] = True
#             detection_state['start_time'] = time.time()
#             detection_state['frame_with_required_ppe'] = frame.copy()
#     else:
#         elapsed = time.time() - detection_state['start_time']
#         if should_take_picture(detected):
#             print("✅ Full view captured. Saving and alerting.")
#             timestamp = time.strftime("%Y%m%d_%H%M%S")
#             filename = f"computer_vision/logs/{timestamp}.jpg"
#             os.makedirs(os.path.dirname(filename), exist_ok=True)
#             cv2.imwrite(filename, frame)
#             print(f"[📸] Frame saved: {filename}")
#             try:
#                 send_to_arduino('1')
#                 send_sms_alert()
#             except Exception as e:
#                 print(f"[Serial Error] {e}")
            
#             detection_state['awaiting_full_view'] = False
#         elif elapsed >= window_duration:
#             print("⛔ Could not get full PPE view in 5 seconds. Please reposition.")
#             detection_state['awaiting_full_view'] = False

#     # Show video
#     pred_plotted = pred.plot()
#     cv2.imshow('PPE Compliance Detection', pred_plotted)

#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# vid.release()
# cv2.destroyAllWindows()


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
