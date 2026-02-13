from app import app, db, Medicine

def seed_medicines():
    with app.app_context():
        # Clear existing medicines to avoid duplicates
        Medicine.query.delete()
        
        # High-Quality Official Brand Logos (Real Images)
        # Using Clearbit Logo API for official branding
        images = {
            "Glucon-D": "https://logo.clearbit.com/glucond.com", # Fallback to generic if not found, but trying specific
            "Dabur": "https://logo.clearbit.com/dabur.com",
            "Himalaya": "https://logo.clearbit.com/himalayawellness.in",
            "Dettol": "https://logo.clearbit.com/reckitt.com", # Reckitt owns Dettol
            "Zandu": "https://logo.clearbit.com/zanducare.com",
            "Little": "https://logo.clearbit.com/piramal.com", # Piramal owns Little's
            "Nestle": "https://logo.clearbit.com/nestle.in", # Lactogen
        }
        
        # Fallback Category Icons (Clean, Professional Vector Style)
        cat_images = {
            "Energy": "https://i.imgur.com/8J5s2e6.png",
            "Honey": "https://logo.clearbit.com/dabur.com", # Dabur is main honey
            "Digestion": "https://i.imgur.com/3q5Xy9C.png",
            "Baby": "https://logo.clearbit.com/piramal.com",
            "Immunity": "https://logo.clearbit.com/zanducare.com",
            "Syrup": "https://i.imgur.com/4q5Xy9C.png",
            "Ayurveda": "https://logo.clearbit.com/dabur.com",
            "Nutrition": "https://logo.clearbit.com/nestle.in",
            "Liver": "https://logo.clearbit.com/himalayawellness.in",
            "Tablet": "https://logo.clearbit.com/himalayawellness.in",
            "Ointment": "https://i.imgur.com/0X5Xy9C.png",
            "Hygiene": "https://logo.clearbit.com/reckitt.com",
            "Supplement": "https://i.imgur.com/bX5Xy9C.png"
        }
        
        # Define Medicines Data
        medicines = [
            # Energy Drinks (Glucon-D)
            {"name": "Glucon-D Regular 125g", "price": 40, "cat": "Energy", "type": "OTC", "brand": "Glucon-D"},
            {"name": "Glucon-D Regular 250g", "price": 79, "cat": "Energy", "type": "OTC", "brand": "Glucon-D"},
            {"name": "Glucon-D Regular 500g", "price": 140, "cat": "Energy", "type": "OTC", "brand": "Glucon-D"},
            {"name": "Glucon-D Regular 1kg", "price": 255, "cat": "Energy", "type": "OTC", "brand": "Glucon-D"},
            {"name": "Glucon-D Orange 125g", "price": 56, "cat": "Energy", "type": "OTC", "brand": "Glucon-D"},
            {"name": "Glucon-D Orange 200g", "price": 89, "cat": "Energy", "type": "OTC", "brand": "Glucon-D"},
            {"name": "Glucon-D Orange 450g", "price": 219, "cat": "Energy", "type": "OTC", "brand": "Glucon-D"},
            {"name": "Glucon-D Orange 1kg", "price": 415, "cat": "Energy", "type": "OTC", "brand": "Glucon-D"},
            {"name": "Glucon-D Nimbu Pani 125g", "price": 56, "cat": "Energy", "type": "OTC", "brand": "Glucon-D"},
            {"name": "Glucon-D Nimbu Pani 450g", "price": 219, "cat": "Energy", "type": "OTC", "brand": "Glucon-D"},
            {"name": "Glucon-D Nimbu Pani 1kg", "price": 415, "cat": "Energy", "type": "OTC", "brand": "Glucon-D"},

            # Honey
            {"name": "Dabur Honey 100g", "price": 70, "cat": "Honey", "type": "Healthy Food", "brand": "Dabur"},
            {"name": "Dabur Honey 200g", "price": 125, "cat": "Honey", "type": "Healthy Food", "brand": "Dabur"},
            {"name": "Dabur Honey 600g", "price": 250, "cat": "Honey", "type": "Healthy Food", "brand": "Dabur"},

            # Digestion & Isabgol
            {"name": "Sat Isabgol 50g", "price": 90, "cat": "Digestion", "type": "OTC", "brand": "Dabur"},
            {"name": "Sat Isabgol 100g", "price": 175, "cat": "Digestion", "type": "OTC", "brand": "Dabur"},
            {"name": "Sat Isabgol 200g", "price": 345, "cat": "Digestion", "type": "OTC", "brand": "Dabur"},

            # Baby Care
            {"name": "Little Baby Wipes (30 Wipes)", "price": 49, "cat": "Baby", "type": "Personal Care", "brand": "Little"},
            {"name": "Little Baby Wipes (72 Wipes)", "price": 99, "cat": "Baby", "type": "Personal Care", "brand": "Little"},
            {"name": "Lactogen Pro 1", "price": 450, "cat": "Nutrition", "type": "Baby Food", "brand": "Nestle"},
            {"name": "Lactogen Pro 2", "price": 450, "cat": "Nutrition", "type": "Baby Food", "brand": "Nestle"},
            {"name": "Lactogen Pro 3", "price": 435, "cat": "Nutrition", "type": "Baby Food", "brand": "Nestle"},
            {"name": "Lactogen Pro 4", "price": 435, "cat": "Nutrition", "type": "Baby Food", "brand": "Nestle"},

            # Immunity (Chyawanprash)
            {"name": "Zandu Chyawanprash 450g", "price": 215, "cat": "Immunity", "type": "Ayurveda", "brand": "Zandu"},
            {"name": "Zandu Chyawanprash 900g", "price": 350, "cat": "Immunity", "type": "Ayurveda", "brand": "Zandu"},
            {"name": "Dabur Chyawanprash 250g", "price": 99, "cat": "Immunity", "type": "Ayurveda", "brand": "Dabur"},
            {"name": "Dabur Chyawanprash 500g", "price": 240, "cat": "Immunity", "type": "Ayurveda", "brand": "Dabur"},
            {"name": "Dabur Chyawanprash 1kg", "price": 430, "cat": "Immunity", "type": "Ayurveda", "brand": "Dabur"},
            {"name": "Dabur Chyawanprash Sugar Free 500g", "price": 255, "cat": "Immunity", "type": "Ayurveda", "brand": "Dabur"},
            {"name": "Dabur Chyawanprash Sugar Free 900g", "price": 440, "cat": "Immunity", "type": "Ayurveda", "brand": "Dabur"},

            # Dabur Syrups (Ayurveda)
            {"name": "Dabur Dashmularishta 450ml", "price": 215, "cat": "Ayurveda", "type": "Ayurveda", "brand": "Dabur"},
            {"name": "Dabur Dashmularishta 680ml", "price": 268, "cat": "Ayurveda", "type": "Ayurveda", "brand": "Dabur"},
            {"name": "Dabur Ashokarishta 450ml", "price": 155, "cat": "Ayurveda", "type": "Ayurveda", "brand": "Dabur"},
            {"name": "Dabur Ashokarishta 680ml", "price": 200, "cat": "Ayurveda", "type": "Ayurveda", "brand": "Dabur"},
            {"name": "Dabur Punarnavarishta 450ml", "price": 210, "cat": "Ayurveda", "type": "Ayurveda", "brand": "Dabur"},
            {"name": "Dabur Ashwagandharishta 680ml", "price": 300, "cat": "Ayurveda", "type": "Ayurveda", "brand": "Dabur"},
            {"name": "Dabur Pathyadiarishta 450ml", "price": 192, "cat": "Ayurveda", "type": "Ayurveda", "brand": "Dabur"},
            {"name": "Dabur Lohasava 450ml", "price": 195, "cat": "Ayurveda", "type": "Ayurveda", "brand": "Dabur"},
            {"name": "Dabur Lohasava 680ml", "price": 245, "cat": "Ayurveda", "type": "Ayurveda", "brand": "Dabur"},

            # Baidyanath Syrups
            {"name": "Baidyanath Dashmularishta 680ml", "price": 275, "cat": "Ayurveda", "type": "Ayurveda", "brand": "Baidyanath"},
            {"name": "Baidyanath Abhayarishta 680ml", "price": 255, "cat": "Ayurveda", "type": "Ayurveda", "brand": "Baidyanath"},
            {"name": "Baidyanath Ashokarishta 680ml", "price": 200, "cat": "Ayurveda", "type": "Ayurveda", "brand": "Baidyanath"},
            {"name": "Baidyanath Lohasav 450ml", "price": 198, "cat": "Ayurveda", "type": "Ayurveda", "brand": "Baidyanath"},
            {"name": "Baidyanath Arjunarishta 680ml", "price": 281, "cat": "Ayurveda", "type": "Ayurveda", "brand": "Baidyanath"},

            # Liver & Tablets (Himalaya)
            {"name": "Liv 52 Tablet", "price": 215, "cat": "Liver", "type": "Prescription", "brand": "Himalaya"},
            {"name": "Liv 52 DS Tablet", "price": 300, "cat": "Liver", "type": "Prescription", "brand": "Himalaya"},
            {"name": "Liv 52 Syrup 100ml", "price": 140, "cat": "Liver", "type": "Prescription", "brand": "Himalaya"},
            {"name": "Liv 52 Syrup 200ml", "price": 250, "cat": "Liver", "type": "Prescription", "brand": "Himalaya"},
            {"name": "Liv 52 DS Syrup 100ml", "price": 220, "cat": "Liver", "type": "Prescription", "brand": "Himalaya"},
            {"name": "Liv 52 DS Syrup 200ml", "price": 351, "cat": "Liver", "type": "Prescription", "brand": "Himalaya"},

            # Other Conditions (Himalaya)
            {"name": "Septiline Tablet", "price": 275, "cat": "Tablet", "type": "Prescription", "brand": "Himalaya"},
            {"name": "Septiline Syrup 200ml", "price": 200, "cat": "Syrup", "type": "Prescription", "brand": "Himalaya"},
            {"name": "Pilex Tablet", "price": 250, "cat": "Tablet", "type": "Prescription", "brand": "Himalaya"},
            {"name": "Pilex Forte Ointment 30g", "price": 160, "cat": "Ointment", "type": "Prescription", "brand": "Himalaya"},
            {"name": "Cystone Tablet", "price": 260, "cat": "Tablet", "type": "Prescription", "brand": "Himalaya"},
            {"name": "Cystone Syrup 200ml", "price": 225, "cat": "Syrup", "type": "Prescription", "brand": "Himalaya"},
            {"name": "Evecare Syrup 200ml", "price": 190, "cat": "Syrup", "type": "Prescription", "brand": "Himalaya"},
            {"name": "Gasex Tablet", "price": 200, "cat": "Tablet", "type": "Prescription", "brand": "Himalaya"},
            {"name": "Neeri Syrup 100ml", "price": 164, "cat": "Syrup", "type": "Prescription", "brand": "Himalaya"},
            {"name": "Neeri Syrup 200ml", "price": 313, "cat": "Syrup", "type": "Prescription", "brand": "Himalaya"},

            # Ointments & Powders
            {"name": "Anovate Ointment 20g", "price": 145, "cat": "Ointment", "type": "OTC", "brand": "Generic"}, 
            {"name": "Abzorb Powder", "price": 175, "cat": "Hygiene", "type": "Personal Care", "brand": "Generic"},
            {"name": "Candid Powder 60g", "price": 104, "cat": "Hygiene", "type": "Personal Care", "brand": "Glenmark"},
            {"name": "Candid Powder 120g", "price": 174, "cat": "Hygiene", "type": "Personal Care", "brand": "Glenmark"},
            {"name": "Clocip Powder 75g", "price": 93, "cat": "Hygiene", "type": "Personal Care", "brand": "Cipla"},
            {"name": "Clocip Powder 120g", "price": 168, "cat": "Hygiene", "type": "Personal Care", "brand": "Cipla"},

            # Hygiene
            {"name": "Dettol Liquid 60ml", "price": 41, "cat": "Hygiene", "type": "Personal Care", "brand": "Dettol"},
            {"name": "Dettol Liquid 125ml", "price": 83, "cat": "Hygiene", "type": "Personal Care", "brand": "Dettol"},
            {"name": "Dettol Liquid 250ml", "price": 159, "cat": "Hygiene", "type": "Personal Care", "brand": "Dettol"},
            {"name": "Dettol Liquid 550ml", "price": 267, "cat": "Hygiene", "type": "Personal Care", "brand": "Dettol"},
            {"name": "Dettol Liquid 1L", "price": 485, "cat": "Hygiene", "type": "Personal Care", "brand": "Dettol"},

            # Multivitamins
            {"name": "Maxirich (10 Tablets)", "price": 129, "cat": "Supplement", "type": "Supplements", "brand": "Cipla"}
        ]

        print(f"Starting seed of {len(medicines)} medicines...")
        for m in medicines:
            # 1. Try Specific Manual Image (User Uploaded)
            img = None
            if m['name'] == "Glucon-D Regular 125g":
                img = "/static/images/medicines/glucond_reg125gm.jpg"
            elif m['name'] == "Dabur Honey 100g":
                img = "/static/images/medicines/honey100gm.jpg"

            # 2. Try Specific Brand Logo (If no manual override)
            if not img:
                img = images.get(m.get('brand'), None)
            
            # 3. Key Mapping (Manual Overrides for common brands not in dict)
            if not img:
                if "Baidyanath" in m['name']: img = "https://logo.clearbit.com/baidyanath.co.in"
                elif "Cipla" in m.get('brand', ''): img = "https://logo.clearbit.com/cipla.com"
                elif "Glenmark" in m.get('brand', ''): img = "https://logo.clearbit.com/glenmarkpharma.com"
                elif "Glucon-D" in m['brand']: img = "https://logo.clearbit.com/glucond.com" # Retry generic brand if specific item missed
            
            # 4. Fallback to Category Icon
            if not img:
                img = cat_images.get(m['cat'], "https://i.imgur.com/7X5Xy9C.png")
                img = cat_images.get(m['cat'], "https://i.imgur.com/7X5Xy9C.png")
            
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
