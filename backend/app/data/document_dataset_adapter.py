import os
from typing import Dict, Any, List

class DocumentDatasetAdapter:
    """Adapter for document layout datasets (e.g. RVL-CDIP, FUNSD)."""
    
    def __init__(self, dataset_path: str = "dataset/document_understanding"):
        self.dataset_path = dataset_path
        # Field zone definitions (simulating learned field regions)
        self.field_zones = {
            "candidate_name": [0.3, 0.4, 0.6, 0.15], # [top, left, width, height] relative coordinates
            "issuer_name": [0.05, 0.3, 0.4, 0.1],
            "certificate_id": [0.7, 0.6, 0.3, 0.1],
            "issue_date": [0.7, 0.2, 0.3, 0.1],
            "certificate_title": [0.15, 0.25, 0.5, 0.1]
        }
    
    def get_layout_references(self, document_type: str = "certificate") -> Dict[str, List[float]]:
        """
        Returns likely field zones based on document type.
        """
        # In a real scenario, this would load pre-trained anchor boxes or region maps from RVL-CDIP or FUNSD.
        return self.field_zones

    def identify_likely_zones(self, img_width: int, img_height: int) -> Dict[str, Dict[str, int]]:
        """
        Map relative zones to pixel coordinates.
        """
        pixel_zones = {}
        for field, (top, left, width, height) in self.field_zones.items():
            pixel_zones[field] = {
                "x_min": int(left * img_width),
                "y_min": int(top * img_height),
                "x_max": int((left + width) * img_width),
                "y_max": int((top + height) * img_height)
            }
        return pixel_zones

    def map_extracted_segments(self, ocr_results: List[Dict[str, Any]], img_width: int, img_height: int) -> Dict[str, Any]:
        """
        Use document dataset references to map OCR text boxes to logical fields.
        """
        pixel_zones = self.identify_likely_zones(img_width, img_height)
        mapped_data = {field: "" for field in pixel_zones}
        
        for res in ocr_results:
            bbox = res.get('bbox', [])
            text = res.get('text', '')
            if not bbox: continue
            
            # Simple centroid intersection check
            cx = (bbox[0][0] + bbox[1][0] + bbox[2][0] + bbox[3][0]) / 4
            cy = (bbox[0][1] + bbox[1][1] + bbox[2][1] + bbox[3][1]) / 4
            
            for field, bounds in pixel_zones.items():
                if bounds["x_min"] <= cx <= bounds["x_max"] and bounds["y_min"] <= cy <= bounds["y_max"]:
                    mapped_data[field] = (mapped_data[field] + " " + text).strip()
                    
        return mapped_data

document_adapter = DocumentDatasetAdapter()
