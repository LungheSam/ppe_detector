import serial
import platform

ser = None

# Try to initialize the serial connection
try:
    port = 'COM4' if platform.system() == 'Windows' else '/dev/ttyUSB0'
    ser = serial.Serial(port, 9600, timeout=1)
    print(f"[INFO] Connected to Arduino on {port}")
except Exception as e:
    print(f"[WARNING] Could not connect to Arduino on serial port: {e}")
    ser = None  # Mark serial as unavailable

def send_to_arduino(signal):
    if ser:
        try:
            ser.write(signal.encode())
            print(f"[SERIAL] Sent signal: {signal}")
        except Exception as e:
            print(f"[SERIAL ERROR] Failed to send signal: {e}")
    else:
        print("Hello, World")  # Serial unavailable fallback
