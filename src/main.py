from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, Column, String, Integer, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:secure123@localhost:5432/medgenomics")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

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

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/patients")
def get_patients(db: Session = Depends(get_db)):
    patients = db.query(Patient).all()
    return [{"id": p.id, "name": p.name, "conditions": p.conditions, "genomic_data": p.genomic_data} for p in patients]

@app.get("/inventory")
def get_inventory(db: Session = Depends(get_db)):
    supplies = db.query(Inventory).all()
    return [{"id": s.id, "item_name": s.item_name, "category": s.category, "qty_on_hand": s.qty_on_hand, "reorder_point": s.reorder_point, "cost": float(s.cost), "location": s.location, "supplier": s.supplier} for s in supplies]

@app.get("/")
async def root():
    return FileResponse("static/dashboard.html", media_type="text/html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
