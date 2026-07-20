from typing import List, Dict, Any

class ExplainabilityService:
    """Human-readable explanation of risk scores."""
    
    def generate_explanation(self, rule_data: Dict[str, Any], forensic_data: Dict[str, Any], verification_match: Dict[str, Any]) -> List[str]:
        reasons = list(rule_data.get("reasons", []))

        # Forensic findings — only report strong signals
        if forensic_data.get("ela_score", 0.0) > 0.50:
            reasons.append("Error Level Analysis detected editing artefacts in the image.")
        if forensic_data.get("copy_move_score", 0.0) > 0.40:
            reasons.append("Copy-move forgery patterns found — regions may have been cloned.")
        if forensic_data.get("tampering_score", 0.0) > 0.55:
            reasons.append("Composite tampering score is high — multiple forgery signals align.")
        if forensic_data.get("color_consistency_score", 0.0) > 0.50:
            reasons.append("Color inconsistency across image quadrants suggests pasted content.")
        if forensic_data.get("compression_artifact_score", 0.0) > 0.65:
            reasons.append("Unusual JPEG compression artefacts detected — typical of digital forgery.")

        # Verification match
        if not verification_match.get("match_found"):
            reasons.append("Certificate ID not found in the verification database.")
        elif verification_match.get("match_score", 0.0) < 0.60:
            score_pct = verification_match.get('match_score', 0.0) * 100
            reasons.append(f"ID matched but data consistency is low ({score_pct:.0f}% similarity).")

        if not reasons:
            reasons.append("All structural, visual, and database integrity checks passed.")

        return reasons

explainability_service = ExplainabilityService()
