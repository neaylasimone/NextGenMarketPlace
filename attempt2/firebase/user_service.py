# user_service.py - User profile and wishlist management
from .firebase_config import db
import firebase_admin
from firebase_admin import firestore
import datetime
from typing import Dict, List, Optional

def get_user_profile(user_id):
    """
    Get user profile data
    
    Args:
        user_id (str): User's ID
        
    Returns:
        dict: Result with success status and user data or error
    """
    try:
        doc_ref = db.collection('users').document(user_id)
        doc = doc_ref.get()
        
        if doc.exists:
            return {'success': True, 'data': doc.to_dict()}
        else:
            return {'success': False, 'error': 'User profile not found'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def update_user_profile(user_id, profile_data):
    """
    Update user profile
    
    Args:
        user_id (str): User's ID
        profile_data (dict): New profile data
        
    Returns:
        dict: Result with success status or error
    """
    try:
        user_ref = db.collection('users').document(user_id)
        user_ref.update(profile_data)
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# ---- WISHLIST MANAGEMENT ----

def add_to_wishlist(user_id, wishlist_item):
    """
    Add item to user's wishlist
    
    Args:
        user_id (str): User's ID
        wishlist_item (dict): Item to add to wishlist
            {
              'item_name': 'Item Name',
              'category': 'Electronics/Clothing/etc',
              'description': 'What I'm looking for',
              'preferred_condition': 'New/Used/etc',
              'brand': 'Brand name if applicable',
              'model': 'Model number if applicable',
              'year': 'Year of manufacture if applicable',
              'size': 'Size if applicable',
              'color': 'Color if applicable',
              'tags': ['tag1', 'tag2'],
              'willing_to_trade': [
                {
                  'name': 'Item Name',
                  'category': 'Electronics/Clothing/etc',
                  'condition': 'New/Used/etc',
                  'description': 'Description of what you're offering',
                  'brand': 'Brand name if applicable',
                  'model': 'Model number if applicable',
                  'year': 'Year of manufacture if applicable',
                  'size': 'Size if applicable',
                  'color': 'Color if applicable',
                  'tags': ['tag1', 'tag2']
                }
              ],
              'shipping_preferences': {
                'willing_to_pay_shipping': True/False,
                'max_shipping_cost': 20.00
              }
            }
            
    Returns:
        dict: Result with success status or error
    """
    try:
        user_ref = db.collection('users').document(user_id)
        
        # Get current wishlist
        user_data = user_ref.get().to_dict()
        wishlist = user_data.get('wishlist', [])
        
        # Add new item with timestamp
        wishlist_item['added_at'] = datetime.datetime.now()
        wishlist.append(wishlist_item)
        
        # Update wishlist
        user_ref.update({
            'wishlist': wishlist,
            'last_updated': datetime.datetime.now()
        })
        
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def remove_from_wishlist(user_id, item_index):
    """
    Remove item from wishlist by index
    
    Args:
        user_id (str): User's ID
        item_index (int): Index of item to remove
        
    Returns:
        dict: Result with success status or error
    """
    try:
        user_ref = db.collection('users').document(user_id)
        
        # Get current wishlist
        user_data = user_ref.get().to_dict()
        wishlist = user_data.get('wishlist', [])
        
        # Check if index is valid
        if 0 <= item_index < len(wishlist):
            # Remove item
            wishlist.pop(item_index)
            
            # Update wishlist
            user_ref.update({'wishlist': wishlist})
            
            return {'success': True}
        else:
            return {'success': False, 'error': 'Invalid item index'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def update_wishlist_item(user_id, item_index, new_item):
    """
    Update specific wishlist item
    
    Args:
        user_id (str): User's ID
        item_index (int): Index of item to update
        new_item (dict): New item data
        
    Returns:
        dict: Result with success status or error
    """
    try:
        user_ref = db.collection('users').document(user_id)
        
        # Get current wishlist
        user_data = user_ref.get().to_dict()
        wishlist = user_data.get('wishlist', [])
        
        # Check if index is valid
        if 0 <= item_index < len(wishlist):
            # Update item
            wishlist[item_index] = new_item
            
            # Update wishlist
            user_ref.update({'wishlist': wishlist})
            
            return {'success': True}
        else:
            return {'success': False, 'error': 'Invalid item index'}
    except Exception as e:
        return {'success': False, 'error': str(e)}