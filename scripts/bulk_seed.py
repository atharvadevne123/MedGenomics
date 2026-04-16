#!/usr/bin/env python3
"""
Bulk seed script — inserts 10,000 patients and 8,000 supply items.

Usage:
    DB_HOST=localhost DB_PASSWORD=yourpassword python scripts/bulk_seed.py

Credentials are read from environment variables; no secrets are hardcoded.
"""
import os
import random
import json
import psycopg2
from psycopg2.extras import execute_batch

# ── Connection (read credentials from environment) ────────────────────────────
conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    database=os.getenv("DB_NAME", "medgenomics"),
    user=os.getenv("DB_USER", "admin"),
    password=os.getenv("DB_PASSWORD"),   # required — no default
    port=int(os.getenv("DB_PORT", "5432")),
)
cursor = conn.cursor()

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "Michael", "Jennifer",
    "William", "Linda", "David", "Barbara", "Richard", "Elizabeth",
    "Joseph", "Susan", "Thomas", "Jessica", "Charles", "Sarah",
    "Christopher", "Karen",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
    "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez",
    "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore",
    "Jackson", "Martin",
]
CONDITIONS = [
    "cancer", "diabetes", "atrial_fibrillation", "kidney_failure",
    "infection", "heart_disease", "stroke", "hypertension",
    "asthma", "copd", "depression", "anxiety", "pneumonia", "covid",
]
MUTATIONS = ["BRCA1", "BRCA2", "TP53", "PTEN", "PALB2", "SCN5A", "KCNQ1", "KCNH2", "RYR2", "DSP"]
DNA_MARKERS = ["A+1", "A+2", "B-14", "C+1", "TP53-M", "APOE4", "MTHFR-V"]
LOCATIONS = [
    "Main Hospital - Cardiology", "City Medical - Oncology", "County Clinic",
    "University Hospital - Surgery", "Metro Health - Emergency",
    "Regional Medical Center", "Veterans Hospital", "Community Health Center",
]
TREATMENTS = [
    "Chemotherapy (Docetaxel)", "Anticoagulation (Warfarin)", "Insulin therapy",
    "CPAP therapy", "Dialysis (3x weekly)", "Beta-blockers", "ACE inhibitors", "Statins",
]

# ── Truncate tables safely — wrapped in try/except so the script does not ─────
# crash when run before the application has started and created the schema.
print("Clearing existing data...")
try:
    cursor.execute("TRUNCATE TABLE patients CASCADE")
    cursor.execute("TRUNCATE TABLE inventory CASCADE")
    conn.commit()
except Exception as e:
    conn.rollback()
    print(f"Warning: Could not truncate tables ({e}). Attempting DELETE instead.")
    try:
        cursor.execute("DELETE FROM patients")
        cursor.execute("DELETE FROM inventory")
        conn.commit()
    except Exception as e2:
        conn.rollback()
        print(f"Error: Could not clear tables: {e2}")
        cursor.close()
        conn.close()
        raise SystemExit(1)

# ── Generate 10,000 patients ──────────────────────────────────────────────────
print("Generating 10,000 patients...")
patient_data = []
for i in range(10000):
    patient_id = f"pat_{i:07d}"
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    name = f"{first} {last}"
    initials = f"{first[0]}{last[0]}"
    age = random.randint(18, 95)
    risk_score = round(random.uniform(5.0, 99.0), 1)
    dna_marker = random.choice(DNA_MARKERS)
    conditions = json.dumps({c: True for c in random.sample(CONDITIONS, random.randint(1, 3))})
    genomic_data = json.dumps({
        "mutations": random.sample(MUTATIONS, random.randint(1, 5)),
        "expression_level": random.choice(["low", "moderate", "high"]),
        "last_visit": f"2026-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
        "location": random.choice(LOCATIONS),
        "current_treatment": random.choice(TREATMENTS),
        "treatment_status": random.choice(["Active", "Monitoring", "Completed"]),
    })
    patient_data.append((patient_id, name, age, risk_score, dna_marker, initials, conditions, genomic_data))

execute_batch(
    cursor,
    """
    INSERT INTO patients (id, name, age, risk_score, dna_marker, initials, conditions, genomic_data)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """,
    patient_data,
    page_size=1000,
)
conn.commit()
print(f"  Inserted {len(patient_data):,} patients")

# ── Generate 8,000 supply items ───────────────────────────────────────────────
print("Generating 8,000 supply items...")
CATEGORIES = ["Medications", "Diagnostics", "Equipment", "Supplies", "PPE"]
supply_data = []
for i in range(8000):
    supply_id = f"s_{i:06d}"
    item_name = f"Supply Item {i}"
    category = random.choice(CATEGORIES)
    qty_on_hand = random.randint(5, 500)
    reorder_point = random.randint(10, 100)
    cost = round(random.uniform(10.0, 10000.0), 2)
    location = random.choice(LOCATIONS)
    supplier = f"Supplier-{random.randint(1, 100)}"
    supply_data.append((supply_id, item_name, category, qty_on_hand, reorder_point, cost, location, supplier))

execute_batch(
    cursor,
    """
    INSERT INTO inventory (id, item_name, category, qty_on_hand, reorder_point, cost, location, supplier)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """,
    supply_data,
    page_size=1000,
)
conn.commit()
print(f"  Inserted {len(supply_data):,} supply items")

cursor.close()
conn.close()
print("\nDatabase seeding complete!")
print(f"Total: {len(patient_data):,} patients + {len(supply_data):,} supplies")
