import os
import firebase_admin
from firebase_admin import credentials, firestore
from sample_data import populate_sample_data

def main():
    # Initialize Firebase Admin SDK
    try:
        cred_path = os.path.join(os.path.dirname(__file__), "nextgenmarketplace-3c041-firebase-adminsdk-fbsvc-a51be76f07.json")
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            
            # Populate sample data
            result = populate_sample_data(db)
            if result['success']:
                print("Successfully populated database with sample data!")
            else:
                print(f"Error populating database: {result['error']}")
        else:
            print("Firebase Admin SDK credentials file not found. Please add the credentials file to the firebase directory.")
    except Exception as e:
        print(f"Error initializing Firebase: {str(e)}")

if __name__ == "__main__":
    main() 