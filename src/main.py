from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthCredentials
from sqlalchemy import create_engine, Column, String, Integer, Float, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime, timedelta
import os
import json
import jwt
import hashlib

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./medgenomics.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Security config
SECRET_KEY = os.getenv("SECRET_KEY", "medgenomics-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

security = HTTPBearer()

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

# Database Models
class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user")  # admin, doctor, lab_tech, viewer
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

# Pydantic Models
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

# Helper functions
def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str):
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthCredentials) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

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

@app.get("/login")
async def login_page():
    return FileResponse("static/login.html", media_type="text/html")

@app.get("/register")
async def register_page():
    return FileResponse("static/register.html", media_type="text/html")

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

# Authentication Endpoints
@app.post("/api/register", response_model=TokenResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    # Create new user
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role="viewer"  # Default role
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate token
    access_token = create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user.id, "username": user.username, "email": user.email, "role": user.role}
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
        "user": {"id": user.id, "username": user.username, "email": user.email, "role": user.role}
    }

# Patient CRUD Endpoints
@app.post("/api/patients", response_model=PatientResponse)
def create_patient(patient_data: PatientCreate, db: Session = Depends(get_db), credentials: HTTPAuthCredentials = Depends(security)):
    verify_token(credentials)

    import uuid
    patient_id = f"MG-{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[4:5].upper()}"
    patient = Patient(
        id=patient_id,
        name=patient_data.name,
        age=patient_data.age,
        risk_score=patient_data.risk_score,
        dna_marker=patient_data.dna_marker,
        initials=patient_data.initials,
        conditions=patient_data.conditions,
        genomic_data=patient_data.genomic_data
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient

@app.get("/api/patients/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@app.put("/api/patients/{patient_id}", response_model=PatientResponse)
def update_patient(patient_id: str, patient_data: PatientUpdate, db: Session = Depends(get_db), credentials: HTTPAuthCredentials = Depends(security)):
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
def delete_patient(patient_id: str, db: Session = Depends(get_db), credentials: HTTPAuthCredentials = Depends(security)):
    verify_token(credentials)

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    db.delete(patient)
    db.commit()
    return {"message": "Patient deleted successfully"}

@app.get("/api/patients/search", response_model=list[dict])
def search_patients(query: str = "", risk_min: float = 0, risk_max: float = 100, db: Session = Depends(get_db)):
    seed_data(db)
    patients = db.query(Patient).all()

    # Filter by risk score
    patients = [p for p in patients if risk_min <= p.risk_score <= risk_max]

    # Filter by query (search name, id, dna_marker)
    if query:
        query_lower = query.lower()
        patients = [p for p in patients if
                    query_lower in p.name.lower() or
                    query_lower in p.id.lower() or
                    query_lower in p.dna_marker.lower()]

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

# Inventory CRUD Endpoints
@app.post("/api/inventory", response_model=InventoryResponse)
def create_inventory(inventory_data: InventoryCreate, db: Session = Depends(get_db), credentials: HTTPAuthCredentials = Depends(security)):
    verify_token(credentials)

    item_id = f"INV-{str(len(db.query(Inventory).all()) + 1).zfill(3)}"
    item = Inventory(
        id=item_id,
        item_name=inventory_data.item_name,
        category=inventory_data.category,
        qty_on_hand=inventory_data.qty_on_hand,
        reorder_point=inventory_data.reorder_point,
        cost=inventory_data.cost,
        location=inventory_data.location,
        supplier=inventory_data.supplier
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@app.get("/api/inventory/{item_id}", response_model=InventoryResponse)
def get_inventory_item(item_id: str, db: Session = Depends(get_db)):
    item = db.query(Inventory).filter(Inventory.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.put("/api/inventory/{item_id}", response_model=InventoryResponse)
def update_inventory(item_id: str, inventory_data: InventoryUpdate, db: Session = Depends(get_db), credentials: HTTPAuthCredentials = Depends(security)):
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
def delete_inventory(item_id: str, db: Session = Depends(get_db), credentials: HTTPAuthCredentials = Depends(security)):
    verify_token(credentials)

    item = db.query(Inventory).filter(Inventory.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()
    return {"message": "Item deleted successfully"}

@app.get("/api/inventory/search", response_model=list[dict])
def search_inventory(query: str = "", category: str = "", db: Session = Depends(get_db)):
    seed_data(db)
    items = db.query(Inventory).all()

    # Filter by category
    if category:
        items = [i for i in items if i.category.lower() == category.lower()]

    # Filter by query (search name, id, supplier)
    if query:
        query_lower = query.lower()
        items = [i for i in items if
                 query_lower in i.item_name.lower() or
                 query_lower in i.id.lower() or
                 query_lower in i.supplier.lower()]

    return [
        {
            "id": i.id,
            "item_name": i.item_name,
            "category": i.category,
            "qty_on_hand": i.qty_on_hand,
            "reorder_point": i.reorder_point,
            "cost": float(i.cost),
            "location": i.location,
            "supplier": i.supplier
        }
        for i in items
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
