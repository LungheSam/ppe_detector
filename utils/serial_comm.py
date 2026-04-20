import serial
import serial.tools.list_ports
import platform
import sys
import os
import time

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from firebase.firebase_logger import log_to_firebase

ser = None

def find_arduino_port():
    """Automatically find Arduino port"""
    print("[INFO] Scanning for Arduino...")
    ports = serial.tools.list_ports.comports()
    
    for port in ports:
        print(f"  Found: {port.device} - {port.description}")
        
        # Check for Arduino in description
        if 'Arduino' in port.description or 'CH340' in port.description or 'USB' in port.description:
            print(f"[INFO] Found Arduino on {port.device}")
            return port.device
    
    # Common Linux ports to try
    common_ports = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyACM0', '/dev/ttyACM1']
    for port in common_ports:
        try:
            test_ser = serial.Serial(port, 9600, timeout=0.5)
            test_ser.close()
            print(f"[INFO] Found working port: {port}")
            return port
        except:
            continue
    
    print("[WARNING] No Arduino found")
    return None

# Try to initialize the serial connection
arduino_port = find_arduino_port()

if arduino_port:
    try:
        ser = serial.Serial(arduino_port, 9600, timeout=1)
        time.sleep(2)  # Wait for Arduino to reset
        print(f"[INFO] Connected to Arduino on {arduino_port}")
    except Exception as e:
        print(f"[WARNING] Could not connect to Arduino: {e}")
        ser = None
else:
    print("[WARNING] No Arduino detected. Running in simulation mode.")
    ser = None

def send_to_arduino(signal):
    """Send signal to Arduino: '1' for grant, '0' for deny"""
    if ser:
        try:
            ser.write(signal.encode())
            print(f"[SERIAL] Sent signal: {signal}")
            return True
        except Exception as e:
            print(f"[SERIAL ERROR] Failed to send signal: {e}")
            return False
    else:
        print(f"[SIMULATION] Would send: {signal}")
        return False

def read_from_arduino():
    """Read RFID UID from Arduino"""
    if ser:
        try:
            if ser.in_waiting > 0:
                data = ser.readline().decode('utf-8').strip()
                if data:
                    if data.startswith("UID:"):
                        uid = data.replace("UID:", "").strip()
                        print(f"[RFID] Card detected: {uid}")
                        return uid
                    else:
                        # Print other Arduino messages but don't return them
                        print(f"[ARDUINO] {data}")
        except Exception as e:
            print(f"[SERIAL ERROR] Failed to read: {e}")
    return None

def check_rfid_card(uid):
    """
    Check if RFID card is valid in Firebase Firestore
    Returns: (is_valid, user_name, message)
    """
    try:
        from firebase_admin import firestore
        
        # Get Firestore client
        db = firestore.client()
        
        # Query the 'registered_cards' collection for matching UID
        cards_ref = db.collection('registered_cards')
        query = cards_ref.where('uid', '==', uid).limit(1)
        results = query.get()
        
        for doc in results:
            card_data = doc.to_dict()
            user_name = card_data.get('name', 'Unknown User')
            print(f"[FIREBASE] Card validated: {user_name} (UID: {uid})")
            return True, user_name, f"Card accepted. Welcome {user_name}"
        
        # Card not found
        print(f"[FIREBASE] Card rejected: {uid} not registered")
        return False, None, "Card not recognized. Access denied."
            
    except Exception as e:
        print(f"[FIREBASE ERROR] Failed to check card: {e}")
        return False, None, f"Database error: {str(e)}"

if __name__ == "__main__":
    print("="*50)
    print("[INFO] Starting RFID Reader Test")
    print("[INFO] Tap your RFID card on the reader")
    print("[INFO] Press Ctrl+C to stop")
    print("="*50)
    
    try:
        while True:
            uid = read_from_arduino()
            if uid:
                print(f"✅ Card UID: {uid}")
                
                # Check against Firebase Firestore
                is_valid, user, msg = check_rfid_card(uid)
                print(f"   Valid: {is_valid}")
                if user:
                    print(f"   User: {user}")
                print(f"   Message: {msg}")
                
                # Send feedback to Arduino
                if is_valid:
                    send_to_arduino('1')
                else:
                    send_to_arduino('0')
            
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\n[INFO] Stopped by user")
        if ser:
            ser.close()
            print("[INFO] Serial connection closed")