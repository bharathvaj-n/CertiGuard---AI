import asyncio
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from passlib.context import CryptContext

from app.core.config import settings          # single source of truth for DB URL
from app.models.cert_models import Base, User, MockCertificate, CertificateRecord

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Always use the same URL the running app uses
DATABASE_URL = settings.DATABASE_URL


async def init_db():
    # Ensure the db directory exists
    db_file = DATABASE_URL.replace("sqlite+aiosqlite:///", "").replace("sqlite+aiosqlite://", "")
    os.makedirs(os.path.dirname(db_file), exist_ok=True)

    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:

        # ── Admin user ────────────────────────────────────────────────
        result = await session.execute(select(User).where(User.username == "admin"))
        existing = result.scalars().first()
        if existing:
            # Re-hash to ensure password is always correct
            existing.hashed_password = pwd_context.hash("admin123")
            existing.is_admin = True
            print("Admin user updated: admin / admin123")
        else:
            admin = User(
                username="admin",
                hashed_password=pwd_context.hash("admin123"),
                is_admin=True,
            )
            session.add(admin)
            print("Admin user created: admin / admin123")

        # ── Mock verification records ─────────────────────────────────
        mock_genuine = [
            ("CERT-001", "John Doe",       "MIT",      "Computer Science"),
            ("CERT-002", "Jane Smith",      "Stanford", "Mechanical Engineering"),
            ("CERT-003", "Robert Brown",    "Harvard",  "Data Science"),
            ("CERT-004", "Alice Johnson",   "Oxford",   "Physics"),
            ("CERT-005", "Michael Davis",   "Cambridge","Economics"),
        ]
        for cid, name, issuer, course in mock_genuine:
            res = await session.execute(
                select(MockCertificate).where(MockCertificate.certificate_id == cid)
            )
            if not res.scalars().first():
                session.add(MockCertificate(
                    certificate_id=cid,
                    candidate_name=name,
                    issuer_name=issuer,
                    issue_date=datetime.now() - timedelta(days=365),
                    course_name=course,
                    status="Genuine",
                ))

        # ── Seed history ──────────────────────────────────────────────
        mock_history = [
            ("user_upload_01.pdf", "Genuine",     15.5, "CG-REF-101"),
            ("user_upload_02.jpg", "Suspicious",  45.2, "CG-REF-102"),
            ("user_upload_03.png", "Likely Fake", 82.8, "CG-REF-103"),
        ]
        for fname, status, risk, ver_id in mock_history:
            res = await session.execute(
                select(CertificateRecord).where(CertificateRecord.verification_id == ver_id)
            )
            if not res.scalars().first():
                session.add(CertificateRecord(
                    filename=fname,
                    file_path="uploads/" + fname,
                    status=status,
                    risk_score=risk,
                    verification_id=ver_id,
                    extracted_data={"candidate_name": "Test User", "issuer_name": "Unknown"},
                    reasons=["Template mismatch"] if status != "Genuine" else [],
                ))

        await session.commit()
        print("Database seeded successfully.")
        print("DB path:", db_file)


if __name__ == "__main__":
    asyncio.run(init_db())
