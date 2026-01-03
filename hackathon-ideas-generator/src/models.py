from pydantic import BaseModel, Field
from typing import List, Literal


class HackathonConstraints(BaseModel):
    duration_hours: int = Field(..., gt=0, le=72)
    max_team_size: int = Field(..., ge=1, le=6)
    target_level: Literal["junior", "mid", "mid-senior"]
    audience: Literal["students", "professionals", "mixed"]

    soft_guidelines: List[str]
    forbidden_patterns: List[str]
