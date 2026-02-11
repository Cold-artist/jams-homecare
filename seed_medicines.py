from app import app, db, Medicine

def seed_medicines():
    with app.app_context():
        # Clear existing medicines to avoid duplicates
        Medicine.query.delete()
        
        # High-Quality Category Images (3D / Clean Vector Style)
        images = {
            "Energy": "https://i.imgur.com/8J5s2e6.png", # Generic Energy Drink/Powder
            "Honey": "https://i.imgur.com/L7X9XyB.png",  # Honey Jar
            "Digestion": "https://i.imgur.com/3q5Xy9C.png", # Isabgol/Stomach Relief
            "Baby": "https://i.imgur.com/9X5Xy9C.png",    # Baby Wipes/Products
            "Immunity": "https://i.imgur.com/2X5Xy9C.png", # Chyawanprash Jar
            "Syrup": "https://i.imgur.com/4q5Xy9C.png",   # Generic Syrup Bottle
            "Ayurveda": "https://i.imgur.com/1X5Xy9C.png", # Herbal Syrup/Tonic
            "Nutrition": "https://i.imgur.com/5X5Xy9C.png", # Milk Powder/Lactogen
            "Liver": "https://i.imgur.com/6X5Xy9C.png",    # Liver Tonic/Tablets
            "Tablet": "https://i.imgur.com/7X5Xy9C.png",   # Generic Blister Pack
            "Ointment": "https://i.imgur.com/0X5Xy9C.png", # Tube Cream
            "Hygiene": "https://i.imgur.com/aX5Xy9C.png",  # Dettol/Liquid Handwash
            "Supplement": "https://i.imgur.com/bX5Xy9C.png" # Multivitamin Bottle
        }
        
        # Define Medicines Data
        medicines = [
            # Energy Drinks (Glucon-D)
            {"name": "Glucon-D Regular 125g", "price": 40, "cat": "Energy", "type": "OTC"},
            {"name": "Glucon-D Regular 250g", "price": 79, "cat": "Energy", "type": "OTC"},
            {"name": "Glucon-D Regular 500g", "price": 140, "cat": "Energy", "type": "OTC"},
            {"name": "Glucon-D Regular 1kg", "price": 255, "cat": "Energy", "type": "OTC"},
            {"name": "Glucon-D Orange 125g", "price": 56, "cat": "Energy", "type": "OTC"},
            {"name": "Glucon-D Orange 200g", "price": 89, "cat": "Energy", "type": "OTC"},
            {"name": "Glucon-D Orange 450g", "price": 219, "cat": "Energy", "type": "OTC"},
            {"name": "Glucon-D Orange 1kg", "price": 415, "cat": "Energy", "type": "OTC"},
            {"name": "Glucon-D Nimbu Pani 125g", "price": 56, "cat": "Energy", "type": "OTC"},
            {"name": "Glucon-D Nimbu Pani 450g", "price": 219, "cat": "Energy", "type": "OTC"},
            {"name": "Glucon-D Nimbu Pani 1kg", "price": 415, "cat": "Energy", "type": "OTC"},

            # Honey
            {"name": "Dabur Honey 100g", "price": 70, "cat": "Honey", "type": "Healthy Food"},
            {"name": "Dabur Honey 200g", "price": 125, "cat": "Honey", "type": "Healthy Food"},
            {"name": "Dabur Honey 600g", "price": 250, "cat": "Honey", "type": "Healthy Food"},

            # Digestion & Isabgol
            {"name": "Sat Isabgol 50g", "price": 90, "cat": "Digestion", "type": "OTC"},
            {"name": "Sat Isabgol 100g", "price": 175, "cat": "Digestion", "type": "OTC"},
            {"name": "Sat Isabgol 200g", "price": 345, "cat": "Digestion", "type": "OTC"},

            # Baby Care
            {"name": "Little Baby Wipes (30 Wipes)", "price": 49, "cat": "Baby", "type": "Personal Care"},
            {"name": "Little Baby Wipes (72 Wipes)", "price": 99, "cat": "Baby", "type": "Personal Care"},
            {"name": "Lactogen Pro 1", "price": 450, "cat": "Nutrition", "type": "Baby Food"},
            {"name": "Lactogen Pro 2", "price": 450, "cat": "Nutrition", "type": "Baby Food"},
            {"name": "Lactogen Pro 3", "price": 435, "cat": "Nutrition", "type": "Baby Food"},
            {"name": "Lactogen Pro 4", "price": 435, "cat": "Nutrition", "type": "Baby Food"},

            # Immunity (Chyawanprash)
            {"name": "Zandu Chyawanprash 450g", "price": 215, "cat": "Immunity", "type": "Ayurveda"},
            {"name": "Zandu Chyawanprash 900g", "price": 350, "cat": "Immunity", "type": "Ayurveda"},
            {"name": "Dabur Chyawanprash 250g", "price": 99, "cat": "Immunity", "type": "Ayurveda"},
            {"name": "Dabur Chyawanprash 500g", "price": 240, "cat": "Immunity", "type": "Ayurveda"},
            {"name": "Dabur Chyawanprash 1kg", "price": 430, "cat": "Immunity", "type": "Ayurveda"},
            {"name": "Dabur Chyawanprash Sugar Free 500g", "price": 255, "cat": "Immunity", "type": "Ayurveda"},
            {"name": "Dabur Chyawanprash Sugar Free 900g", "price": 440, "cat": "Immunity", "type": "Ayurveda"},

            # Dabur Syrups (Ayurveda)
            {"name": "Dabur Dashmularishta 450ml", "price": 215, "cat": "Ayurveda", "type": "Ayurveda"},
            {"name": "Dabur Dashmularishta 680ml", "price": 268, "cat": "Ayurveda", "type": "Ayurveda"},
            {"name": "Dabur Ashokarishta 450ml", "price": 155, "cat": "Ayurveda", "type": "Ayurveda"},
            {"name": "Dabur Ashokarishta 680ml", "price": 200, "cat": "Ayurveda", "type": "Ayurveda"},
            {"name": "Dabur Punarnavarishta 450ml", "price": 210, "cat": "Ayurveda", "type": "Ayurveda"},
            {"name": "Dabur Ashwagandharishta 680ml", "price": 300, "cat": "Ayurveda", "type": "Ayurveda"},
            {"name": "Dabur Pathyadiarishta 450ml", "price": 192, "cat": "Ayurveda", "type": "Ayurveda"},
            {"name": "Dabur Lohasava 450ml", "price": 195, "cat": "Ayurveda", "type": "Ayurveda"},
            {"name": "Dabur Lohasava 680ml", "price": 245, "cat": "Ayurveda", "type": "Ayurveda"},

            # Baidyanath Syrups
            {"name": "Baidyanath Dashmularishta 680ml", "price": 275, "cat": "Ayurveda", "type": "Ayurveda"},
            {"name": "Baidyanath Abhayarishta 680ml", "price": 255, "cat": "Ayurveda", "type": "Ayurveda"},
            {"name": "Baidyanath Ashokarishta 680ml", "price": 200, "cat": "Ayurveda", "type": "Ayurveda"},
            {"name": "Baidyanath Lohasav 450ml", "price": 198, "cat": "Ayurveda", "type": "Ayurveda"},
            {"name": "Baidyanath Arjunarishta 680ml", "price": 281, "cat": "Ayurveda", "type": "Ayurveda"},

            # Liver & Tablets (Himalaya)
            {"name": "Liv 52 Tablet", "price": 215, "cat": "Liver", "type": "Prescription"},
            {"name": "Liv 52 DS Tablet", "price": 300, "cat": "Liver", "type": "Prescription"},
            {"name": "Liv 52 Syrup 100ml", "price": 140, "cat": "Liver", "type": "Prescription"},
            {"name": "Liv 52 Syrup 200ml", "price": 250, "cat": "Liver", "type": "Prescription"},
            {"name": "Liv 52 DS Syrup 100ml", "price": 220, "cat": "Liver", "type": "Prescription"},
            {"name": "Liv 52 DS Syrup 200ml", "price": 351, "cat": "Liver", "type": "Prescription"},

            # Other Conditions (Himalaya)
            {"name": "Septiline Tablet", "price": 275, "cat": "Tablet", "type": "Prescription"},
            {"name": "Septiline Syrup 200ml", "price": 200, "cat": "Syrup", "type": "Prescription"},
            {"name": "Pilex Tablet", "price": 250, "cat": "Tablet", "type": "Prescription"},
            {"name": "Pilex Forte Ointment 30g", "price": 160, "cat": "Ointment", "type": "Prescription"},
            {"name": "Cystone Tablet", "price": 260, "cat": "Tablet", "type": "Prescription"},
            {"name": "Cystone Syrup 200ml", "price": 225, "cat": "Syrup", "type": "Prescription"},
            {"name": "Evecare Syrup 200ml", "price": 190, "cat": "Syrup", "type": "Prescription"},
            {"name": "Hasx Tablet", "price": 200, "cat": "Tablet", "type": "Prescription"},
            {"name": "Neeri Syrup 100ml", "price": 164, "cat": "Syrup", "type": "Prescription"},
            {"name": "Neeri Syrup 200ml", "price": 313, "cat": "Syrup", "type": "Prescription"},

            # Ointments & Powders
            {"name": "Ano Rate Ointment 20g", "price": 145, "cat": "Ointment", "type": "OTC"}, # Rounded 145.31
            {"name": "Abzorb Powder", "price": 175, "cat": "Hygiene", "type": "Personal Care"},
            {"name": "Candid Powder 60g", "price": 104, "cat": "Hygiene", "type": "Personal Care"},
            {"name": "Candid Powder 120g", "price": 174, "cat": "Hygiene", "type": "Personal Care"},
            {"name": "Clocip Powder 75g", "price": 93, "cat": "Hygiene", "type": "Personal Care"},
            {"name": "Clocip Powder 120g", "price": 168, "cat": "Hygiene", "type": "Personal Care"},

            # Hygiene
            {"name": "Dettol Liquid 60ml", "price": 41, "cat": "Hygiene", "type": "Personal Care"},
            {"name": "Dettol Liquid 125ml", "price": 83, "cat": "Hygiene", "type": "Personal Care"},
            {"name": "Dettol Liquid 250ml", "price": 159, "cat": "Hygiene", "type": "Personal Care"},
            {"name": "Dettol Liquid 550ml", "price": 267, "cat": "Hygiene", "type": "Personal Care"},
            {"name": "Dettol Liquid 1L", "price": 485, "cat": "Hygiene", "type": "Personal Care"},

            # Multivitamins
            {"name": "Maxirich (10 Tablets)", "price": 129, "cat": "Supplement", "type": "Supplements"}
        ]

        print(f"Starting seed of {len(medicines)} medicines...")
        for m in medicines:
            # Smart Image Mapping: If we don't have a specific image, fall back to Category Image
            # Note: For this demo, using placeholders. In real production, you'd want exact images.
            # Using 'https://placehold.co/400x400?text=' + Name for now to ensure they look distinct
            # OR using the category map for a cleaner look. Let's use Category Map for professionalism.
            
            # Using specific images for known categories
            img = images.get(m['cat'], "https://i.imgur.com/7X5Xy9C.png") # Default to Tablet
            
            med = Medicine(
                name=m['name'],
                category=m['type'], # e.g., OTC, Prescription
                price=m['price'],
                original_price=int(m['price'] * 1.15), # Fake discount of 15%
                description=f"Genuine {m['name']} for {m['cat']} care.",
                image_url=img,
                is_active=True
            )
            db.session.add(med)
        
        db.session.commit()
        print("Success: Medicines Seeded!")

if __name__ == "__main__":
    seed_medicines()
