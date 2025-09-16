
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from .database import Base, engine, get_db
from .models import User, Division, DecisionMaker, Calculation
from .schemas import (
    LoginRequest, LoginResponse,
    DivisionCreate, DivisionRead,
    DecisionMakerCreate, DecisionMakerRead,
    CalculationCreate, CalculationRead
)
from .seed import run_seed
import hashlib

app = FastAPI(title="OppWinProb CRUD API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    run_seed()

@app.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or user.password_hash != hash_pw(payload.password):
        return LoginResponse(ok=False, message="Invalid credentials")
    return LoginResponse(ok=True, message="Login successful")

@app.get("/divisions", response_model=List[DivisionRead])
def list_divisions(db: Session = Depends(get_db)):
    return db.query(Division).order_by(Division.id).all()

@app.post("/divisions", response_model=DivisionRead)
def create_division(payload: DivisionCreate, db: Session = Depends(get_db)):
    exists = db.query(Division).filter(Division.name == payload.name).first()
    if exists:
        raise HTTPException(400, detail="Division already exists")
    obj = Division(name=payload.name, weight_modifier=payload.weight_modifier)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@app.put("/divisions/{division_id}", response_model=DivisionRead)
def update_division(division_id: int, payload: DivisionCreate, db: Session = Depends(get_db)):
    obj = db.query(Division).get(division_id)
    if not obj:
        raise HTTPException(404, detail="Division not found")
    obj.name = payload.name
    obj.weight_modifier = payload.weight_modifier
    db.commit()
    db.refresh(obj)
    return obj

@app.delete("/divisions/{division_id}")
def delete_division(division_id: int, db: Session = Depends(get_db)):
    obj = db.query(Division).get(division_id)
    if not obj:
        raise HTTPException(404, detail="Division not found")
    db.delete(obj)
    db.commit()
    return {"ok": True}

@app.get("/decision_makers", response_model=List[DecisionMakerRead])
def list_dms(db: Session = Depends(get_db)):
    return db.query(DecisionMaker).order_by(DecisionMaker.id).all()

@app.post("/decision_makers", response_model=DecisionMakerRead)
def create_dm(payload: DecisionMakerCreate, db: Session = Depends(get_db)):
    obj = DecisionMaker(name=payload.name, role=payload.role, score=payload.score)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@app.put("/decision_makers/{dm_id}", response_model=DecisionMakerRead)
def update_dm(dm_id: int, payload: DecisionMakerCreate, db: Session = Depends(get_db)):
    obj = db.query(DecisionMaker).get(dm_id)
    if not obj:
        raise HTTPException(404, detail="Decision Maker not found")
    obj.name = payload.name
    obj.role = payload.role
    obj.score = payload.score
    db.commit()
    db.refresh(obj)
    return obj

@app.delete("/decision_makers/{dm_id}")
def delete_dm(dm_id: int, db: Session = Depends(get_db)):
    obj = db.query(DecisionMaker).get(dm_id)
    if not obj:
        raise HTTPException(404, detail="Decision Maker not found")
    db.delete(obj)
    db.commit()
    return {"ok": True}

def compute_probability(dm_score: float, division_weight: float, budget_fit: float, timeline_fit: float) -> float:
    base = 0.25
    dm_component = (dm_score / 100.0) * 0.5
    fit_component = ((budget_fit + timeline_fit) / 2.0) * 0.2
    prob = base + dm_component + division_weight + fit_component
    return max(0.0, min(1.0, prob))

@app.post("/calculations", response_model=CalculationRead)
def create_calc(payload: CalculationCreate, db: Session = Depends(get_db)):
    division = db.query(Division).get(payload.division_id)
    dm = db.query(DecisionMaker).get(payload.decision_maker_id)
    if not division or not dm:
        raise HTTPException(400, detail="Bad division or decision_maker id")

    result = compute_probability(dm.score, division.weight_modifier, payload.budget_fit, payload.timeline_fit)
    calc = Calculation(
        division_id=division.id,
        decision_maker_id=dm.id,
        budget_fit=payload.budget_fit,
        timeline_fit=payload.timeline_fit,
        result=result
    )
    db.add(calc)
    db.commit()
    db.refresh(calc)
    return calc

@app.get("/calculations", response_model=List[CalculationRead])
def list_calcs(db: Session = Depends(get_db)):
    return db.query(Calculation).order_by(Calculation.id.desc()).all()


from fastapi import Response
import csv
import io

@app.get("/calculations/count")
def count_calcs(db: Session = Depends(get_db)):
    return {"count": db.query(Calculation).count()}

@app.get("/calculations/export")
def export_calcs(offset: int = 0, limit: int = 1000, db: Session = Depends(get_db)):
    q = db.query(Calculation).order_by(Calculation.id).offset(offset).limit(limit).all()
    # Join friendly fields
    rows = []
    for c in q:
        rows.append([
            c.id,
            c.created_at.isoformat() if c.created_at else "",
            c.result,
            c.budget_fit, c.timeline_fit,
            c.division_id, c.division.name if c.division else "",
            c.decision_maker_id,
            c.decision_maker.name if c.decision_maker else "",
            c.decision_maker.role if c.decision_maker else "",
            c.decision_maker.score if c.decision_maker else ""
        ])
    header = ["id","created_at","result","budget_fit","timeline_fit",
              "division_id","division_name","decision_maker_id",
              "decision_maker_name","decision_maker_role","decision_maker_score"]
    sio = io.StringIO()
    writer = csv.writer(sio)
    writer.writerow(header)
    writer.writerows(rows)
    data = sio.getvalue().encode("utf-8")
    filename = f"calculations_{offset}_{offset+len(rows)-1 if rows else offset}.csv"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=data, media_type="text/csv", headers=headers)

@app.get("/decision_makers/export")
def export_dms(offset: int = 0, limit: int = 1000, db: Session = Depends(get_db)):
    q = db.query(DecisionMaker).order_by(DecisionMaker.id).offset(offset).limit(limit).all()
    header = ["id","name","role","score"]
    sio = io.StringIO()
    writer = csv.writer(sio)
    writer.writerow(header)
    for dm in q:
        writer.writerow([dm.id, dm.name, dm.role, dm.score])
    data = sio.getvalue().encode("utf-8")
    filename = f"decision_makers_{offset}_{offset+len(q)-1 if q else offset}.csv"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=data, media_type="text/csv", headers=headers)

@app.get("/divisions/export")
def export_divisions(offset: int = 0, limit: int = 1000, db: Session = Depends(get_db)):
    q = db.query(Division).order_by(Division.id).offset(offset).limit(limit).all()
    header = ["id","name","weight_modifier"]
    sio = io.StringIO()
    writer = csv.writer(sio)
    writer.writerow(header)
    for d in q:
        writer.writerow([d.id, d.name, d.weight_modifier])
    data = sio.getvalue().encode("utf-8")
    filename = f"divisions_{offset}_{offset+len(q)-1 if q else offset}.csv"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=data, media_type="text/csv", headers=headers)
