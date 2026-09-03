from pydantic import BaseModel


class TechnologyRead(BaseModel):
    id: int
    name: str
    slug: str
    icon: str
    keywords: list[str]
    trusted_domains: list[str]
    official_domains: list[str]
    active: bool
    refresh_interval_hours: int

    model_config = {"from_attributes": True}
