import cv2
import numpy as np
from typing import Dict, Any
from app.data.forgery_dataset_adapter import forgery_adapter


def preprocess_for_forensics(img: np.ndarray) -> np.ndarray:
    """
    Enhance image for forensic analysis:
    - Denoise to reduce scanner noise
    - CLAHE for contrast normalisation
    Returns BGR image suitable for forensic scoring.
    """
    # Mild denoising — preserve edges, remove scanner grain
    denoised = cv2.fastNlMeansDenoisingColored(img, None, h=5, hColor=5,
                                               templateWindowSize=7, searchWindowSize=21)
    # CLAHE on L channel of LAB for contrast normalisation
    lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_eq = clahe.apply(l)
    lab_eq = cv2.merge([l_eq, a, b])
    return cv2.cvtColor(lab_eq, cv2.COLOR_LAB2BGR)


class ImageForensicsService:

    def analyze_image(self, image_path: str, img: np.ndarray = None) -> Dict[str, Any]:
        if img is None:
            img = cv2.imread(image_path)
        if img is None:
            return _empty_result()

        # Preprocess before forensic scoring
        processed = preprocess_for_forensics(img)

        scores = forgery_adapter.generate_forensic_features_from_img(processed)

        # Blur score on original (not processed) — CLAHE would affect it
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur_val = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        # Map: 500+ → 0.0 (sharp), 50 → 0.5, 10 → 0.9
        blur_score = float(np.clip(1.0 - (blur_val / 500.0), 0.0, 1.0))

        # Composite tampering score — weighted combination of strongest signals
        tampering_score = float(np.clip(
            scores["ela_score"] * 0.40 +
            scores["copy_move_score"] * 0.30 +
            scores["edge_inconsistency_score"] * 0.15 +
            scores["color_consistency_score"] * 0.15,
            0.0, 1.0
        ))

        return {
            "tampering_score":            tampering_score,
            "ela_score":                  scores["ela_score"],
            "copy_move_score":            scores["copy_move_score"],
            "logo_region_consistency":    1.0 - scores["noise_score"],
            "compression_artifact_score": scores["compression_artifact_score"],
            "edge_mismatch_score":        scores["edge_inconsistency_score"],
            "color_consistency_score":    scores["color_consistency_score"],
            "blur_score":                 blur_score,
            "noise_score":                scores["noise_score"],
        }


def _empty_result() -> Dict[str, Any]:
    return {
        "tampering_score": 0.0, "ela_score": 0.0, "copy_move_score": 0.0,
        "logo_region_consistency": 1.0, "compression_artifact_score": 0.0,
        "edge_mismatch_score": 0.0, "color_consistency_score": 0.0,
        "blur_score": 0.0, "noise_score": 0.0,
    }


image_forensics_service = ImageForensicsService()
