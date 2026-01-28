
import os
from app import app, db, LabTest

def populate_lab_data():
    with app.app_context():
        # Create table if not exists
        db.create_all()
        
        # Clear existing data to ensure clean state
        try:
            db.session.query(LabTest).delete()
            db.session.commit()
            print("Cleared existing Lab Tests.")
        except Exception as e:
            print(f"Error clearing tests: {e}")

        print("Populating Lab Tests...")
        
        tests = [
             # --- MAX CARE HEALTH KITS (Smart Categorized) ---
            {
                "name": "Max Care Health Kit 1",
                "category": "Health Packages",
                "price": 999,
                "original_price": 2970,
                "description": "Essential metabolic screening.",
                "components": "Diabetes: Fasting Blood Sugar • Heart Health: Lipid Profile (Cholesterol, Triglycerides, HDL, LDL, VLDL) • Liver Function: LFT (Bilirubin, SGOT, SGPT, Alk Phos, Protein, Albumin) • Kidney Function: KFT (Urea, Creatinine, Uric Acid, Sodium, Potassium) • Iron Profile: Serum Iron Study",
                "significance": "Basic annual screening for vital organ health.",
                "tat": "24 Hours",
                "sample_type": "Blood"
            },
            {
                "name": "Max Care Health Kit 2",
                "category": "Health Packages",
                "price": 1250,
                "original_price": 3620,
                "description": "Comprehensive metabolic & hormonal check.",
                "components": "Includes Kit 1 Tests + HbA1c (3-Month Avg Sugar) • Thyroid Profile: T3, T4, TSH • Complete Blood Count: Hb, RBC, WBC, Platelets, Indices • Urine Analysis: Routine & Microscopy",
                "significance": "Recommended for full body monitoring including diabetes and thyroid.",
                "tat": "24 Hours",
                "sample_type": "Blood & Urine"
            },
            {
                "name": "Max Care Health Kit 3",
                "category": "Health Packages",
                "price": 2250,
                "original_price": 4620,
                "description": "Advanced profile with Vitamin deficiency check.",
                "components": "Includes Kit 2 Tests + Vitamin Deficiency Check: Vitamin D (Total) & Vitamin B12 • Full Metabolic Screening",
                "significance": "Ideal for fatigue/weakness issues + complete metabolic health.",
                "tat": "24 Hours",
                "sample_type": "Blood & Urine"
            },
            {
                "name": "Max Care Health Kit 4",
                "category": "Health Packages",
                "price": 2700,
                "original_price": 6540,
                "description": "Premium profile including Bone & Arthritis markers.",
                "components": "Includes Kit 3 Tests + Bone & Joints: Calcium, Phosphorus, RA Factor (Rheumatoid), CRP • Inflammation Check: C-Reactive Protein (CRP)",
                "significance": "Complete elderly or adult care focused on bones and joints.",
                "tat": "24 Hours",
                "sample_type": "Blood & Urine"
            },
            {
                "name": "Max Care Health Kit 5",
                "category": "Health Packages",
                "price": 3200,
                "original_price": 9660,
                "description": "Ultimate full-body executive screening.",
                "components": "Includes Kit 4 Tests + Cardiac Risk: Homocysteine, Lipoprotein-A, hs-CRP • Allergy Check: Total IgE Antibody • Electrolytes: Sodium, Potassium, Chloride",
                "significance": "Our most exhaustive package for detailed health analysis.",
                "tat": "24-48 Hours",
                "sample_type": "Blood & Urine"
            },

            # --- INDIVIDUAL TESTS (Max Lab Menu) ---
            
            # 1. Diabetes
            {
                "name": "HbA1c (Glycosylated Hemoglobin)",
                "category": "Diabetes",
                "price": 550,
                "description": "Average blood sugar level over past 3 months.",
                "components": "HbA1c Level, Mean Plasma Glucose.",
                "significance": "Gold standard for diagnosing and monitoring diabetes.",
                "tat": "6 Hours",
                "sample_type": "Blood"
            },
            {
                "name": "Fasting Blood Sugar (FBS)",
                "category": "Diabetes",
                "price": 150,
                "description": "Glucose level after 8-10 hours fasting.",
                "components": "Glucose (Plasma/Serum).",
                "significance": "Screening for pre-diabetes and diabetes.",
                "tat": "4 Hours",
                "sample_type": "Blood"
            },

            # 2. Thyroid
            {
                "name": "Thyroid Profile (Total T3, T4, TSH)",
                "category": "Thyroid",
                "price": 550,
                "description": "Complete assessment of thyroid hormone levels.",
                "components": "Triiodothyronine (T3), Thyroxine (T4), TSH.",
                "significance": "Diagnose hypothyroidism (weight gain) or hyperthyroidism.",
                "tat": "8 Hours",
                "sample_type": "Blood"
            },
             {
                "name": "TSH (Thyroid Stimulating Hormone)",
                "category": "Thyroid",
                "price": 300,
                "description": "Single parameter thyroid screen.",
                "components": "TSH Ultrasensitive.",
                "significance": "Primary screening test to check thyroid function.",
                "tat": "6 Hours",
                "sample_type": "Blood"
            },

            # 3. Heart & Lipid
            {
                "name": "Lipid Profile",
                "category": "Heart",
                "price": 650,
                "description": "Cholesterol analysis for heart health.",
                "components": "Total Cholesterol, Triglycerides, HDL, LDL, VLDL.",
                "significance": "Evaluate risk of coronary artery disease and stroke.",
                "tat": "12 Hours",
                "sample_type": "Blood"
            },

            # 4. Fever
             {
                "name": "Complete Blood Count (CBC)",
                "category": "Fever",
                "price": 350,
                "description": "General health check of blood cells.",
                "components": "Hb, RBC, WBC, Platelets, MCV, MCH, MCHC.",
                "significance": "Indicators of infection, anemia, and general health.",
                "tat": "4 Hours",
                "sample_type": "Blood"
            },
             {
                "name": "Dengue NS1 Antigen",
                "category": "Fever",
                "price": 850,
                "description": "Early detection of dengue virus.",
                "components": "Dengue NS1 (ELISA/Rapid).",
                "significance": "Detects acute dengue infection within first 5 days.",
                "tat": "4-6 Hours",
                "sample_type": "Blood"
            },
             {
                "name": "Typhoid IgG/IgM (Rapid)",
                "category": "Fever",
                "price": 450,
                "description": "Rapid typhoid screening.",
                "components": "Salmonella Typhi Antibodies.",
                "significance": "Diagnosis of typhoid (enteric) fever.",
                "tat": "2 Hours",
                "sample_type": "Blood"
            },
             {
                "name": "MP Slide/Card (Malaria)",
                "category": "Fever",
                "price": 250,
                "description": "Detection of malarial parasite.",
                "components": "Plasmodium vivax/falciparum.",
                "significance": "Confirms malaria infection.",
                "tat": "4 Hours",
                "sample_type": "Blood"
            },

            # 5. Routine / Organ Function
             {
                "name": "Liver Function Test (LFT)",
                "category": "Routine",
                "price": 800,
                "description": "State of liver health.",
                "components": "Bilirubin, SGOT (AST), SGPT (ALT), Alk Phos, Protein.",
                "significance": "Screening for jaundice, liver damage, and alcohol effects.",
                "tat": "12 Hours",
                "sample_type": "Blood"
            },
             {
                "name": "Kidney Function Test (KFT)",
                "category": "Routine",
                "price": 800,
                "description": "Evaluation of kidney efficiency.",
                "components": "Urea, Creatinine, Uric Acid, Sodium, Potassium.",
                "significance": "Detects kidney markers and electrolyte balance.",
                "tat": "12 Hours",
                "sample_type": "Blood"
            },
            {
                "name": "Urine Routine & Microscopy",
                "category": "Routine",
                "price": 200,
                "description": "Basic urine examination.",
                "components": "pH, Sugar, Protein, Pus Cells, RBCs, Crystals.",
                "significance": "UTI, diabetes, and kidney stones screening.",
                "tat": "4 Hours",
                "sample_type": "Urine"
            },

            # 6. Vitamins
            {
                "name": "Vitamin D (25-OH)",
                "category": "Vitamins",
                "price": 1250,
                "description": "Bone health vitamin.",
                "components": "Total 25-Hydroxy Vitamin D.",
                "significance": "Crucial for bone strength and immunity.",
                "tat": "24 Hours",
                "sample_type": "Blood"
            },
            {
                "name": "Vitamin B12",
                "category": "Vitamins",
                "price": 1100,
                "description": "Nerve health vitamin.",
                "components": "Serum Vitamin B12.",
                "significance": "Prevents nerve damage and anemia.",
                "tat": "24 Hours",
                "sample_type": "Blood"
            },

            # 7. Women
            {
                "name": "Beta HCG (Total)",
                "category": "Women",
                "price": 750,
                "description": "Pregnancy confirmation.",
                "components": "Beta Human Chorionic Gonadotropin.",
                "significance": "Confirms pregnancy.",
                "tat": "6 Hours",
                "sample_type": "Blood"
            },
            {
                "name": "Prolactin",
                "category": "Women",
                "price": 600,
                "description": "Hormone test for menstrual health.",
                "components": "Serum Prolactin.",
                "significance": "Evaluates menstrual irregularity and infertility.",
                "tat": "24 Hours",
                "sample_type": "Blood"
            }
        ]
        
        for t in tests:
            test = LabTest(**t)
            db.session.add(test)
        
        db.session.commit()
        print(f"Successfully added {len(tests)} lab tests.")

if __name__ == "__main__":
    populate_lab_data()
