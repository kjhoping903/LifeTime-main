from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import Literal
from datetime import datetime

app = FastAPI(title="LifeTime API", version="0.1.0")

# For development only. Set explicit allowed origins before deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

FacilityType = Literal["aed", "emergency_room"]

class Position(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

class RecommendationRequest(BaseModel):
    start: Position
    departure_at: datetime  # Requires timezone offset

    @field_validator("departure_at")
    @classmethod
    def timezone_required(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("departure_at must include timezone offset")
        return value

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/facilities/nearby")
def nearby(latitude: float = Query(ge=-90, le=90), longitude: float = Query(ge=-180, le=180),
           facility_type: FacilityType | None = None, radius_m: int = Query(default=3000, ge=1, le=20000)):
    # Response contract placeholder; no fabricated real facilities.
    return {"facilities": [], "count": 0}

@app.get("/api/facilities/{id}")
def facility_detail(id: str):
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Facility not found")

@app.post("/api/aeds/recommendations")
def recommendations(request: RecommendationRequest):
    # Route API is not yet connected: report unavailable, not a made-up ETA.
    from fastapi import HTTPException
    raise HTTPException(status_code=503, detail="Walking route provider not configured")
