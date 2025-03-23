# trade_service.py - Functions for handling trade operations
from datetime import datetime
from typing import Dict, List, Optional
from .firebase_config import db

def propose_trade(user_id: str, item_id: str, trade_data: Dict) -> Dict:
    """
    Propose a trade for an item.
    
    Args:
        user_id (str): ID of the user proposing the trade
        item_id (str): ID of the item being traded for
        trade_data (dict): Trade proposal details including offered items and message
        
    Returns:
        dict: Result with success status and trade ID or error message
    """
    try:
        # Create trade proposal document
        trade_ref = db.collection('trades').document()
        trade_ref.set({
            'proposer_id': user_id,
            'item_id': item_id,
            'offered_items': trade_data.get('offered_items', []),
            'message': trade_data.get('message', ''),
            'status': 'pending',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        })
        
        return {
            'success': True,
            'trade_id': trade_ref.id
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_trade_proposals(user_id: str) -> Dict:
    """
    Get all trade proposals for a user's items.
    
    Args:
        user_id (str): ID of the user
        
    Returns:
        dict: Result with success status and list of trade proposals or error message
    """
    try:
        # Get user's items
        items_ref = db.collection('items').where('user_id', '==', user_id).get()
        item_ids = [item.id for item in items_ref]
        
        # Get trade proposals for these items
        trades_ref = db.collection('trades').where('item_id', 'in', item_ids).get()
        trades = []
        
        for trade in trades_ref:
            trade_data = trade.to_dict()
            trade_data['id'] = trade.id
            trades.append(trade_data)
        
        return {
            'success': True,
            'trades': trades
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def accept_trade(trade_id: str, user_id: str) -> Dict:
    """
    Accept a trade proposal.
    
    Args:
        trade_id (str): ID of the trade proposal
        user_id (str): ID of the user accepting the trade
        
    Returns:
        dict: Result with success status or error message
    """
    try:
        trade_ref = db.collection('trades').document(trade_id)
        trade = trade_ref.get()
        
        if not trade.exists:
            return {
                'success': False,
                'error': 'Trade proposal not found'
            }
        
        trade_data = trade.to_dict()
        
        # Verify user owns the item
        item_ref = db.collection('items').document(trade_data['item_id'])
        item = item_ref.get()
        
        if not item.exists or item.to_dict()['user_id'] != user_id:
            return {
                'success': False,
                'error': 'Unauthorized to accept this trade'
            }
        
        # Update trade status
        trade_ref.update({
            'status': 'accepted',
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

def reject_trade(trade_id: str, user_id: str) -> Dict:
    """
    Reject a trade proposal.
    
    Args:
        trade_id (str): ID of the trade proposal
        user_id (str): ID of the user rejecting the trade
        
    Returns:
        dict: Result with success status or error message
    """
    try:
        trade_ref = db.collection('trades').document(trade_id)
        trade = trade_ref.get()
        
        if not trade.exists:
            return {
                'success': False,
                'error': 'Trade proposal not found'
            }
        
        trade_data = trade.to_dict()
        
        # Verify user owns the item
        item_ref = db.collection('items').document(trade_data['item_id'])
        item = item_ref.get()
        
        if not item.exists or item.to_dict()['user_id'] != user_id:
            return {
                'success': False,
                'error': 'Unauthorized to reject this trade'
            }
        
        # Update trade status
        trade_ref.update({
            'status': 'rejected',
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