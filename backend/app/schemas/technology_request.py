from datetime import datetime

from pydantic import BaseModel, Field


class TechnologyRequestCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    note: str | None = Field(default=None, max_length=500)


class TechnologyRequestRead(BaseModel):
    id: int
    name: str
    note: str | None
    request_count: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
