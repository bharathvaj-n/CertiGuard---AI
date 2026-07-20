"""
CertiGuard AI — Inference Engine
=================================
Loads the trained GBM+RF ensemble and produces:
  - risk_score  : 0-100 (0 = definitely genuine, 100 = definitely fake)
  - status      : "Genuine" | "Needs Manual Review" | "Suspicious" | "Likely Fake"
  - confidence  : model confidence in its prediction (0-1)
  - top_reasons : top features driving the decision
"""

import joblib
import pandas as pd
import numpy as np
import os
from typing import Dict, Any, List

from app.services.feature_engineering import FEATURE_COLUMNS


# ------------------------------------------------------------------ #
#  Decision thresholds                                                 #
# ------------------------------------------------------------------ #
# Tuned to minimise false positives (genuine → fake misclassification)
THRESHOLD_GENUINE        = 0.35   # prob_fake < 0.35  → Genuine
THRESHOLD_MANUAL_REVIEW  = 0.50   # 0.35 ≤ prob_fake < 0.50 → Needs Manual Review
THRESHOLD_SUSPICIOUS     = 0.65   # 0.50 ≤ prob_fake < 0.65 → Suspicious
# prob_fake ≥ 0.65 → Likely Fake

# Features that, when high, are strong fake indicators
FAKE_INDICATOR_FEATURES = {
    "tampering_score":            "High image tampering detected",
    "ela_score":                  "Error Level Analysis shows editing artefacts",
    "copy_move_score":            "Copy-move forgery patterns detected",
    "compression_artifact_score": "Unusual JPEG compression artefacts",
    "edge_mismatch_score":        "Inconsistent edge transitions (splicing)",
    "color_consistency_score":    "Color inconsistency across image regions",
    "noise_score":                "Irregular noise distribution",
}

# Features that, when low, are fake indicators
GENUINE_INDICATOR_FEATURES = {
    "ocr_confidence":          "Low OCR confidence — text may be altered",
    "structural_completeness": "Key certificate fields could not be extracted",
    "logo_region_consistency": "Logo/seal region appears inconsistent",
    "layout_confidence":       "Certificate structure deviates from expected layout",
}


class PredictionClassifier:

    def __init__(self):
        self.model_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "models", "certificate_classifier.pkl")
        )
        self._model = None

    def _load_model(self):
        if self._model is None and os.path.exists(self.model_path):
            self._model = joblib.load(self.model_path)
        return self._model

    def predict_risk(self, feature_vector: Dict[str, Any]) -> Dict[str, Any]:
        model = self._load_model()

        # Ensure canonical feature order
        fv = {k: feature_vector.get(k, 0.0) for k in FEATURE_COLUMNS}

        if model is not None:
            try:
                df = pd.DataFrame([fv], columns=FEATURE_COLUMNS)
                probs = model.predict_proba(df)[0]
                prob_fake = float(probs[1]) if len(probs) > 1 else 0.5
                confidence = float(max(probs))
            except Exception:
                prob_fake, confidence = self._heuristic(fv)
        else:
            prob_fake, confidence = self._heuristic(fv)

        risk_score = prob_fake * 100.0
        status = self._status(prob_fake)
        top_reasons = self._explain(fv, prob_fake)

        return {
            "risk_score":   float(risk_score),
            "status":       status,
            "prob_fake":    float(prob_fake),
            "confidence":   float(confidence),
            "top_reasons":  top_reasons,
        }

    # ---------------------------------------------------------------- #

    @staticmethod
    def _status(prob_fake: float) -> str:
        if prob_fake >= THRESHOLD_SUSPICIOUS:
            return "Likely Fake"
        if prob_fake >= THRESHOLD_MANUAL_REVIEW:
            return "Suspicious"
        if prob_fake >= THRESHOLD_GENUINE:
            return "Needs Manual Review"
        return "Genuine"

    @staticmethod
    def _heuristic(fv: Dict[str, Any]):
        """Calibrated fallback when no model is available."""
        score = 0.20  # start optimistic
        score += fv.get("tampering_score", 0.0) * 0.30
        score += fv.get("ela_score", 0.0) * 0.25
        score += fv.get("copy_move_score", 0.0) * 0.20
        score += fv.get("edge_mismatch_score", 0.0) * 0.10
        score += fv.get("color_consistency_score", 0.0) * 0.10
        score -= fv.get("ocr_confidence", 0.0) * 0.05
        score -= fv.get("structural_completeness", 0.0) * 0.05
        prob_fake = float(np.clip(score, 0.0, 1.0))
        confidence = 0.60  # heuristic confidence is moderate
        return prob_fake, confidence

    @staticmethod
    def _explain(fv: Dict[str, Any], prob_fake: float) -> List[str]:
        """Return top 5 features driving the prediction."""
        reasons = []

        # Fake indicators — high values are suspicious
        for feat, msg in FAKE_INDICATOR_FEATURES.items():
            val = fv.get(feat, 0.0)
            if val > 0.55:
                reasons.append(f"{msg} ({val:.2f})")

        # Genuine indicators — low values are suspicious
        for feat, msg in GENUINE_INDICATOR_FEATURES.items():
            val = fv.get(feat, 1.0)
            if val < 0.45:
                reasons.append(f"{msg} ({val:.2f})")

        # If no strong signals and prediction is genuine
        if not reasons and prob_fake < THRESHOLD_GENUINE:
            reasons.append("All forensic and structural checks passed.")

        return reasons[:5]


prediction_classifier = PredictionClassifier()
