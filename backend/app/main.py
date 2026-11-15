from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.api.auth import router as auth_router
from app.api.wallets import router as wallets_router
from app.api import credit_requests

from app.db.session import get_db


app = FastAPI(
    title="PayFast API",
    description="API para la plataforma FinTech PayFast",
    version="1.0.0"
)

app.include_router(auth_router)
app.include_router(wallets_router)
app.include_router(credit_requests.router)

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