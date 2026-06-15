from sqlalchemy import select, text
from sqlalchemy.orm import Session

from src.constants.error_codes import ERROR_CODES
from src.constants.log_templates import LOG_TEMPLATES
from src.middlewares.error_handler import AppError
from src.models.journal import Journal
from src.models.user import User
from src.schemas.journal import JournalCreate, JournalUpdate
from src.utils.logger import app_logger


def _column_exists(db: Session, table_name: str, column_name: str) -> bool:
    result = db.execute(
        text(
            "SELECT 1 FROM information_schema.columns WHERE table_name = :table AND column_name = :column"
        ),
        {"table": table_name, "column": column_name},
    )
    return result.scalar() is not None


def list_journals(db: Session, user: User, mood_level: int | None = None) -> list[Journal]:
    app_logger.info(LOG_TEMPLATES["JOURNAL_LIST"].format(user_id=user.id, mood_level=mood_level or "all"))
    query = select(Journal).where(Journal.user_id == user.id).order_by(Journal.created_at.desc())
    if mood_level:
        query = query.where(Journal.mood_level == mood_level)
    journals = list(db.scalars(query).all())
    has_mood_tags = _column_exists(db, "journals", "mood_tags")
    if not has_mood_tags:
        for journal in journals:
            journal.mood_tags = []
    return journals


def create_journal(db: Session, user: User, payload: JournalCreate) -> Journal:
    has_mood_tags = _column_exists(db, "journals", "mood_tags")
    if not has_mood_tags:
        payload_data = payload.model_dump(exclude={"mood_tags"})
        app_logger.info(
            LOG_TEMPLATES["JOURNAL_CREATE"].format(
                user_id=user.id,
                title=payload.title,
                mood_level=payload.mood_level,
                mood_tags="column_missing",
            )
        )
        journal = Journal(user_id=user.id, **payload_data)
        journal.mood_tags = payload.mood_tags
    else:
        app_logger.info(
            LOG_TEMPLATES["JOURNAL_CREATE"].format(
                user_id=user.id,
                title=payload.title,
                mood_level=payload.mood_level,
                mood_tags=",".join(payload.mood_tags) if payload.mood_tags else "none",
            )
        )
        journal = Journal(user_id=user.id, **payload.model_dump())
    db.add(journal)
    db.commit()
    db.refresh(journal)
    return journal


def update_journal(db: Session, user: User, journal_id: int, payload: JournalUpdate) -> Journal:
    journal = db.get(Journal, journal_id)
    if not journal or journal.user_id != user.id:
        raise AppError("JOURNAL_NOT_FOUND", f"Journal[id={journal_id}] update failed: {ERROR_CODES['JOURNAL_NOT_FOUND']}", 404)
    has_mood_tags = _column_exists(db, "journals", "mood_tags")
    update_data = payload.model_dump(exclude_unset=True)
    if not has_mood_tags and "mood_tags" in update_data:
        del update_data["mood_tags"]
    for field, value in update_data.items():
        setattr(journal, field, value)
    if not has_mood_tags and payload.mood_tags is not None:
        journal.mood_tags = payload.mood_tags
    app_logger.info(
        LOG_TEMPLATES["JOURNAL_UPDATE"].format(
            journal_id=journal_id, title=journal.title, is_private=journal.is_private
        )
    )
    db.commit()
    db.refresh(journal)
    return journal


def delete_journal(db: Session, user: User, journal_id: int) -> None:
    journal = db.get(Journal, journal_id)
    if not journal or journal.user_id != user.id:
        raise AppError("JOURNAL_NOT_FOUND", f"Journal[id={journal_id}] delete failed: {ERROR_CODES['JOURNAL_NOT_FOUND']}", 404)
    app_logger.info(LOG_TEMPLATES["JOURNAL_DELETE"].format(journal_id=journal_id, user_id=user.id))
    db.delete(journal)
    db.commit()

