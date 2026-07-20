import pandas as pd
from typing import Dict, Any


# Canonical feature order — must match training exactly
FEATURE_COLUMNS = [
    "ocr_confidence",
    "structural_completeness",
    "ocr_word_count",
    "id_valid",
    "issue_date_valid",
    "issuer_match_score",
    "tampering_score",
    "ela_score",
    "copy_move_score",
    "logo_region_consistency",
    "compression_artifact_score",
    "edge_mismatch_score",
    "color_consistency_score",
    "noise_score",
    "blur_score",
    "verification_match",
    "layout_confidence",
]


class FeatureEngineering:

    def generate_features(
        self,
        ocr_data: Dict[str, Any],
        layout_data: Dict[str, Any],
        forensic_data: Dict[str, Any],
        rule_data: Dict[str, Any],
        verification_match: Dict[str, Any],
    ) -> Dict[str, Any]:

        flags = rule_data.get("validation_flags", {})

        features = {
            # OCR quality
            "ocr_confidence":          float(ocr_data.get("ocr_confidence", 0.0)),
            "structural_completeness": float(ocr_data.get("structural_completeness", 0.0)),
            "ocr_word_count":          min(int(ocr_data.get("ocr_word_count", 0)), 1000) / 1000.0,

            # Rule engine
            "id_valid":                int(not flags.get("invalid_id_format", False)),
            "issue_date_valid":        int(not flags.get("missing_issue_date", False)),
            "issuer_match_score":      float(verification_match.get("match_score", 0.0)),
            "layout_confidence":       float(rule_data.get("rule_score", 0.0)),

            # Forensics — all calibrated scores
            "tampering_score":            float(forensic_data.get("tampering_score", 0.0)),
            "ela_score":                  float(forensic_data.get("ela_score", 0.0)),
            "copy_move_score":            float(forensic_data.get("copy_move_score", 0.0)),
            "logo_region_consistency":    float(forensic_data.get("logo_region_consistency", 1.0)),
            "compression_artifact_score": float(forensic_data.get("compression_artifact_score", 0.0)),
            "edge_mismatch_score":        float(forensic_data.get("edge_mismatch_score", 0.0)),
            "color_consistency_score":    float(forensic_data.get("color_consistency_score", 0.0)),
            "noise_score":                float(forensic_data.get("noise_score", 0.0)),
            "blur_score":                 float(forensic_data.get("blur_score", 0.0)),

            # DB verification
            "verification_match": int(verification_match.get("match_found", False)),
        }

        # Ensure canonical column order
        return {k: features[k] for k in FEATURE_COLUMNS}

    def to_dataframe(self, features: Dict[str, Any]) -> pd.DataFrame:
        return pd.DataFrame([features], columns=FEATURE_COLUMNS)


feature_engineering = FeatureEngineering()
