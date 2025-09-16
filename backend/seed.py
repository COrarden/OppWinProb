
from .database import Base, engine, SessionLocal
from .models import User, Division, DecisionMaker
import hashlib

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def run_seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            db.add(User(username="admin", password_hash=hash_pw("admin123")))

        if db.query(Division).count() == 0:
            db.add_all([
                Division(name="General Contracting", weight_modifier=0.05),
                Division(name="Construction Services", weight_modifier=0.02),
                Division(name="Roofing", weight_modifier=-0.01),
            ])

        if db.query(DecisionMaker).count() == 0:
            db.add_all([
                DecisionMaker(name="Alice Johnson", role="CFO", score=72),
                DecisionMaker(name="Bob Smith", role="VP Ops", score=65),
                DecisionMaker(name="Carmen Diaz", role="Director", score=58),
            ])
        db.commit()
    finally:
        db.close()
