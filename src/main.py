from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Integer, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
import os
import json

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./medgenomics.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Patient(Base):
    __tablename__ = "patients"
    id = Column(String, primary_key=True)
    name = Column(String)
    age = Column(Integer)
    risk_score = Column(Float)
    dna_marker = Column(String)
    initials = Column(String)
    conditions = Column(JSON)
    genomic_data = Column(JSON)

class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(String, primary_key=True)
    item_name = Column(String)
    category = Column(String)
    qty_on_hand = Column(Integer)
    reorder_point = Column(Integer)
    cost = Column(Float)
    location = Column(String)
    supplier = Column(String)

Base.metadata.create_all(bind=engine)

# Pydantic models for response
class PatientResponse(BaseModel):
    id: str
    name: str
    age: int
    risk_score: float
    dna_marker: str
    initials: str
    conditions: dict
    genomic_data: dict

class InventoryResponse(BaseModel):
    id: str
    item_name: str
    category: str
    qty_on_hand: int
    reorder_point: int
    cost: float
    location: str
    supplier: str

def seed_data(db: Session):
    """Seed initial data if database is empty"""
    if db.query(Patient).first() is None:
        patients_data = [
            Patient(
                id="MG-4829-X",
                name="Elena Vance",
                age=42,
                risk_score=92.0,
                dna_marker="A+2",
                initials="EV",
                conditions={"Type 1 Diabetes": True, "Hypercholesterolemia": True},
                genomic_data={"BRCA2": "homozygous", "expression_level": "high"}
            ),
            Patient(
                id="MG-9102-K",
                name="Marcus Thorne",
                age=29,
                risk_score=48.0,
                dna_marker="B-14",
                initials="MT",
                conditions={"Asymptomatic": True},
                genomic_data={"APOE": "heterozygous", "expression_level": "moderate"}
            ),
            Patient(
                id="MG-1123-W",
                name="Sarah Jenkins",
                age=67,
                risk_score=14.0,
                dna_marker="A+2",
                initials="SJ",
                conditions={"Type 2 Diabetes": True},
                genomic_data={"MTHFR": "wild-type", "expression_level": "low"}
            ),
            Patient(
                id="MG-5521-P",
                name="Julian Rossi",
                age=34,
                risk_score=89.0,
                dna_marker="TP53-M",
                initials="JR",
                conditions={"Familial Cancer Syndrome": True},
                genomic_data={"TP53": "mutant", "expression_level": "high"}
            ),
            Patient(
                id="MG-3021-R",
                name="Isabella Martinez",
                age=56,
                risk_score=62.0,
                dna_marker="C+1",
                initials="IM",
                conditions={"Cardiovascular Risk": True},
                genomic_data={"APOB": "variant", "expression_level": "moderate"}
            ),
        ]
        for patient in patients_data:
            db.add(patient)
        db.commit()

    if db.query(Inventory).first() is None:
        inventory_data = [
            Inventory(
                id="INV-001",
                item_name="TaqPath qPCR Master Mix",
                category="Reagents",
                qty_on_hand=8,
                reorder_point=50,
                cost=45.99,
                location="Shelf A3",
                supplier="Thermo Fisher Scientific"
            ),
            Inventory(
                id="INV-002",
                item_name="NovaSeq 6000 S4 Reagent Kit",
                category="Kits",
                qty_on_hand=42,
                reorder_point=50,
                cost=8500.00,
                location="Freezer B1",
                supplier="Illumina"
            ),
            Inventory(
                id="INV-003",
                item_name="96-Well Microplates",
                category="Equipment",
                qty_on_hand=250,
                reorder_point=500,
                cost=2.50,
                location="Cabinet C2",
                supplier="Qiagen"
            ),
            Inventory(
                id="INV-004",
                item_name="Ethanol 70% Clinical Grade",
                category="Reagents",
                qty_on_hand=15,
                reorder_point=60,
                cost=12.00,
                location="Storage D1",
                supplier="LabSource Inc."
            ),
            Inventory(
                id="INV-005",
                item_name="Exome Enrichment Kit v2",
                category="Kits",
                qty_on_hand=24,
                reorder_point=24,
                cost=3200.00,
                location="Freezer B2",
                supplier="Agilent Technologies"
            ),
            Inventory(
                id="INV-006",
                item_name="Proteinase K Solution",
                category="Reagents",
                qty_on_hand=2,
                reorder_point=20,
                cost=125.50,
                location="Shelf A1",
                supplier="Qiagen"
            ),
            Inventory(
                id="INV-007",
                item_name="Magnetic Separation Rack",
                category="Equipment",
                qty_on_hand=5,
                reorder_point=5,
                cost=450.00,
                location="Bench E1",
                supplier="Promega"
            ),
            Inventory(
                id="INV-008",
                item_name="SYBR Green Dye",
                category="Reagents",
                qty_on_hand=18,
                reorder_point=30,
                cost=89.99,
                location="Shelf A2",
                supplier="Bio-Rad"
            ),
        ]
        for item in inventory_data:
            db.add(item)
        db.commit()

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return FileResponse("static/index.html", media_type="text/html")

@app.get("/patient-pool")
async def patient_pool():
    return FileResponse("static/patient-pool.html", media_type="text/html")

@app.get("/inventory")
async def inventory_page():
    return FileResponse("static/inventory.html", media_type="text/html")

@app.get("/analytics")
async def analytics():
    return FileResponse("static/analytics.html", media_type="text/html")

@app.get("/genomic-records")
async def genomic_records():
    return FileResponse("static/genomic-records.html", media_type="text/html")

@app.get("/api/patients", response_model=list[dict])
def get_patients(db: Session = Depends(get_db)):
    # Seed data on first request
    seed_data(db)
    patients = db.query(Patient).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "age": p.age,
            "risk_score": p.risk_score,
            "dna_marker": p.dna_marker,
            "initials": p.initials,
            "conditions": p.conditions,
            "genomic_data": p.genomic_data
        }
        for p in patients
    ]

@app.get("/api/inventory", response_model=list[dict])
def get_inventory(db: Session = Depends(get_db)):
    # Seed data on first request
    seed_data(db)
    supplies = db.query(Inventory).all()
    return [
        {
            "id": s.id,
            "item_name": s.item_name,
            "category": s.category,
            "qty_on_hand": s.qty_on_hand,
            "reorder_point": s.reorder_point,
            "cost": float(s.cost),
            "location": s.location,
            "supplier": s.supplier
        }
        for s in supplies
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
