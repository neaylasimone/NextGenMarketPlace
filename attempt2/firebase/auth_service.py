# auth_service.py - Authentication related functions
import firebase_admin
from firebase_admin import auth
import datetime
import re
from typing import Dict, Optional
from firebase_config import db

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_password(password: str) -> bool:
    """
    Validate password strength
    Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    """
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True

def validate_username(username: str) -> bool:
    """
    Validate username
    Requirements:
    - 3-20 characters
    - Alphanumeric and underscores only
    """
    pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return bool(re.match(pattern, username))

def register_user(email: str, password: str, username: str) -> Dict:
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
        # Validate inputs
        if not validate_email(email):
            return {'success': False, 'error': 'Invalid email format'}
        if not validate_password(password):
            return {'success': False, 'error': 'Password does not meet security requirements'}
        if not validate_username(username):
            return {'success': False, 'error': 'Invalid username format'}
        
        # Check if email already exists
        try:
            auth.get_user_by_email(email)
            return {'success': False, 'error': 'Email already registered'}
        except auth.UserNotFoundError:
            pass
        
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
            'last_login': None,
            'listed_items': [],
            'wishlist': [],
            'is_active': True
        })
        
        return {'success': True, 'user': user}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def update_user_profile(user_id: str, updates: Dict) -> Dict:
    """
    Update a user's profile information
    
    Args:
        user_id (str): User's ID
        updates (dict): Fields to update
        
    Returns:
        dict: Result with success status or error
    """
    try:
        # Validate user exists
        user = auth.get_user(user_id)
        
        # Update Firebase Auth profile if username is being updated
        if 'username' in updates:
            if not validate_username(updates['username']):
                return {'success': False, 'error': 'Invalid username format'}
            auth.update_user(user_id, display_name=updates['username'])
        
        # Update Firestore profile
        db.collection('users').document(user_id).update(updates)
        
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_user_by_email(email: str) -> Dict:
    """
    Get a user by email
    
    Args:
        email (str): User's email
        
    Returns:
        dict: Result with success status and user data or error
    """
    try:
        if not validate_email(email):
            return {'success': False, 'error': 'Invalid email format'}
            
        user = auth.get_user_by_email(email)
        return {'success': True, 'user': user}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_user(user_id: str) -> Dict:
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

def delete_user(user_id: str) -> Dict:
    """
    Delete a user
    
    Args:
        user_id (str): User's ID
        
    Returns:
        dict: Result with success status or error
    """
    try:
        # Delete user from Firebase Auth
        auth.delete_user(user_id)
        
        # Delete user profile from Firestore
        db.collection('users').document(user_id).delete()
        
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def verify_id_token(id_token: str) -> Dict:
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

def reset_password(email: str) -> Dict:
    """
    Send password reset email to user
    
    Args:
        email (str): User's email
        
    Returns:
        dict: Result with success status or error
    """
    try:
        if not validate_email(email):
            return {'success': False, 'error': 'Invalid email format'}
            
        # Generate password reset link
        link = auth.generate_password_reset_link(email)
        
        # TODO: Send email with reset link
        # This would typically be handled by your email service
        
        return {'success': True, 'reset_link': link}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def update_password(user_id: str, new_password: str) -> Dict:
    """
    Update user's password
    
    Args:
        user_id (str): User's ID
        new_password (str): New password
        
    Returns:
        dict: Result with success status or error
    """
    try:
        if not validate_password(new_password):
            return {'success': False, 'error': 'Password does not meet security requirements'}
            
        auth.update_user(user_id, password=new_password)
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}