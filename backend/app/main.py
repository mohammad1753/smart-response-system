import logging

from fastapi import FastAPI

from app.core.config import Settings
from app.core.logging import setup_logging

setup_logging()

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Smart Response System",
    description="AI-powered customer support system",
    version= "0.0.1"

)

@app.get("/")
async def root():
    logger.info("Root endpoint requested")
    return{
        "message": "AI Customer Supporting system",
        "status": "runnig",
    }

@app.get("/health")
async def health():
    logger.info("Health check requested")
    return{
        "status": "healty"
    }