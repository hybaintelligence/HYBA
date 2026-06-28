from fastapi import FastAPI
from hyba_genesis_api.database import initialize_database

app = FastAPI()

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    initialize_database()

@app.get("/api/v1/health/readiness")
async def read_readiness():
    return {"status": "ready", "message": "Backend is ready to serve requests."}
