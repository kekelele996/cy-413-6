from sqlalchemy import text
from sqlalchemy.orm import Session

from src.config.database import SessionLocal
from src.constants.log_templates import LOG_TEMPLATES
from src.utils.logger import app_logger

MIGRATIONS: list[tuple[str, str]] = [
    (
        "001_add_journal_mood_tags",
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'journals' AND column_name = 'mood_tags'
            ) THEN
                ALTER TABLE journals ADD COLUMN mood_tags TEXT[] NOT NULL DEFAULT '{}';
                RAISE NOTICE 'Migration 001 applied: added journals.mood_tags';
            ELSE
                RAISE NOTICE 'Migration 001 skipped: journals.mood_tags already exists';
            END IF;
        END $$;
        """,
    ),
]


def run_migrations() -> None:
    db: Session = SessionLocal()
    try:
        applied = 0
        skipped = 0
        for name, sql in MIGRATIONS:
            result = db.execute(text("SELECT 1 FROM information_schema.tables WHERE table_name = 'journals'"))
            table_exists = result.scalar() is not None
            if not table_exists:
                app_logger.info(LOG_TEMPLATES["MIGRATION_SKIP"].format(name=name, reason="table not ready"))
                skipped += 1
                continue
            try:
                db.execute(text(sql))
                db.commit()
                app_logger.info(LOG_TEMPLATES["MIGRATION_APPLY"].format(name=name))
                applied += 1
            except Exception as exc:
                db.rollback()
                app_logger.warning(
                    LOG_TEMPLATES["MIGRATION_WARN"].format(name=name, error=str(exc))
                )
                skipped += 1
        app_logger.info(
            LOG_TEMPLATES["MIGRATION_SUMMARY"].format(applied=applied, skipped=skipped, total=len(MIGRATIONS))
        )
    finally:
        db.close()
