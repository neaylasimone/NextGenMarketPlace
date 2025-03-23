# TO RUN:
# pip3 install streamlit pandas scikit-learn numpy
# streamlit run app.py

import streamlit as st

# Configure Streamlit page - MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="NextGenMarket - Buy & Barter Marketplace",
    page_icon="🔄",
    layout="wide"
)

import pandas as pd
from datetime import datetime
import uuid
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from firebase.firebase_app import initialize_firebase
from firebase.auth_service import register_user, login_user, get_user_profile
from firebase.item_service import list_new_item, get_user_listed_items, update_listed_item, delete_listed_item
from firebase.search_service import search_items, find_potential_matches, find_trade_matches, rate_trade_value
from firebase.user_service import add_to_wishlist, remove_from_wishlist, update_user_profile
import json
import os

# Initialize Firebase
auth = initialize_firebase()

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

# Utility functions
def create_item_card(item, is_detail=False, show_trade_btn=True):
    """Create a card display for an item"""
    col1, col2 = st.columns([1, 3])
    with col1:
        image_url = item.get('images', [None])[0] if item.get('images') else "https://via.placeholder.com/150"
        st.image(image_url, use_container_width=True)
    
    with col2:
        st.markdown(f"<h3 style='color: #1E88E5; margin-bottom: 0.5rem;'>{item['name']}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #666;'>{item['description']}</p>", unsafe_allow_html=True)
        
        # Display price if for sale
        if item.get('for_sale', False):
            st.markdown(f"<p style='color: #FFC107; font-weight: 500;'>Price: ${item.get('price', 0)}</p>", unsafe_allow_html=True)
        
        # Display trade value if for trade
        if item.get('for_trade', False):
            st.markdown(f"<p style='color: #4CAF50;'>Available for Trade</p>", unsafe_allow_html=True)
            if item.get('looking_for'):
                st.write("Looking for:")
                for trade_item in item['looking_for']:
                    if isinstance(trade_item, dict):
                        # Handle dictionary format
                        st.write(f"- {trade_item.get('item_type', 'Any')} ({trade_item.get('condition', 'Any condition')})")
                    else:
                        # Handle string format
                        st.write(f"- {trade_item}")
        
        if item.get('condition'):
            st.write(f"**Condition:** {item['condition']}")
        
        if is_detail:
            # Additional details
            if item.get('specs'):
                st.write("**Specifications:**")
                for key, value in item['specs'].items():
                    if isinstance(value, list):
                        st.write(f"**{key.replace('_', ' ').title()}:**")
                        for item in value:
                            st.write(f"- {item}")
                    else:
                        st.write(f"**{key.replace('_', ' ').title()}:** {value}")
            
            # Action buttons
            if st.session_state.logged_in and item['user_id'] != st.session_state.user_id:
                if show_trade_btn and item.get('for_trade', False):
                    if st.button("🔄 Propose Trade", key=f"trade_{item['id']}"):
                        st.session_state.selected_item = item
                        st.session_state.active_tab = "Propose Trade"
                        st.rerun()
                
                if item.get('for_sale', False):
                    if st.button("🛒 Add to Cart", key=f"cart_{item['id']}"):
                        st.session_state.cart_items.append(item)
                        st.success("Added to cart!")
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
    st.title("Login to NextGenMarket")
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if not email or not password:
                st.error("Please fill in all fields")
            else:
                result = login_user(email, password)
                if result['success']:
                    st.session_state.user_id = result['user_id']
                    st.session_state.logged_in = True
                    st.session_state.username = result.get('username', '')
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error(result.get('error', 'Login failed'))
    
    st.markdown("---")
    st.subheader("Don't have an account?")
    
    with st.form("register_form"):
        reg_email = st.text_input("Email")
        reg_password = st.text_input("Password", type="password")
        reg_username = st.text_input("Username")
        reg_submit = st.form_submit_button("Register")
        
        if reg_submit:
            if not reg_email or not reg_password or not reg_username:
                st.error("Please fill in all fields")
            else:
                result = register_user(reg_email, reg_password, reg_username)
                if result['success']:
                    st.success("Registration successful! Please login.")
                    st.rerun()
                else:
                    st.error(result.get('error', 'Registration failed'))

def browse_marketplace():
    st.title("Browse Marketplace")
    
    # Search bar
    search_query = st.text_input("🔍 Search items", value=st.session_state.search_query)
    if search_query:
        st.session_state.search_query = search_query
        result = search_items(search_query)
        if result['success']:
            items = result['items']
            if not items:
                st.info("No items found matching your search.")
            else:
                st.write(f"Found {len(items)} items matching your search")
                for item in items:
                    create_item_card(item)
        else:
            st.error(f"Error searching items: {result.get('error', 'Unknown error')}")
    else:
        # Show all active items
        result = search_items("")  # Empty query to get all items
        if result['success']:
            items = result['items']
            if not items:
                st.info("No items available in the marketplace.")
            else:
                st.write(f"Showing {len(items)} items")
                for item in items:
                    create_item_card(item)
        else:
            st.error(f"Error loading items: {result.get('error', 'Unknown error')}")

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
    create_item_card(item, is_detail=True)
    
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
    st.title("Create New Listing")
    
    with st.form("create_listing_form"):
        # Basic Information
        st.subheader("Basic Information")
        name = st.text_input("Item Name")
        description = st.text_area("Description")
        category = st.selectbox(
            "Category",
            ["Electronics", "Clothing", "Home Goods", "Tools", 
             "Toys & Games", "Books", "Handmade", "Services", "Other"]
        )
        condition = st.selectbox(
            "Condition",
            ["New", "Like New", "Good", "Fair", "Poor"]
        )
        
        # Additional Details
        st.subheader("Additional Details")
        brand = st.text_input("Brand (optional)")
        model = st.text_input("Model (optional)")
        year = st.text_input("Year (optional)")
        size = st.text_input("Size (optional)")
        color = st.text_input("Color (optional)")
        tags = st.text_input("Tags (comma-separated, optional)")
        
        # Pricing and Trade Options
        st.subheader("Pricing & Trade Options")
        col1, col2 = st.columns(2)
        with col1:
            for_sale = st.checkbox("Available for Sale")
            if for_sale:
                price = st.number_input("Price ($)", min_value=0.0, value=0.0)
        with col2:
            for_trade = st.checkbox("Available for Trade")
            if for_trade:
                st.write("What are you looking for?")
                looking_for = []
                num_trade_items = st.number_input("Number of items you're looking for", min_value=1, value=1)
                for i in range(num_trade_items):
                    st.write(f"Item {i+1}")
                    trade_item = {
                        'category': st.selectbox(
                            f"Category for item {i+1}",
                            ["Electronics", "Clothing", "Home Goods", "Tools", 
                             "Toys & Games", "Books", "Handmade", "Services", "Other"],
                            key=f"trade_cat_{i}"
                        ),
                        'item_type': st.text_input(f"Type of item {i+1}"),
                        'condition': st.selectbox(
                            f"Preferred condition for item {i+1}",
                            ["Any", "New", "Like New", "Good", "Fair", "Poor"],
                            key=f"trade_cond_{i}"
                        ),
                        'description': st.text_area(f"Description for item {i+1}")
                    }
                    looking_for.append(trade_item)
        
        # Shipping Options
        st.subheader("Shipping Options")
        willing_to_ship = st.checkbox("Willing to ship")
        if willing_to_ship:
            shipping_cost = st.number_input("Shipping cost ($)", min_value=0.0, value=0.0)
        
        # Images
        st.subheader("Images")
        uploaded_files = st.file_uploader("Upload images", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        
        submit = st.form_submit_button("Create Listing")
        
        if submit:
            if not name or not description or not category or not condition:
                st.error("Please fill in all required fields")
            else:
                # Prepare item data
                item_data = {
                    'name': name,
                    'description': description,
                    'category': category,
                    'condition': condition,
                    'for_sale': for_sale,
                    'for_trade': for_trade,
                    'created_at': datetime.datetime.now(),
                    'active': True
                }
                
                # Add optional fields if provided
                if brand:
                    item_data['brand'] = brand
                if model:
                    item_data['model'] = model
                if year:
                    item_data['year'] = year
                if size:
                    item_data['size'] = size
                if color:
                    item_data['color'] = color
                if tags:
                    item_data['tags'] = [tag.strip() for tag in tags.split(',')]
                
                # Add pricing if for sale
                if for_sale:
                    item_data['price'] = price
                
                # Add trade preferences if for trade
                if for_trade:
                    item_data['looking_for'] = looking_for
                
                # Add shipping information
                item_data['shipping'] = {
                    'willing_to_ship': willing_to_ship,
                    'shipping_cost': shipping_cost if willing_to_ship else 0
                }
                
                # Handle image uploads (in a real app, you'd upload these to a storage service)
                if uploaded_files:
                    # For demo, we'll just store the file names
                    item_data['images'] = [f.name for f in uploaded_files]
                
                # Create the listing
                result = list_new_item(st.session_state.user_id, item_data)
                if result['success']:
                    st.success("Listing created successfully!")
                    st.session_state.active_tab = "My Listings"
                    st.rerun()
                else:
                    st.error(f"Error creating listing: {result.get('error', 'Unknown error')}")

def my_listings_page():
    st.title("My Listings")
    
    # Get user's listings from Firebase
    result = get_user_listed_items(st.session_state.user_id)
    if not result['success']:
        st.error(f"Error fetching listings: {result.get('error', 'Unknown error')}")
        return
    
    listings = result['items']
    
    if not listings:
        st.info("You haven't created any listings yet.")
        if st.button("Create Your First Listing"):
            st.session_state.active_tab = "Create Listing"
            st.rerun()
    else:
        # Display listings in a grid
        for listing in listings:
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
                            st.image(image_name, use_container_width=True)
                    
                    # Listing actions
                    st.write("**Actions:**")
                    if st.button("Edit", key=f"edit_{listing['id']}"):
                        st.session_state.editing_listing = listing
                        st.session_state.active_tab = "Edit Listing"
                        st.rerun()
                    
                    if st.button("Delete", key=f"delete_{listing['id']}"):
                        if st.warning("Are you sure you want to delete this listing?"):
                            result = delete_listed_item(st.session_state.user_id, listing['id'])
                            if result['success']:
                                st.success("Listing deleted successfully!")
                                st.rerun()
                            else:
                                st.error(f"Error deleting listing: {result.get('error', 'Unknown error')}")
                    
                    # Toggle active status
                    status = "Active" if listing.get('active', True) else "Inactive"
                    if st.button(f"Mark as {'Inactive' if status == 'Active' else 'Active'}", 
                               key=f"toggle_{listing['id']}"):
                        updated_listing = listing.copy()
                        updated_listing['active'] = not listing.get('active', True)
                        result = update_listed_item(st.session_state.user_id, listing['id'], updated_listing)
                        if result['success']:
                            st.success(f"Listing marked as {'Inactive' if status == 'Active' else 'Active'}")
                            st.rerun()
                        else:
                            st.error(f"Error updating listing: {result.get('error', 'Unknown error')}")

def trade_proposals_page():
    st.header("Trade Proposals")
    
    # Tabs for incoming and outgoing proposals
    tab1, tab2 = st.tabs(["Received Proposals", "Sent Proposals"])
    
    with tab1:
        st.info("You have no incoming trade proposals.")
    
    with tab2:
        st.info("You have no outgoing trade proposals.")

def propose_trade_page():
    if 'trade_item' not in st.session_state:
        st.error("No trade item selected")
        return
    
    trade_item = st.session_state.trade_item
    
    st.header("Propose a Trade")
    
    # Show the item we want
    st.subheader("You want to receive:")
    create_item_card(trade_item, show_trade_btn=False)
    
    st.divider()
    
    # Select what to offer
    st.subheader("Select what you'll offer:")
    
    # Get user's items from Firebase
    result = get_user_listed_items(st.session_state.user_id)
    if not result['success']:
        st.error(f"Error fetching your items: {result.get('error', 'Unknown error')}")
        return
    
    my_items = result['items']
    
    if not my_items:
        st.info("You don't have any items listed. Create a listing first!")
        if st.button("Create Listing"):
            st.session_state.active_tab = "Create Listing"
            st.rerun()
        return
    
    # Filter items that are available for trade
    tradeable_items = [item for item in my_items if item.get('for_trade', False)]
    
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
        st.write(f"Item: {trade_item['name']}")
        st.write(f"Value: ${trade_item.get('price', 0)}")
        st.write(f"Category: {trade_item['category']}")
    
    # Calculate trade fairness
    my_price = my_item.get('price', 0)
    their_price = trade_item.get('price', 0)
    price_difference = abs(my_price - their_price)
    price_ratio = min(my_price, their_price) / max(my_price, their_price) if max(my_price, their_price) > 0 else 0
    
    # Use Firebase's rate_trade_value function
    trade_value_result = rate_trade_value(my_item, trade_item)
    if trade_value_result['success']:
        is_fair = trade_value_result.get('is_fair', False)
        if is_fair:
            st.success("✅ This appears to be a fair trade!")
        else:
            st.warning("⚠️ This trade is somewhat uneven but might still be acceptable.")
    else:
        st.warning("⚠️ Unable to evaluate trade fairness automatically.")
    
    if price_difference > 0:
        if my_price > their_price:
            st.write(f"You're giving ${price_difference} more in value")
            include_cash = st.checkbox(f"Request ${price_difference} to balance the trade")
        else:
            st.write(f"You're receiving ${price_difference} more in value")
            include_cash = st.checkbox(f"Include ${price_difference} to balance the trade")
    
    # Additional comments
    message = st.text_area("Message to the other trader (optional)", 
                          placeholder="Explain why you think this is a good trade...")
    
    # Submit proposal
    if st.button("Send Trade Proposal", use_container_width=True):
        # Here you would typically call a Firebase function to save the trade proposal
        # For now, we'll just show a success message
        st.success("🤝 Your trade proposal has been sent! You'll be notified when the other person responds.")
        st.balloons()
        st.session_state.active_tab = "Trade Proposals"
        st.rerun()
    
    # Cancel
    if st.button("Cancel", use_container_width=True):
        st.session_state.active_tab = "Browse"
        if 'trade_item' in st.session_state:
            del st.session_state.trade_item
        if 'my_item' in st.session_state:
            del st.session_state.my_item
        st.rerun()

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
                st.image(image_name, use_container_width=True)
        
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
                    'updated_at': datetime.datetime.now()
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
                result = update_listed_item(st.session_state.user_id, listing['id'], updated_listing)
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
        browse_marketplace()
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


    