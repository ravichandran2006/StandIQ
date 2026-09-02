from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class StandardCreate(BaseModel):
    is_number: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=500)
    standard_type: str | None = Field(default=None, max_length=80)
    status: str = Field(default="unknown", min_length=1, max_length=30)
    publication_info: str | None = None
    review_info: str | None = None
    technical_committee: str | None = Field(default=None, max_length=255)


class StandardUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(default=None, min_length=1, max_length=500)
    standard_type: str | None = Field(default=None, max_length=80)
    status: str | None = Field(default=None, min_length=1, max_length=30)
    publication_info: str | None = None
    review_info: str | None = None
    technical_committee: str | None = Field(default=None, max_length=255)


class StandardSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    is_number: str
    title: str
    standard_type: str | None
    status: str


class StandardResponse(StandardSummary):
    publication_info: str | None
    review_info: str | None
    technical_committee: str | None
    created_at: datetime
    updated_at: datetime


class StandardListResponse(BaseModel):
    items: list[StandardSummary]
    total: int
    offset: int
    limit: int


class VersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    standard_id: str
    edition_label: str
    edition_year: int | None
    publication_date: date | None
    is_current: bool | None
    status: str


class RelationshipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    source_standard_id: str
    target_standard_id: str
    relationship_type: str
    evidence_note: str | None