from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class WaypointInput(BaseModel):
    x: float = Field(..., ge=-1000.0, le=1000.0)
    y: float = Field(..., ge=-1000.0, le=1000.0)
    label: str | None = Field(default=None, max_length=30)


class AbortInput(BaseModel):
    reason: str = Field(..., min_length=3, max_length=180)


class MissionEvent(BaseModel):
    timestamp_ms: int
    level: str
    message: str
    details: dict[str, Any] | None = None
