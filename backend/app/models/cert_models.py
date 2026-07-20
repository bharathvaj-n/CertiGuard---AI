from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

class UploadedCertificate(Base):
    __tablename__ = "uploaded_certificates"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    file_path = Column(String)
    file_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=func.now())

class VerificationRecord(Base):
    __tablename__ = "verification_records"
    id = Column(Integer, primary_key=True, index=True)
    certificate_id = Column(String, unique=True, index=True)
    candidate_name = Column(String)
    issuer_name = Column(String)
    issue_date = Column(DateTime)
    course_name = Column(String)
    status = Column(String, default="Genuine")
    created_at = Column(DateTime, default=func.now())

# Alias for compatibility
MockCertificate = VerificationRecord

class CertificateRecord(Base):
    __tablename__ = "certificate_records"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    file_path = Column(String)
    upload_id = Column(Integer, ForeignKey("uploaded_certificates.id"), nullable=True)
    status = Column(String, index=True) 
    risk_score = Column(Float)
    extracted_data = Column(JSON)
    forensic_summary = Column(JSON, nullable=True) # Merged from AnalysisResult
    feature_vector = Column(JSON, nullable=True) # Merged from AnalysisResult
    reasons = Column(JSON)
    verification_id = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    report_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
