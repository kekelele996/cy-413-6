-- Migration: 001_add_journal_mood_tags
-- Description: 为 journals 表添加 mood_tags 字段，用于日记与情绪记录联动
-- Re-runnable: YES (使用 IF NOT EXISTS)
-- Applied At: 2026-06-15

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
