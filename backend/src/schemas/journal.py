from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from src.constants.error_codes import ERROR_CODES
from src.constants.mood import MoodTag


class JournalBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    mood_level: int = Field(ge=1, le=10)
    mood_tags: list[str] = []
    weather: str | None = None
    is_private: bool = True

    @field_validator("mood_tags")
    @classmethod
    def validate_mood_tags(cls, value: list[str]) -> list[str]:
        allowed = {tag.value for tag in MoodTag}
        invalid = [item for item in value if item not in allowed]
        if invalid:
            raise ValueError(f"{ERROR_CODES['MOOD_TAG_INVALID']}: {invalid}")
        return value


class JournalCreate(JournalBase):
    pass


class JournalUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1)
    mood_level: int | None = Field(default=None, ge=1, le=10)
    mood_tags: list[str] | None = None
    weather: str | None = None
    is_private: bool | None = None

    @field_validator("mood_tags")
    @classmethod
    def validate_mood_tags_update(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        allowed = {tag.value for tag in MoodTag}
        invalid = [item for item in value if item not in allowed]
        if invalid:
            raise ValueError(f"{ERROR_CODES['MOOD_TAG_INVALID']}: {invalid}")
        return value


class JournalRead(JournalBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = {"from_attributes": True}

