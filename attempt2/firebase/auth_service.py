# auth_service.py - Authentication related functions
import streamlit as st
from .firebase_config import db
import firebase_admin
from firebase_admin import auth
import datetime
import re
from typing import Dict, Optional, Any

def validate_email(email: str) -> bool:
    """Validate email format"""
    return '@' in email and '.' in email

def validate_password(password: str) -> bool:
    """Validate password strength"""
    return len(password) >= 6

def validate_username(username: str) -> bool:
    """Validate username format"""
    return len(username) >= 3 and len(username) <= 20

def get_next_user_id() -> str:
    """Get the next available user ID"""
    try:
        # Get all users and find the highest ID
        users_ref = db.collection('users')
        users = users_ref.get()
        max_id = 0
        
        for user in users:
            user_data = user.to_dict()
            if 'user_id' in user_data:
                try:
                    user_num = int(user_data['user_id'].replace('user', ''))
                    max_id = max(max_id, user_num)
                except ValueError:
                    continue
        
        return f"user{max_id + 1}"
    except Exception as e:
        print(f"Error getting next user ID: {str(e)}")
        return "user1"  # Default to user1 if there's an error

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
        if db is None:
            return {'success': False, 'error': 'Database not initialized'}
            
        # Validate inputs
        if not validate_email(email):
            return {'success': False, 'error': 'Invalid email format'}
        if not validate_password(password):
            return {'success': False, 'error': 'Password does not meet security requirements'}
        if not validate_username(username):
            return {'success': False, 'error': 'Invalid username format'}
        
        # Check if email already exists in Auth
        try:
            auth.get_user_by_email(email)
            return {'success': False, 'error': 'Email already registered'}
        except auth.UserNotFoundError:
            pass
            
        # Check if username already exists in Firestore
        users_ref = db.collection('users')
        existing_user = users_ref.where('username', '==', username).limit(1).get()
        if existing_user:
            return {'success': False, 'error': 'Username already taken'}
        
        # Get next user ID
        user_id = get_next_user_id()
        
        # Create user in Firebase Auth
        user = auth.create_user(
            email=email,
            password=password,
            display_name=username
        )
        
        # Create user profile in Firestore
        user_data = {
            'user_id': user_id,
            'email': email,
            'username': username,
            'created_at': datetime.datetime.now(),
            'last_login': datetime.datetime.now(),
            'listed_items': [],
            'wishlist': [],
            'is_active': True
        }
        
        db.collection('users').document(user_id).set(user_data)
        
        return {
            'success': True,
            'user_id': user_id,
            'email': email,
            'username': username
        }
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
        if db is None:
            return {'success': False, 'error': 'Database not initialized'}
            
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
        if db is None:
            return {'success': False, 'error': 'Database not initialized'}
            
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
        if db is None:
            return {'success': False, 'error': 'Database not initialized'}
            
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
        if db is None:
            return {'success': False, 'error': 'Database not initialized'}
            
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
        if db is None:
            return {'success': False, 'error': 'Database not initialized'}
            
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
        if db is None:
            return {'success': False, 'error': 'Database not initialized'}
            
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
        if db is None:
            return {'success': False, 'error': 'Database not initialized'}
            
        if not validate_password(new_password):
            return {'success': False, 'error': 'Password does not meet security requirements'}
            
        auth.update_user(user_id, password=new_password)
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def login_user(email: str, password: str) -> Dict:
    """
    Login a user with email and password
    
    Args:
        email (str): User's email
        password (str): User's password
        
    Returns:
        dict: Result with success status and user data or error
    """
    try:
        if db is None:
            return {'success': False, 'error': 'Database not initialized'}
            
        # Validate inputs
        if not validate_email(email):
            return {'success': False, 'error': 'Invalid email format'}
        if not validate_password(password):
            return {'success': False, 'error': 'Password does not meet security requirements'}
        
        # Try to sign in with Firebase Auth
        try:
            user = auth.get_user_by_email(email)
        except auth.UserNotFoundError:
            return {'success': False, 'error': 'User not found'}
            
        # Get user profile from Firestore
        user_doc = db.collection('users').document(user.uid).get()
        if not user_doc.exists:
            return {'success': False, 'error': 'User profile not found'}
            
        user_data = user_doc.to_dict()
        
        # Update last login time
        db.collection('users').document(user.uid).update({
            'last_login': datetime.datetime.now()
        })
        
        return {
            'success': True,
            'user_id': user.uid,
            'email': user.email,
            'username': user_data.get('username', '')
        }
        
    except Exception as e:
        error_message = str(e)
        if "INVALID_PASSWORD" in error_message:
            return {'success': False, 'error': 'Invalid password'}
        elif "EMAIL_NOT_FOUND" in error_message:
            return {'success': False, 'error': 'Email not found'}
        else:
            return {'success': False, 'error': f'Login failed: {error_message}'}

def logout():
    """Logout the current user"""
    st.session_state.user_id = None
    st.session_state.user_email = None
    st.session_state.username = None
    st.session_state.logged_in = False
    st.experimental_rerun()

def get_user_profile(user_id):
    """Get user profile data"""
    try:
        if db is None:
            return {'success': False, 'error': 'Database not initialized'}
            
        user_doc = db.collection('users').document(user_id).get()
        if not user_doc.exists:
            return {'success': False, 'error': 'User profile not found'}
            
        return {'success': True, 'data': user_doc.to_dict()}
    except Exception as e:
        return {'success': False, 'error': str(e)}