#!/usr/bin/env python3
"""
Bulk seed script — inserts 5,000 patients and 3,000 inventory items.

Works with both SQLite (local dev) and PostgreSQL (production).
Reads DATABASE_URL from environment; defaults to the local SQLite file.

Usage:
    python scripts/bulk_seed.py
    DATABASE_URL=postgresql://user:pass@host/db python scripts/bulk_seed.py
"""
import datetime
import json
import os
import random
import sys
from pathlib import Path

# Allow running from any directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./medgenomics.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)
Session = sessionmaker(bind=engine)

# ── Reference data ─────────────────────────────────────────────────────────────

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "Michael", "Jennifer", "William", "Linda",
    "David", "Barbara", "Richard", "Elizabeth", "Joseph", "Susan", "Thomas", "Jessica",
    "Charles", "Sarah", "Christopher", "Karen", "Daniel", "Lisa", "Matthew", "Nancy",
    "Anthony", "Betty", "Mark", "Margaret", "Donald", "Sandra", "Steven", "Ashley",
    "Paul", "Dorothy", "Andrew", "Kimberly", "Joshua", "Emily", "Kevin", "Donna",
    "Brian", "Michelle", "George", "Carol", "Timothy", "Amanda", "Ronald", "Melissa",
    "Edward", "Deborah", "Jason", "Stephanie", "Jeffrey", "Rebecca", "Ryan", "Sharon",
    "Jacob", "Laura", "Gary", "Cynthia", "Nicholas", "Kathleen", "Eric", "Amy",
    "Jonathan", "Angela", "Stephen", "Shirley", "Larry", "Anna", "Justin", "Brenda",
    "Scott", "Pamela", "Brandon", "Emma", "Benjamin", "Nicole", "Samuel", "Helen",
    "Aiden", "Sofia", "Lucas", "Isabella", "Mason", "Mia", "Ethan", "Ava",
    "Noah", "Olivia", "Liam", "Charlotte", "Logan", "Amelia", "Oliver", "Harper",
    "Riya", "Priya", "Arjun", "Vikram", "Ananya", "Rahul", "Neha", "Aditya",
    "Yuki", "Hiroshi", "Mei", "Wei", "Fatima", "Hassan", "Layla", "Omar",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill",
    "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell",
    "Mitchell", "Carter", "Roberts", "Patel", "Shah", "Kumar", "Singh", "Chen",
    "Wang", "Li", "Zhang", "Liu", "Yang", "Huang", "Kim", "Park", "Choi",
    "Tanaka", "Watanabe", "Suzuki", "Sato", "Ahmed", "Ali", "Hassan", "Khan",
    "Okonkwo", "Adeyemi", "Mensah", "Diallo", "Mbeki", "Nkosi", "Osei", "Boateng",
    "Mueller", "Schmidt", "Fischer", "Weber", "Kowalski", "Novak", "Kovac", "Popov",
    "Costa", "Ferreira", "Silva", "Santos", "Oliveira", "Souza", "Carvalho",
]

CONDITIONS_LIST = [
    "Type 1 Diabetes", "Type 2 Diabetes", "Hypercholesterolemia", "Hypertension",
    "Cardiovascular Risk", "Atrial Fibrillation", "Heart Failure", "Coronary Artery Disease",
    "Familial Cancer Syndrome", "Breast Cancer Risk", "Colorectal Cancer Risk", "Lung Cancer",
    "BRCA Mutation Carrier", "Lynch Syndrome", "Li-Fraumeni Syndrome",
    "Chronic Kidney Disease", "Polycystic Kidney Disease",
    "Asthma", "COPD", "Cystic Fibrosis",
    "Alzheimer Risk", "Parkinson Risk", "Huntington Disease",
    "Sickle Cell Trait", "Hemophilia A", "Thalassemia",
    "Celiac Disease", "Crohn Disease", "Ulcerative Colitis",
    "Rheumatoid Arthritis", "Lupus", "Multiple Sclerosis",
    "Obesity Risk", "Metabolic Syndrome", "Hyperthyroidism",
    "Asymptomatic", "Under Observation",
]

GENES = ["BRCA1", "BRCA2", "TP53", "PTEN", "PALB2", "ATM", "CHEK2", "RAD51C",
         "APOE", "APOB", "MTHFR", "SCN5A", "KCNQ1", "KCNH2", "RYR2", "DSP",
         "MLH1", "MSH2", "MSH6", "PMS2", "EPCAM", "APC", "MUTYH",
         "CFTR", "HBB", "F8", "F9", "SMN1", "DMD", "FMR1",
         "LRRK2", "SNCA", "GBA", "PINK1", "PARK7", "APP", "PSEN1", "PSEN2",
         "VHL", "MEN1", "RET", "NF1", "NF2", "TSC1", "TSC2",
         "SLC2A1", "GAA", "GBA1", "HEXA", "HEXB"]

EXPRESSION_LEVELS = ["low", "moderate", "high", "very high", "suppressed"]
TREATMENT_STATUSES = ["Active", "Monitoring", "Completed", "Pending Review", "On Hold"]
TREATMENTS = [
    "Chemotherapy (Docetaxel)", "Anticoagulation (Warfarin)", "Insulin therapy",
    "CPAP therapy", "Dialysis (3x weekly)", "Beta-blockers", "ACE inhibitors",
    "Statins (Atorvastatin)", "Immunotherapy (Pembrolizumab)", "PARP Inhibitors",
    "Targeted Therapy (Imatinib)", "Hormone Therapy (Tamoxifen)", "CRISPR Gene Therapy",
    "Bone Marrow Transplant", "Genetic Counseling", "Watchful Waiting",
    "Aspirin (low-dose)", "Metformin", "Prophylactic Mastectomy Evaluation",
    "Colonoscopy Surveillance", "Annual MRI", "Echocardiography", "Holter Monitor",
]
DNA_MARKERS = ["A+1", "A+2", "A-3", "B+1", "B-14", "B+7", "C+1", "C-2", "C+5",
               "D+2", "D-8", "E+3", "TP53-M", "APOE4", "MTHFR-V", "BRCA1-del",
               "BRCA2-ins", "MLH1-sv", "MSH2-fs", "RYR2-ms", "SCN5A-ns"]

HOSPITAL_LOCATIONS = [
    "Main Hospital - Oncology", "City Medical Center - Cardiology",
    "University Hospital - Genetics", "Regional Medical Center - Hematology",
    "Community Health - Internal Medicine", "Veterans Hospital - Neurology",
    "Metro Health - Endocrinology", "Children's Hospital - Pediatric Genetics",
    "Cancer Center - Surgical Oncology", "Research Institute - Clinical Trials",
]

# ── Inventory reference data ───────────────────────────────────────────────────

REAGENT_NAMES = [
    "TaqPath qPCR Master Mix", "SYBR Green Dye", "Proteinase K Solution",
    "RNase A Solution", "DNase I (RNase-Free)", "T4 DNA Ligase",
    "Klenow Fragment", "Phi29 DNA Polymerase", "Q5 High-Fidelity DNA Polymerase",
    "KAPA HiFi HotStart ReadyMix", "NEBNext Ultra II DNA Library Prep Kit",
    "Qubit dsDNA BR Assay Kit", "Qubit dsDNA HS Assay Kit",
    "Agilent High Sensitivity DNA Kit", "Bioanalyzer RNA 6000 Nano Kit",
    "RNeasy Mini Kit", "QIAamp DNA Mini Kit", "DNeasy Blood & Tissue Kit",
    "Maxwell RSC Blood DNA Kit", "PureLink Genomic DNA Mini Kit",
    "SPRI Select Reagent", "AMPure XP Beads", "Dynabeads MyOne Streptavidin",
    "Ethanol 70% Clinical Grade", "Ethanol 100% Molecular Grade",
    "Nuclease-Free Water", "TE Buffer (10mM Tris, 1mM EDTA)",
    "TBE Buffer (10x)", "TAE Buffer (50x)", "PBS Buffer (10x)",
    "Tris-HCl pH 8.0", "EDTA Disodium Salt", "Sodium Chloride Solution",
    "Agarose (molecular biology grade)", "GelRed Nucleic Acid Stain",
    "Loading Dye (6x)", "DNA Ladder (1 kb)", "RNA Ladder",
    "Bradford Protein Assay Reagent", "BCA Protein Assay Kit",
    "ELISA Substrate (TMB)", "Streptavidin-HRP Conjugate",
    "Formaldehyde Solution 37%", "Xylene (ACS grade)", "Hematoxylin Solution",
    "Eosin Y Solution", "Permount Mounting Medium", "Paraffin Wax",
]

KIT_NAMES = [
    "NovaSeq 6000 S4 Reagent Kit (300 cycles)", "NovaSeq 6000 S2 Reagent Kit (200 cycles)",
    "NextSeq 550 High Output Kit v2.5 (75 cycles)", "NextSeq 550 Mid Output Kit v2.5",
    "MiSeq Reagent Kit v3 (600 cycles)", "MiSeq Reagent Kit v2 (300 cycles)",
    "Exome Enrichment Kit v2", "TruSeq DNA PCR-Free Library Prep Kit",
    "TruSeq Stranded mRNA Library Prep Kit", "TruSeq Stranded Total RNA Kit",
    "Chromium Next GEM Single Cell 3' Kit v3.1", "Chromium Next GEM ATAC Kit v2",
    "Oxford Nanopore Ligation Sequencing Kit V14", "Oxford Nanopore Rapid Sequencing Kit v2",
    "PacBio SMRTbell Prep Kit 3.0", "PacBio Sequel II Sequencing Kit 2.0",
    "Ion AmpliSeq Cancer Hotspot Panel v2", "Ion AmpliSeq Comprehensive Cancer Panel",
    "QIAGEN ClinCNV Panel", "Agilent SureSelect Clinical Research Exome v2",
    "BRCA1/BRCA2 MASTR Plus Dx", "Hereditary Cancer MASTR Plus Dx",
    "FoundationOne CDx Kit", "Guardant360 CDx Liquid Biopsy Kit",
    "SureSelect Human All Exon V8", "Twist Human Core Exome Kit",
    "CRISPR-Cas9 Nucleofection Kit", "Edit-R CRISPR-Cas9 Synthetic gRNA",
    "Lipofectamine CRISPRMAX Transfection Kit", "T7E1 Assay Kit",
    "Biofire FilmArray Respiratory Panel", "Biofire Blood Culture ID Panel",
    "cobas SARS-CoV-2 & Influenza A/B Test", "Xpert Xpress SARS-CoV-2 Test",
    "LAMP-Based COVID-19 Detection Kit", "ddPCR Mutation Detection Kit",
]

EQUIPMENT_NAMES = [
    "96-Well Microplate (flat-bottom, clear)", "96-Well Microplate (V-bottom)",
    "384-Well Microplate (low-volume)", "8-Strip PCR Tubes with Caps",
    "0.2 mL PCR Tubes (individual)", "1.5 mL Microcentrifuge Tubes",
    "2.0 mL Microcentrifuge Tubes", "15 mL Conical Tubes",
    "50 mL Conical Tubes", "Flow Cytometry Tubes (5 mL)",
    "10 µL Pipette Tips (filter)", "20 µL Pipette Tips (filter)",
    "200 µL Pipette Tips (filter)", "1000 µL Pipette Tips (filter)",
    "10 µL Pipette Tips (standard)", "200 µL Pipette Tips (standard)",
    "1000 µL Pipette Tips (standard)", "Multichannel Pipette Tips (300 µL)",
    "Gel Electrophoresis Cassettes (E-Gel 2% EX)", "Nitrocellulose Membrane (0.45 µm)",
    "PVDF Membrane (0.2 µm)", "Whatman Filter Paper No. 1",
    "Parafilm M (4 in × 250 ft)", "Cryogenic Vials (2 mL)",
    "CryoPure Tubes with O-Ring (1.8 mL)", "Cell Culture Flask T-25",
    "Cell Culture Flask T-75", "Cell Culture Flask T-175",
    "96-Well Cell Culture Plate", "Serological Pipettes (10 mL)",
    "Serological Pipettes (25 mL)", "Syringe Filter 0.22 µm",
    "Syringe Filter 0.45 µm", "Magnetic Separation Rack (8-tube)",
    "Nucleospin Column (silica membrane)", "Spin Column (cellulose acetate)",
    "Slide Mailer (polypropylene)", "Microscope Slides (frosted end)",
    "Coverslips (18×18 mm, #1.5)", "Hybridization Bags",
]

CONSUMABLE_NAMES = [
    "Nitrile Gloves (Medium)", "Nitrile Gloves (Large)", "Nitrile Gloves (Small)",
    "Latex-Free Exam Gloves (Medium)", "Lab Coat (Size M)", "Lab Coat (Size L)",
    "Safety Goggles (Anti-fog)", "Face Shield (disposable)",
    "N95 Respirator Mask", "KN95 Mask", "Surgical Mask (50-pack)",
    "Disposable Bouffant Caps", "Disposable Shoe Covers",
    "Biohazard Bags (red, 1-gallon)", "Biohazard Bags (red, 10-gallon)",
    "Sharps Container (1L)", "Sharps Container (8L)",
    "Autoclave Bags (polypropylene)", "Autoclave Tape",
    "Bench Coat (24 in × 19 in)", "Absorbent Pads (12 in × 12 in)",
    "Kim Wipes (1-ply)", "Lint-Free Wipes (100-pack)",
    "Liquid Nitrogen Storage Gloves", "Cryogenic Apron",
    "UV Safety Glasses (amber)", "Ice Bucket (2L)", "Ice Bucket (4L)",
    "Label Tape (white, 1 in)", "Cryo Labels (1.5 mL tube)",
    "Barcode Labels (for 96-well plate)", "Sharpie Markers (fine tip, black)",
    "Notebook (spiral-bound, lab grade)", "Tongs (stainless steel, 12 in)",
]

SUPPLIERS = [
    "Thermo Fisher Scientific", "Illumina", "Qiagen", "Bio-Rad Laboratories",
    "Agilent Technologies", "Promega Corporation", "New England Biolabs",
    "Sigma-Aldrich (MilliporeSigma)", "Oxford Nanopore Technologies",
    "Pacific Biosciences", "10x Genomics", "Fluidigm Corporation",
    "Roche Diagnostics", "Abbott Laboratories", "Becton Dickinson",
    "Eppendorf AG", "Sartorius AG", "VWR International", "Fisher Scientific",
    "Cole-Parmer", "BioLegend", "R&D Systems", "Abcam",
    "GenScript Biotech", "Twist Bioscience", "Integrated DNA Technologies",
    "Eurofins Genomics", "ATCC", "Corning Life Sciences",
]

SHELF_LOCATIONS = (
    [f"Shelf {r}{n}" for r in "ABCDE" for n in range(1, 9)] +
    [f"Freezer {n} ({t})" for n in range(1, 7) for t in ["-20°C", "-80°C"]] +
    [f"Cold Room {n}" for n in range(1, 4)] +
    [f"Cabinet {r}{n}" for r in "ABC" for n in range(1, 7)] +
    [f"Storage Unit {n}" for n in range(1, 11)]
)

CATEGORIES = ["Reagents", "Kits", "Equipment", "Consumables"]


def clear_tables(session):
    print("Clearing existing patient and inventory data...")
    try:
        session.execute(text("DELETE FROM patients"))
        session.execute(text("DELETE FROM inventory"))
        session.commit()
        print("  Tables cleared.")
    except Exception as e:
        session.rollback()
        print(f"  Error clearing tables: {e}")
        raise


def generate_patients(n: int) -> list[dict]:
    print(f"Generating {n:,} patients...")
    rows = []
    now = datetime.datetime.utcnow().isoformat()
    for i in range(n):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        name = f"{first} {last}"
        initials = f"{first[0]}{last[0]}"
        age = random.randint(18, 95)
        risk_score = round(random.uniform(2.0, 99.0), 1)
        dna_marker = random.choice(DNA_MARKERS)

        # 1–3 conditions
        num_cond = random.randint(1, 3)
        conditions = {c: True for c in random.sample(CONDITIONS_LIST, num_cond)}

        # Pick 1–3 genes, one becomes the primary key in genomic_data
        num_genes = random.randint(1, 3)
        selected_genes = random.sample(GENES, num_genes)
        zygosity_choices = ["homozygous", "heterozygous", "wild-type", "mutant", "variant", "deletion", "insertion"]
        genomic_data = {g: random.choice(zygosity_choices) for g in selected_genes}
        genomic_data["expression_level"] = random.choice(EXPRESSION_LEVELS)
        genomic_data["last_visit"] = f"2025-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        genomic_data["location"] = random.choice(HOSPITAL_LOCATIONS)
        genomic_data["current_treatment"] = random.choice(TREATMENTS)
        genomic_data["treatment_status"] = random.choice(TREATMENT_STATUSES)

        rows.append({
            "id": f"MG-{i + 10000:05d}-{chr(65 + (i % 26))}",
            "name": name,
            "age": age,
            "risk_score": risk_score,
            "dna_marker": dna_marker,
            "initials": initials,
            "conditions": json.dumps(conditions),
            "genomic_data": json.dumps(genomic_data),
            "created_at": now,
            "updated_at": now,
        })
    return rows


def generate_inventory(n: int) -> list[dict]:
    print(f"Generating {n:,} inventory items...")
    all_names = (
        [(name, "Reagents") for name in REAGENT_NAMES] +
        [(name, "Kits") for name in KIT_NAMES] +
        [(name, "Equipment") for name in EQUIPMENT_NAMES] +
        [(name, "Consumables") for name in CONSUMABLE_NAMES]
    )
    rows = []
    now = datetime.datetime.utcnow().isoformat()
    for i in range(n):
        base_name, category = random.choice(all_names)
        # Add a lot number to make each entry unique
        item_name = f"{base_name} (Lot {random.randint(100000, 999999)})"

        qty = random.randint(1, 600)
        reorder = random.randint(10, 200)

        # Cost varies by category
        if category == "Kits":
            cost = round(random.uniform(500.0, 12000.0), 2)
        elif category == "Equipment":
            cost = round(random.uniform(1.0, 800.0), 2)
        elif category == "Reagents":
            cost = round(random.uniform(20.0, 500.0), 2)
        else:  # Consumables
            cost = round(random.uniform(0.5, 150.0), 2)

        rows.append({
            "id": f"INV-{i + 10000:05d}",
            "item_name": item_name,
            "category": category,
            "qty_on_hand": qty,
            "reorder_point": reorder,
            "cost": cost,
            "location": random.choice(SHELF_LOCATIONS),
            "supplier": random.choice(SUPPLIERS),
            "created_at": now,
            "updated_at": now,
        })
    return rows


def bulk_insert(session, table: str, rows: list[dict], batch_size: int = 500):
    cols = list(rows[0].keys())
    col_names = ", ".join(cols)
    placeholders = ", ".join(f":{c}" for c in cols)
    stmt = text(f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})")

    total = len(rows)
    inserted = 0
    for start in range(0, total, batch_size):
        batch = rows[start: start + batch_size]
        session.execute(stmt, batch)
        session.commit()
        inserted += len(batch)
        print(f"  {inserted:,}/{total:,} inserted into {table}...", end="\r")
    print()


def main():
    session = Session()
    try:
        clear_tables(session)

        patients = generate_patients(5000)
        bulk_insert(session, "patients", patients)
        print(f"  {len(patients):,} patients seeded.")

        inventory = generate_inventory(3000)
        bulk_insert(session, "inventory", inventory)
        print(f"  {len(inventory):,} inventory items seeded.")

        print(f"\nDone! Database now has {len(patients):,} patients and {len(inventory):,} inventory items.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
