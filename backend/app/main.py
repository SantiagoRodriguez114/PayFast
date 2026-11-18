from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.api.auth import router as auth_router
from app.api.wallets import router as wallets_router
from app.api import credit_requests
from app.api.risk_evaluations import router as risk_evaluations_router
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

from app.db.session import get_db


app = FastAPI(
    title="PayFast API",
    description="API para la plataforma FinTech PayFast",
    version="1.0.0"
)

allowed_origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]

if settings.frontend_origin:
    allowed_origins.append(settings.frontend_origin.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router)
app.include_router(wallets_router)
app.include_router(credit_requests.router)
app.include_router(risk_evaluations_router)

@app.get("/")
def home():
    return {
        "message": "Bienvenido a PayFast",
        "status": "operational"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.get("/health/database")
def database_health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected"
        }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Database connection unavailable"
        )