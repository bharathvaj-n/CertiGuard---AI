from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.db import get_db
from app.models.cert_models import CertificateRecord
from app.api.auth import oauth2_scheme

router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)):
    # Count of each status
    statuses = ["Genuine", "Suspicious", "Likely Fake"]
    counts = {}
    
    total = await db.execute(select(func.count(CertificateRecord.id)))
    counts["total"] = total.scalar() or 0
    
    for status in statuses:
        res = await db.execute(select(func.count(CertificateRecord.id)).where(CertificateRecord.status == status))
        counts[status.lower().replace(" ", "_")] = res.scalar() or 0
        
    return counts

@router.get("/recent")
async def get_recent_verifications(limit: int = 5, db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)):
    result = await db.execute(select(CertificateRecord).order_by(CertificateRecord.created_at.desc()).limit(limit))
    records = result.scalars().all()
    
    return [
        {
            "id": r.id,
            "filename": r.filename,
            "status": r.status,
            "risk_score": r.risk_score,
            "verification_id": r.verification_id,
            "created_at": r.created_at,
            "candidate_name": r.extracted_data.get("candidate_name") if r.extracted_data else "Unknown",
        }
        for r in records
    ]
