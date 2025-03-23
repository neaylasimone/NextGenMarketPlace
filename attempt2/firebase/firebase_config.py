# firebase_config.py - Firebase configuration and initialization
import os
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore, auth, storage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Firebase config for client-side auth
firebase_config = {
    "apiKey": "AIzaSyAATMva5buJTHF2tMjGRkTx5rz8SClKmV4",
    "authDomain": "nextgenmarketplace.firebaseapp.com",
    "projectId": "nextgenmarketplace",
    "storageBucket": "nextgenmarketplace.appspot.com",
    "messagingSenderId": "1234567890",
    "appId": "1:1234567890:web:abcdef1234567890",
    "databaseURL": "https://nextgenmarketplace-default-rtdb.firebaseio.com"
}

# Initialize Firebase Admin SDK
try:
    # Get the absolute path to the service account key file
    current_dir = Path(__file__).parent
    cred_path = current_dir / "nextgenmarketplace-3c041-firebase-adminsdk-fbsvc-a51be76f07.json"
    
    if cred_path.exists():
        cred = credentials.Certificate(str(cred_path))
        if not firebase_admin._apps:
            firebase_app = firebase_admin.initialize_app(cred)
        else:
            firebase_app = firebase_admin.get_app()
        db = firestore.client()
        auth = auth
        storage = storage
    else:
        print("Firebase Admin SDK credentials file not found. Please add the credentials file to the firebase directory.")
        firebase_app = None
        db = None
        auth = None
        storage = None
except Exception as e:
    print(f"Error initializing Firebase: {str(e)}")
    firebase_app = None
    db = None
    auth = None
    storage = None