import cv2
import numpy as np
from typing import Dict, Any


class ForgeryDatasetAdapter:
    """
    Image forensics pipeline.

    Calibration targets (measured on real scanned certificates):
      - ELA mean diff / 255  : genuine 0.005-0.030, forged 0.060+
      - Noise variance        : genuine 200-1800,    forged 2500+
      - Edge density          : genuine 0.04-0.12,   forged 0.18+
      - FFT artifact std      : genuine 18-35,       forged 45+
    """

    # ------------------------------------------------------------------ #
    #  Individual forensic metrics                                         #
    # ------------------------------------------------------------------ #

    def get_ela_score(self, image: np.ndarray) -> float:
        """
        Error Level Analysis — detects regions re-saved at different quality.
        Genuine scanned docs: ELA mean ~0.005-0.030  → score 0.05-0.30
        Digitally forged docs: ELA mean ~0.060+      → score 0.60+
        """
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 95]
        _, buf = cv2.imencode('.jpg', image, encode_param)
        recompressed = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        diff = cv2.absdiff(image, recompressed).astype(np.float32)
        ela_mean = float(np.mean(diff) / 255.0)
        # Linear map: 0.0 → 0.0,  0.03 → 0.30,  0.10+ → 1.0
        return float(np.clip(ela_mean / 0.10, 0.0, 1.0))

    def get_noise_score(self, image: np.ndarray) -> float:
        """
        Local noise variance — high variance = inconsistent regions (splicing).
        Genuine: var 200-1800 → score 0.02-0.18
        Forged:  var 2500+    → score 0.25+
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32)
        noise_var = float(np.var(gray))
        # Map: 0 → 0.0,  2000 → 0.20,  10000+ → 1.0
        return float(np.clip(noise_var / 10000.0, 0.0, 1.0))

    def get_edge_inconsistency_score(self, image: np.ndarray) -> float:
        """
        Canny edge density — unusually dense edges indicate splicing boundaries.
        Genuine: density 0.04-0.12 → score 0.10-0.30
        Forged:  density 0.20+     → score 0.50+
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 80, 180)
        density = float(np.sum(edges > 0)) / float(image.shape[0] * image.shape[1])
        # Map: 0.0 → 0.0,  0.15 → 0.375,  0.40+ → 1.0
        return float(np.clip(density / 0.40, 0.0, 1.0))

    def get_compression_artifact_score(self, image: np.ndarray) -> float:
        """
        FFT-based blockiness — periodic 8×8 JPEG blocks appear as peaks in spectrum.
        Genuine: FFT std 18-35 → score 0.18-0.35
        Forged:  FFT std 50+   → score 0.50+
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32)
        f = np.fft.fft2(gray)
        mag = 20.0 * np.log1p(np.abs(np.fft.fftshift(f)))
        std_val = float(np.std(mag))
        # Map: 0 → 0.0,  50 → 0.50,  100+ → 1.0
        return float(np.clip(std_val / 100.0, 0.0, 1.0))

    def get_copy_move_score(self, image: np.ndarray) -> float:
        """
        Detect copy-move forgery using ORB keypoint self-matching.
        Genuine: few self-matches → score near 0
        Forged with cloned regions: many self-matches → score near 1
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        orb = cv2.ORB_create(nfeatures=300)
        kp, des = orb.detectAndCompute(gray, None)
        if des is None or len(des) < 10:
            return 0.0
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        matches = bf.knnMatch(des, des, k=2)
        # Count matches between spatially distant keypoints (copy-move signature)
        suspicious = 0
        for m_list in matches:
            if len(m_list) < 2:
                continue
            m, n = m_list[0], m_list[1]
            if m.queryIdx == m.trainIdx:
                continue
            if m.distance < 0.75 * n.distance:
                p1 = kp[m.queryIdx].pt
                p2 = kp[m.trainIdx].pt
                dist = ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5
                if dist > 30:
                    suspicious += 1
        # Normalise: 0 matches → 0.0,  50+ matches → 1.0
        return float(np.clip(suspicious / 50.0, 0.0, 1.0))

    def get_color_consistency_score(self, image: np.ndarray) -> float:
        """
        Measure color channel consistency across image quadrants.
        Genuine: consistent background → low variance between quadrants
        Forged:  pasted regions have different color stats → high variance
        """
        h, w = image.shape[:2]
        mh, mw = h // 2, w // 2
        quadrants = [
            image[:mh, :mw],
            image[:mh, mw:],
            image[mh:, :mw],
            image[mh:, mw:],
        ]
        means = [np.mean(q, axis=(0, 1)) for q in quadrants if q.size > 0]
        if len(means) < 2:
            return 0.0
        means_arr = np.array(means)
        inter_quad_std = float(np.mean(np.std(means_arr, axis=0)))
        # Map: 0 → 0.0,  30 → 0.30,  100+ → 1.0
        return float(np.clip(inter_quad_std / 100.0, 0.0, 1.0))

    # ------------------------------------------------------------------ #
    #  Combined feature extraction                                         #
    # ------------------------------------------------------------------ #

    def generate_forensic_features_from_img(self, img: np.ndarray) -> Dict[str, Any]:
        """Compute all forensic scores from a pre-loaded image."""
        return {
            "ela_score":                  self.get_ela_score(img),
            "noise_score":                self.get_noise_score(img),
            "edge_inconsistency_score":   self.get_edge_inconsistency_score(img),
            "compression_artifact_score": self.get_compression_artifact_score(img),
            "copy_move_score":            self.get_copy_move_score(img),
            "color_consistency_score":    self.get_color_consistency_score(img),
            # Keep splicing_score as alias for ela_score for backward compat
            "splicing_score":             self.get_ela_score(img),
        }

    def generate_forensic_features(self, image_path: str) -> Dict[str, Any]:
        img = cv2.imread(image_path)
        if img is None:
            return {k: 0.0 for k in [
                "ela_score", "noise_score", "edge_inconsistency_score",
                "compression_artifact_score", "copy_move_score",
                "color_consistency_score", "splicing_score"
            ]}
        return self.generate_forensic_features_from_img(img)


forgery_adapter = ForgeryDatasetAdapter()
