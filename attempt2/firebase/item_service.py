# item_service.py - Item listing and management
from firebase_config import db
import datetime
from firebase_admin import firestore

def list_new_item(user_id, item_data):
    """
    Add a new item for trading/selling
    
    Args:
        user_id (str): User's ID
        item_data (dict): Item data
            {
              'name': 'Item Name',
              'description': 'Item description',
              'condition': 'New/Used/etc',
              'images': ['url1', 'url2'],
              'for_sale': True/False,
              'price': 100,  # if for sale
              'for_trade': True/False,
              'looking_for': ['Item1', 'Item2']  # if for trade
            }
            
    Returns:
        dict: Result with success status and item ID or error
    """
    try:
        # Add user_id and other metadata to item
        complete_item_data = {
            **item_data,
            'user_id': user_id,
            'created_at': datetime.datetime.now(),
            'active': True
        }
        
        # Create a new item document in the items collection
        item_ref = db.collection('items').document()
        item_ref.set(complete_item_data)
        
        # Update the user's profile with the item reference
        user_ref = db.collection('users').document(user_id)
        user_ref.update({
            'listed_items': firestore.ArrayUnion([item_ref.id])
        })
        
        return {'success': True, 'item_id': item_ref.id}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_user_listed_items(user_id):
    """
    Get all items listed by a user
    
    Args:
        user_id (str): User's ID
        
    Returns:
        dict: Result with success status and items or error
    """
    try:
        items_ref = db.collection('items').where('user_id', '==', user_id)
        docs = items_ref.stream()
        
        items = []
        for doc in docs:
            items.append({'id': doc.id, **doc.to_dict()})
        
        return {'success': True, 'items': items}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def update_listed_item(item_id, item_data):
    """
    Update a listed item
    
    Args:
        item_id (str): Item's ID
        item_data (dict): New item data
        
    Returns:
        dict: Result with success status or error
    """
    try:
        item_ref = db.collection('items').document(item_id)
        
        # Add updated_at timestamp
        update_data = {
            **item_data,
            'updated_at': datetime.datetime.now()
        }
        
        item_ref.update(update_data)
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def delete_listed_item(user_id, item_id):
    """
    Delete a listed item
    
    Args:
        user_id (str): User's ID
        item_id (str): Item's ID
        
    Returns:
        dict: Result with success status or error
    """
    try:
        # Remove from items collection
        db.collection('items').document(item_id).delete()
        
        # Remove from user's listed items
        user_ref = db.collection('users').document(user_id)
        user_ref.update({
            'listed_items': firestore.ArrayRemove([item_id])
        })
        
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}