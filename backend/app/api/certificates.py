from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import os
import uuid

from app.core.db import get_db
from app.models.cert_models import CertificateRecord
from app.services.ocr_service import ocr_service
from app.services.report_service import report_service
from app.schemas.cert_schemas import AnalyzeRequest
from app.api.auth import oauth2_scheme
from concurrent.futures import ThreadPoolExecutor
import asyncio

router = APIRouter()
_executor = ThreadPoolExecutor(max_workers=4)
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_certificate(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    allowed_extensions = ["pdf", "jpg", "jpeg", "png"]
    ext = file.filename.split(".")[-1].lower() if file.filename else ""
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"File type '.{ext}' is not supported. Upload a PDF, JPG, or PNG.")

    # Read into memory to check size before writing to disk
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds the 10 MB size limit.")
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    file_id = str(uuid.uuid4())
    filename = f"{file_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        buffer.write(contents)

    return {
        "filename": file.filename,
        "file_path": file_path,
        "file_id": file_id
    }

@router.post("/analyze")
async def analyze_certificate(
    data: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    from app.services.layout_service import layout_service
    from app.services.image_forensics_service import image_forensics_service
    from app.services.rule_engine import rule_engine
    from app.services.verification_service import verification_service
    from app.services.feature_engineering import feature_engineering
    from app.ml.predict_classifier import prediction_classifier
    from app.services.explainability_service import explainability_service
    from app.models.cert_models import UploadedCertificate, CertificateRecord

    file_id = data.file_id
    filename = data.filename
    file_path = data.file_path

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        loop = asyncio.get_event_loop()

        # Step 1: Load image ONCE — shared across all pipeline steps
        img = await loop.run_in_executor(_executor, ocr_service._load_image, file_path)

        # Step 2: Run OCR, Forensics IN PARALLEL
        ocr_future = loop.run_in_executor(_executor, lambda: ocr_service.extract_text_from_image(file_path, img))
        forensics_future = loop.run_in_executor(_executor, lambda: image_forensics_service.analyze_image(file_path, img))

        ocr_data, forensic_summary = await asyncio.gather(ocr_future, forensics_future)

        # Step 3: Layout with real OCR results (fast, no re-read)
        ocr_data.pop("_name_next", None)
        layout_data = layout_service.analyze_layout(file_path, ocr_data.get("ocr_results_list", []), img)
        for k, v in layout_data.items():
            if v and not ocr_data.get(k):
                ocr_data[k] = v

        # Step 4: Rule engine + DB match IN PARALLEL
        rule_data = rule_engine.validate(ocr_data, forensic_summary)
        verification_match = await verification_service.match_certificate(ocr_data, db)

        # Step 5: Feature engineering + ML prediction (fast, sequential)
        features = feature_engineering.generate_features(ocr_data, layout_data, forensic_summary, rule_data, verification_match)
        prediction = prediction_classifier.predict_risk(features)
        explanations = explainability_service.generate_explanation(rule_data, forensic_summary, verification_match)

        status = prediction["status"]
        risk_score = prediction["risk_score"]

        # Step 6: Save to DB
        stmt = select(UploadedCertificate).where(UploadedCertificate.file_id == file_id)
        result = await db.execute(stmt)
        upload_record = result.scalars().first()
        if not upload_record:
            upload_record = UploadedCertificate(filename=filename, file_path=file_path, file_id=file_id)
            db.add(upload_record)
            await db.flush()

        verification_id = f"CG-REF-{uuid.uuid4().hex[:8].upper()}"
        compat_record = CertificateRecord(
            filename=filename,
            file_path=file_path,
            upload_id=upload_record.id,
            status=status,
            risk_score=risk_score,
            extracted_data=ocr_data,
            forensic_summary=forensic_summary,
            feature_vector=features,
            reasons=explanations,
            verification_id=verification_id
        )
        db.add(compat_record)
        await db.commit()
        await db.refresh(compat_record)

        return {
            "id": compat_record.id,
            "verification_id": verification_id,
            "extracted_data": ocr_data,
            "status": status,
            "risk_score": risk_score,
            "reasons": explanations,
            "forensic_summary": forensic_summary,
            "verification_match": verification_match
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

@router.get("/history")
async def get_history(db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)):
    stmt = select(CertificateRecord).order_by(CertificateRecord.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{id}")
async def get_certificate(id: int, db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)):
    stmt = select(CertificateRecord).where(CertificateRecord.id == id)
    result = await db.execute(stmt)
    record = result.scalars().first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record

@router.delete("/{id}")
async def delete_certificate(id: int, db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)):
    # 1. Find the compat record
    stmt = select(CertificateRecord).where(CertificateRecord.id == id)
    result = await db.execute(stmt)
    compat_record = result.scalars().first()
    
    if not compat_record:
        raise HTTPException(status_code=404, detail="Record not found")

    # 2. Delete source record if exists
    if compat_record.upload_id:
        from app.models.cert_models import UploadedCertificate
        from sqlalchemy import delete
        await db.execute(delete(UploadedCertificate).where(UploadedCertificate.id == compat_record.upload_id))

    # 3. Delete the compat record itself
    await db.delete(compat_record)
    await db.commit()
    
    return {"status": "success", "message": "Record and associated source data deleted"}

@router.get("/{id}/report")
async def get_certificate_report(
    id: int,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    stmt = select(CertificateRecord).where(CertificateRecord.id == id)
    result = await db.execute(stmt)
    record = result.scalars().first()
    
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
        
    report_name = f"Report_{record.verification_id}.pdf"
    REPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../reports"))
    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_path = os.path.join(REPORTS_DIR, report_name)
    
    report_service.generate_verification_report(record, report_path)
    
    # Optional: Update the record with the report path
    record.report_path = report_path
    await db.commit()
    
    return FileResponse(
        path=report_path,
        filename=report_name,
        media_type="application/pdf"
    )
