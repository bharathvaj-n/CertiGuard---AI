from pydantic import BaseModel
from typing import Optional

class AnalyzeRequest(BaseModel):
    file_id: str
    filename: str
    file_path: str
