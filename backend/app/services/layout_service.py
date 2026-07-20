import cv2
import numpy as np
from typing import Dict, Any, List
from app.data.document_dataset_adapter import document_adapter

class LayoutService:
    def __init__(self):
        self.adapter = document_adapter

    def analyze_layout(self, image_path: str, ocr_results: List[Dict[str, Any]], img: np.ndarray = None) -> Dict[str, Any]:
        """Accept pre-loaded image to avoid redundant disk reads."""
        if img is None:
            img = cv2.imread(image_path)
        if img is None:
            return {}
        h, w = img.shape[:2]
        mapped_data = self.adapter.map_extracted_segments(ocr_results, w, h)
        return {k: v for k, v in mapped_data.items() if v}

layout_service = LayoutService()
