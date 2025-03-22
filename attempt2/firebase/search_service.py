# search_service.py - Search and item discovery functionality
from firebase_config import db
from user_service import get_user_profile

def search_items(search_query):
    """
    Search all active items
    
    Args:
        search_query (str): Search query
        
    Returns:
        dict: Result with success status and items or error
    """
    try:
        # Query for active items
        items_ref = db.collection('items').where('active', '==', True)
        docs = items_ref.stream()
        
        # Filter results client-side based on the search query
        # Note: For production, consider using Algolia or another full-text search solution
        items = []
        for doc in docs:
            data = doc.to_dict()
            if (search_query.lower() in data.get('name', '').lower() or 
                search_query.lower() in data.get('description', '').lower()):
                items.append({'id': doc.id, **data})
        
        return {'success': True, 'items': items}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def find_potential_matches(user_id):
    """
    Find potential matches between user's wishlist and listed items
    
    Args:
        user_id (str): User's ID
        
    Returns:
        dict: Result with success status and matches or error
    """
    try:
        # Get current user's wishlist
        user_profile = get_user_profile(user_id)
        if not user_profile['success']:
            return {'success': False, 'error': user_profile['error']}
        
        user_wishlist = user_profile['data'].get('wishlist', [])
        potential_matches = []
        
        # For each item in wishlist, search for matching listings
        for wish_item in user_wishlist:
            # Get the item name the user is looking for
            item_name = wish_item.get('item_name', '').lower()
            
            # Query for active items
            items_ref = db.collection('items').where('active', '==', True)
            docs = items_ref.stream()
            
            for doc in docs:
                item = doc.to_dict()
                # Skip user's own items
                if item.get('user_id') == user_id:
                    continue
                
                # Check if this item matches what the user is looking for
                if (item_name in item.get('name', '').lower() or
                    item_name in item.get('description', '').lower()):
                    potential_matches.append({
                        'wishlist_item': wish_item,
                        'matched_item': {'id': doc.id, **item}
                    })
        
        return {'success': True, 'matches': potential_matches}
    except Exception as e:
        return {'success': False, 'error': str(e)}