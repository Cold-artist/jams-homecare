
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
            # Blood Sugar Tests
            {"name": "Fasting Blood Sugar", "category": "Diabetes", "price": 50, "description": "Measures blood glucose after fasting.", "components": "Glucose (Fasting)", "significance": "Diabetes screening."},
            {"name": "Post Prandial Blood Sugar (2 Hours)", "category": "Diabetes", "price": 50, "description": "Measures blood glucose 2 hours after a meal.", "components": "Glucose (PP)", "significance": "Diabetes management."},
            {"name": "Random Blood Sugar", "category": "Diabetes", "price": 50, "description": "Measures blood glucose at any time.", "components": "Glucose (Random)", "significance": "Quick diabetes check."},
            {"name": "HbA1c", "category": "Diabetes", "price": 450, "description": "Average blood sugar over the last 3 months.", "components": "Glycosylated Haemoglobin", "significance": "Long-term diabetes control."},

            # Liver Function Related
            {"name": "Bilirubin (Total / Direct / Indirect)", "category": "Liver", "price": 170, "description": "Checks for jaundice and liver issues.", "components": "Total, Direct, Indirect Bilirubin", "significance": "Liver health."},
            {"name": "SGOT (AST)", "category": "Liver", "price": 120, "description": "Liver enzyme test.", "components": "Aspartate Aminotransferase", "significance": "Liver damage."},
            {"name": "SGPT (ALT)", "category": "Liver", "price": 120, "description": "Liver enzyme test.", "components": "Alanine Aminotransferase", "significance": "Liver damage."},
            {"name": "Liver Function Test (LFT)", "category": "Liver", "price": 650, "description": "Complete liver health check.", "components": "Bilirubin, SGOT, SGPT, ALP, Protein, Albumin", "significance": "Comprehensive liver assessment."},
            {"name": "Total Protein Test", "category": "Liver", "price": 170, "description": "Measures proteins in blood.", "components": "Total Protein, Albumin, Globulin", "significance": "Nutritional status, liver/kidney health."},

            # Kidney Function Related
            {"name": "Urea Test", "category": "Kidney", "price": 140, "description": "Measures waste product in blood.", "components": "Blood Urea Nitrogen", "significance": "Kidney function."},
            {"name": "Creatinine Test", "category": "Kidney", "price": 110, "description": "Key marker for kidney health.", "components": "Serum Creatinine", "significance": "Kidney function."},
            {"name": "Kidney Function Test (KFT)", "category": "Kidney", "price": 750, "description": "Complete kidney health check.", "components": "Urea, Creatinine, Uric Acid, Electrolytes", "significance": "Comprehensive kidney assessment."},
            {"name": "PCR (Protein Creatinine Ratio)", "category": "Kidney", "price": 500, "description": "Urine test for protein.", "components": "Protein, Creatinine Ratio", "significance": "Kidney damage, diabetes complication."},

            # Urine Tests
            {"name": "Urine Routine & Microscopy (Urine R/M)", "category": "Urine", "price": 100, "description": "Basic urine examination.", "components": "Physical, Chemical, Microscopic analysis", "significance": "UTI, kidney disease, diabetes."},
            {"name": "Urine Culture", "category": "Urine", "price": 450, "description": "Detects bacteria in urine.", "components": "Bacterial Culture & Sensitivity", "significance": "Urinary Tract Infection (UTI)."},

            # Complete Blood & Basic Tests
            {"name": "Complete Blood Count (CBC)", "category": "Routine", "price": 200, "description": "Overall health check.", "components": "Hb, TLC, DLC, Platelets, RBC indices", "significance": "Anemia, infection, leukemia."},
            {"name": "Haemoglobin", "category": "Routine", "price": 70, "description": "Measures oxygen-carrying protein.", "components": "Hb", "significance": "Anemia."},
            {"name": "Platelet Count", "category": "Routine", "price": 100, "description": "Essential for blood clotting.", "components": "Platelet Count", "significance": "Dengue, bleeding disorders."},
            {"name": "ESR", "category": "Routine", "price": 70, "description": "Inflammation marker.", "components": "Erythrocyte Sedimentation Rate", "significance": "Infection, inflammation."},
            {"name": "Blood Group", "category": "Routine", "price": 80, "description": "Identifies blood type.", "components": "ABO & Rh Typing", "significance": "Emergency, pregnancy."},

            # Thyroid Tests
            {"name": "Thyroid Function Test (TFT – T3, T4, TSH)", "category": "Thyroid", "price": 490, "description": "Complete thyroid check.", "components": "Total T3, Total T4, TSH", "significance": "Thyroid disorders."},
            {"name": "TSH", "category": "Thyroid", "price": 220, "description": "Thyroid Stimulating Hormone.", "components": "TSH", "significance": "Thyroid screening."},

            # Lipid & Cholesterol
            {"name": "Lipid Profile", "category": "Heart", "price": 400, "description": "Cholesterol and fat levels.", "components": "Cholesterol, Triglycerides, HDL, LDL, VLDL", "significance": "Heart disease risk."},
            {"name": "Total Cholesterol", "category": "Heart", "price": 110, "description": "Total measuring of cholesterol.", "components": "Total Cholesterol", "significance": "Heart health."},

            # Electrolytes
            {"name": "Sodium Test", "category": "Electrolytes", "price": 170, "description": "Electrolyte balance.", "components": "Serum Sodium", "significance": "Dehydration, nerve function."},
            {"name": "Potassium Test", "category": "Electrolytes", "price": 170, "description": "Electrolyte balance.", "components": "Serum Potassium", "significance": "Heart and muscle function."},

            # Infection & Inflammation
            {"name": "CRP (C-Reactive Protein)", "category": "Infection", "price": 420, "description": "Inflammation marker.", "components": "CRP Quantitative", "significance": "Infection, inflammation."},
            {"name": "Widal", "category": "Fever", "price": 130, "description": "Typhoid screening.", "components": "Salmonella Antibodies", "significance": "Typhoid fever."},
            {"name": "Typhi Dot (IgM / IgG)", "category": "Fever", "price": 800, "description": "Rapid typhoid test.", "components": "IgM & IgG Antibodies", "significance": "Typhoid fever."},

            # Male Health
            {"name": "PSA Test", "category": "Male Health", "price": 800, "description": "Prostate screening.", "components": "Prostate Specific Antigen", "significance": "Prostate health."},

            # Pancreas Tests
            {"name": "Amylase Test", "category": "Pancreas", "price": 390, "description": "Pancreatic enzyme.", "components": "Serum Amylase", "significance": "Pancreatitis."},
            {"name": "Lipase Test", "category": "Pancreas", "price": 350, "description": "Pancreatic enzyme.", "components": "Serum Lipase", "significance": "Pancreatitis."},

            # Vitamins & Minerals
            {"name": "Vitamin B12", "category": "Vitamins", "price": 1200, "description": "Nerve health vitamin.", "components": "Cyanocobalamin", "significance": "Nerve health, anemia."},
            {"name": "Vitamin D", "category": "Vitamins", "price": 1200, "description": "Bone health vitamin.", "components": "25-OH Vitamin D", "significance": "Bone health, immunity."},
            {"name": "Iron", "category": "Vitamins", "price": 500, "description": "Iron levels.", "components": "Serum Iron", "significance": "Anemia."},
            {"name": "Calcium", "category": "Vitamins", "price": 130, "description": "Bone mineral.", "components": "Serum Calcium", "significance": "Bone health."},
            {"name": "Uric Acid Test", "category": "Kidney", "price": 110, "description": "Joint health / Kidney.", "components": "Serum Uric Acid", "significance": "Gout, kidney stones."}
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
