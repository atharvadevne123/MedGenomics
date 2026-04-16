from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, Column, String, Integer, Float, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime
import os
import csv
import io
import json
import hashlib
import hmac
import base64
import time
import uuid

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./medgenomics.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Security config
SECRET_KEY = os.getenv("SECRET_KEY", "medgenomics-secret-key-change-in-production")
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

security = HTTPBearer(auto_error=False)

# Restrict CORS to trusted origins only.
# Never use allow_origins=["*"] together with allow_credentials=True.
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8000,http://127.0.0.1:8000",
).split(",")

app = FastAPI(title="MedGenomics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── ORM models ────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user")
    created_at = Column(DateTime, default=datetime.utcnow)


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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


Base.metadata.create_all(bind=engine)


# ── Auth helpers ───────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password


def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = int(time.time()) + ACCESS_TOKEN_EXPIRE_MINUTES * 60
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    sig = hmac.new(SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{sig}"


def verify_token(credentials: HTTPAuthorizationCredentials) -> dict:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authorization required")
    try:
        token = credentials.credentials
        payload_b64, sig = token.rsplit(".", 1)
        expected_sig = hmac.new(SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            raise HTTPException(status_code=401, detail="Invalid token")
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + "=="))
        if payload.get("exp", 0) < int(time.time()):
            raise HTTPException(status_code=401, detail="Token expired")
        return payload
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


# ── Pydantic schemas ───────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class PatientCreate(BaseModel):
    name: str
    age: int
    risk_score: float
    dna_marker: str
    initials: str
    conditions: dict = {}
    genomic_data: dict = {}


class PatientUpdate(BaseModel):
    name: str = None
    age: int = None
    risk_score: float = None
    dna_marker: str = None
    conditions: dict = None
    genomic_data: dict = None


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


class InventoryCreate(BaseModel):
    item_name: str
    category: str
    qty_on_hand: int
    reorder_point: int
    cost: float
    location: str
    supplier: str


class InventoryUpdate(BaseModel):
    item_name: str = None
    category: str = None
    qty_on_hand: int = None
    reorder_point: int = None
    cost: float = None
    location: str = None
    supplier: str = None


class InventoryAdjust(BaseModel):
    qty_on_hand: int


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


# ── Seed data ──────────────────────────────────────────────────────────────────

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


# ── Page routes ────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    try:
        return FileResponse("static/index.html", media_type="text/html")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Page not found")


@app.get("/login")
async def login_page():
    try:
        return FileResponse("static/login.html", media_type="text/html")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Page not found")


@app.get("/register")
async def register_page():
    try:
        return FileResponse("static/register.html", media_type="text/html")
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


# ── API routes ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "healthy"}


# Auth endpoints

@app.post("/api/register", response_model=TokenResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role="viewer",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user.id, "username": user.username, "email": user.email, "role": user.role},
    }


@app.post("/api/login", response_model=TokenResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user.id, "username": user.username, "email": user.email, "role": user.role},
    }


# Patient endpoints — /search must be declared before /{patient_id}

@app.get("/api/patients", response_model=list[PatientResponse])
def get_patients(db: Session = Depends(get_db)):
    try:
        return db.query(Patient).all()
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch patients")


@app.post("/api/patients", response_model=PatientResponse, status_code=201)
def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    try:
        patient_id = f"MG-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:1].upper()}"
        db_patient = Patient(
            id=patient_id,
            name=patient.name,
            age=patient.age,
            risk_score=patient.risk_score,
            dna_marker=patient.dna_marker,
            initials=patient.initials,
            conditions=patient.conditions,
            genomic_data=patient.genomic_data,
        )
        db.add(db_patient)
        db.commit()
        db.refresh(db_patient)
        return db_patient
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create patient")


@app.get("/api/patients/search", response_model=list[PatientResponse])
def search_patients(
    query: str = "",
    risk_min: float = 0,
    risk_max: float = 100,
    db: Session = Depends(get_db),
):
    patients = db.query(Patient).all()
    patients = [p for p in patients if risk_min <= p.risk_score <= risk_max]
    if query:
        query_lower = query.lower()
        patients = [p for p in patients if
                    query_lower in p.name.lower() or
                    query_lower in p.id.lower() or
                    query_lower in p.dna_marker.lower()]
    return patients


@app.get("/api/patients/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@app.put("/api/patients/{patient_id}", response_model=PatientResponse)
def update_patient(
    patient_id: str,
    patient_data: PatientUpdate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    verify_token(credentials)
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if patient_data.name is not None:
        patient.name = patient_data.name
    if patient_data.age is not None:
        patient.age = patient_data.age
    if patient_data.risk_score is not None:
        patient.risk_score = patient_data.risk_score
    if patient_data.dna_marker is not None:
        patient.dna_marker = patient_data.dna_marker
    if patient_data.conditions is not None:
        patient.conditions = patient_data.conditions
    if patient_data.genomic_data is not None:
        patient.genomic_data = patient_data.genomic_data
    db.commit()
    db.refresh(patient)
    return patient


@app.delete("/api/patients/{patient_id}")
def delete_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    verify_token(credentials)
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    db.delete(patient)
    db.commit()
    return {"message": "Patient deleted successfully"}


# Inventory endpoints — /search must be declared before /{item_id}

@app.get("/api/inventory", response_model=list[InventoryResponse])
def get_inventory(db: Session = Depends(get_db)):
    try:
        return db.query(Inventory).all()
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch inventory")


@app.post("/api/inventory", response_model=InventoryResponse)
def create_inventory(
    inventory_data: InventoryCreate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    verify_token(credentials)
    item_id = f"INV-{str(db.query(Inventory).count() + 1).zfill(3)}"
    item = Inventory(
        id=item_id,
        item_name=inventory_data.item_name,
        category=inventory_data.category,
        qty_on_hand=inventory_data.qty_on_hand,
        reorder_point=inventory_data.reorder_point,
        cost=inventory_data.cost,
        location=inventory_data.location,
        supplier=inventory_data.supplier,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/api/inventory/search", response_model=list[InventoryResponse])
def search_inventory(query: str = "", category: str = "", db: Session = Depends(get_db)):
    items = db.query(Inventory).all()
    if category:
        items = [i for i in items if i.category.lower() == category.lower()]
    if query:
        query_lower = query.lower()
        items = [i for i in items if
                 query_lower in i.item_name.lower() or
                 query_lower in i.id.lower() or
                 query_lower in i.supplier.lower()]
    return items


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


@app.get("/api/inventory/{item_id}", response_model=InventoryResponse)
def get_inventory_item(item_id: str, db: Session = Depends(get_db)):
    item = db.query(Inventory).filter(Inventory.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.put("/api/inventory/{item_id}", response_model=InventoryResponse)
def update_inventory(
    item_id: str,
    inventory_data: InventoryUpdate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    verify_token(credentials)
    item = db.query(Inventory).filter(Inventory.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if inventory_data.item_name is not None:
        item.item_name = inventory_data.item_name
    if inventory_data.category is not None:
        item.category = inventory_data.category
    if inventory_data.qty_on_hand is not None:
        item.qty_on_hand = inventory_data.qty_on_hand
    if inventory_data.reorder_point is not None:
        item.reorder_point = inventory_data.reorder_point
    if inventory_data.cost is not None:
        item.cost = inventory_data.cost
    if inventory_data.location is not None:
        item.location = inventory_data.location
    if inventory_data.supplier is not None:
        item.supplier = inventory_data.supplier
    db.commit()
    db.refresh(item)
    return item


@app.delete("/api/inventory/{item_id}")
def delete_inventory(
    item_id: str,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    verify_token(credentials)
    item = db.query(Inventory).filter(Inventory.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"message": "Item deleted successfully"}


# Export endpoints

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
