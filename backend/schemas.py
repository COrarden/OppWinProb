
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    ok: bool
    message: str

class DivisionBase(BaseModel):
    name: str
    weight_modifier: float = 0.0

class DivisionCreate(DivisionBase):
    pass

class DivisionRead(DivisionBase):
    id: int
    class Config:
        from_attributes = True

class DecisionMakerBase(BaseModel):
    name: str
    role: str = ""
    score: float = Field(50.0, ge=0, le=100)

class DecisionMakerCreate(DecisionMakerBase):
    pass

class DecisionMakerRead(DecisionMakerBase):
    id: int
    class Config:
        from_attributes = True

class CalculationBase(BaseModel):
    division_id: int
    decision_maker_id: int
    budget_fit: float = Field(0.5, ge=0, le=1)
    timeline_fit: float = Field(0.5, ge=0, le=1)
    result: float

class CalculationCreate(CalculationBase):
    pass

class CalculationRead(CalculationBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True
