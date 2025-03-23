# TO RUN:
# pip3 install streamlit pandas scikit-learn numpy
# streamlit run app.py

import streamlit as st

st.set_page_config(
    page_title="NextGenMarket - Buy & Barter Marketplace",
    page_icon="🔄",
    layout="wide"
)

import firebase_admin
from firebase_admin import credentials, firestore, auth
from datetime import datetime
import json
import os
from dotenv import load_dotenv
from firebase.firebase_config import initialize_firebase
from firebase.item_service import (
    add_item, get_item, get_all_items, update_item, delete_item,
    search_items, get_user_items
)
from firebase.gemini import generate_content, search_items_semantic

# Configure Streamlit page - MUST BE FIRST STREAMLIT COMMAND
# Load environment variables
load_dotenv()

# Initialize Firebase Admin SDK
initialize_firebase()
db = firestore.client()

# Define categories
CATEGORIES = {
    "Electronics": "📱",
    "Clothing": "👕",
    "Home Goods": "🏠",
    "Tools": "🔧",
    "Toys & Games": "🎮",
    "Books": "📚",
    "Handmade": "🎨",
    "Services": "💼",
    "Other": "📦"
}

import pandas as pd
import uuid
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Import mock data
from mock_data import (
    MOCK_USERS, MOCK_ITEMS, MOCK_TRADE_PROPOSALS,
    get_mock_search_results, get_mock_user_profile,
    get_mock_item, get_mock_trade_proposals,
    get_mock_user_items, rate_mock_trade_value
)

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "Welcome"
if 'editing_listing' not in st.session_state:
    st.session_state.editing_listing = None
if 'trade_item' not in st.session_state:
    st.session_state.trade_item = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'cart_items' not in st.session_state:
    st.session_state.cart_items = []
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""

# Initialize the app with custom styling
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #1E88E5;
        --secondary-color: #FFC107;
        --background-color: #F8F9FA;
        --text-color: #212529;
    }

    /* Header styling */
    .stTitle {
        color: var(--primary-color) !important;
        font-weight: 700 !important;
    }

    /* Button styling */
    .stButton > button {
        background-color: var(--primary-color);
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #1565C0;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    /* Card styling */
    div[data-testid="stHorizontalBlock"] > div {
        background-color: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: transform 0.3s ease;
    }
    div[data-testid="stHorizontalBlock"] > div:hover {
        transform: translateY(-5px);
    }

    /* Sidebar styling */
    .css-1d391kg {
        background-color: var(--background-color);
    }

    /* Input fields styling */
    .stTextInput > div > div > input {
        border-radius: 6px;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 4px 4px 0 0;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--primary-color) !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Mock authentication functions
def login_user(email, password):
    """Login user using Firebase Authentication"""
    try:
        # Get user by email
        user = auth.get_user_by_email(email)
        
        # Get user data from Firestore
        user_doc = db.collection('users').document(user.uid).get()
        if not user_doc.exists:
            return {'success': False, 'error': 'User profile not found'}
        
        user_data = user_doc.to_dict()
        
        return {
            'success': True,
            'user_id': user_data['id'],
            'email': user_data['email'],
            'username': user_data['username']
        }
    except Exception as e:
        print(f"Error logging in user: {str(e)}")
        return {'success': False, 'error': str(e)}

def register_user(email, password, username):
    """Register a new user in Firebase"""
    try:
        # Create user in Firebase Auth
        user = auth.create_user(
            email=email,
            password=password,
            display_name=username
        )
        
        # Create user document in Firestore
        user_data = {
            'id': user.uid,
            'email': email,
            'username': username,
            'created_at': datetime.now(),
            'profile': {
                'bio': '',
                'location': '',
                'rating': 5.0,
                'completed_trades': 0
            }
        }
        
        # Add to users collection
        db.collection('users').document(user.uid).set(user_data)
        
        return {
            'success': True,
            'user_id': user.uid,
            'email': email,
            'username': username
        }
    except Exception as e:
        print(f"Error registering user: {str(e)}")
        return {'success': False, 'error': str(e)}

def get_user_profile(user_id):
    """Get user profile from Firestore"""
    try:
        # Get user document from Firestore
        user_doc = db.collection('users').document(user_id).get()
        if not user_doc.exists:
            return None
        
        user_data = user_doc.to_dict()
        return user_data
    except Exception as e:
        print(f"Error getting user profile: {str(e)}")
        return None

# Mock item service functions
def add_item(user_id, item_data):
    """Mock add item function"""
    new_item = {
        'id': f"item{len(MOCK_ITEMS) + 1}",
        'user_id': user_id,
        **item_data
    }
    MOCK_ITEMS.append(new_item)
    return {'success': True, 'item_id': new_item['id']}

def get_item(item_id):
    """Mock get item function"""
    return get_mock_item(item_id)

def get_all_items():
    """Get all active items from Firestore"""
    try:
        # Get all items from Firestore
        items_ref = db.collection('items').where('active', '==', True).get()
        items = [item.to_dict() for item in items_ref]
        return items
    except Exception as e:
        print(f"Error getting all items: {str(e)}")
        return []
    
def update_item(item_id, user_id, item_data):
    """Mock update item function"""
    for item in MOCK_ITEMS:
        if item['id'] == item_id and item['user_id'] == user_id:
            item.update(item_data)
            return {'success': True}
    return {'success': False, 'error': 'Item not found or unauthorized'}

def delete_item(item_id, user_id):
    """Mock delete item function"""
    for item in MOCK_ITEMS:
        if item['id'] == item_id and item['user_id'] == user_id:
            MOCK_ITEMS.remove(item)
            return {'success': True}
    return {'success': False, 'error': 'Item not found or unauthorized'}

def search_items(query, category=None):
    """Mock search items function"""
    results = get_mock_search_results(query, category)
    return {'success': True, 'items': results}

def get_user_items(user_id):
    """Mock get user items function"""
    items = get_mock_user_items(user_id)
    return {'success': True, 'items': items}

# Mock trade service functions
def propose_trade(from_user_id, to_user_id, offered_item_id, wanted_item_id, message):
    """Mock propose trade function"""
    new_proposal = {
        'id': f"trade{len(MOCK_TRADE_PROPOSALS) + 1}",
        'from_user_id': from_user_id,
        'to_user_id': to_user_id,
        'offered_item_id': offered_item_id,
        'wanted_item_id': wanted_item_id,
        'status': 'pending',
        'created_at': datetime.now(),
        'message': message
    }
    MOCK_TRADE_PROPOSALS.append(new_proposal)
    return {'success': True, 'proposal_id': new_proposal['id']}

def get_trade_proposals(user_id, direction="received"):
    """Mock get trade proposals function"""
    proposals = get_mock_trade_proposals(user_id, direction)
    return {'success': True, 'proposals': proposals}

def accept_trade(proposal_id, user_id):
    """Mock accept trade function"""
    for proposal in MOCK_TRADE_PROPOSALS:
        if proposal['id'] == proposal_id and proposal['to_user_id'] == user_id:
            proposal['status'] = 'accepted'
            return {'success': True}
    return {'success': False, 'error': 'Proposal not found or unauthorized'}

def reject_trade(proposal_id, user_id):
    """Mock reject trade function"""
    for proposal in MOCK_TRADE_PROPOSALS:
        if proposal['id'] == proposal_id and proposal['to_user_id'] == user_id:
            proposal['status'] = 'rejected'
            return {'success': True}
    return {'success': False, 'error': 'Proposal not found or unauthorized'}

# Mock search service functions
def semantic_search(query):
    """Mock semantic search function"""
    return get_mock_search_results(query)

def find_potential_matches(item_id, user_id):
    """Mock find potential matches function"""
    item = get_mock_item(item_id)
    if not item:
        return []
    
    matches = []
    for other_item in MOCK_ITEMS:
        if other_item['user_id'] != user_id and other_item['id'] != item_id:
            # Simple matching based on category and price range
            if other_item['category'] == item['category']:
                price_diff = abs(other_item['price'] - item['price'])
                if price_diff <= item['price'] * 0.2:  # Within 20% price difference
                    matches.append(other_item)
    
    return matches

def find_trade_matches(item_id, user_id):
    """Mock find trade matches function"""
    return find_potential_matches(item_id, user_id)

def rate_trade_value(item1, item2):
    """Mock rate trade value function"""
    return rate_mock_trade_value(item1, item2)

# Utility functions
def create_item_card(item):
    """Create a card for displaying an item"""
    with st.container():
        # Create columns for the card layout
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Display item image
            try:
                if item.get('image_url'):
                    st.image(item['image_url'], width=150)
                elif item.get('images') and len(item['images']) > 0:
                    # If images is a list of file names, show a placeholder
                    st.image("https://via.placeholder.com/150", width=150)
                else:
                    st.image("https://via.placeholder.com/150", width=150)
            except Exception as e:
                st.error(f"Error loading image: {str(e)}")
                st.image("https://via.placeholder.com/150", width=150)
        
        with col2:
            # Display item details
            st.subheader(item.get('name', 'Unnamed Item'))
            st.write(f"**Category:** {item.get('category', 'Uncategorized')}")
            st.write(f"**Description:** {item.get('description', 'No description available')}")
            st.write(f"**Condition:** {item.get('condition', 'Not specified')}")
            st.write(f"**Location:** {item.get('location', 'Not specified')}")
            
            # Add trade button
            if st.button("Propose Trade", key=f"trade_{item.get('id')}"):
                if 'user_id' not in st.session_state or not st.session_state.user_id:
                    st.warning("Please log in to propose a trade")
                else:
                    st.session_state.selected_item = item
                    st.session_state.active_tab = "Propose Trade"
                    st.rerun()

# UI Components
def top_nav():
    # Create a container for the top navigation
    with st.container():
        # Add a light gray background
        st.markdown(
            """
            <style>
            .top-nav {
                background-color: #f8f9fa;
                padding: 1rem;
                border-bottom: 1px solid #dee2e6;
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                z-index: 1000;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        
        # Create columns for search, cart, and profile - adjusted ratios
        col1, col2, col3 = st.columns([2.5, 1, 1.5])
        
        with col1:
            # Global search bar
            search_query = st.text_input("🔍", placeholder="Search across all items...", 
                                       value=st.session_state.search_query,
                                       label_visibility="collapsed")
            if search_query != st.session_state.search_query:
                st.session_state.search_query = search_query
                st.session_state.active_tab = "Browse"
                st.rerun()
        
        with col2:
            # Cart button with item count
            cart_count = len(st.session_state.cart_items)
            if st.button(f"🛒 Cart ({cart_count})", use_container_width=True):
                st.session_state.active_tab = "Cart"
                st.rerun()
        
        with col3:
            # Profile section with adjusted column ratios
            if st.session_state.logged_in:
                col3_1, col3_2 = st.columns([1.2, 0.8])  # Adjusted ratio for profile and logout
                with col3_1:
                    if st.button("👤 " + st.session_state.username[:10] + "...", use_container_width=True):
                        st.session_state.active_tab = "Profile"
                        st.rerun()
                with col3_2:
                    if st.button("Logout", use_container_width=True):
                        st.session_state.logged_in = False
                        st.session_state.username = ""
                        st.session_state.active_tab = "Browse"
                        st.rerun()
            else:
                if st.button("👤 Login / Register", use_container_width=True):
                    st.session_state.active_tab = "Login"
                    st.rerun()

def header():
    col1, col2, col3 = st.columns([3, 3, 2])
    
    with col1:
        st.markdown('<div style="display: flex; align-items: center; gap: 1rem;">', unsafe_allow_html=True)
        st.image("assets/nextgen_icon.png", width=50)
        st.markdown("""
            <h1 style='color: #1E88E5; margin: 0;'>Next Gen Marketplace</h1>
            <p style='color: #666; font-size: 1.1em; margin-top: 0.5rem;'>Buy • Sell • Barter • Build Community</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if st.session_state.logged_in:
            st.markdown(f"<p style='color: #1E88E5; font-weight: 500;'>Welcome, {st.session_state.username}! 👋</p>", unsafe_allow_html=True)

def sidebar():
    with st.sidebar:
        st.title("Navigation")
        
        if st.button("🔍 Browse Marketplace", use_container_width=True):
            st.session_state.active_tab = "Browse"
            st.rerun()
            
        if st.button("➕ Create Listing", use_container_width=True):
            if st.session_state.logged_in:
                st.session_state.active_tab = "Create Listing"
            else:
                st.session_state.active_tab = "Login"
                st.session_state.redirect_after_login = "Create Listing"
            st.rerun()
            
        if st.button("🧰 My Listings", use_container_width=True):
            if st.session_state.logged_in:
                st.session_state.active_tab = "My Listings"
            else:
                st.session_state.active_tab = "Login"
                st.session_state.redirect_after_login = "My Listings"
            st.rerun()
            
        if st.button("📋 Trade Proposals", use_container_width=True):
            if st.session_state.logged_in:
                st.session_state.active_tab = "Trade Proposals"
            else:
                st.session_state.active_tab = "Login"
                st.session_state.redirect_after_login = "Trade Proposals"
            st.rerun()
            
        st.divider()
        st.write("### Filter by Category")
        categories = ["All", "Electronics", "Clothing", "Home Goods", "Tools", 
                     "Toys & Games", "Books", "Handmade", "Services", "Other"]
        
        for category in categories:
            if st.button(category, key=f"cat_{category}", use_container_width=True):
                st.session_state.active_tab = "Browse"
                st.session_state.selected_category = category
                st.rerun()

def login_page():
    """Display login page"""
    st.title("Welcome to NextGen Marketplace")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login"):
            if email and password:
                result = login_user(email, password)
                if result['success']:
                    # Initialize session state
                    st.session_state.user_id = result['user_id']
                    st.session_state.user_email = result['email']
                    st.session_state.username = result['username']
                    st.session_state.logged_in = True
                    st.session_state.active_tab = "Browse"
                    
                    # Fetch user profile data
                    user_profile = get_user_profile(result['user_id'])
                    if user_profile:
                        st.session_state.user_profile = user_profile
                    
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error(result.get('error', 'Login failed'))
            else:
                st.error("Please fill in all fields")
    
    with tab2:
        st.subheader("Register")
        email = st.text_input("Email", key="register_email")
        password = st.text_input("Password", type="password", key="register_password")
        username = st.text_input("Username", key="register_username")
        
        if st.button("Register"):
            if email and password and username:
                result = register_user(email, password, username)
                if result['success']:
                    # Initialize session state
                    st.session_state.user_id = result['user_id']
                    st.session_state.user_email = result['email']
                    st.session_state.username = result['username']
                    st.session_state.logged_in = True
                    st.session_state.active_tab = "Browse"
                    
                    # Fetch user profile data
                    user_profile = get_user_profile(result['user_id'])
                    if user_profile:
                        st.session_state.user_profile = user_profile
                    
                    st.success("Registration successful!")
                    st.rerun()
                else:
                    st.error(result.get('error', 'Registration failed'))
            else:
                st.error("Please fill in all fields")

def browse_page():
    """Display the marketplace browse page"""
    st.title("Browse Marketplace")
    
    # Initialize items in session state if not exists
    if 'items' not in st.session_state:
        st.session_state.items = []
    
    # Get items from Firestore
    try:
        items_ref = db.collection('items')
        items = items_ref.get()
        items = [item.to_dict() for item in items]
        st.session_state.items = items
    except Exception as e:
        st.error(f"Error loading items: {str(e)}")
        print(f"Error loading items: {str(e)}")
        items = []
    
    # Search and filter options
    col1, col2 = st.columns([2, 1])
    with col1:
        search_query = st.text_input("Search items", "")
    with col2:
        category = st.selectbox(
            "Category",
            ["All"] + list(CATEGORIES.keys()),
            index=0
        )
    
    # Filter items based on search and category
    filtered_items = items
    if search_query:
        search_query = search_query.lower()
        filtered_items = [
            item for item in filtered_items
            if search_query in item.get('name', '').lower() or
               search_query in item.get('description', '').lower()
        ]
    
    if category != "All":
        filtered_items = [
            item for item in filtered_items
            if item.get('category') == category
        ]
    
    # Display items in a grid
    if filtered_items:
        # Calculate number of columns based on screen width
        num_cols = 3
        
        # Create columns
        cols = st.columns(num_cols)
        
        # Display items in grid
        for idx, item in enumerate(filtered_items):
            with cols[idx % num_cols]:
                create_item_card(item)
    else:
        st.info("No items found. Try adjusting your search or filters.")

def item_detail_page():
    if 'detail_item' not in st.session_state:
        st.error("Item not found")
        return
    
    item = st.session_state.detail_item
    
    # Back button
    if st.button("← Back to Marketplace"):
        st.session_state.active_tab = "Browse"
        st.rerun()
    
    st.header(item['title'])
    create_item_card(item)
    
    # Show potential trades
    if 'barter_available' in item and item['barter_available']:
        st.subheader("Potential Trades")
        st.write("Our AI suggests these fair trades based on value and category:")
        
        potential_trades = suggest_trades(item['id'], st.session_state.user_id)
        
        if not potential_trades:
            st.info("No matching trades found. Check back later or browse more items.")
        else:
            for trade_item in potential_trades:
                with st.expander(f"Trade for: {trade_item['title']} (Match Score: {trade_item['match_score']:.2f})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("You Would Give:")
                        st.write(f"**{item['title']}**")
                        st.write(f"Value: ${item['price']}")
                    
                    with col2:
                        st.subheader("You Would Receive:")
                        st.write(f"**{trade_item['title']}**")
                        st.write(f"Value: ${trade_item['price']}")
                    
                    trade_difference = abs(item['price'] - trade_item['price'])
                    
                    if trade_difference > 0:
                        if item['price'] > trade_item['price']:
                            st.write(f"**Trade Gap:** You're giving ${trade_difference} more in value")
                        else:
                            st.write(f"**Trade Gap:** You're receiving ${trade_difference} more in value")
                    else:
                        st.write("**Even Trade:** Equal value exchange!")
                    
                    if trade_item['is_fair']:
                        st.success("✅ Our AI considers this a fair trade")
                    else:
                        st.warning("⚠️ This trade may not be completely fair")
                    
                    if st.button("View This Item", key=f"view_trade_{trade_item['id']}"):
                        st.session_state.detail_item = trade_item
                        st.rerun()
                    
                    if st.button("Propose This Trade", key=f"propose_{trade_item['id']}"):
                        st.session_state.active_tab = "Propose Trade"
                        st.session_state.trade_item = trade_item
                        st.session_state.my_item = item
                        st.rerun()

def create_listing_page():
    """Create a new listing"""
    st.title("Create New Listing")
    
    # Create a form for the new listing
    with st.form("new_listing_form"):
        # Basic Information
        st.subheader("Basic Information")
        name = st.text_input("Item Name")
        description = st.text_area("Description")
        category = st.selectbox("Category", ["Electronics", "Clothing", "Books", "Home & Garden", "Sports", "Other"])
        condition = st.selectbox("Condition", ["New", "Like New", "Good", "Fair", "Poor"])
        
        # Pricing Options
        st.subheader("Pricing")
        pricing_type = st.radio("Pricing Type", ["Fixed Price", "Trade Only", "Both"])
        
        if pricing_type in ["Fixed Price", "Both"]:
            price = st.number_input("Price ($)", min_value=0.0, value=0.0)
        
        # Trade Preferences
        if pricing_type in ["Trade Only", "Both"]:
            st.subheader("Trade Preferences")
            trade_categories = st.multiselect(
                "Categories you're interested in trading for",
                ["Electronics", "Clothing", "Books", "Home & Garden", "Sports", "Other"]
            )
            trade_conditions = st.multiselect(
                "Conditions you're interested in trading for",
                ["New", "Like New", "Good", "Fair", "Poor"]
            )
        
        # Shipping Options
        st.subheader("Shipping")
        shipping_options = st.multiselect(
            "Shipping Options",
            ["Local Pickup", "Standard Shipping", "Express Shipping"]
        )
        
        # Images
        st.subheader("Images")
        uploaded_files = st.file_uploader("Upload Images", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        
        # Submit button
        submitted = st.form_submit_button("Create Listing")
        
        if submitted:
            if not name or not description or not category or not condition:
                st.error("Please fill in all required fields")
            else:
                try:
                    # Create new item data
                    new_item = {
                        'name': name,
                        'description': description,
                        'category': category,
                        'condition': condition,
                        'price': price if pricing_type in ["Fixed Price", "Both"] else None,
                        'trade_categories': trade_categories if pricing_type in ["Trade Only", "Both"] else [],
                        'trade_conditions': trade_conditions if pricing_type in ["Trade Only", "Both"] else [],
                        'shipping_options': shipping_options,
                        'user_id': st.session_state.user_id,
                        'username': st.session_state.username,
                        'active': True,
                        'created_at': datetime.now()
                    }
                    
                    # Add to Firestore
                    doc_ref = db.collection('items').document()
                    new_item['id'] = doc_ref.id
                    
                    # Handle image uploads
                    image_urls = []
                    for uploaded_file in uploaded_files:
                        try:
                            # Upload to Firebase Storage
                            storage_path = f"items/{doc_ref.id}/{uploaded_file.name}"
                            bucket = storage.bucket()
                            blob = bucket.blob(storage_path)
                            blob.upload_from_string(uploaded_file.getvalue(), content_type=uploaded_file.type)
                            
                            # Get public URL
                            blob.make_public()
                            image_urls.append(blob.public_url)
                        except Exception as e:
                            st.error(f"Error uploading image {uploaded_file.name}: {str(e)}")
                            print(f"Error uploading image: {str(e)}")
                    
                    new_item['images'] = image_urls
                    
                    # Save to Firestore
                    doc_ref.set(new_item)
                    
                    # Update local state
                    if 'items' not in st.session_state:
                        st.session_state.items = []
                    st.session_state.items.append(new_item)
                    
                    st.success("Listing created successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating listing: {str(e)}")
                    print(f"Error creating listing: {str(e)}")

def my_listings_page():
    st.title("My Listings")
    
    try:
        # Get user's listings from Firestore
        user_listings = db.collection('items').where('user_id', '==', st.session_state.user_id).get()
        user_listings = [item.to_dict() for item in user_listings]
        
        if not user_listings:
            st.info("You haven't created any listings yet.")
            if st.button("Create Your First Listing"):
                st.session_state.active_tab = "Create Listing"
                st.rerun()
        else:
            # Display listings in a grid
            for listing in user_listings:
                with st.expander(f"{listing['name']} - {listing['category']}", expanded=True):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write("**Description:**")
                        st.write(listing['description'])
                        
                        # Display item details
                        details = []
                        if listing.get('brand'):
                            details.append(f"Brand: {listing['brand']}")
                        if listing.get('model'):
                            details.append(f"Model: {listing['model']}")
                        if listing.get('year'):
                            details.append(f"Year: {listing['year']}")
                        if listing.get('size'):
                            details.append(f"Size: {listing['size']}")
                        if listing.get('color'):
                            details.append(f"Color: {listing['color']}")
                        
                        if details:
                            st.write("**Details:**")
                            for detail in details:
                                st.write(detail)
                        
                        # Display pricing and trade options
                        st.write("**Availability:**")
                        if listing.get('for_sale'):
                            st.write(f"Price: ${listing.get('price', 0):.2f}")
                        if listing.get('for_trade'):
                            st.write("Available for trade")
                            if listing.get('looking_for'):
                                st.write("Looking for:")
                                for item in listing['looking_for']:
                                    st.write(f"- {item['item_type']} ({item['category']})")
                        
                        # Display shipping information
                        if listing.get('shipping'):
                            shipping = listing['shipping']
                            if shipping.get('willing_to_ship'):
                                st.write(f"Shipping available (Cost: ${shipping.get('shipping_cost', 0):.2f})")
                    
                    with col2:
                        # Display images if available
                        if listing.get('images'):
                            st.write("**Images:**")
                            for image_name in listing['images']:
                                try:
                                    st.image("https://via.placeholder.com/150", width=200)
                                except Exception as e:
                                    st.error(f"Error loading image: {str(e)}")
                        
                        # Listing actions
                        st.write("**Actions:**")
                        if st.button("Edit", key=f"edit_{listing['id']}"):
                            st.session_state.editing_listing = listing
                            st.session_state.active_tab = "Edit Listing"
                            st.rerun()
                        
                        if st.button("Delete", key=f"delete_{listing['id']}"):
                            if st.warning("Are you sure you want to delete this listing?"):
                                try:
                                    # Delete from Firestore
                                    db.collection('items').document(listing['id']).delete()
                                    # Remove from local state
                                    MOCK_ITEMS = [item for item in MOCK_ITEMS if item['id'] != listing['id']]
                                    st.success("Listing deleted successfully!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting listing: {str(e)}")
                        
                        # Toggle active status
                        status = "Active" if listing.get('active', True) else "Inactive"
                        if st.button(f"Mark as {'Inactive' if status == 'Active' else 'Active'}", 
                                   key=f"toggle_{listing['id']}"):
                            try:
                                # Update in Firestore
                                db.collection('items').document(listing['id']).update({
                                    'active': not listing.get('active', True)
                                })
                                # Update local state
                                for item in MOCK_ITEMS:
                                    if item['id'] == listing['id']:
                                        item['active'] = not item.get('active', True)
                                st.success(f"Listing marked as {'Inactive' if status == 'Active' else 'Active'}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error updating listing status: {str(e)}")
    except Exception as e:
        st.error(f"Error loading your listings: {str(e)}")
        print(f"Error loading listings: {str(e)}")

def trade_proposals_page():
    """Display trade proposals and allow sending new proposals"""
    st.title("Trade Proposals")
    
    # Get current user's items
    try:
        user_items = db.collection('items').where('user_id', '==', st.session_state.user_id).get()
        user_items = [item.to_dict() for item in user_items]
        
        if not user_items:
            st.info("You don't have any items listed yet.")
            return
        
        # Get all trade proposals for user's items
        proposals = db.collection('trade_proposals').where('item_owner_id', '==', st.session_state.user_id).get()
        proposals = [proposal.to_dict() for proposal in proposals]
        
        # Display trade proposals for user's items
        st.subheader("Trade Offers for Your Items")
        if not proposals:
            st.info("No trade proposals yet")
        else:
            for proposal in proposals:
                with st.expander(f"Trade Offer for {proposal['item_name']}", expanded=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Offered By:**")
                        st.write(f"User: {proposal['proposer_name']}")
                        st.write(f"Item: {proposal['proposed_item_name']}")
                        st.write(f"Category: {proposal['proposed_item_category']}")
                        st.write(f"Condition: {proposal['proposed_item_condition']}")
                        st.write(f"Price: ${proposal['proposed_item_price']}")
                        st.write(f"Status: {proposal['status']}")
                        st.write(f"Proposed: {proposal['created_at'].strftime('%Y-%m-%d %H:%M')}")
                        
                        # Display the message
                        st.write("**Message:**")
                        st.write(proposal['message'])
                    
                    with col2:
                        if proposal['status'] == 'pending':
                            st.write("**Actions:**")
                            if st.button("Accept", key=f"accept_{proposal['id']}"):
                                try:
                                    # Update proposal status in Firestore
                                    db.collection('trade_proposals').document(proposal['id']).update({
                                        'status': 'accepted',
                                        'accepted_at': datetime.now()
                                    })
                                    st.success("Trade proposal accepted!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error accepting proposal: {str(e)}")
                                    print(f"Error accepting proposal: {str(e)}")
                            
                            if st.button("Reject", key=f"reject_{proposal['id']}"):
                                try:
                                    # Update proposal status in Firestore
                                    db.collection('trade_proposals').document(proposal['id']).update({
                                        'status': 'rejected',
                                        'rejected_at': datetime.now()
                                    })
                                    st.success("Trade proposal rejected!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error rejecting proposal: {str(e)}")
                                    print(f"Error rejecting proposal: {str(e)}")
        
        # Section to send new trade proposals
        st.subheader("Send a Trade Proposal")
        
        # Get all active items from other users
        all_items = db.collection('items').where('active', '==', True).get()
        all_items = [item.to_dict() for item in all_items]
        
        other_items = [item for item in all_items if item['user_id'] != st.session_state.user_id]
        
        if not other_items:
            st.info("No items available to trade")
            return
        
        # Create two columns for item selection
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Your Item to Trade**")
            user_item_id = st.selectbox(
                "Select your item",
                options=[item['id'] for item in user_items],
                format_func=lambda x: next((item['name'] for item in user_items if item['id'] == x), x)
            )
        
        with col2:
            st.write("**Item You Want**")
            target_item_id = st.selectbox(
                "Select the item you want",
                options=[item['id'] for item in other_items],
                format_func=lambda x: next((item['name'] for item in other_items if item['id'] == x), x)
            )
        
        # Show item details
        st.write("**Item Details**")
        col1, col2 = st.columns(2)
        
        with col1:
            user_item = next((item for item in user_items if item['id'] == user_item_id), None)
            if user_item:
                st.write("**Your Item:**")
                st.write(f"Name: {user_item['name']}")
                st.write(f"Category: {user_item['category']}")
                st.write(f"Condition: {user_item['condition']}")
                st.write(f"Price: ${user_item['price']}")
        
        with col2:
            target_item = next((item for item in other_items if item['id'] == target_item_id), None)
            if target_item:
                st.write("**Target Item:**")
                st.write(f"Name: {target_item['name']}")
                st.write(f"Category: {target_item['category']}")
                st.write(f"Condition: {target_item['condition']}")
                st.write(f"Price: ${target_item['price']}")
        
        # Trade match analysis
        if user_item and target_item:
            st.write("**Trade Match Analysis**")
            price_difference = abs(user_item['price'] - target_item['price'])
            price_match = "Good" if price_difference <= 20 else "Fair" if price_difference <= 50 else "Poor"
                
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Price Difference", f"${price_difference}")
            with col2:
                st.metric("Price Match", price_match)
            with col3:
                st.metric("Category Match", "Same" if user_item['category'] == target_item['category'] else "Different")
        
        # Message to the other trader
        st.write("**Message to the Trader**")
        message = st.text_area(
            "Explain why you think this is a good trade...",
            placeholder="Hi! I'm interested in trading my [item] for your [item] because...",
            height=150
        )
        
        # Send proposal button
        if st.button("Send Trade Proposal"):
            if not message:
                st.error("Please include a message explaining your trade proposal")
            else:
                try:
                    # Create trade proposal in Firestore
                    proposal_data = {
                        'item_id': target_item['id'],
                        'proposed_item_id': user_item_id,
                        'proposer_id': st.session_state.user_id,
                        'proposer_name': st.session_state.username,
                        'proposed_item_name': user_item['name'],
                        'proposed_item_category': user_item['category'],
                        'proposed_item_condition': user_item['condition'],
                        'proposed_item_price': user_item.get('price', 0),
                        'item_name': target_item['name'],
                        'item_owner_id': target_item['user_id'],
                        'message': message,
                        'status': 'pending',
                        'created_at': datetime.now()
                    }
                    
                    # Add to trade_proposals collection
                    db.collection('trade_proposals').add(proposal_data)
                    
                    st.success("Trade proposal sent successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error sending trade proposal: {str(e)}")
                    print(f"Error sending trade proposal: {str(e)}")
                    
    except Exception as e:
        st.error(f"Error loading items: {str(e)}")
        print(f"Error loading items: {str(e)}")

def propose_trade_page():
    if 'selected_item' not in st.session_state:
        st.error("No item selected for trade")
        st.session_state.active_tab = "Browse"
        st.rerun()
        return
    
    target_item = st.session_state.selected_item
    
    st.header("Propose a Trade")
    
    # Show the item we want
    st.subheader("You want to receive:")
    create_item_card(target_item)
    
    st.divider()
    
    # Select what to offer
    st.subheader("Select what you'll offer:")
    
    # Get user's items from Firebase
    try:
        user_items = db.collection('items').where('user_id', '==', st.session_state.user_id).get()
        user_items = [item.to_dict() for item in user_items]
        
        if not user_items:
            st.info("You don't have any items listed. Create a listing first!")
            if st.button("Create Listing"):
                st.session_state.active_tab = "Create Listing"
                st.rerun()
            return
        
        # Filter items that are available for trade
        tradeable_items = [item for item in user_items if item.get('for_trade', False)]
        
        if not tradeable_items:
            st.info("None of your items are marked as available for trade. Edit your listings to enable trading!")
            if st.button("Edit Listings"):
                st.session_state.active_tab = "My Listings"
                st.rerun()
            return
        
        selected_item = st.selectbox(
            "Choose one of your items to trade",
            options=[f"{item['name']} (${item.get('price', 0)})" for item in tradeable_items],
            index=0
        )
        
        selected_index = [f"{item['name']} (${item.get('price', 0)})" for item in tradeable_items].index(selected_item)
        my_item = tradeable_items[selected_index]
        
        # Show trade comparison
        st.subheader("Trade Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**You Give:**")
            st.write(f"Item: {my_item['name']}")
            st.write(f"Value: ${my_item.get('price', 0)}")
            st.write(f"Category: {my_item['category']}")
        
        with col2:
            st.write("**You Receive:**")
            st.write(f"Item: {target_item['name']}")
            st.write(f"Value: ${target_item.get('price', 0)}")
            st.write(f"Category: {target_item['category']}")
        
        # Calculate trade fairness
        my_price = my_item.get('price', 0)
        their_price = target_item.get('price', 0)
        price_difference = abs(my_price - their_price)
        price_ratio = min(my_price, their_price) / max(my_price, their_price) if max(my_price, their_price) > 0 else 0
        
        # Trade fairness analysis
        if price_ratio >= 0.8:
            st.success("✅ This appears to be a fair trade!")
        elif price_ratio >= 0.6:
            st.warning("⚠️ This trade is somewhat uneven but might still be acceptable.")
        else:
            st.error("❌ This trade might be significantly uneven.")
        
        if price_difference > 0:
            if my_price > their_price:
                st.write(f"You're giving ${price_difference} more in value")
                include_cash = st.checkbox(f"Request ${price_difference} to balance the trade")
            else:
                st.write(f"You're receiving ${price_difference} more in value")
                include_cash = st.checkbox(f"Include ${price_difference} to balance the trade")
        
        # Message to the other trader
        st.subheader("Message to the Trader")
        message = st.text_area(
            "Explain why you think this is a good trade...",
            placeholder="Hi! I'm interested in trading my [item] for your [item] because...",
            height=150
        )
        
        # Submit proposal
        if st.button("Send Trade Proposal", use_container_width=True):
            if not message:
                st.error("Please include a message explaining your trade proposal")
            else:
                try:
                    # Create trade proposal in Firestore
                    proposal_data = {
                        'item_id': target_item['id'],
                        'proposed_item_id': my_item['id'],
                        'proposer_id': st.session_state.user_id,
                        'proposer_name': st.session_state.username,
                        'proposed_item_name': my_item['name'],
                        'proposed_item_category': my_item['category'],
                        'proposed_item_condition': my_item['condition'],
                        'proposed_item_price': my_item.get('price', 0),
                        'item_name': target_item['name'],
                        'item_owner_id': target_item['user_id'],
                        'message': message,
                        'status': 'pending',
                        'created_at': datetime.now()
                    }
                    
                    # Add to trade_proposals collection
                    db.collection('trade_proposals').add(proposal_data)
                    
                    st.success("🤝 Your trade proposal has been sent! You'll be notified when the other person responds.")
                    st.balloons()
                    st.session_state.active_tab = "Trade Proposals"
                    st.rerun()
                except Exception as e:
                    st.error(f"Error sending trade proposal: {str(e)}")
                    print(f"Error sending trade proposal: {str(e)}")
        
        # Cancel
        if st.button("Cancel", use_container_width=True):
            st.session_state.active_tab = "Browse"
            if 'selected_item' in st.session_state:
                del st.session_state.selected_item
            st.rerun()
            
    except Exception as e:
        st.error(f"Error loading your items: {str(e)}")
        

def cart_page():
    st.header("Shopping Cart")
    
    if not st.session_state.cart_items:
        st.info("Your cart is empty")
        if st.button("Browse Marketplace"):
            st.session_state.active_tab = "Browse"
            st.rerun()
    else:
        total = 0
        for item in st.session_state.cart_items:
            st.divider()
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"**{item['title']}**")
                st.write(f"${item['price']}")
            
            with col2:
                if st.button("Remove", key=f"remove_{item['id']}"):
                    st.session_state.cart_items.remove(item)
                    st.rerun()
            
            total += item['price']
        
        st.divider()
        st.write(f"**Total: ${total}**")
        
        if st.button("Proceed to Checkout", use_container_width=True):
            st.success("🎉 Order placed successfully!")
            st.balloons()
            st.session_state.cart_items = []
            st.rerun()

def profile_page():
    st.header("My Profile")
    
    if not st.session_state.logged_in:
        st.error("Please log in to view your profile")
        login_page()
        return
    
    # Profile Stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Active Listings", "5")
    with col2:
        st.metric("Completed Trades", "12")
    with col3:
        st.metric("Rating", "4.8 ⭐")
    
    # Quick Actions
    st.subheader("Quick Actions")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📦 My Listings", use_container_width=True):
            st.session_state.active_tab = "My Listings"
            st.rerun()
    with col2:
        if st.button("🤝 Trade Proposals", use_container_width=True):
            st.session_state.active_tab = "Trade Proposals"
            st.rerun()
    
    # Profile Settings
    st.subheader("Profile Settings")
    with st.expander("Edit Profile"):
        st.text_input("Display Name", value=st.session_state.username)
        st.text_input("Email", value="user@example.com")
        st.text_area("Bio", value="I love trading and finding unique items!")
        if st.button("Save Changes"):
            st.success("Profile updated successfully!")

def edit_listing_page():
    if 'editing_listing' not in st.session_state:
        st.error("No listing selected for editing")
        st.session_state.active_tab = "My Listings"
        st.rerun()
        return
    
    listing = st.session_state.editing_listing
    st.title("Edit Listing")
    
    with st.form("edit_listing_form"):
        # Basic Information
        st.subheader("Basic Information")
        name = st.text_input("Item Name", value=listing['name'])
        description = st.text_area("Description", value=listing['description'])
        category = st.selectbox(
            "Category",
            ["Electronics", "Clothing", "Home Goods", "Tools", 
             "Toys & Games", "Books", "Handmade", "Services", "Other"],
            index=["Electronics", "Clothing", "Home Goods", "Tools", 
                  "Toys & Games", "Books", "Handmade", "Services", "Other"].index(listing['category'])
        )
        condition = st.selectbox(
            "Condition",
            ["New", "Like New", "Good", "Fair", "Poor"],
            index=["New", "Like New", "Good", "Fair", "Poor"].index(listing['condition'])
        )
        
        # Additional Details
        st.subheader("Additional Details")
        brand = st.text_input("Brand (optional)", value=listing.get('brand', ''))
        model = st.text_input("Model (optional)", value=listing.get('model', ''))
        year = st.text_input("Year (optional)", value=listing.get('year', ''))
        size = st.text_input("Size (optional)", value=listing.get('size', ''))
        color = st.text_input("Color (optional)", value=listing.get('color', ''))
        tags = st.text_input("Tags (comma-separated, optional)", 
                           value=','.join(listing.get('tags', [])))
        
        # Pricing and Trade Options
        st.subheader("Pricing & Trade Options")
        col1, col2 = st.columns(2)
        with col1:
            for_sale = st.checkbox("Available for Sale", value=listing.get('for_sale', False))
            if for_sale:
                price = st.number_input("Price ($)", min_value=0.0, 
                                      value=listing.get('price', 0.0))
        with col2:
            for_trade = st.checkbox("Available for Trade", value=listing.get('for_trade', False))
            if for_trade:
                st.write("What are you looking for?")
                looking_for = listing.get('looking_for', [])
                num_trade_items = st.number_input("Number of items you're looking for", 
                                                min_value=1, value=max(1, len(looking_for)))
                
                # Display existing trade items
                for i in range(num_trade_items):
                    st.write(f"Item {i+1}")
                    trade_item = looking_for[i] if i < len(looking_for) else {
                        'category': "Electronics",
                        'item_type': "",
                        'condition': "Any",
                        'description': ""
                    }
                    
                    looking_for[i] = {
                        'category': st.selectbox(
                            f"Category for item {i+1}",
                            ["Electronics", "Clothing", "Home Goods", "Tools", 
                             "Toys & Games", "Books", "Handmade", "Services", "Other"],
                            index=["Electronics", "Clothing", "Home Goods", "Tools", 
                                  "Toys & Games", "Books", "Handmade", "Services", "Other"].index(trade_item['category']),
                            key=f"trade_cat_{i}"
                        ),
                        'item_type': st.text_input(f"Type of item {i+1}", 
                                                 value=trade_item['item_type'],
                                                 key=f"trade_type_{i}"),
                        'condition': st.selectbox(
                            f"Preferred condition for item {i+1}",
                            ["Any", "New", "Like New", "Good", "Fair", "Poor"],
                            index=["Any", "New", "Like New", "Good", "Fair", "Poor"].index(trade_item['condition']),
                            key=f"trade_cond_{i}"
                        ),
                        'description': st.text_area(f"Description for item {i+1}", 
                                                  value=trade_item['description'],
                                                  key=f"trade_desc_{i}")
                    }
        
        # Shipping Options
        st.subheader("Shipping Options")
        shipping = listing.get('shipping', {})
        willing_to_ship = st.checkbox("Willing to ship", value=shipping.get('willing_to_ship', False))
        if willing_to_ship:
            shipping_cost = st.number_input("Shipping cost ($)", min_value=0.0, 
                                          value=shipping.get('shipping_cost', 0.0))
        
        # Images
        st.subheader("Images")
        if listing.get('images'):
            st.write("Current images:")
            for image_name in listing['images']:
                try:
                    st.image("https://via.placeholder.com/150", width=200)
                except Exception as e:
                    st.error(f"Error loading image: {str(e)}")
        
        uploaded_files = st.file_uploader("Upload new images", type=['png', 'jpg', 'jpeg'], 
                                        accept_multiple_files=True)
        
        submit = st.form_submit_button("Save Changes")
        
        if submit:
            if not name or not description or not category or not condition:
                st.error("Please fill in all required fields")
            else:
                # Prepare updated item data
                updated_listing = {
                    'name': name,
                    'description': description,
                    'category': category,
                    'condition': condition,
                    'for_sale': for_sale,
                    'for_trade': for_trade,
                    'updated_at': datetime.now()
                }
                
                # Add optional fields if provided
                if brand:
                    updated_listing['brand'] = brand
                if model:
                    updated_listing['model'] = model
                if year:
                    updated_listing['year'] = year
                if size:
                    updated_listing['size'] = size
                if color:
                    updated_listing['color'] = color
                if tags:
                    updated_listing['tags'] = [tag.strip() for tag in tags.split(',')]
                
                # Add pricing if for sale
                if for_sale:
                    updated_listing['price'] = price
                
                # Add trade preferences if for trade
                if for_trade:
                    updated_listing['looking_for'] = looking_for
                
                # Add shipping information
                updated_listing['shipping'] = {
                    'willing_to_ship': willing_to_ship,
                    'shipping_cost': shipping_cost if willing_to_ship else 0
                }
                
                # Handle new image uploads
                if uploaded_files:
                    # For demo, we'll just store the file names
                    updated_listing['images'] = [f.name for f in uploaded_files]
                
                # Update the listing
                result = update_item(listing['id'], st.session_state.user_id, updated_listing)
                if result['success']:
                    st.success("Listing updated successfully!")
                    del st.session_state.editing_listing
                    st.session_state.active_tab = "My Listings"
                    st.rerun()
                else:
                    st.error(f"Error updating listing: {result.get('error', 'Unknown error')}")

# Main App Logic
def main():
    top_nav()
    header()
    sidebar()
    
    # Render the active tab
    if st.session_state.active_tab == "Login":
        login_page()
    elif st.session_state.active_tab == "Browse":
        browse_page()
    elif st.session_state.active_tab == "Item Detail":
        item_detail_page()
    elif st.session_state.active_tab == "Create Listing":
        if st.session_state.logged_in:
            create_listing_page()
        else:
            st.error("Please log in to create a listing")
            login_page()
    elif st.session_state.active_tab == "My Listings":
        if st.session_state.logged_in:
            my_listings_page()
        else:
            st.error("Please log in to view your listings")
            login_page()
    elif st.session_state.active_tab == "Trade Proposals":
        if st.session_state.logged_in:
            trade_proposals_page()
        else:
            st.error("Please log in to view trade proposals")
            login_page()
    elif st.session_state.active_tab == "Propose Trade":
        if st.session_state.logged_in:
            propose_trade_page()
        else:
            st.error("Please log in to propose trades")
            login_page()
    elif st.session_state.active_tab == "Cart":
        cart_page()
    elif st.session_state.active_tab == "Profile":
        profile_page()
    elif st.session_state.active_tab == "Edit Listing":
        edit_listing_page()

if __name__ == "__main__":
    main()


    