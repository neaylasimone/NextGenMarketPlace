# firebase_config.py - Firebase configuration and initialization
import os
import firebase_admin
from firebase_admin import credentials, firestore, auth, storage

# Firebase config for client-side auth
firebase_config = {
    "apiKey": "AIzaSyCOaOWgmWZACwroiwMk8PgZ3FkouTFf7zs",
    "authDomain": "nextgenmarketplace-3c041.firebaseapp.com",
    "projectId": "nextgenmarketplace-3c041",
    "storageBucket": "nextgenmarketplace-3c041.appspot.com",
    "messagingSenderId": "647637034752",
    "appId": "1:647637034752:web:d188f7820264ad6a10b5e5",
    "measurementId": "G-XKD3BYRLJM",
    "databaseURL": "https://nextgenmarketplace-3c041-default-rtdb.firebaseio.com"
}

# Initialize Firebase Admin SDK
try:
    cred_path = os.path.join(os.path.dirname(__file__), "nextgenmarketplace-3c041-firebase-adminsdk-fbsvc-a51be76f07.json")
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
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
    print(f"Error initializing Firebase Admin SDK: {str(e)}")
    firebase_app = None
    db = None
    auth = None
    storage = None