# sms_alerts/send_sms.py

import africastalking
import json
import os

def send_sms_alert():
    try:
        # Load credentials
        cred_path = os.path.join(os.path.dirname(__file__), 'credentials.json')
        with open(cred_path, 'r') as f:
            creds = json.load(f)

        africastalking.initialize(
            username=creds["username"],
            api_key=creds["apiKey"]
        )

        sms = africastalking.SMS

        # Define your message and recipient(s)
        recipients = [creds["phoneNumber"]]  # e.g. "+2567XXXXXXXX"
        message = "✅ Worker with full PPE detected (Hardhat + Vest). Entry allowed."

        response = sms.send(message, recipients)
        print("[SMS Sent] Response:", response)

    except Exception as e:
        print("[SMS Error]", e)
