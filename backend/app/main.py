from fastapi import FastAPI

app = FastAPI(
    title="PayFast API",
    description="API para la plataforma FinTech PayFast",
    version="1.0.0"
)


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