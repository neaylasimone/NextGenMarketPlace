# TO RUN:
# pip3 install streamlit pandas scikit-learn numpy
# streamlit run app.py

import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Initialize the app with custom styling
st.set_page_config(
    page_title="NextGenMarket - Buy & Barter Marketplace",
    page_icon="🔄",
    layout="wide"
)

# Custom CSS styling
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

# Replace Firebase with mock object during testing
class MockDB:
    def collection(self, *args, **kwargs):
        class MockCollection:
            def document(self, *args, **kwargs):
                class MockDoc:
                    def get(self):
                        class Fake:
                            def __init__(self):
                                self.exists = False
                        return Fake()
                return MockDoc()
            
            def where(self, *args, **kwargs):
                return self
            
            def stream(self):
                return []
        return MockCollection()

db = MockDB()

# Session state initialization
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "Browse"
if 'cart_items' not in st.session_state:
    st.session_state.cart_items = []
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""

# Utility functions
def get_trade_value(item_description, category, condition, images=None):
    """AI-powered function to estimate the value of an item"""
    # In a real app, this would use an ML model or API
    # For demo, we'll use a simple calculation based on random values and text analysis
    
    # Base value by category (just for demo)
    category_values = {
        "Electronics": (50, 500),
        "Clothing": (10, 100),
        "Home Goods": (20, 200),
        "Tools": (15, 150),
        "Toys & Games": (5, 80),
        "Books": (3, 30),
        "Handmade": (10, 150),
        "Services": (20, 100),
        "Other": (5, 50)
    }
    
    # Condition multiplier
    condition_multiplier = {
        "New": 1.0,
        "Like New": 0.9,
        "Good": 0.7,
        "Fair": 0.5,
        "Poor": 0.3
    }
    
    # Get base range and apply condition
    min_val, max_val = category_values.get(category, (5, 100))
    multiplier = condition_multiplier.get(condition, 0.5)
    
    # Text analysis would affect the range within min and max
    # More detailed descriptions typically indicate higher value items
    description_factor = min(1.0, len(item_description) / 200)
    
    # Calculate final value
    base_value = random.uniform(min_val, max_val) * multiplier * (0.8 + 0.4 * description_factor)
    
    # For demo purposes, round to whole dollar amount
    return round(base_value)

def suggest_trades(item_id, user_id):
    """Find potential trade matches based on item value and category"""
    # Get the current item
    item_doc = db.collection('items').document(item_id).get()
    if not item_doc.exists:
        return []
    
    item = item_doc.to_dict()
    user_items = []
    
    # Get all available items for trading (excluding user's own items)
    items_ref = db.collection('items').where('user_id', '!=', user_id).where('barter_available', '==', True).stream()
    
    all_items = []
    for doc in items_ref:
        trade_item = doc.to_dict()
        trade_item['id'] = doc.id
        all_items.append(trade_item)
    
    if not all_items:
        return []
    
    # Extract descriptions for similarity comparison
    descriptions = [item['description']] + [i['description'] for i in all_items]
    
    # Use TF-IDF to find similar items
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(descriptions)
    
    # Get similarity scores
    similarity_scores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
    
    # Calculate trade fairness based on price and similarity
    for i, trade_item in enumerate(all_items):
        price_ratio = min(item['price'], trade_item['price']) / max(item['price'], trade_item['price'])
        similarity = similarity_scores[i]
        
        # Combine price ratio and similarity for overall match score
        trade_item['match_score'] = (price_ratio * 0.7) + (similarity * 0.3)
        
        # Determine if this is a fair trade (over 0.7 is considered fair)
        trade_item['is_fair'] = trade_item['match_score'] > 0.7
    
    # Sort by match score
    sorted_items = sorted(all_items, key=lambda x: x['match_score'], reverse=True)
    
    return sorted_items[:5]  # Return top 5 matches

def create_item_card(item, is_detail=False, show_trade_btn=True):
    col1, col2 = st.columns([1, 3])
    
    with col1:
        image_url = item.get('image_url', "https://via.placeholder.com/150")
        st.image(image_url, use_container_width=True)
    
    with col2:
        st.markdown(f"<h3 style='color: #1E88E5; margin-bottom: 0.5rem;'>{item['title']}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #666;'>{item['description']}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #FFC107; font-weight: 500;'>Trade Value: ${item.get('trade_value', item['price'])}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #4CAF50;'>Category: {item['category']}</p>", unsafe_allow_html=True)
        
        # Display price and barter status
        price_col, barter_col, action_col = st.columns([1, 1, 1])
        with price_col:
            st.write(f"💰 ${item['price']}")
        with barter_col:
            if item.get('barter_available', False):
                st.write("🔄 Available for trade")
        with action_col:
            if not is_detail and item not in st.session_state.cart_items:
                if st.button("🛒 Add to Cart", key=f"cart_{item['id']}"):
                    st.session_state.cart_items.append(item)
                    st.success("Added to cart!")
                    st.rerun()
        
        st.write(f"**Condition:** {item['condition']}")
        
        if is_detail:
            st.write("**Description:**")
            st.write(item['description'])
            
            # Owner details
            st.write(f"**Posted by:** {item.get('username', 'Anonymous')}")
            st.write(f"**Posted on:** {item.get('created_at', 'Unknown date')}")
            
            # Actions
            if item.get('user_id') != st.session_state.user_id:
                col1, col2 = st.columns(2)
                with col1:
                    st.button("Contact Seller", key=f"contact_{item['id']}")
                with col2:
                    if item.get('barter_available', False) and show_trade_btn:
                        if st.button("Propose Trade", key=f"trade_{item['id']}"):
                            st.session_state.active_tab = "Propose Trade"
                            st.session_state.trade_item = item
                            st.rerun()
            else:
                st.info("This is your listing")
        else:
            # Truncate description
            short_desc = item['description'][:100] + "..." if len(item['description']) > 100 else item['description']
            st.write(short_desc)
            
            # View details button
            if st.button("View Details", key=f"view_{item['id']}"):
                st.session_state.active_tab = "Item Detail"
                st.session_state.detail_item = item
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
    st.header("Login / Register")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", use_container_width=True):
            if username and password:  # Basic validation
                st.session_state.logged_in = True
                st.session_state.username = username
                
                if 'redirect_after_login' in st.session_state:
                    next_page = st.session_state.redirect_after_login
                    del st.session_state.redirect_after_login
                    st.success(f"Welcome {username}! You've successfully logged in.")
                    st.session_state.active_tab = next_page
                else:
                    st.success(f"Welcome {username}! You've successfully logged in.")
                    st.session_state.active_tab = "Browse"
                st.rerun()
            else:
                st.error("Please enter both username and password")
    
    with tab2:
        new_username = st.text_input("Choose Username", key="reg_username")
        email = st.text_input("Email", key="reg_email")
        new_password = st.text_input("Create Password", type="password", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
        
        if st.button("Register", use_container_width=True):
            if new_username and email and new_password and confirm_password:
                if new_password == confirm_password:
                    st.session_state.logged_in = True
                    st.session_state.username = new_username
                    st.success(f"Welcome {new_username}! Your account has been created successfully.")
                    st.session_state.active_tab = "Browse"
                    st.rerun()
                else:
                    st.error("Passwords do not match")
            else:
                st.error("Please fill in all fields")

def browse_marketplace():
    # Remove the search bar from here since it's now in the top nav
    col1, col2 = st.columns(2)
    
    with col1:
        selected_category = st.selectbox(
            "Category",
            ["All Categories", "Electronics", "Clothing", "Home Goods", "Tools", 
             "Toys & Games", "Books", "Handmade", "Services", "Other"],
            index=0
        )
    
    with col2:
        sort_by = st.selectbox(
            "Sort by",
            ["Newest First", "Price: Low to High", "Price: High to Low", "Trade Value"]
        )
    
    # Filter for barter-only items
    barter_only = st.checkbox("Show only items available for trade")
    
    # Use the global search query if it exists
    search_term = st.session_state.search_query
    
    # Realistic mock data
    items = [
        {
            'id': 'item_1',
            'title': 'PlayStation 4 Pro (1TB) - Like New',
            'description': 'PS4 Pro in excellent condition. Includes original controller, power cable, and HDMI cable. Only used for 6 months, selling because I upgraded to PS5.',
            'price': 250,
            'category': 'Electronics',
            'condition': 'Like New',
            'barter_available': True,
            'user_id': 'user_1',
            'username': 'GamerPro',
            'created_at': '2025-03-20',
            'trade_value': 280,
            'image_url': 'https://images.unsplash.com/photo-1486401899868-0e435ed85128?ixlib=rb-1.2.1&auto=format&fit=crop&w=1050&q=80'
        },
        {
            'id': 'item_2',
            'title': 'Handcrafted Boho Dreamcatcher',
            'description': 'Beautiful handmade dreamcatcher with natural feathers and wooden beads. Perfect for bedroom or living room decor. Each piece is unique!',
            'price': 45,
            'category': 'Handmade',
            'condition': 'New',
            'barter_available': True,
            'user_id': 'user_2',
            'username': 'CraftLover',
            'created_at': '2025-03-19',
            'trade_value': 50,
            'image_url': 'https://images.unsplash.com/photo-1596360629200-740a8a92d5c4?ixlib=rb-1.2.1&auto=format&fit=crop&w=1050&q=80'
        },
        {
            'id': 'item_3',
            'title': 'Vintage Leather Jacket - Size M',
            'description': 'Genuine leather jacket in classic brown. Some natural wear adds character. Perfect for that retro look!',
            'price': 120,
            'category': 'Clothing',
            'condition': 'Good',
            'barter_available': True,
            'user_id': 'user_3',
            'username': 'VintageFinder',
            'created_at': '2025-03-18',
            'trade_value': 150,
            'image_url': 'https://images.unsplash.com/photo-1551028719-00167b16eac5?ixlib=rb-1.2.1&auto=format&fit=crop&w=1050&q=80'
        },
        {
            'id': 'item_4',
            'title': 'Custom Beaded Earrings Set',
            'description': 'Handmade beaded earrings set (3 pairs). Colors: turquoise, coral, and silver. Perfect for summer!',
            'price': 35,
            'category': 'Handmade',
            'condition': 'New',
            'barter_available': True,
            'user_id': 'user_4',
            'username': 'BeadArtist',
            'created_at': '2025-03-17',
            'trade_value': 40,
            'image_url': 'https://images.unsplash.com/photo-1630019852942-f89202989a59?ixlib=rb-1.2.1&auto=format&fit=crop&w=1050&q=80'
        },
        {
            'id': 'item_5',
            'title': 'MacBook Air M1 (2020)',
            'description': 'Space Gray MacBook Air with M1 chip. 8GB RAM, 256GB SSD. Includes charger and original box. Perfect condition!',
            'price': 750,
            'category': 'Electronics',
            'condition': 'Like New',
            'barter_available': False,
            'user_id': 'user_5',
            'username': 'TechDeals',
            'created_at': '2025-03-16',
            'trade_value': 800,
            'image_url': 'https://images.unsplash.com/photo-1611186871348-b1ce696e52c9?ixlib=rb-1.2.1&auto=format&fit=crop&w=1050&q=80'
        },
        {
            'id': 'item_6',
            'title': 'Yoga Mat + Blocks Set',
            'description': 'Premium yoga mat (6mm thick) with 2 cork blocks and strap. Perfect for home practice!',
            'price': 55,
            'category': 'Sports & Fitness',
            'condition': 'Good',
            'barter_available': True,
            'user_id': 'user_6',
            'username': 'YogaLife',
            'created_at': '2025-03-15',
            'trade_value': 65,
            'image_url': 'https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?ixlib=rb-1.2.1&auto=format&fit=crop&w=1050&q=80'
        }
    ]
    
    # Apply filters
    if selected_category != "All Categories":
        items = [item for item in items if item['category'] == selected_category]
    
    if search_term:
        items = [item for item in items if search_term.lower() in item['title'].lower() or 
                search_term.lower() in item['description'].lower()]
    
    if barter_only:
        items = [item for item in items if item['barter_available']]
    
    # Apply sorting
    if sort_by == "Price: Low to High":
        items = sorted(items, key=lambda x: x['price'])
    elif sort_by == "Price: High to Low":
        items = sorted(items, key=lambda x: x['price'], reverse=True)
    elif sort_by == "Trade Value":
        items = sorted(items, key=lambda x: x['trade_value'], reverse=True)
    
    # Display items
    if not items:
        st.info("No items match your search criteria.")
    else:
        for item in items:
            st.divider()
            create_item_card(item)

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
    st.header("Create New Listing")
    
    # Form inputs
    title = st.text_input("Title", placeholder="Enter a descriptive title")
    
    col1, col2 = st.columns(2)
    with col1:
        category = st.selectbox(
            "Category",
            ["Electronics", "Clothing", "Home Goods", "Tools", 
             "Toys & Games", "Books", "Handmade", "Services", "Other"]
        )
    with col2:
        condition = st.selectbox(
            "Condition",
            ["New", "Like New", "Good", "Fair", "Poor"]
        )
    
    description = st.text_area("Description", placeholder="Provide details about your item", height=150)
    
    # Listing Type Selection with improved UI
    st.markdown("### Listing Type")
    listing_type_col1, listing_type_col2 = st.columns(2)
    
    with listing_type_col1:
        for_sale = st.checkbox("Available for Sale", value=True)
        if for_sale:
            price = st.number_input("Sale Price ($)", min_value=1, step=1)
    
    with listing_type_col2:
        barter_available = st.checkbox("Available for Trade/Barter", value=True)
        if barter_available:
            st.info("Trade value will be calculated based on item details")
            if st.button("Calculate Trade Value"):
                trade_value = get_trade_value(description, category, condition)
                st.session_state.estimated_value = trade_value
                st.success(f"Estimated Trade Value: ${trade_value}")
    
    if not for_sale and not barter_available:
        st.error("Please select at least one option: For Sale or For Trade")
    
    uploaded_files = st.file_uploader("Upload Images (Max 5)", accept_multiple_files=True, type=["jpg", "jpeg", "png"])
    
    # Create listing button
    if st.button("Create Listing", use_container_width=True, type="primary"):
        if not title or not description:
            st.error("Please fill in all required fields")
        elif not for_sale and not barter_available:
            st.error("Please select at least one listing type (Sale or Trade)")
        elif for_sale and not price:
            st.error("Please set a sale price")
        else:
            st.success("🎉 Your listing has been created successfully!")
            st.balloons()
            st.session_state.active_tab = "My Listings"
            st.rerun()

def my_listings_page():
    st.header("My Listings")
    
    # Tabs for active and sold items
    tab1, tab2 = st.tabs(["Active Listings", "Sold/Completed"])
    
    with tab1:
        # In real app, fetch from Firebase
        # For demo, create mock data
        my_items = []
        for i in range(3):
            category = random.choice(["Electronics", "Clothing", "Home Goods"])
            condition = random.choice(["New", "Like New", "Good"])
            price = random.randint(20, 300)
            
            item = {
                'id': f"my_item_{i}",
                'title': f"My Item {i+1}",
                'description': f"This is the description for my item {i+1}. I'm selling it because I don't need it anymore.",
                'price': price,
                'category': category,
                'condition': condition,
                'barter_available': True,
                'user_id': st.session_state.user_id,
                'username': st.session_state.username,
                'created_at': '2025-03-18',
                'trade_value': get_trade_value("Sample description", category, condition)
            }
            my_items.append(item)
        
        if not my_items:
            st.info("You haven't created any listings yet.")
        else:
            for item in my_items:
                st.divider()
                create_item_card(item, show_trade_btn=False)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("Edit", key=f"edit_{item['id']}"):
                        st.write("Edit functionality would go here")
                with col2:
                    if st.button("Mark as Sold", key=f"sold_{item['id']}"):
                        st.write("Mark as sold functionality would go here")
                with col3:
                    if st.button("Delete", key=f"delete_{item['id']}"):
                        st.write("Delete functionality would go here")
    
    with tab2:
        st.info("No completed transactions.")

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
    
    # In real app, fetch user's items from Firebase
    # For demo, create mock data
    my_items = []
    for i in range(3):
        category = random.choice(["Electronics", "Clothing", "Home Goods"])
        condition = random.choice(["New", "Like New", "Good"])
        price = random.randint(20, 300)
        
        item = {
            'id': f"my_item_{i}",
            'title': f"My Item {i+1}",
            'description': f"This is the description for my item {i+1}.",
            'price': price,
            'category': category,
            'condition': condition,
            'barter_available': True,
            'user_id': st.session_state.user_id,
            'username': st.session_state.username or "Me",
            'created_at': '2025-03-18',
            'trade_value': get_trade_value("Sample description", category, condition),
            'image_url': "https://via.placeholder.com/150"  # Add placeholder image
        }
        my_items.append(item)
    
    selected_item = st.selectbox(
        "Choose one of your items to trade",
        options=[f"{item['title']} (${item['price']})" for item in my_items],
        index=0
    )
    
    selected_index = [f"{item['title']} (${item['price']})" for item in my_items].index(selected_item)
    my_item = my_items[selected_index]
    
    # Show trade comparison
    st.subheader("Trade Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**You Give:**")
        st.write(f"Item: {my_item['title']}")
        st.write(f"Value: ${my_item['price']}")
        st.write(f"Category: {my_item['category']}")
    
    with col2:
        st.write("**You Receive:**")
        st.write(f"Item: {trade_item['title']}")
        st.write(f"Value: ${trade_item['price']}")
        st.write(f"Category: {trade_item['category']}")
    
    # Calculate trade fairness
    price_difference = abs(my_item['price'] - trade_item['price'])
    price_ratio = min(my_item['price'], trade_item['price']) / max(my_item['price'], trade_item['price'])
    
    # This would ideally use the suggest_trades function
    if price_ratio > 0.8:
        st.success("✅ This appears to be a fair trade!")
    elif price_ratio > 0.6:
        st.warning("⚠️ This trade is somewhat uneven but might still be acceptable.")
    else:
        st.error("⛔ This trade is significantly uneven and may be rejected.")
    
    if price_difference > 0:
        if my_item['price'] > trade_item['price']:
            st.write(f"You're giving ${price_difference} more in value")
            # Offer to add cash to make it fair
            include_cash = st.checkbox(f"Request ${price_difference} to balance the trade")
        else:
            st.write(f"You're receiving ${price_difference} more in value")
            # Offer to add cash to make it fair
            include_cash = st.checkbox(f"Include ${price_difference} to balance the trade")
    
    # Additional comments
    message = st.text_area("Message to the other trader (optional)", 
                          placeholder="Explain why you think this is a good trade...")
    
    col1, col2 = st.columns(2)
    
    # Submit proposal
    if st.button("Send Trade Proposal", use_container_width=True):
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
            st.session_state.active_tab = "Checkout"
            st.rerun()

def checkout_page():
    st.header("Checkout")
    
    if not st.session_state.cart_items:
        st.info("Your cart is empty")
        if st.button("Browse Marketplace", use_container_width=False):
            st.session_state.active_tab = "Browse"
            st.rerun()
        return

    # Initialize checkout step in session state if not exists
    if 'checkout_step' not in st.session_state:
        st.session_state.checkout_step = 1
    
    # Calculate total
    total = sum(item['price'] for item in st.session_state.cart_items)
    shipping_cost = 0

    # Custom CSS for better input and button sizing
    st.markdown("""
        <style>
        /* Input field width */
        .stTextInput input {
            width: 100%;
            max-width: 400px;
        }
        
        /* Smaller width for email and phone inputs */
        [data-testid="stTextInput"] input[type="text"][aria-label*="Email"],
        [data-testid="stTextInput"] input[type="text"][aria-label*="Phone"] {
            max-width: 300px;
        }
        
        /* Button sizing */
        .stButton button {
            width: auto;
            min-width: 150px;
            max-width: 300px;
            padding: 0.5rem 1rem;
        }
        
        /* Radio button spacing */
        .stRadio > div {
            margin-bottom: 1rem;
        }
        
        /* Container width */
        .main-container {
            max-width: 800px;
            margin: 0 auto;
        }
        </style>
    """, unsafe_allow_html=True)

    # Simple step indicator
    st.markdown(f"**Step {st.session_state.checkout_step} of 2:** {'Shipping Details' if st.session_state.checkout_step == 1 else 'Payment'}")

    # Order Summary - Always visible but simplified
    with st.sidebar:
        st.subheader("Order Summary")
        
        for item in st.session_state.cart_items:
            st.write(f"{item['title']} - ${item['price']:.2f}")
        
        st.divider()
        
        if 'shipping_method' in st.session_state:
            if "Express" in st.session_state.shipping_method:
                shipping_cost = 9.99
            elif "Next Day" in st.session_state.shipping_method:
                shipping_cost = 19.99

        st.write(f"Subtotal: ${total:.2f}")
        st.write(f"Shipping: ${shipping_cost:.2f}")
        st.write(f"**Total: ${(total + shipping_cost):.2f}**")

    # Step 1: Shipping Information
    if st.session_state.checkout_step == 1:
        with st.form("shipping_form"):
            # Contact Information
            st.subheader("Contact Information")
            col1, col2 = st.columns([1, 2])
            with col1:
                email = st.text_input("Email")
            with col2:
                phone = st.text_input("Phone")
            
            # Shipping Information
            st.subheader("Shipping Address")
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("First Name")
            with col2:
                last_name = st.text_input("Last Name")
            
            address = st.text_input("Street Address")
            apartment = st.text_input("Apartment, suite, etc. (optional)")
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                city = st.text_input("City")
            with col2:
                state = st.text_input("State")
            with col3:
                zip_code = st.text_input("ZIP")
            
            # Shipping Method - Simplified options
            st.subheader("Shipping Method")
            shipping_method = st.radio(
                "Select Shipping Method",
                ["Standard (Free)",
                 "Express ($9.99)",
                 "Next Day ($19.99)"]
            )
            
            st.session_state.shipping_method = shipping_method
            
            # Continue button
            if st.form_submit_button("Continue to Payment"):
                if all([email, first_name, last_name, address, city, state, zip_code, phone]):
                    st.session_state.shipping_info = {
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name,
                        'address': address,
                        'apartment': apartment,
                        'city': city,
                        'state': state,
                        'zip_code': zip_code,
                        'phone': phone,
                        'shipping_method': shipping_method
                    }
                    st.session_state.checkout_step = 2
                    st.rerun()
                else:
                    st.error("Please fill in all required fields")

    # Step 2: Payment
    elif st.session_state.checkout_step == 2:
        # Simplified shipping info review
        st.write("**Shipping to:**", 
                f"{st.session_state.shipping_info['first_name']} {st.session_state.shipping_info['last_name']}, "
                f"{st.session_state.shipping_info['address']}, "
                f"{st.session_state.shipping_info['city']}, {st.session_state.shipping_info['state']}")
        
        if st.button("← Edit Shipping Info", use_container_width=False):
            st.session_state.checkout_step = 1
            st.rerun()
        
        st.divider()
        
        # Payment form
        with st.form("payment_form"):
            st.subheader("Payment Details")
            card_number = st.text_input("Card Number")
            col1, col2 = st.columns(2)
            with col1:
                expiry = st.text_input("Expiry (MM/YY)")
            with col2:
                cvv = st.text_input("CVV")

            # Simplified billing address
            same_as_shipping = st.checkbox("Billing address same as shipping", value=True)
            
            if not same_as_shipping:
                billing_address = st.text_input("Billing Address")
                col1, col2 = st.columns(2)
                with col1:
                    billing_city = st.text_input("City")
                with col2:
                    billing_state = st.text_input("State")
                billing_zip = st.text_input("ZIP")

            # Place Order button
            if st.form_submit_button("Place Order"):
                if all([card_number, expiry, cvv]):
                    st.success("Order placed successfully!")
                    st.balloons()
                    st.session_state.cart_items = []
                    st.session_state.checkout_step = 1
                    if 'shipping_info' in st.session_state:
                        del st.session_state.shipping_info
                    st.session_state.active_tab = "Browse"
                    st.rerun()
                else:
                    st.error("Please fill in all payment details")

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
    elif st.session_state.active_tab == "Checkout":
        checkout_page()
    elif st.session_state.active_tab == "Profile":
        profile_page()

if __name__ == "__main__":
    main()


    