from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Integer, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
import os
import csv
import io

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./medgenomics.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(title="MedGenomics API")

# Restrict CORS to trusted origins only.
# Never use allow_origins=["*"] together with allow_credentials=True.
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8000,http://127.0.0.1:8000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Content-Type"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── ORM models ────────────────────────────────────────────────────────────────

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


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class PatientResponse(BaseModel):
    id: str
    name: str
    age: int
    risk_score: float
    dna_marker: str
    initials: str
    conditions: dict
    genomic_data: dict

    class Config:
        from_attributes = True


class InventoryResponse(BaseModel):
    id: str
    item_name: str
    category: str
    qty_on_hand: int
    reorder_point: int
    cost: float
    location: str
    supplier: str

    class Config:
        from_attributes = True


class PatientCreate(BaseModel):
    id: str
    name: str
    age: int
    risk_score: float
    dna_marker: str
    initials: str
    conditions: dict = {}
    genomic_data: dict = {}


class InventoryAdjust(BaseModel):
    qty_on_hand: int


# ── Seed data ─────────────────────────────────────────────────────────────────

def seed_data(db: Session) -> None:
    """Populate tables with sample data when they are empty."""
    if db.query(Patient).first() is None:
        patients = [
            Patient(
                id="MG-4829-X", name="Elena Vance", age=42, risk_score=92.0,
                dna_marker="A+2", initials="EV",
                conditions={"Type 1 Diabetes": True, "Hypercholesterolemia": True},
                genomic_data={"BRCA2": "homozygous", "expression_level": "high"},
            ),
            Patient(
                id="MG-9102-K", name="Marcus Thorne", age=29, risk_score=48.0,
                dna_marker="B-14", initials="MT",
                conditions={"Asymptomatic": True},
                genomic_data={"APOE": "heterozygous", "expression_level": "moderate"},
            ),
            Patient(
                id="MG-1123-W", name="Sarah Jenkins", age=67, risk_score=14.0,
                dna_marker="A+2", initials="SJ",
                conditions={"Type 2 Diabetes": True},
                genomic_data={"MTHFR": "wild-type", "expression_level": "low"},
            ),
            Patient(
                id="MG-5521-P", name="Julian Rossi", age=34, risk_score=89.0,
                dna_marker="TP53-M", initials="JR",
                conditions={"Familial Cancer Syndrome": True},
                genomic_data={"TP53": "mutant", "expression_level": "high"},
            ),
            Patient(
                id="MG-3021-R", name="Isabella Martinez", age=56, risk_score=62.0,
                dna_marker="C+1", initials="IM",
                conditions={"Cardiovascular Risk": True},
                genomic_data={"APOB": "variant", "expression_level": "moderate"},
            ),
        ]
        db.add_all(patients)
        db.commit()

    if db.query(Inventory).first() is None:
        items = [
            Inventory(
                id="INV-001", item_name="TaqPath qPCR Master Mix", category="Reagents",
                qty_on_hand=8, reorder_point=50, cost=45.99,
                location="Shelf A3", supplier="Thermo Fisher Scientific",
            ),
            Inventory(
                id="INV-002", item_name="NovaSeq 6000 S4 Reagent Kit", category="Kits",
                qty_on_hand=42, reorder_point=50, cost=8500.00,
                location="Freezer B1", supplier="Illumina",
            ),
            Inventory(
                id="INV-003", item_name="96-Well Microplates", category="Equipment",
                qty_on_hand=250, reorder_point=500, cost=2.50,
                location="Cabinet C2", supplier="Qiagen",
            ),
            Inventory(
                id="INV-004", item_name="Ethanol 70% Clinical Grade", category="Reagents",
                qty_on_hand=15, reorder_point=60, cost=12.00,
                location="Storage D1", supplier="LabSource Inc.",
            ),
            Inventory(
                id="INV-005", item_name="Exome Enrichment Kit v2", category="Kits",
                qty_on_hand=24, reorder_point=24, cost=3200.00,
                location="Freezer B2", supplier="Agilent Technologies",
            ),
            Inventory(
                id="INV-006", item_name="Proteinase K Solution", category="Reagents",
                qty_on_hand=2, reorder_point=20, cost=125.50,
                location="Shelf A1", supplier="Qiagen",
            ),
            Inventory(
                id="INV-007", item_name="Magnetic Separation Rack", category="Equipment",
                qty_on_hand=5, reorder_point=5, cost=450.00,
                location="Bench E1", supplier="Promega",
            ),
            Inventory(
                id="INV-008", item_name="SYBR Green Dye", category="Reagents",
                qty_on_hand=18, reorder_point=30, cost=89.99,
                location="Shelf A2", supplier="Bio-Rad",
            ),
        ]
        db.add_all(items)
        db.commit()


@app.on_event("startup")
def on_startup() -> None:
    """Seed initial data once when the application starts (not on every request)."""
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()


# ── Page routes ───────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    try:
        return FileResponse("static/index.html", media_type="text/html")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Page not found")


@app.get("/patient-pool")
async def patient_pool():
    try:
        return FileResponse("static/patient-pool.html", media_type="text/html")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Page not found")


@app.get("/inventory")
async def inventory_page():
    try:
        return FileResponse("static/inventory.html", media_type="text/html")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Page not found")


@app.get("/analytics")
async def analytics():
    try:
        return FileResponse("static/analytics.html", media_type="text/html")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Page not found")


@app.get("/genomic-records")
async def genomic_records():
    try:
        return FileResponse("static/genomic-records.html", media_type="text/html")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Page not found")


# ── API routes ────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/api/patients", response_model=list[PatientResponse])
def get_patients(db: Session = Depends(get_db)):
    try:
        return db.query(Patient).all()
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch patients")


@app.post("/api/patients", response_model=PatientResponse, status_code=201)
def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    if db.query(Patient).filter(Patient.id == patient.id).first():
        raise HTTPException(status_code=409, detail="Patient ID already exists")
    try:
        db_patient = Patient(**patient.model_dump())
        db.add(db_patient)
        db.commit()
        db.refresh(db_patient)
        return db_patient
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create patient")


@app.get("/api/inventory", response_model=list[InventoryResponse])
def get_inventory(db: Session = Depends(get_db)):
    try:
        return db.query(Inventory).all()
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch inventory")


@app.put("/api/inventory/{item_id}/adjust", response_model=InventoryResponse)
def adjust_inventory(item_id: str, adjustment: InventoryAdjust, db: Session = Depends(get_db)):
    item = db.query(Inventory).filter(Inventory.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    try:
        item.qty_on_hand = adjustment.qty_on_hand
        db.commit()
        db.refresh(item)
        return item
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to adjust stock")


@app.get("/api/export/report")
def export_report(db: Session = Depends(get_db)):
    try:
        patients = db.query(Patient).all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Name", "Age", "Risk Score", "DNA Marker", "Initials", "Conditions"])
        for p in patients:
            conditions_str = ", ".join(k for k, v in (p.conditions or {}).items() if v)
            writer.writerow([p.id, p.name, p.age, p.risk_score, p.dna_marker, p.initials, conditions_str])
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=medgenomics_report.csv"},
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate report")


@app.get("/api/analytics/export")
def export_analytics(db: Session = Depends(get_db)):
    try:
        patients = db.query(Patient).all()
        inventory = db.query(Inventory).all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Patients", len(patients)])
        writer.writerow(["Critical Risk (>80%)", sum(1 for p in patients if p.risk_score > 80)])
        writer.writerow(["Moderate Risk (40-80%)", sum(1 for p in patients if 40 <= p.risk_score <= 80)])
        writer.writerow(["Low Risk (<40%)", sum(1 for p in patients if p.risk_score < 40)])
        writer.writerow([])
        writer.writerow(["Total Inventory Items", len(inventory)])
        writer.writerow(["Low Stock Items", sum(1 for i in inventory if i.qty_on_hand < i.reorder_point)])
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=medgenomics_analytics.csv"},
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to export analytics")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
