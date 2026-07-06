from pydantic import BaseModel
from typing import List, Dict, Optional

class RegionInfo(BaseModel):
    id: int
    bbox: List[int]      # [x, y, w, h]
    centroid: List[int]  # [cx, cy]
    area: float
    location: str
    severity: str        # 'low', 'medium', 'high'
    crop_ref_url: Optional[str] = None
    crop_cmp_url: Optional[str] = None


class DiffStatistics(BaseModel):
    total_regions: int
    total_changed_area_px: float
    change_percentage: float
    regions: List[RegionInfo]

class ComparisonResponse(BaseModel):
    session_id: str
    status: str
    similarity_score: float
    statistics: DiffStatistics
    summary: str
    visualizations: Dict[str, str]  # Map of visual type (e.g. 'color_diff') to file URL
