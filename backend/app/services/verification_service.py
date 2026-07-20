from fuzzywuzzy import fuzz
from typing import Dict, Any
from sqlalchemy.future import select
from app.models.cert_models import MockCertificate # Assumed model name, could be 'verification_records' table in DB

class VerificationService:
    """Validate extracted fields against existing database."""
    
    async def match_certificate(self, extracted_data: Dict[str, Any], db_session: Any) -> Dict[str, Any]:
        """
        Compare extracted fields against simulation bank.
        """
        # Search by Cert ID primarily
        cert_id = str(extracted_data.get("certificate_id", "") or "")
        
        # Simulation if no DB found
        if not cert_id:
            return {
                "match_found": False,
                "match_score": 0.0,
                "matched_record": None,
                "verification_notes": "No certificate ID extracted for lookup."
            }
            
        # Mock DB search
        stmt = select(MockCertificate).where(MockCertificate.certificate_id == cert_id)
        result = await db_session.execute(stmt)
        record = result.scalars().first()
        
        if record:
            # Field similarity check
            # Name
            name_score = fuzz.ratio(str(extracted_data.get("candidate_name", "")).lower(), str(record.candidate_name).lower()) / 100.0
            # Issuer
            issuer_score = fuzz.ratio(str(extracted_data.get("issuer_name", "")).lower(), str(record.issuer_name).lower()) / 100.0
            
            avg_score = (name_score + issuer_score) / 2.0
            
            return {
                "match_found": True,
                "match_score": avg_score,
                "matched_record": {
                    "id": record.certificate_id,
                    "name": record.candidate_name,
                    "issuer": record.issuer_name,
                    "course": record.course_name
                },
                "verification_notes": f"Matched ID {cert_id} with {avg_score*100:.1f}% data consistency."
            }
            
        return {
            "match_found": False,
            "match_score": 0.0,
            "matched_record": None,
            "verification_notes": f"No record found for ID: {cert_id}."
        }

verification_service = VerificationService()
