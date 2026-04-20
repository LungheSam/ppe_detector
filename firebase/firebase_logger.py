import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import os

# Get the absolute path to the project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Path to your Firebase key file (inside firebase folder)
key_file_path = os.path.join(PROJECT_ROOT, "firebase", "serviceAccountKey.json")

# Check if the file exists
if not os.path.exists(key_file_path):
    print(f"❌ Firebase key file not found at: {key_file_path}")
    print("Please make sure serviceAccountKey.json is in the firebase folder")
    db = None
else:
    # Initialize Firebase (only once)
    cred = credentials.Certificate(key_file_path)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("[FIREBASE] Firebase initialized successfully with Firestore")

def log_to_firebase(status, details="", card_uid=None, user_name=None):
    """
    Log access attempt to Firestore
    status: 'CARD_ACCEPTED', 'CARD_REJECTED', 'PPE_APPROVED', 'PPE_REJECTED'
    """
    try:
        if not db:
            print("[FIREBASE ERROR] Firestore client not initialized")
            return False
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M:%S'),
            'status': status,
            'details': details,
            'card_uid': card_uid if card_uid else 'N/A',
            'user_name': user_name if user_name else 'N/A'
        }
        
        # Add document to 'access_logs' collection
        db.collection('access_logs').add(log_entry)
        print(f"[FIREBASE] Logged: {status} - {details}")
        return True
    except Exception as e:
        print(f"[FIREBASE ERROR] Failed to log: {e}")
        return False