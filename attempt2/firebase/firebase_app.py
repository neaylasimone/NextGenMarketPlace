# app.py - Main Streamlit application
import streamlit as st
import json
import os
import pyrebase
import datetime
#import auth_service
#import user_service
#import item_service
#import search_service

# Configure Streamlit page
st.set_page_config(
    page_title="Trading App",
    page_icon="🔄",
    layout="wide"
)

# Firebase config for client-side auth (different from admin SDK)
firebase_config = {
    "apiKey": "YOUR_API_KEY",
    "authDomain": "YOUR_PROJECT_ID.firebaseapp.com",
    "projectId": "YOUR_PROJECT_ID",
    "storageBucket": "YOUR_PROJECT_ID.appspot.com",
    "messagingSenderId": "YOUR_MESSAGING_SENDER_ID",
    "appId": "YOUR_APP_ID",
    "databaseURL": ""  # Required by pyrebase
}

# Initialize Firebase for client side (authentication)
'''
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

# Initialize session state for user auth
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'username' not in st.session_state:
    st.session_state.username = None
'''
# Login/Register functions
def login(email, password):
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        user_result = auth_service.get_user_by_email(email)
        if user_result['success']:
            st.session_state.user_id = user_result['user'].uid
            st.session_state.user_email = email
            st.session_state.username = user_result['user'].display_name
            return True
    except Exception as e:
        st.error(f"Login failed: {str(e)}")
    return False

def register(email, password, username):
    try:
        result = auth_service.register_user(email, password, username)
        if result['success']:
            st.session_state.user_id = result['user'].uid
            st.session_state.user_email = email
            st.session_state.username = username
            return True
        else:
            st.error(f"Registration failed: {result['error']}")
    except Exception as e:
        st.error(f"Registration failed: {str(e)}")
    return False

def logout():
    st.session_state.user_id = None
    st.session_state.user_email = None
    st.session_state.username = None
    st.experimental_rerun()

# Main app UI
def main():
    st.title("Trading App")
    
    # Sidebar
    with st.sidebar:
        st.title("Navigation")
        
        if st.session_state.user_id:
            st.write(f"Logged in as: {st.session_state.username}")
            
            page = st.radio(
                "Go to",
                ["My Items", "Add New Item", "My Wishlist", "Search Items", "Potential Matches"]
            )
            
            if st.button("Logout"):
                logout()
        else:
            auth_option = st.radio("Select option", ["Login", "Register"])
            
            if auth_option == "Login":
                with st.form("login_form"):
                    email = st.text_input("Email")
                    password = st.text_input("Password", type="password")
                    submit = st.form_submit_button("Login")
                    
                    if submit:
                        if login(email, password):
                            st.success("Login successful!")
                            st.experimental_rerun()
            else:
                with st.form("register_form"):
                    email = st.text_input("Email")
                    username = st.text_input("Username")
                    password = st.text_input("Password", type="password")
                    confirm_password = st.text_input("Confirm Password", type="password")
                    submit = st.form_submit_button("Register")
                    
                    if submit:
                        if password != confirm_password:
                            st.error("Passwords do not match")
                        else:
                            if register(email, password, username):
                                st.success("Registration successful!")
                                st.experimental_rerun()
            
            # Show sample page for not logged in users
            page = "Welcome"
    
    # Content based on selected page
    if not st.session_state.user_id:
        welcome_page()
    elif page == "My Items":
        my_items_page()
    elif page == "Add New Item":
        add_item_page()
    elif page == "My Wishlist":
        wishlist_page()
    elif page == "Search Items":
        search_page()
    elif page == "Potential Matches":
        matches_page()

def welcome_page():
    st.header("Welcome to the Trading App")
    st.write("Please login or register to start trading items.")
    
    # Sample items display
    st.subheader("Sample Items for Trade")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.image("https://via.placeholder.com/150", caption="Sample Item 1")
        st.write("Vintage Camera")
    
    with col2:
        st.image("https://via.placeholder.com/150", caption="Sample Item 2")
        st.write("Mountain Bike")
    
    with col3:
        st.image("https://via.placeholder.com/150", caption="Sample Item 3")
        st.write("Antique Book")

def my_items_page():
    st.header("My Listed Items")
    
    # Get user's items
    result = item_service.get_user_listed_items(st.session_state.user_id)
    
    if result['success']:
        if not result['items']:
            st.info("You haven't listed any items yet.")
        else:
            for i, item in enumerate(result['items']):
                with st.expander(f"{item['name']} ({item['condition']})"):
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        if 'images' in item and item['images']:
                            st.image(item['images'][0], width=150)
                        else:
                            st.image("https://via.placeholder.com/150", width=150)
                    
                    with col2:
                        st.write(f"**Description:** {item['description']}")
                        
                        if item.get('for_sale', False):
                            st.write(f"**Price:** ${item['price']}")
                        
                        if item.get('for_trade', False):
                            st.write("**Looking to trade for:**")
                            for trade_item in item.get('looking_for', []):
                                st.write(f"- {trade_item}")
                        
                        col_edit, col_delete = st.columns(2)
                        with col_edit:
                            if st.button("Edit", key=f"edit_{item['id']}"):
                                st.session_state.edit_item = item
                                st.experimental_rerun()
                        
                        with col_delete:
                            if st.button("Delete", key=f"delete_{item['id']}"):
                                if item_service.delete_listed_item(st.session_state.user_id, item['id'])['success']:
                                    st.success("Item deleted successfully!")
                                    st.experimental_rerun()
                                else:
                                    st.error("Failed to delete item.")
    else:
        st.error(f"Error loading items: {result['error']}")

def add_item_page():
    st.header("List a New Item")
    
    with st.form("add_item_form"):
        name = st.text_input("Item Name")
        description = st.text_area("Description")
        condition = st.selectbox("Condition", ["New", "Like New", "Good", "Fair", "Poor"])
        
        # For simplicity, we're not handling actual image uploads
        # In a real app, you'd use st.file_uploader and Firebase Storage
        st.write("Image Upload (Not implemented in this demo)")
        
        for_sale = st.checkbox("Item is for sale")
        price = st.number_input("Price ($)", min_value=0.0, step=0.01, disabled=not for_sale)
        
        for_trade = st.checkbox("Item is available for trade")
        
        looking_for = []
        if for_trade:
            st.write("What are you looking to trade for?")
            trade_item_1 = st.text_input("Item 1")
            trade_item_2 = st.text_input("Item 2")
            trade_item_3 = st.text_input("Item 3")
            
            looking_for = [item for item in [trade_item_1, trade_item_2, trade_item_3] if item]
        
        submit = st.form_submit_button("List Item")
        
        if submit:
            if not name:
                st.error("Please enter an item name.")
            elif not description:
                st.error("Please enter a description.")
            elif not (for_sale or for_trade):
                st.error("Please select at least one option: for sale or for trade.")
            elif for_trade and not looking_for:
                st.error("Please enter at least one item you're looking to trade for.")
            else:
                # Create item data
                item_data = {
                    'name': name,
                    'description': description,
                    'condition': condition,
                    'images': ["https://via.placeholder.com/150"],  # Placeholder
                    'for_sale': for_sale,
                    'price': price if for_sale else 0,
                    'for_trade': for_trade,
                    'looking_for': looking_for if for_trade else []
                }
                
                # Add item
                result = item_service.list_new_item(st.session_state.user_id, item_data)
                
                if result['success']:
                    st.success("Item listed successfully!")
                    st.experimental_rerun()
                else:
                    st.error(f"Failed to list item: {result['error']}")

def wishlist_page():
    st.header("My Wishlist")
    
    # Get user profile with wishlist
    result = user_service.get_user_profile(st.session_state.user_id)
    
    if result['success']:
        wishlist = result['data'].get('wishlist', [])
        
        # Add new wishlist item form
        with st.form("add_wishlist_form"):
            st.subheader("Add to Wishlist")
            item_name = st.text_input("Item Name")
            description = st.text_area("Description (what you're looking for)")
            
            st.write("What are you willing to trade?")
            trade_item_1 = st.text_input("I can offer item 1")
            trade_item_2 = st.text_input("I can offer item 2")
            trade_item_3 = st.text_input("I can offer item 3")
            
            willing_to_trade = [item for item in [trade_item_1, trade_item_2, trade_item_3] if item]
            
            submit = st.form_submit_button("Add to Wishlist")
            
            if submit:
                if not item_name:
                    st.error("Please enter an item name.")
                elif not willing_to_trade:
                    st.error("Please enter at least one item you're willing to trade.")
                else:
                    # Create wishlist item
                    wishlist_item = {
                        'item_name': item_name,
                        'description': description,
                        'willing_to_trade': willing_to_trade
                    }
                    
                    # Add to wishlist
                    add_result = user_service.add_to_wishlist(st.session_state.user_id, wishlist_item)
                    
                    if add_result['success']:
                        st.success("Item added to wishlist!")
                        st.experimental_rerun()
                    else:
                        st.error(f"Failed to add item to wishlist: {add_result['error']}")
        
        # Display current wishlist
        st.subheader("My Current Wishlist")
        
        if not wishlist:
            st.info("Your wishlist is empty.")
        else:
            for i, item in enumerate(wishlist):
                with st.expander(f"{item['item_name']}"):
                    st.write(f"**Description:** {item.get('description', 'No description')}")
                    
                    st.write("**Willing to Trade:**")
                    for trade_item in item.get('willing_to_trade', []):
                        st.write(f"- {trade_item}")
                    
                    if st.button("Remove", key=f"remove_{i}"):
                        if user_service.remove_from_wishlist(st.session_state.user_id, i)['success']:
                            st.success("Item removed from wishlist!")
                            st.experimental_rerun()
                        else:
                            st.error("Failed to remove item from wishlist.")
    else:
        st.error(f"Error loading wishlist: {result['error']}")

def search_page():
    st.header("Search Items")
    
    search_query = st.text_input("Search for items")
    
    if search_query:
        result = search_service.search_items(search_query)
        
        if result['success']:
            if not result['items']:
                st.info(f"No items found matching '{search_query}'.")
            else:
                st.write(f"Found {len(result['items'])} items matching '{search_query}':")
                
                for item in result['items']:
                    with st.expander(f"{item['name']} ({item['condition']})"):
                        col1, col2 = st.columns([1, 3])
                        
                        with col1:
                            if 'images' in item and item['images']:
                                st.image(item['images'][0], width=150)
                            else:
                                st.image("https://via.placeholder.com/150", width=150)
                        
                        with col2:
                            st.write(f"**Description:** {item['description']}")
                            
                            if item.get('for_sale', False):
                                st.write(f"**Price:** ${item['price']}")
                            
                            if item.get('for_trade', False):
                                st.write("**Looking to trade for:**")
                                for trade_item in item.get('looking_for', []):
                                    st.write(f"- {trade_item}")
                            
                            # Get the owner username
                            owner = auth_service.get_user(item['user_id'])
                            if owner['success']:
                                st.write(f"**Listed by:** {owner['user'].display_name}")
        else:
            st.error(f"Error searching items: {result['error']}")

def matches_page():
    st.header("Potential Matches")
    
    if st.button("Find Matches"):
        result = search_service.find_potential_matches(st.session_state.user_id)
        
        if result['success']:
            if not result['matches']:
                st.info("No potential matches found for your wishlist items.")
            else:
                st.write(f"Found {len(result['matches'])} potential matches!")
                
                for match in result['matches']:
                    wishlist_item = match['wishlist_item']
                    matched_item = match['matched_item']
                    
                    with st.expander(f"Match for '{wishlist_item['item_name']}'"):
                        st.write("### What you're looking for:")
                        st.write(f"**Item:** {wishlist_item['item_name']}")
                        st.write(f"**Description:** {wishlist_item.get('description', 'No description')}")
                        
                        st.write("### Matched Item:")
                        col1, col2