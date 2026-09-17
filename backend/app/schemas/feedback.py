from datetime import datetime

from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    email: str | None = Field(default=None, max_length=255)
    rating: int | None = Field(default=None, ge=1, le=5)
    message: str = Field(min_length=1, max_length=4000)


class FeedbackRead(BaseModel):
    id: int
    name: str | None
    email: str | None
    rating: int | None
    message: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FeedbackPublicRead(BaseModel):
    """Approved reviews shown on the public site — no email address."""

    id: int
    name: str | None
    rating: int | None
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}
