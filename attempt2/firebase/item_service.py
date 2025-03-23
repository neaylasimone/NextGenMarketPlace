# item_service.py - Functions for handling item operations
from datetime import datetime
from typing import Dict, List, Optional
from .firebase_config import db, storage

def add_item(user_id: str, item_data: Dict) -> Dict:
    """
    Add a new item to the marketplace.
    
    Args:
        user_id (str): ID of the user adding the item
        item_data (dict): Item details including name, description, category, etc.
        
    Returns:
        dict: Result with success status and item ID or error message
    """
    try:
        # Create item document
        item_ref = db.collection('items').document()
        item_ref.set({
            'user_id': user_id,
            'name': item_data['name'],
            'description': item_data['description'],
            'category': item_data['category'],
            'condition': item_data.get('condition', 'new'),
            'price': item_data.get('price', 0),
            'images': item_data.get('images', []),
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'status': 'active'
        })
        
        return {
            'success': True,
            'item_id': item_ref.id
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_item(item_id: str) -> Dict:
    """
    Get item details by ID.
    
    Args:
        item_id (str): ID of the item
        
    Returns:
        dict: Result with success status and item data or error message
    """
    try:
        item_ref = db.collection('items').document(item_id)
        item = item_ref.get()
        
        if not item.exists:
            return {
                'success': False,
                'error': 'Item not found'
            }
        
        item_data = item.to_dict()
        item_data['id'] = item.id
        return {
            'success': True,
            'item': item_data
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def update_item(item_id: str, user_id: str, item_data: Dict) -> Dict:
    """
    Update an existing item.
    
    Args:
        item_id (str): ID of the item to update
        user_id (str): ID of the user updating the item
        item_data (dict): Updated item details
        
    Returns:
        dict: Result with success status or error message
    """
    try:
        item_ref = db.collection('items').document(item_id)
        item = item_ref.get()
        
        if not item.exists:
            return {
                'success': False,
                'error': 'Item not found'
            }
        
        if item.to_dict()['user_id'] != user_id:
            return {
                'success': False,
                'error': 'Unauthorized to update this item'
            }
        
        # Update only provided fields
        update_data = {
            'updated_at': datetime.now()
        }
        for key, value in item_data.items():
            if value is not None:
                update_data[key] = value
        
        item_ref.update(update_data)
        
        return {
            'success': True
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def delete_item(item_id: str, user_id: str) -> Dict:
    """
    Delete an item from the marketplace.
    
    Args:
        item_id (str): ID of the item to delete
        user_id (str): ID of the user deleting the item
        
    Returns:
        dict: Result with success status or error message
    """
    try:
        item_ref = db.collection('items').document(item_id)
        item = item_ref.get()
        
        if not item.exists:
            return {
                'success': False,
                'error': 'Item not found'
            }
        
        if item.to_dict()['user_id'] != user_id:
            return {
                'success': False,
                'error': 'Unauthorized to delete this item'
            }
        
        item_ref.delete()
        
        return {
            'success': True
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def search_items(query: str) -> Dict:
    """
    Search items by name, description, or category.
    
    Args:
        query (str): Search query string
        
    Returns:
        dict: Result with success status and list of matching items or error message
    """
    try:
        items_ref = db.collection('items')
        items = []
        
        # Get all active items
        query_ref = items_ref.where('status', '==', 'active').get()
        
        for item in query_ref:
            item_data = item.to_dict()
            item_data['id'] = item.id
            
            # Simple text search
            search_text = f"{item_data['name']} {item_data['description']} {item_data['category']}".lower()
            if query.lower() in search_text:
                items.append(item_data)
        
        return {
            'success': True,
            'items': items
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_user_items(user_id: str) -> Dict:
    """
    Get all items listed by a user.
    
    Args:
        user_id (str): ID of the user
        
    Returns:
        dict: Result with success status and list of items or error message
    """
    try:
        items_ref = db.collection('items').where('user_id', '==', user_id).get()
        items = []
        
        for item in items_ref:
            item_data = item.to_dict()
            item_data['id'] = item.id
            items.append(item_data)
        
        return {
            'success': True,
            'items': items
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def add_to_wishlist(user_id: str, item_id: str) -> Dict:
    """
    Add an item to a user's wishlist.
    
    Args:
        user_id (str): ID of the user
        item_id (str): ID of the item to add
        
    Returns:
        dict: Result with success status or error message
    """
    try:
        user_ref = db.collection('users').document(user_id)
        user = user_ref.get()
        
        if not user.exists:
            return {
                'success': False,
                'error': 'User not found'
            }
        
        user_data = user.to_dict()
        wishlist = user_data.get('wishlist', [])
        
        if item_id not in wishlist:
            wishlist.append(item_id)
            user_ref.update({
                'wishlist': wishlist,
                'updated_at': datetime.now()
            })
        
        return {
            'success': True
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def remove_from_wishlist(user_id: str, item_id: str) -> Dict:
    """
    Remove an item from a user's wishlist.
    
    Args:
        user_id (str): ID of the user
        item_id (str): ID of the item to remove
        
    Returns:
        dict: Result with success status or error message
    """
    try:
        user_ref = db.collection('users').document(user_id)
        user = user_ref.get()
        
        if not user.exists:
            return {
                'success': False,
                'error': 'User not found'
            }
        
        user_data = user.to_dict()
        wishlist = user_data.get('wishlist', [])
        
        if item_id in wishlist:
            wishlist.remove(item_id)
            user_ref.update({
                'wishlist': wishlist,
                'updated_at': datetime.now()
            })
        
        return {
            'success': True
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_wishlist_items(user_id: str) -> Dict:
    """
    Get all items in a user's wishlist.
    
    Args:
        user_id (str): ID of the user
        
    Returns:
        dict: Result with success status and list of items or error message
    """
    try:
        user_ref = db.collection('users').document(user_id)
        user = user_ref.get()
        
        if not user.exists:
            return {
                'success': False,
                'error': 'User not found'
            }
        
        user_data = user.to_dict()
        wishlist = user_data.get('wishlist', [])
        
        items = []
        for item_id in wishlist:
            item_result = get_item(item_id)
            if item_result['success']:
                items.append(item_result['item'])
        
        return {
            'success': True,
            'items': items
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def find_potential_matches(user_id: str) -> Dict:
    """
    Find potential matches based on user's wishlist and other users' items.
    
    Args:
        user_id (str): ID of the user
        
    Returns:
        dict: Result with success status and list of matching items or error message
    """
    try:
        # Get user's wishlist
        wishlist_result = get_wishlist_items(user_id)
        if not wishlist_result['success']:
            return wishlist_result
        
        wishlist_items = wishlist_result['items']
        if not wishlist_items:
            return {
                'success': True,
                'items': []
            }
        
        # Get all active items
        items_ref = db.collection('items').where('status', '==', 'active').get()
        matches = []
        
        for item in items_ref:
            item_data = item.to_dict()
            item_data['id'] = item.id
            
            # Skip user's own items
            if item_data['user_id'] == user_id:
                continue
            
            # Check if item matches any wishlist item's category
            for wishlist_item in wishlist_items:
                if item_data['category'] == wishlist_item['category']:
                    matches.append(item_data)
                    break
        
        return {
            'success': True,
            'items': matches
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }