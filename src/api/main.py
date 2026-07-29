from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

class PredictionRequest(BaseModel):
    features: dict = Field(..., description="Input features")

class PredictionResponse(BaseModel):
    prediction: str
    probability: float
    model_name: str = "ml-demand-forecasting"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class HealthResponse(BaseModel):
    status: str = "healthy"
    model: str = "ml-demand-forecasting"
    version: str = "1.0.0"

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="Demand Forecasting API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/api/v1/health", response_model=HealthResponse, tags=["System"])
async def health() -> HealthResponse:
    return HealthResponse()

@app.post("/api/v1/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict(request: PredictionRequest) -> PredictionResponse:
    return PredictionResponse(prediction="ok", probability=0.95)
