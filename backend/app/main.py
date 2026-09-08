from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("certiguard-ai")

# Load env variables
load_dotenv()

app = FastAPI(title="CertiGuard AI API", version="1.0.0")

# CORS configuration
origins = [
    url.strip()
    for url in os.getenv("FRONTEND_URL", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if url.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    os.makedirs("db", exist_ok=True)

    # Initialize DB tables
    from app.core.db import engine
    from app.models.cert_models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ready.")

    # Pre-warm all heavy services in background so first request is fast
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    import numpy as np

    def warmup():
        try:
            logger.info("Warming up OCR engine...")
            from app.services.ocr_service import ocr_service
            blank = np.zeros((100, 100, 3), dtype=np.uint8)
            ocr_service.extract_text_from_image("__warmup__", blank)
            logger.info("OCR engine ready.")
        except Exception as e:
            logger.warning(f"OCR warmup warning: {e}")

        try:
            logger.info("Warming up ML classifier...")
            from app.ml.predict_classifier import prediction_classifier
            prediction_classifier.predict_risk({
                "ocr_confidence": 0.9, "text_length": 500, "field_count": 5,
                "id_valid": 1, "issue_date_valid": 1, "issuer_match_score": 0.9,
                "tampering_score": 0.1, "logo_region_consistency": 0.9,
                "compression_artifact_score": 0.2, "edge_mismatch_score": 0.1,
                "verification_match": 1, "layout_confidence": 0.95
            })
            logger.info("ML classifier ready.")
        except Exception as e:
            logger.warning(f"ML warmup warning: {e}")

    loop = asyncio.get_event_loop()
    loop.run_in_executor(ThreadPoolExecutor(max_workers=1), warmup)
    logger.info("Server startup complete. Services warming up in background.")

@app.get("/")
async def root():
    return {"message": "Welcome to CertiGuard AI API", "status": "online"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "certiguard-ai-backend"}

from app.api import auth, dashboard, certificates

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(certificates.router, prefix="/api/certificates", tags=["Certificates"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
