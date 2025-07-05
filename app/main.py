from fastapi import FastAPI, Request
import time
import logging

from .api import router
from .database import engine, Base
from .rag_system import rag_system

# Setup logging for audit trail
logging.basicConfig(level=logging.INFO)
audit_logger = logging.getLogger("audit")

# Create database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="UltraSafe Medical Records API",
    description="A prototype API for managing medical records with HIPAA-compliant semantic search.",
    version="1.0.0"
)

# HIPAA Compliance: Audit Logging Middleware
@app.middleware("http")
async def audit_log_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Log details for the audit trail
    audit_logger.info(
        f'AUDIT - Client: {request.client.host} - User-Agent: "{request.headers.get("user-agent")}" '
        f'- Method: {request.method} - Path: {request.url.path} '
        f'- Status: {response.status_code} - Duration: {process_time:.4f}s'
    )
    return response

# Include the API router
app.include_router(router)

@app.on_event("startup")
async def startup_event():
    # This ensures the RAG system is ready when the app starts
    global rag_system
    if not rag_system.initialized:
        rag_system.initialize()
    print("FastAPI application startup complete.")

@app.get("/", tags=["Health Check"])
def read_root():
    """A simple health check endpoint."""
    return {"status": "ok", "message": "Medical Records API is running."}