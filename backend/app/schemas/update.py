from datetime import datetime

from pydantic import BaseModel, HttpUrl

from app.schemas.technology import TechnologyRead


class SourceRead(BaseModel):
    id: int
    name: str
    domain: str
    source_type: str
    official: bool
    trust_score: int

    model_config = {"from_attributes": True}


class DeveloperUpdateRead(BaseModel):
    id: int
    title: str
    canonical_url: HttpUrl
    original_excerpt: str | None
    summary: str
    why_it_matters: str | None
    recommended_action: str | None
    version: str | None
    category: str
    impact_level: str
    published_at: datetime | None
    discovered_at: datetime
    source: SourceRead
    technologies: list[TechnologyRead]

    model_config = {"from_attributes": True}


class FeedResponse(BaseModel):
    items: list[DeveloperUpdateRead]
    total: int
    page: int
    page_size: int
    new_updates: int
    requiring_action: int
    technologies_tracked: int
    last_updated_at: datetime | None
    refresh_running: bool = False
    stale: bool = False
    refresh_started: bool = False
    cooldown_until: datetime | None = None
