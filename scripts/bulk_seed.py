#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import execute_batch
import random
import json

# Database connection
conn = psycopg2.connect(
    host="localhost",
    database="medgenomics",
    user="admin",
    password="secure123",
    port=5432
)
cursor = conn.cursor()

FIRST_NAMES = ["James", "Mary", "Robert", "Patricia", "Michael", "Jennifer", "William", "Linda", "David", "Barbara", "Richard", "Elizabeth", "Joseph", "Susan", "Thomas", "Jessica", "Charles", "Sarah", "Christopher", "Karen"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]
CONDITIONS = ["cancer", "diabetes", "atrial_fibrillation", "kidney_failure", "infection", "heart_disease", "stroke", "hypertension", "asthma", "copd", "depression", "anxiety", "pneumonia", "covid"]
MUTATIONS = ["BRCA1", "BRCA2", "TP53", "PTEN", "PALB2", "SCN5A", "KCNQ1", "KCNH2", "RYR2", "DSP"]
ADDRESSES = ["123 Main St", "456 Oak Ave", "789 Elm St", "321 Pine Rd", "654 Maple Dr", "987 Cedar Ln", "147 Birch Way", "258 Spruce St"]
LOCATIONS = ["Main Hospital - Cardiology", "City Medical - Oncology", "County Clinic", "University Hospital - Surgery", "Metro Health - Emergency", "Regional Medical Center", "Veterans Hospital", "Community Health Center"]
TREATMENTS = ["Chemotherapy (Docetaxel)", "Anticoagulation (Warfarin)", "Insulin therapy", "CPAP therapy", "Dialysis (3x weekly)", "Beta-blockers", "ACE inhibitors", "Statins"]

print("Clearing existing data...")
cursor.execute("DELETE FROM patients")
cursor.execute("DELETE FROM inventory")
conn.commit()

print("Generating 10,000 patients...")
patient_data = []
for i in range(10000):
    patient_id = f"pat_{i:07d}"
    name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    conditions = json.dumps(random.sample(CONDITIONS, random.randint(1, 3)))
    genomic_data = json.dumps({
        "age": random.randint(18, 95),
        "gender": random.choice(['M', 'F']),
        "address": random.choice(ADDRESSES),
        "risk_score": random.randint(10, 99),
        "mutations": random.sample(MUTATIONS, random.randint(1, 5)),
        "medical_history": "Previous medical conditions",
        "last_visit": f"2026-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
        "location": random.choice(LOCATIONS),
        "current_treatment": random.choice(TREATMENTS),
        "treatment_status": random.choice(['Active', 'Monitoring', 'Completed']),
        "admission_date": f"2025-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    })
    patient_data.append((patient_id, name, conditions, genomic_data))

# Batch insert patients
cursor.execute("TRUNCATE TABLE patients")
execute_batch(cursor, "INSERT INTO patients (id, name, conditions, genomic_data) VALUES (%s, %s, %s, %s)", patient_data, page_size=1000)
conn.commit()
print(f"✓ Inserted 10,000 patients")

print("Generating 8,000 supplies...")
supply_data = []
for i in range(8000):
    supply_id = f"s_{i:06d}"
    item_name = f"Supply Item {i}"
    category = random.choice(['Medications', 'Diagnostics', 'Equipment', 'Supplies', 'PPE'])
    qty_on_hand = random.randint(5, 500)
    reorder_point = random.randint(10, 100)
    cost = round(random.uniform(10, 10000), 2)
    location = random.choice(LOCATIONS)
    supplier = f"Supplier-{random.randint(1, 100)}"
    supply_data.append((supply_id, item_name, category, qty_on_hand, reorder_point, cost, location, supplier))

# Batch insert supplies
cursor.execute("TRUNCATE TABLE inventory")
execute_batch(cursor, "INSERT INTO inventory (id, item_name, category, qty_on_hand, reorder_point, cost, location, supplier) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", supply_data, page_size=1000)
conn.commit()
print(f"✓ Inserted 8,000 supplies")

cursor.close()
conn.close()
print("\n✅ Database seeding complete!")
print(f"Total: 10,000 patients + 8,000 supplies")
