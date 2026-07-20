import re
from typing import Dict, Any, List

class RuleEngine:
    """Rule-based validation of certificates."""
    
    def validate(self, extracted_data: Dict[str, Any], forensic_summary: Dict[str, Any]) -> Dict[str, Any]:
        reasons = []
        validation_flags = {}
        score_deductions = 0.0

        # 1. Certificate ID check
        cert_id = str(extracted_data.get("certificate_id", "") or "").strip()
        if cert_id and not re.match(r"^[A-Z0-9\-/\.\s]{3,30}$", cert_id.upper()):
            validation_flags["invalid_id_format"] = True
            reasons.append(f"Certificate ID '{cert_id}' uses an unconventional format")
            score_deductions += 0.08  # reduced: format alone is weak signal
        elif not cert_id:
            validation_flags["missing_id"] = True
            reasons.append("Certificate ID could not be extracted by OCR")
            score_deductions += 0.05  # OCR miss ≠ fake

        # 2. Missing fields — reduced weight, OCR often misses fields on genuine certs
        required_fields = ["candidate_name", "issuer_name", "issue_date"]
        missing_count = 0
        for field in required_fields:
            if not extracted_data.get(field):
                validation_flags[f"missing_{field}"] = True
                reasons.append(f"Could not extract field: {field.replace('_', ' ')}")
                missing_count += 1
        # Cap total missing-field deduction at 0.15 regardless of how many are missing
        score_deductions += min(missing_count * 0.05, 0.15)

        # 3. OCR confidence — only penalise very low confidence
        ocr_conf = extracted_data.get("ocr_confidence", 1.0)
        if ocr_conf < 0.45:
            validation_flags["low_ocr_confidence"] = True
            reasons.append(f"OCR confidence is very low ({ocr_conf:.2f}) — image may be too blurry")
            score_deductions += 0.10

        # 4. Forensic tampering — only flag strong evidence
        tampering_score = forensic_summary.get("tampering_score", 0.0)
        if tampering_score > 0.65:
            validation_flags["suspicious_tampering"] = True
            reasons.append("Strong image tampering indicators detected in forensic analysis")
            score_deductions += 0.25
        elif tampering_score > 0.50:
            reasons.append("Moderate image inconsistencies detected — may be due to scanning")
            score_deductions += 0.08

        # 5. Blur check — only extreme blur
        blur_score = forensic_summary.get("blur_score", 0.0)
        if blur_score > 0.85:
            validation_flags["high_blur"] = True
            reasons.append("Image is excessively blurry, reducing verification confidence")
            score_deductions += 0.08

        return {
            "validation_flags": validation_flags,
            "rule_score": max(0.0, 1.0 - score_deductions),
            "reasons": reasons
        }

rule_engine = RuleEngine()
