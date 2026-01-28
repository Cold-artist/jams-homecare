
from app import app, db, LabTest

def seed_db():
    with app.app_context():
        # Drop table to force schema update (since we added original_price)
        # Note: This is hacky for dev but works for this task
        try:
            LabTest.__table__.drop(db.engine)
            print("Dropped old LabTest table.")
        except:
            pass

        # Ensure tables exist
        db.create_all()
        
        # Clear existing tests (redundant after drop but safe)
        print("Clearing existing Lab Tests...")

        print("Seeding Max Lab Packages (Haldwani Local Rates)...")
        packages = [
            {
                "name": "Max Care Health Check 1",
                "category": "Health Packages",
                "price": 999,
                "original_price": 1800,
                "description": "Essential full body screening covering 37 Parameters.",
                "components": "• Diabetes: Fasting Blood Sugar\n• Heart/Lipid Profile: Cholesterol, Triglycerides, HDL, LDL, VLDL, Ratios\n• Thyroid: T3, T4, TSH\n• Kidney: Uric Acid\n• Bone: Calcium",
                "significance": "Essential baseline checkup for general wellness.",
                "tat": "24 Hours",
                "sample_type": "Blood"
            },
            {
                "name": "Max Care Health Check 2",
                "category": "Health Packages",
                "price": 1250,
                "original_price": 2400,
                "description": "Comprehensive screening with Liver & Kidney functions (60 Parameters).",
                "components": "• Includes ALL tests in Check 1 PLUS:\n• Diabetes: HbA1c (Average Sugar)\n• Liver Function Test (LFT): Bilirubin, SGOT, SGPT, Alk Phos, Protein, Albumin\n• Kidney Function Test (KFT): Urea, Creatinine\n• Hemogram: CBC, ESR, Platelets",
                "significance": "Recommended for annual screening. Covers all vital organs.",
                "tat": "24 Hours",
                "sample_type": "Blood & Urine"
            },
            {
                "name": "Max Care Health Check 3",
                "category": "Health Packages",
                "price": 2250,
                "original_price": 4100,
                "description": "Advanced profile including Vitamins (62 Parameters).",
                "components": "• Includes ALL tests in Check 2 PLUS:\n• Vitamins: Vitamin D (Total), Vitamin B12\n• Iron Deficiency: Iron Studies",
                "significance": "Detects silent deficiencies (Vit D/B12) causing fatigue and bone issues.",
                "tat": "24-48 Hours",
                "sample_type": "Blood"
            },
             {
                "name": "Max Care Health Check 3 (Couple Pack)",
                "category": "Health Packages",
                "price": 4000,
                "original_price": 8200,
                "description": "1+1 Family Offer for Check 3 (Save ₹500).",
                "components": "• Complete Max Care Health Check 3 for TWO Persons.\n• Includes Vitamins D & B12 for both.",
                "significance": "Best Value: Complete protection for you and your partner.",
                "tat": "24-48 Hours",
                "sample_type": "Blood"
            },
            {
                "name": "Max Care Health Check 4",
                "category": "Health Packages",
                "price": 2700,
                "original_price": 4900,
                "description": "Extensive profile with Inflammation & Urine markers (80 Parameters).",
                "components": "• Includes ALL tests in Check 3 PLUS:\n• Infection/Inflammation: CRP (C-Reactive Protein)\n• Urine: Complete Routine & Microscopy\n• Electrolytes: Sodium, Potassium, Chloride",
                "significance": "Deep screening for infection, inflammation, and metabolic health.",
                "tat": "24-48 Hours",
                "sample_type": "Blood & Urine"
            },
             {
                "name": "Max Care Health Check 4 (Couple Pack)",
                "category": "Health Packages",
                "price": 5000,
                "original_price": 9800,
                "description": "1+1 Family Offer for Check 4 (Save ₹400).",
                "components": "• Complete Max Care Health Check 4 for TWO Persons.",
                "significance": "Comprehensive screening for couples.",
                "tat": "24-48 Hours",
                "sample_type": "Blood & Urine"
            },
            {
                "name": "Max Care Health Check 5",
                "category": "Health Packages",
                "price": 3200,
                "original_price": 6400,
                "description": "Premium Executive Profile with Cardiac & Pancreas markers (94 Parameters).",
                "components": "• Includes ALL tests in Check 4 PLUS:\n• Cardiac Markers: Lp(a), Apo-A1, Apo-B, hs-CRP\n• Pancreas: Amylase, Lipase\n• Arthritis: RA Factor",
                "significance": "The most detailed health audit available. Detailed heart & pancreas insights.",
                "tat": "48 Hours",
                "sample_type": "Blood & Urine"
            },
            {
                "name": "Max Care Health Check 5 (Couple Pack)",
                "category": "Health Packages",
                "price": 6000,
                "original_price": 12800,
                "description": "1+1 Family Offer for Check 5 (Save ₹400).",
                "components": "• Complete Max Care Health Check 5 for TWO Persons.",
                "significance": "Complete peace of mind for you and your partner.",
                "tat": "48 Hours",
                "sample_type": "Blood & Urine"
            }
        ]

        print("Seeding Single Tests (Estimates based on Max Lab standards)...")
        # Standard Single Tests (Prices estimated for Haldwani market)
        single_tests = [
            {"name": "CBC (Complete Blood Count)", "category": "Routine", "price": 350, "description": "Checks Hemoglobin, RBC, WBC, Platelets.", "components": "Hb, TLC, DLC, Platelet Count, RBC indices", "significance": "General health, infection, anemia."},
            {"name": "Thyroid Profile (Total)", "category": "Thyroid", "price": 550, "description": "T3, T4, and TSH levels.", "components": "Total T3, Total T4, TSH", "significance": "Thyroid disorders."},
            {"name": "Lipid Profile", "category": "Heart", "price": 650, "description": "Cholesterol and Triglycerides check.", "components": "Total Cholesterol, Triglycerides, HDL, LDL, VLDL", "significance": "Heart health risk assessment."},
            {"name": "HbA1c", "category": "Diabetes", "price": 500, "description": "Average blood sugar over last 3 months.", "components": "Glycosylated Haemoglobin", "significance": "Diabetes management."},
            {"name": "Liver Function Test (LFT)", "category": "Routine", "price": 850, "description": "Checks liver health.", "components": "Bilirubin, SGOT, SGPT, ALP, Protein", "significance": "Liver damage or disease."},
            {"name": "Kidney Function Test (KFT)", "category": "Routine", "price": 850, "description": "Checks kidney performance.", "components": "Urea, Creatinine, Uric Acid, Electrolytes", "significance": "Kidney health."},
            {"name": "Vitamin D (Total)", "category": "Vitamins", "price": 1000, "description": "Bone health vitamin.", "components": "25-OH Vitamin D", "significance": "Bone weakness, fatigue."},
            {"name": "Vitamin B12", "category": "Vitamins", "price": 1000, "description": "Nerve health vitamin.", "components": "Cyanocobalamin", "significance": "Nerve issues, anemia."},
            {"name": "Urine Routine & Microscopy", "category": "Routine", "price": 200, "description": "Basic urine exam.", "components": "Physical, Chemical, Microscopic", "significance": "UTI, kidney issues."},
            {"name": "Dengue NS1 Antigen", "category": "Fever", "price": 600, "description": "Early dengue detection.", "components": "Dengue NS1", "significance": "Fever diagnosis."},
            {"name": "Typhoid (Widal)", "category": "Fever", "price": 250, "description": "Typhoid fever check.", "components": "Salmonella Typhi Antibodies", "significance": "Fever diagnosis."},
            {"name": "CRP (C-Reactive Protein)", "category": "Heart", "price": 450, "description": "Inflammation marker.", "components": "CRP Quantitative", "significance": "Infection or inflammation body-wide."}
        ]

        all_tests = packages + single_tests

        for t in all_tests:
            test = LabTest(
                name=t['name'],
                category=t['category'],
                price=t['price'],
                original_price=t.get('original_price'), # Handle optional field
                description=t['description'],
                components=t.get('components', ''),
                significance=t.get('significance', ''),
                tat=t.get('tat', '24 Hours'),
                sample_type=t.get('sample_type', 'Blood')
            )
            db.session.add(test)
        
        db.session.commit()
        print("Database seeded successfully!")

if __name__ == "__main__":
    seed_db()
