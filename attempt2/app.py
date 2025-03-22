import streamlit as st
# import firebase_admin
# from firebase_admin import credentials, firestore
import pandas as pd
from datetime import datetime
import uuid
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Initialize the app
st.set_page_config(
    page_title="CommuniTrade - Buy & Barter Marketplace",
    page_icon="🔄",
    layout="wide"
)

# Initialize Firebase (in production, use proper auth credentials)
# @st.cache_resource
# def initialize_firebase():
#     try:
#         firebase_admin.get_app()
#     except ValueError:
#         # Use this in development, replace with actual credentials in production
#         cred = credentials.Certificate("firebase-key.json")
#         firebase_admin.initialize_app(cred)
#     return firestore.client()

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
# db = initialize_firebase()

# Session state initialization
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "Browse"

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
        # Placeholder for image
        st.image("https://via.placeholder.com/150", use_column_width=True)
    
    with col2:
        st.subheader(item['title'])
        
        # Display price and barter status
        price_col, barter_col = st.columns(2)
        with price_col:
            st.write(f"💰 ${item['price']}")
        with barter_col:
            if item.get('barter_available', False):
                st.write("🔄 Available for trade")
        
        st.write(f"**Condition:** {item['condition']}")
        st.write(f"**Category:** {item['category']}")
        
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
                            st.experimental_rerun()
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
                st.experimental_rerun()

# UI Components
def header():
    col1, col2, col3 = st.columns([3, 3, 2])
    
    with col1:
        st.title("🔄 CommuniTrade")
        st.write("Buy • Sell • Barter • Build Community")
    
    with col3:
        if st.session_state.logged_in:
            st.write(f"Welcome, {st.session_state.username}!")
            if st.button("Logout"):
                st.session_state.logged_in = False
                st.session_state.username = ""
                st.experimental_rerun()
        else:
            if st.button("Login / Register"):
                st.session_state.active_tab = "Login"
                st.experimental_rerun()

def sidebar():
    with st.sidebar:
        st.title("Navigation")
        
        if st.button("🔍 Browse Marketplace"):
            st.session_state.active_tab = "Browse"
            st.experimental_rerun()
            
        if st.button("➕ Create Listing"):
            if st.session_state.logged_in:
                st.session_state.active_tab = "Create Listing"
            else:
                st.session_state.active_tab = "Login"
                st.session_state.redirect_after_login = "Create Listing"
            st.experimental_rerun()
            
        if st.button("🧰 My Listings"):
            if st.session_state.logged_in:
                st.session_state.active_tab = "My Listings"
            else:
                st.session_state.active_tab = "Login"
                st.session_state.redirect_after_login = "My Listings"
            st.experimental_rerun()
            
        if st.button("📋 Trade Proposals"):
            if st.session_state.logged_in:
                st.session_state.active_tab = "Trade Proposals"
            else:
                st.session_state.active_tab = "Login"
                st.session_state.redirect_after_login = "Trade Proposals"
            st.experimental_rerun()
            
        st.divider()
        st.write("### Filter by Category")
        categories = ["All", "Electronics", "Clothing", "Home Goods", "Tools", 
                     "Toys & Games", "Books", "Handmade", "Services", "Other"]
        
        for category in categories:
            if st.button(category, key=f"cat_{category}"):
                st.session_state.active_tab = "Browse"
                st.session_state.selected_category = category
                st.experimental_rerun()

def login_page():
    st.header("Login / Register")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login"):
            # In a real app, authenticate with Firebase Auth
            # For this demo, we'll just set logged in to true
            st.session_state.logged_in = True
            st.session_state.username = username
            
            # Redirect if needed
            if 'redirect_after_login' in st.session_state:
                st.session_state.active_tab = st.session_state.redirect_after_login
                del st.session_state.redirect_after_login
            else:
                st.session_state.active_tab = "Browse"
                
            st.experimental_rerun()
    
    with tab2:
        new_username = st.text_input("Choose Username", key="reg_username")
        email = st.text_input("Email", key="reg_email")
        new_password = st.text_input("Create Password", type="password", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
        
        if st.button("Register"):
            # For demo purposes, this just logs the user in
            st.session_state.logged_in = True
            st.session_state.username = new_username
            st.session_state.active_tab = "Browse"
            st.experimental_rerun()

def browse_marketplace():
    st.header("Browse Marketplace")
    
    # Search and filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input("Search items", placeholder="What are you looking for?")
    
    with col2:
        selected_category = st.selectbox(
            "Category",
            ["All Categories", "Electronics", "Clothing", "Home Goods", "Tools", 
             "Toys & Games", "Books", "Handmade", "Services", "Other"],
            index=0
        )
    
    with col3:
        sort_by = st.selectbox(
            "Sort by",
            ["Newest First", "Price: Low to High", "Price: High to Low", "Trade Value"]
        )
    
    # Filter for barter-only items
    barter_only = st.checkbox("Show only items available for trade")
    
    # Get items from Firebase
    # For demo purposes, create mock data
    items = []
    
    # In real app, this would query Firebase
    for i in range(10):
        category = random.choice(["Electronics", "Clothing", "Home Goods", "Tools", 
                                "Toys & Games", "Books", "Handmade", "Services", "Other"])
        condition = random.choice(["New", "Like New", "Good", "Fair", "Poor"])
        barter = random.choice([True, False, True])  # More likely to be available for barter
        price = random.randint(10, 500)
        
        item = {
            'id': f"item_{i}",
            'title': f"Sample Item {i+1}",
            'description': f"This is a sample description for item {i+1}. It provides details about the condition, features, and any other relevant information.",
            'price': price,
            'category': category,
            'condition': condition,
            'barter_available': barter,
            'user_id': f"user_{random.randint(1, 10)}",
            'username': f"user_{random.randint(1, 10)}",
            'created_at': '2025-03-20',
            'trade_value': get_trade_value("Sample description", category, condition)
        }
        items.append(item)
    
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
    # Default is "Newest First" which is fine as is
    
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
        st.experimental_rerun()
    
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
                        st.experimental_rerun()
                    
                    if st.button("Propose This Trade", key=f"propose_{trade_item['id']}"):
                        st.session_state.active_tab = "Propose Trade"
                        st.session_state.trade_item = trade_item
                        st.session_state.my_item = item
                        st.experimental_rerun()

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
    
    col1, col2 = st.columns(2)
    with col1:
        price = st.number_input("Price ($)", min_value=1, step=1)
    with col2:
        barter_available = st.checkbox("Available for trade/barter", value=True)
    
    st.file_uploader("Upload Images (Max 5)", accept_multiple_files=True, type=["jpg", "jpeg", "png"])
    
    if st.button("Preview Trade Value"):
        trade_value = get_trade_value(description, category, condition)
        st.session_state.estimated_value = trade_value
        st.info(f"Estimated Trade Value: ${trade_value}")
        st.write("This is what our AI thinks your item is worth for bartering purposes.")
    
    if st.button("Create Listing"):
        if not title or not description or not price:
            st.error("Please fill in all required fields")
        else:
            # In a real app, save to Firebase
            st.success("Your listing has been created successfully!")
            st.session_state.active_tab = "My Listings"
            st.experimental_rerun()

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
            'trade_value': get_trade_value("Sample description", category, condition)
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
    
    # Submit proposal
    if st.button("Send Trade Proposal"):
        st.success("Your trade proposal has been sent! You'll be notified when the other person responds.")
        st.session_state.active_tab = "Trade Proposals"
        st.experimental_rerun()
    
    # Cancel
    if st.button("Cancel"):
        st.session_state.active_tab = "Browse"
        if 'trade_item' in st.session_state:
            del st.session_state.trade_item
        if 'my_item' in st.session_state:
            del st.session_state.my_item
        st.experimental_rerun()

# Main App Logic
def main():
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

if __name__ == "__main__":
    main()


    