
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Float, ForeignKey, DateTime, func
from .database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))

class Division(Base):
    __tablename__ = "divisions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    weight_modifier: Mapped[float] = mapped_column(Float, default=0.0)

class DecisionMaker(Base):
    __tablename__ = "decision_makers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    role: Mapped[str] = mapped_column(String(128), default="")
    score: Mapped[float] = mapped_column(Float, default=50.0)  # 0-100

class Calculation(Base):
    __tablename__ = "calculations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    division_id: Mapped[int] = mapped_column(ForeignKey("divisions.id"))
    decision_maker_id: Mapped[int] = mapped_column(ForeignKey("decision_makers.id"))
    budget_fit: Mapped[float] = mapped_column(Float, default=0.5)  # 0-1
    timeline_fit: Mapped[float] = mapped_column(Float, default=0.5)  # 0-1
    result: Mapped[float] = mapped_column(Float)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

    division = relationship("Division")
    decision_maker = relationship("DecisionMaker")
