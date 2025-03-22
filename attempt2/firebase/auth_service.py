# auth_service.py - Authentication related functions
import firebase_admin
from firebase_admin import auth
import datetime
from firebase_config import db

def register_user(email, password, username):
    """
    Register a new user with Firebase Authentication and create Firestore profile
    
    Args:
        email (str): User's email
        password (str): User's password
        username (str): User's display name
        
    Returns:
        dict: Result with success status and user data or error
    """
    try:
        # Create user in Firebase Auth
        user = auth.create_user(
            email=email,
            password=password,
            display_name=username
        )
        
        # Create user profile in Firestore
        db.collection('users').document(user.uid).set({
            'email': email,
            'username': username,
            'created_at': datetime.datetime.now(),
            'listed_items': [],
            'wishlist': []
        })
        
        return {'success': True, 'user': user}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_user_by_email(email):
    """
    Get a user by email
    
    Args:
        email (str): User's email
        
    Returns:
        dict: Result with success status and user data or error
    """
    try:
        user = auth.get_user_by_email(email)
        return {'success': True, 'user': user}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_user(user_id):
    """
    Get a user by ID
    
    Args:
        user_id (str): User's ID
        
    Returns:
        dict: Result with success status and user data or error
    """
    try:
        user = auth.get_user(user_id)
        return {'success': True, 'user': user}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def delete_user(user_id):
    """
    Delete a user
    
    Args:
        user_id (str): User's ID
        
    Returns:
        dict: Result with success status or error
    """
    try:
        auth.delete_user(user_id)
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def verify_id_token(id_token):
    """
    Verify an ID token
    
    Args:
        id_token (str): ID token to verify
        
    Returns:
        dict: Result with success status and token data or error
    """
    try:
        decoded_token = auth.verify_id_token(id_token)
        return {'success': True, 'token': decoded_token}
    except Exception as e:
        return {'success': False, 'error': str(e)}