from collections import Counter, defaultdict
from datetime import date

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from src.constants.error_codes import ERROR_CODES
from src.constants.log_templates import LOG_TEMPLATES
from src.middlewares.error_handler import AppError
from src.models.journal import Journal
from src.models.mood import Mood
from src.models.user import User
from src.schemas.mood import JournalSummary, MoodCreate, MoodReadWithJournal, MoodTrendPoint, MoodUpdate
from src.utils.formatters import format_date
from src.utils.logger import app_logger


def _enrich_with_journal(db: Session, user: User, moods: list[Mood]) -> list[MoodReadWithJournal]:
    result: list[MoodReadWithJournal] = []
    mood_dates = {mood.record_date for mood in moods}
    journals_by_date: dict[date, list[Journal]] = defaultdict(list)
    if mood_dates:
        journals = list(
            db.scalars(
                select(Journal).where(
                    Journal.user_id == user.id, Journal.created_at >= min(mood_dates)
                )
            ).all()
        )
        for journal in journals:
            journal_date = journal.created_at.date()
            journals_by_date[journal_date].append(journal)
    for mood in moods:
        journal_data = None
        has_journal = False
        day_journals = journals_by_date.get(mood.record_date, [])
        if day_journals:
            latest = max(day_journals, key=lambda j: j.created_at)
            excerpt = latest.content[:40] + "…" if len(latest.content) > 40 else latest.content
            journal_data = JournalSummary(id=latest.id, title=latest.title, content_excerpt=excerpt)
            has_journal = True
        result.append(
            MoodReadWithJournal(
                id=mood.id,
                user_id=mood.user_id,
                mood_level=mood.mood_level,
                mood_tags=mood.mood_tags,
                note=mood.note,
                record_date=mood.record_date,
                created_at=mood.created_at,
                has_journal=has_journal,
                journal=journal_data,
            )
        )
    return result


def list_moods(
    db: Session, user: User, start_date: date | None = None, end_date: date | None = None
) -> list[MoodReadWithJournal]:
    app_logger.info(
        LOG_TEMPLATES["MOOD_LIST"].format(user_id=user.id, start_date=start_date, end_date=end_date)
    )
    query = select(Mood).where(Mood.user_id == user.id).order_by(Mood.record_date.desc(), Mood.id.desc())
    if start_date:
        query = query.where(Mood.record_date >= start_date)
    if end_date:
        query = query.where(Mood.record_date <= end_date)
    moods = list(db.scalars(query).all())
    return _enrich_with_journal(db, user, moods)


def get_today_mood(db: Session, user: User) -> Mood | None:
    today = date.today()
    app_logger.info(LOG_TEMPLATES["MOOD_TODAY_GET"].format(user_id=user.id, today=today))
    mood = db.scalars(
        select(Mood)
        .where(and_(Mood.user_id == user.id, Mood.record_date == today))
        .order_by(Mood.created_at.desc())
        .limit(1)
    ).first()
    return mood


def create_mood(db: Session, user: User, payload: MoodCreate) -> Mood:
    app_logger.info(
        LOG_TEMPLATES["MOOD_CREATE"].format(
            user_id=user.id,
            mood_level=payload.mood_level,
            mood_tags=",".join(payload.mood_tags),
            record_date=payload.record_date,
        )
    )
    mood = Mood(user_id=user.id, **payload.model_dump())
    db.add(mood)
    db.commit()
    db.refresh(mood)
    return mood


def update_mood(db: Session, user: User, mood_id: int, payload: MoodUpdate) -> Mood:
    mood = db.get(Mood, mood_id)
    if not mood or mood.user_id != user.id:
        raise AppError(
            "MOOD_NOT_FOUND", f"Mood[id={mood_id}] update failed: {ERROR_CODES['MOOD_NOT_FOUND']}", 404
        )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(mood, field, value)
    app_logger.info(
        LOG_TEMPLATES["MOOD_UPDATE"].format(
            mood_id=mood_id,
            mood_level=mood.mood_level,
            mood_tags=",".join(mood.mood_tags),
        )
    )
    db.commit()
    db.refresh(mood)
    return mood


def delete_mood(db: Session, user: User, mood_id: int) -> None:
    mood = db.get(Mood, mood_id)
    if not mood or mood.user_id != user.id:
        raise AppError(
            "MOOD_NOT_FOUND", f"Mood[id={mood_id}] delete failed: {ERROR_CODES['MOOD_NOT_FOUND']}", 404
        )
    app_logger.info(LOG_TEMPLATES["MOOD_DELETE"].format(mood_id=mood_id, user_id=user.id))
    db.delete(mood)
    db.commit()


def mood_trend(db: Session, user: User) -> list[MoodTrendPoint]:
    moods = list(
        db.scalars(select(Mood).where(Mood.user_id == user.id).order_by(Mood.record_date.asc())).all()
    )
    grouped: dict[str, list[Mood]] = defaultdict(list)
    for mood in moods:
        grouped[format_date(mood.record_date)].append(mood)
    points: list[MoodTrendPoint] = []
    for day, day_moods in grouped.items():
        avg = sum(item.mood_level for item in day_moods) / len(day_moods)
        tags = Counter(tag for item in day_moods for tag in item.mood_tags)
        dominant = tags.most_common(1)[0][0] if tags else "calm"
        points.append(MoodTrendPoint(date=day, mood_level=round(avg, 2), dominant_tag=dominant))
    app_logger.info(
        LOG_TEMPLATES["MOOD_TREND"].format(user_id=user.id, mood_tags=[point.dominant_tag for point in points])
    )
    return points

