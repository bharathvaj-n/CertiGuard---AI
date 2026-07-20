import easyocr
import cv2
import numpy as np
import os
import re
from typing import Dict, Any, List
import threading


def preprocess_for_ocr(img: np.ndarray) -> np.ndarray:
    """
    Enhance image for OCR:
    1. Convert to grayscale
    2. Denoise
    3. Adaptive threshold (binarise)
    4. Deskew
    Returns a 3-channel BGR image (EasyOCR accepts BGR).
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Denoise
    gray = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)

    # Adaptive binarisation — handles uneven lighting
    binary = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 10
    )

    # Deskew using moments
    coords = np.column_stack(np.where(binary < 128))
    if len(coords) > 100:
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = 90 + angle
        if abs(angle) > 0.5:
            h, w = binary.shape
            M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
            binary = cv2.warpAffine(binary, M, (w, h),
                                    flags=cv2.INTER_CUBIC,
                                    borderMode=cv2.BORDER_REPLICATE)

    # Return as 3-channel so EasyOCR accepts it
    return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)


class OCRService:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        import torch
        use_gpu = torch.cuda.is_available()
        self.reader = easyocr.Reader(['en'], gpu=use_gpu, verbose=False)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _load_image(self, image_path: str) -> np.ndarray:
        """Load image — handles PDF and image files, returns BGR numpy array."""
        ext = os.path.splitext(image_path)[1].lower()
        if ext == '.pdf':
            import fitz
            doc = fitz.open(image_path)
            if doc.page_count == 0:
                raise ValueError(f"Empty PDF: {image_path}")
            page = doc.load_page(0)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
            img = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR if pix.n == 4 else cv2.COLOR_RGB2BGR)
            doc.close()
        else:
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not load image: {image_path}")

        # Resize — 1200px max for OCR (balance speed vs accuracy)
        h, w = img.shape[:2]
        if max(h, w) > 1200:
            scale = 1200.0 / max(h, w)
            img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        return img

    def extract_text_from_image(self, image_path: str, img: np.ndarray = None) -> Dict[str, Any]:
        """Run OCR with preprocessing. Accepts pre-loaded image."""
        if img is None:
            img = self._load_image(image_path)

        # Run OCR on preprocessed image for better accuracy
        processed = preprocess_for_ocr(img)
        results = self.reader.readtext(processed, batch_size=4, paragraph=False, workers=0)

        # If preprocessing hurt results (very few detections), fall back to original
        if len(results) < 3:
            results = self.reader.readtext(img, batch_size=4, paragraph=False, workers=0)

        fields: Dict[str, Any] = {
            "candidate_name": None, "issuer_name": None,
            "certificate_id": None, "issue_date": None,
            "course_name": None, "raw_text": [],
            "confidence": [], "boxes": [],
            "ocr_word_count": 0,
        }
        conf_sum = 0.0
        ocr_list = []

        for (bbox, text, prob) in results:
            text = text.strip()
            if not text:
                continue
            p = float(prob)
            p_bbox = [[int(c) for c in pt] for pt in bbox]

            fields["raw_text"].append(text)
            fields["confidence"].append(p)
            fields["boxes"].append(p_bbox)
            conf_sum += p
            ocr_list.append({"bbox": p_bbox, "text": text, "prob": p})

            lower = text.lower()

            # Certificate ID — multiple patterns
            if re.search(r'\b(cert|id|no|serial|ref)[:\s#]+', lower):
                candidate_id = re.sub(r'[^A-Z0-9\-/]', '', text.upper())
                if len(candidate_id) >= 3:
                    fields["certificate_id"] = candidate_id

            # Issue date — month name or date pattern
            date_pattern = r'\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\d{4})\b'
            months = ["january","february","march","april","may","june",
                      "july","august","september","october","november","december"]
            if any(m in lower for m in months) or re.search(date_pattern, text):
                fields["issue_date"] = text

            # Candidate name — after trigger phrases
            name_triggers = [
                "certifies that", "presented to", "awarded to",
                "this is to certify", "hereby certify", "conferred upon",
                "given to", "this certifies", "is hereby awarded to",
            ]
            trigger = next((t for t in name_triggers if t in lower), None)
            if trigger:
                suffix = text[lower.find(trigger) + len(trigger):].strip()
                if len(suffix.split()) >= 2:
                    fields["candidate_name"] = suffix
                    fields["_name_next"] = False
                else:
                    fields["_name_next"] = True
            elif fields.get("_name_next") and not fields["candidate_name"]:
                if (len(text.split()) >= 2 and
                        not any(w in lower for w in [
                            "certificate", "completion", "achievement",
                            "excellence", "date", "no:", "#", "course",
                        ])):
                    fields["candidate_name"] = text
                    fields["_name_next"] = False

            # Issuer name
            issuer_triggers = [
                "issued by", "authorized by", "signed by", "on behalf of",
                "university", "institute", "college", "academy", "school of",
                "institution", "board of",
            ]
            if any(t in lower for t in issuer_triggers) and not fields["issuer_name"]:
                fields["issuer_name"] = text

            # Course name
            course_triggers = [
                "course", "program", "degree", "diploma",
                "in the field of", "major in", "specialization", "training in",
            ]
            if any(t in lower for t in course_triggers) and not fields["course_name"]:
                fields["course_name"] = text

        n = max(len(results), 1)
        fields["ocr_confidence"] = conf_sum / n
        fields["ocr_word_count"] = sum(len(t.split()) for t in fields["raw_text"])
        fields["ocr_results_list"] = ocr_list

        # Structural completeness score (0-1): how many key fields were found
        found = sum(1 for f in ["candidate_name", "issuer_name", "certificate_id", "issue_date"]
                    if fields.get(f))
        fields["structural_completeness"] = found / 4.0

        return fields


ocr_service = OCRService.get_instance()
