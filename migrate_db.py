import sqlite3
import os

db_path = r'c:\Users\shubh\Documents\homehealthcare\instance\homehealthcare_v2.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Try adding columns to booking
try:
    c.execute("ALTER TABLE booking ADD COLUMN patient_id INTEGER")
    print("Added patient_id to booking")
except Exception as e:
    print(f"Skipping patient_id: {e}")

try:
    c.execute("ALTER TABLE booking ADD COLUMN staff_id INTEGER")
    print("Added staff_id to booking")
except Exception as e:
    print(f"Skipping staff_id: {e}")

conn.commit()
conn.close()
