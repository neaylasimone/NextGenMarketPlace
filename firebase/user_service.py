# user_service.py - User profile management
from firebase_config import db
import firebase_admin
from firebase_admin import firestore

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
              'description': 'What I'm looking for',
              'willing_to_trade': ['Item1', 'Item2']
            }
            
    Returns:
        dict: Result with success status or error
    """
    try:
        user_ref = db.collection('users').document(user_id)
        
        # Get current wishlist
        user_data = user_ref.get().to_dict()
        wishlist = user_data.get('wishlist', [])
        
        # Add new item
        wishlist.append(wishlist_item)
        
        # Update wishlist
        user_ref.update({'wishlist': wishlist})
        
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