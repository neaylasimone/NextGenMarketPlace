# search_service.py - Search and item discovery functionality
from .firebase_app import db
from .user_service import get_user_profile
from .gemini import generate_content
import json
import datetime
from typing import Dict, List, Optional

def search_items(search_query):
    """
    Search all active items using semantic search with Gemini
    
    Args:
        search_query (str): Search query
        
    Returns:
        dict: Result with success status and items or error
    """
    try:
        # Query for active items
        items_ref = db.collection('items').where('active', '==', True)
        docs = items_ref.stream()
        
        # Get all items
        items = []
        for doc in docs:
            items.append({'id': doc.id, **doc.to_dict()})
        
        # Use Gemini to analyze search query and items
        prompt = f"""
        Analyze this search query and list of items to find the best matches.
        Consider semantic meaning, categories, and item details.
        
        Search Query: {search_query}
        
        Items:
        {json.dumps(items, indent=2)}
        
        For each item, provide a relevance score (0-1) and explanation.
        Return as JSON with format:
        {{
            "matches": [
                {{
                    "item_id": "id",
                    "relevance_score": 0.95,
                    "explanation": "Why this is a good match"
                }}
            ]
        }}
        """
        
        # Get Gemini's analysis
        response = generate_content(prompt)
        try:
            analysis = json.loads(response)
        except:
            # Fallback to basic matching if Gemini response isn't valid JSON
            analysis = {"matches": []}
            for item in items:
                if (search_query.lower() in item.get('name', '').lower() or 
                    search_query.lower() in item.get('description', '').lower()):
                    analysis["matches"].append({
                        "item_id": item['id'],
                        "relevance_score": 0.5,
                        "explanation": "Basic text match"
                    })
        
        # Sort matches by relevance score
        matches = sorted(analysis["matches"], key=lambda x: x["relevance_score"], reverse=True)
        
        # Get full item details for matches
        matched_items = []
        for match in matches:
            item = next((item for item in items if item['id'] == match['item_id']), None)
            if item:
                item['relevance_score'] = match['relevance_score']
                item['match_explanation'] = match['explanation']
                matched_items.append(item)
        
        return {'success': True, 'items': matched_items}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def find_potential_matches(user_id):
    """
    Find potential matches between user's wishlist and listed items using Gemini
    
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
        
        # Get all active items
        items_ref = db.collection('items').where('active', '==', True)
        docs = items_ref.stream()
        all_items = []
        for doc in docs:
            all_items.append({'id': doc.id, **doc.to_dict()})
        
        # Use Gemini to analyze matches
        for wish_item in user_wishlist:
            prompt = f"""
            Analyze this wishlist item and list of available items to find potential matches.
            Consider all item details, categories, and trade preferences.
            
            Wishlist Item:
            {json.dumps(wish_item, indent=2)}
            
            Available Items:
            {json.dumps(all_items, indent=2)}
            
            For each potential match, provide a match score (0-1) and explanation.
            Return as JSON with format:
            {{
                "matches": [
                    {{
                        "item_id": "id",
                        "match_score": 0.95,
                        "explanation": "Why this is a good match",
                        "trade_details": "What could be traded"
                    }}
                ]
            }}
            """
            
            # Get Gemini's analysis
            response = generate_content(prompt)
            try:
                analysis = json.loads(response)
            except:
                # Fallback to basic matching if Gemini response isn't valid JSON
                analysis = {"matches": []}
                for item in all_items:
                    if item.get('user_id') != user_id:  # Skip user's own items
                        if (wish_item['item_name'].lower() in item.get('name', '').lower() or
                            wish_item['item_name'].lower() in item.get('description', '').lower()):
                            analysis["matches"].append({
                                "item_id": item['id'],
                                "match_score": 0.5,
                                "explanation": "Basic text match",
                                "trade_details": "Potential trade based on text match"
                            })
            
            # Sort matches by score
            matches = sorted(analysis["matches"], key=lambda x: x["match_score"], reverse=True)
            
            # Get full item details for matches
            for match in matches:
                item = next((item for item in all_items if item['id'] == match['item_id']), None)
                if item:
                    potential_matches.append({
                        'wishlist_item': wish_item,
                        'matched_item': {
                            **item,
                            'match_score': match['match_score'],
                            'match_explanation': match['explanation'],
                            'trade_details': match['trade_details']
                        }
                    })
        
        return {'success': True, 'matches': potential_matches}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def find_trade_matches(user_id):
    """
    Find potential trade matches using Gemini for better matching
    
    Args:
        user_id (str): Current user's ID
        
    Returns:
        dict: Result with success status and matches or error
    """
    try:
        # Get current user's profile
        user_profile = get_user_profile(user_id)
        if not user_profile['success']:
            return {'success': False, 'error': user_profile['error']}
        
        current_user = user_profile['data']
        
        # Skip if user has no wishlist
        if not current_user.get('wishlist') or len(current_user.get('wishlist', [])) == 0:
            return {'success': True, 'matches': []}
        
        # Get current user's listed items
        user_items_result = get_user_listed_items(user_id)
        if not user_items_result.get('success'):
            return {'success': False, 'error': user_items_result.get('error')}
            
        user_items = user_items_result.get('items', [])
        
        # Skip if user has no listed items
        if not user_items:
            return {'success': True, 'matches': []}
        
        # Get all other users
        users_ref = db.collection('users')
        users_docs = users_ref.stream()
        
        trade_matches = []
        
        # Check for potential matches with other users
        for doc in users_docs:
            other_user = {
                'id': doc.id,
                **doc.to_dict()
            }
            
            # Skip self-comparison
            if other_user['id'] == user_id:
                continue
            
            # Skip users with no wishlist
            if not other_user.get('wishlist') or len(other_user.get('wishlist', [])) == 0:
                continue
            
            # Get other user's listed items
            other_user_items_result = get_user_listed_items(other_user['id'])
            if not other_user_items_result.get('success'):
                continue
                
            other_user_items = other_user_items_result.get('items', [])
            
            # Skip users with no listed items
            if not other_user_items:
                continue
            
            # Use Gemini to analyze potential trades
            prompt = f"""
            Analyze these users' items and wishlists to find potential trade matches.
            Consider all item details, categories, and trade preferences.
            
            Current User:
            - Wishlist: {json.dumps(current_user.get('wishlist', []), indent=2)}
            - Listed Items: {json.dumps(user_items, indent=2)}
            
            Other User:
            - Wishlist: {json.dumps(other_user.get('wishlist', []), indent=2)}
            - Listed Items: {json.dumps(other_user_items, indent=2)}
            
            Find potential trades where both users have items the other wants.
            Return as JSON with format:
            {{
                "matches": [
                    {{
                        "current_user_items": ["item_id1", "item_id2"],
                        "other_user_items": ["item_id1", "item_id2"],
                        "match_score": 0.95,
                        "explanation": "Why this is a good trade match"
                    }}
                ]
            }}
            """
            
            # Get Gemini's analysis
            response = generate_content(prompt)
            try:
                analysis = json.loads(response)
            except:
                # Fallback to basic matching if Gemini response isn't valid JSON
                analysis = {"matches": []}
                current_user_has_what_other_wants = find_item_matches(user_items, other_user.get('wishlist', []))
                other_has_what_current_wants = find_item_matches(other_user_items, current_user.get('wishlist', []))
                
                if current_user_has_what_other_wants and other_has_what_current_wants:
                    analysis["matches"].append({
                        "current_user_items": [item['item_id'] for item in current_user_has_what_other_wants],
                        "other_user_items": [item['item_id'] for item in other_has_what_current_wants],
                        "match_score": 0.5,
                        "explanation": "Basic trade match based on text matching"
                    })
            
            # Process matches
            for match in analysis["matches"]:
                current_items = [item for item in user_items if item['id'] in match['current_user_items']]
                other_items = [item for item in other_user_items if item['id'] in match['other_user_items']]
                
                if current_items and other_items:
                    trade_matches.append({
                        'current_user': {
                            'id': user_id,
                            'username': current_user.get('username', ''),
                            'offered_items': current_items
                        },
                        'other_user': {
                            'id': other_user['id'],
                            'username': other_user.get('username', ''),
                            'offered_items': other_items
                        },
                        'match_score': match['match_score'],
                        'explanation': match['explanation']
                    })
        
        # Sort matches by score
        trade_matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        return {'success': True, 'matches': trade_matches}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def find_item_matches(listed_items, wishlist):
    """
    Helper function to find matches between listed items and another user's wishlist
    
    Args:
        listed_items (list): Array of items a user has listed
        wishlist (list): Array of items another user wants
        
    Returns:
        list: Matching items
    """
    matches = []
    
    # For each listed item, check if it matches any wishlist item
    for item in listed_items:
        # Skip inactive items
        if not item.get('active', False):
            continue
        
        # Only consider items marked for trade
        if not item.get('for_trade', False):
            continue
        
        for wish_item in wishlist:
            # Get the item name the user is looking for
            wish_item_name = wish_item.get('item_name', '').lower()
            
            # Check if the listed item matches what the user wants
            name_match = wish_item_name in item.get('name', '').lower()
            desc_match = wish_item_name in item.get('description', '').lower()
            
            # Check if the wishlist item contains something the lister wants
            trade_match = False
            if item.get('looking_for') and wish_item.get('willing_to_trade'):
                for wanted in item.get('looking_for', []):
                    for offered in wish_item.get('willing_to_trade', []):
                        if wanted.lower() in offered.lower():
                            trade_match = True
                            break
                    if trade_match:
                        break
            
            if name_match or desc_match or trade_match:
                matches.append({
                    'item_id': item.get('id'),
                    'name': item.get('name', ''),
                    'description': item.get('description', ''),
                    'match_reason': {
                        'name_match': name_match,
                        'desc_match': desc_match,
                        'trade_match': trade_match
                    }
                })
                # Once we've found a match for this item, no need to check other wishlist items
                break
    
    return matches

def rate_trade_value(item1_id: str, item2_id: str) -> Dict:
    """
    Rate the fairness of a trade between two items
    
    Args:
        item1_id (str): ID of the first item
        item2_id (str): ID of the second item
        
    Returns:
        Dict: Trade rating information
    """
    try:
        if db is None:
            return {'success': False, 'error': 'Database not initialized'}
            
        # Get both items
        item1_doc = db.collection('items').document(item1_id).get()
        item2_doc = db.collection('items').document(item2_id).get()
        
        if not item1_doc.exists or not item2_doc.exists:
            return {'success': False, 'error': 'One or both items not found'}
            
        item1 = item1_doc.to_dict()
        item2 = item2_doc.to_dict()
        
        # Get prices
        price1 = item1.get('price', 0)
        price2 = item2.get('price', 0)
        
        # Calculate price difference percentage
        if price1 == 0 or price2 == 0:
            return {'success': False, 'error': 'One or both items have no price'}
            
        price_diff = abs(price1 - price2)
        price_diff_percent = (price_diff / max(price1, price2)) * 100
        
        # Determine trade rating
        if price_diff_percent <= 10:
            rating = "Fair"
        elif price_diff_percent <= 25:
            rating = "Slightly Unfair"
        else:
            rating = "Unfair"
            
        return {
            'success': True,
            'rating': rating,
            'price_difference': price_diff,
            'price_difference_percent': price_diff_percent,
            'item1_price': price1,
            'item2_price': price2
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}