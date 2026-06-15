from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.database import Base
from src.constants.mood import MoodTag


class Journal(Base):
    __tablename__ = "journals"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    mood_level: Mapped[int] = mapped_column(Integer, nullable=False)
    mood_tags: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    weather: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_private: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="journals")

    def validate_tags_for_log_coupling(self) -> list[str]:
        allowed = {item.value for item in MoodTag}
        return [tag for tag in self.mood_tags if tag in allowed]

