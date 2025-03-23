# Sample data for the NextGenMarketplace app

SAMPLE_USERS = [
    {
        "uid": "user1",
        "email": "john.doe@example.com",
        "display_name": "John Doe",
        "wishlist": [
            {
                "item_name": "PlayStation 5",
                "description": "Looking for a PS5 Digital Edition or Disc Edition. Must include at least one controller and preferably some games.",
                "willing_to_trade": ["Trek Marlin 7", "Leica M3"]
            },
            {
                "item_name": "Apple Watch",
                "description": "Interested in Apple Watch Series 7 or newer, GPS + Cellular preferred. Must be in good condition with original accessories.",
                "willing_to_trade": ["Antique Books", "Fender Strat"]
            }
        ]
    },
    {
        "uid": "user2",
        "email": "jane.smith@example.com",
        "display_name": "Jane Smith",
        "wishlist": [
            {
                "item_name": "Mountain Bike",
                "description": "Looking for a Trek Marlin 7 or similar quality mountain bike. Must be in good condition with recent maintenance.",
                "willing_to_trade": ["Apple Watch", "PS5"]
            },
            {
                "item_name": "Electric Guitar",
                "description": "Interested in a Fender Stratocaster or similar electric guitar. Must include case and preferably an amp.",
                "willing_to_trade": ["Leica M3", "Antique Books"]
            }
        ]
    },
    {
        "uid": "user3",
        "email": "mike.johnson@example.com",
        "display_name": "Mike Johnson",
        "wishlist": [
            {
                "item_name": "Leica Camera",
                "description": "Looking for a Leica M3 or M4 in good condition. Must include original leather case and manual. Willing to pay extra for additional lenses.",
                "willing_to_trade": ["Apple Watch", "PS5"]
            },
            {
                "item_name": "Antique Books",
                "description": "Interested in first editions from the 1800s, particularly works by Charles Dickens or Mark Twain. Must be in good condition with original bindings.",
                "willing_to_trade": ["Trek Marlin 7", "Fender Strat"]
            }
        ]
    }
]

SAMPLE_ITEMS = [
    {
        "id": "item1",
        "user_id": "user1",
        "name": "Trek Marlin 7",
        "description": '2021 Trek Marlin 7 mountain bike in excellent condition. Size M. Includes recent tune-up, new brake pads, and 2.2" tires. Used for light trail riding, well maintained. Comes with original manual and receipt. Frame has some minor scratches but no dents or damage.',
        "condition": "Good",
        "images": ["https://via.placeholder.com/150"],
        "for_sale": True,
        "price": 750.00,
        "for_trade": True,
        "looking_for": ["PlayStation 5", "Apple Watch"],
        "active": True,
        "specs": {
            "frame_size": "M",
            "year": "2021",
            "color": "Matte Black",
            "components": "SRAM NX 1x12 drivetrain, RockShox Judy fork"
        }
    },
    {
        "id": "item2",
        "user_id": "user1",
        "name": "Leica M3",
        "description": "1954 Leica M3 camera in excellent condition. Serial number 854xxx. Includes original leather case, manual, and 50mm f/2 Summicron lens. Recently CLA'd (Clean, Lubricate, Adjust) by Leica specialist. Viewfinder is clear, shutter speeds accurate. Some brassing on edges but no dents or damage.",
        "condition": "Good",
        "images": ["https://via.placeholder.com/150"],
        "for_sale": True,
        "price": 1800.00,
        "for_trade": True,
        "looking_for": ["Apple Watch", "PlayStation 5"],
        "active": True,
        "specs": {
            "model": "M3",
            "year": "1954",
            "lens": "50mm f/2 Summicron",
            "accessories": ["Original leather case", "Manual", "Lens cap"]
        }
    },
    {
        "id": "item3",
        "user_id": "user2",
        "name": "Apple Watch Series 7",
        "description": "Apple Watch Series 7, 45mm, GPS + Cellular (Unlocked). Space Gray Aluminum Case with Black Sport Band. Battery health at 95%. Includes original box, charger, and extra sport band. Screen has no scratches, case has minor wear.",
        "condition": "Like New",
        "images": ["https://via.placeholder.com/150"],
        "for_sale": True,
        "price": 350.00,
        "for_trade": True,
        "looking_for": ["Trek Marlin 7", "Fender Stratocaster"],
        "active": True,
        "specs": {
            "model": "Series 7",
            "size": "45mm",
            "color": "Space Gray",
            "connectivity": "GPS + Cellular",
            "battery_health": "95%"
        }
    },
    {
        "id": "item4",
        "user_id": "user2",
        "name": "PlayStation 5 Digital Edition",
        "description": "PlayStation 5 Digital Edition in perfect condition. Includes original box, stand, and two DualSense controllers (one white, one black). Comes with three games: God of War Ragnarök, Horizon Forbidden West, and Spider-Man 2. All games are physical copies. Console has never been opened or modified.",
        "condition": "Like New",
        "images": ["https://via.placeholder.com/150"],
        "for_sale": True,
        "price": 450.00,
        "for_trade": True,
        "looking_for": ["Trek Marlin 7", "Leica M3"],
        "active": True,
        "specs": {
            "model": "Digital Edition",
            "storage": "825GB SSD",
            "included_games": ["God of War Ragnarök", "Horizon Forbidden West", "Spider-Man 2"],
            "controllers": ["White DualSense", "Black DualSense"]
        }
    },
    {
        "id": "item5",
        "user_id": "user3",
        "name": "Fender Stratocaster",
        "description": "2019 Fender American Professional II Stratocaster in Olympic White. Includes original case, strap, and cable. Recently set up by a professional luthier. Pickups are stock, but bridge has been upgraded to a Callaham. Some minor pick wear but no dings or scratches. Includes original receipt and warranty card.",
        "condition": "Good",
        "images": ["https://via.placeholder.com/150"],
        "for_sale": True,
        "price": 1400.00,
        "for_trade": True,
        "looking_for": ["Leica M3", "Antique Books"],
        "active": True,
        "specs": {
            "model": "American Professional II",
            "year": "2019",
            "color": "Olympic White",
            "pickups": "V-Mod II",
            "modifications": "Callaham bridge upgrade"
        }
    },
    {
        "id": "item6",
        "user_id": "user3",
        "name": "Antique Book Collection",
        "description": "Collection of 10 first edition books from the 1800s. Includes: Charles Dickens' 'A Tale of Two Cities' (1859), Mark Twain's 'The Adventures of Tom Sawyer' (1876), and other classics. All books have original bindings and are in good condition for their age. Includes certificates of authenticity and detailed condition reports.",
        "condition": "Fair",
        "images": ["https://via.placeholder.com/150"],
        "for_sale": True,
        "price": 2500.00,
        "for_trade": True,
        "looking_for": ["Fender Stratocaster", "Trek Marlin 7"],
        "active": True,
        "specs": {
            "notable_books": [
                "A Tale of Two Cities (1859)",
                "The Adventures of Tom Sawyer (1876)"
            ],
            "total_books": 10,
            "era": "1800s",
            "includes": ["Certificates of authenticity", "Condition reports"]
        }
    }
]

def populate_sample_data(db):
    """
    Populate the database with sample data
    
    Args:
        db: Firestore database instance
    """
    try:
        # Add users
        for user in SAMPLE_USERS:
            db.collection('users').document(user['uid']).set(user)
        
        # Add items
        for item in SAMPLE_ITEMS:
            db.collection('items').document(item['id']).set(item)
            
        return {'success': True, 'message': 'Sample data populated successfully'}
    except Exception as e:
        return {'success': False, 'error': str(e)} 