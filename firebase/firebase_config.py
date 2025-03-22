# firebase_config.py - Firebase configuration and initialization
import firebase_admin
from firebase_admin import credentials, firestore, auth

def initialize_firebase():
    """Initialize Firebase if not already initialized"""
    if not firebase_admin._apps:
        # Path to your service account key file
        cred = credentials.Certificate("path/to/serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
    
    # Get Firestore client
    db = firestore.client()
    return db

# Initialize Firebase on module import
db = initialize_firebase()