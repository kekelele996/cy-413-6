import type { ReactNode } from 'react';
import { Badge, Tag } from 'antd';
import { MOOD_LEVEL_LABELS, MOOD_TAG_LABELS } from '../../constants/mood';
import type { Mood } from '../../types';
import { displayDate } from '../../utils/dateRange';
import { moodLevelColor, MOOD_TAG_COLORS } from '../../utils/moodColor';

interface Props {
  mood: Mood;
  footer?: ReactNode;
  showJournalBadge?: boolean;
}

export function MoodCard({ mood, footer, showJournalBadge = true }: Props) {
  return (
    <article className="mood-card">
      <div className="mood-card-head">
        <div>
          <strong>
            {showJournalBadge && mood.has_journal ? (
              <Badge
                status="processing"
                text={displayDate(mood.record_date)}
                color={moodLevelColor(mood.mood_level)}
              />
            ) : (
              displayDate(mood.record_date)
            )}
          </strong>
          <div className="muted">
            等级 {mood.mood_level} · {MOOD_LEVEL_LABELS[mood.mood_level]}
            {showJournalBadge && mood.has_journal && <span style={{ marginLeft: 8 }}>📝 已写日记</span>}
          </div>
        </div>
        <div>
          {mood.mood_tags.map((tag) => (
            <Tag key={tag} color={MOOD_TAG_COLORS[tag]}>
              {MOOD_TAG_LABELS[tag]}
            </Tag>
          ))}
        </div>
      </div>
      {mood.note && <p>{mood.note}</p>}
      {mood.journal && (
        <div style={{ padding: '8px 12px', background: 'var(--bg-secondary)', borderRadius: 6, margin: '8px 0', borderLeft: `3px solid ${moodLevelColor(mood.mood_level)}` }}>
          <p style={{ margin: 0, fontWeight: 600, fontSize: 13 }}>📓 {mood.journal.title}</p>
          <p className="muted" style={{ margin: '4px 0 0 0', fontSize: 12 }}>
            {mood.journal.content_excerpt}
          </p>
        </div>
      )}
      <div className="tone-strip" style={{ background: moodLevelColor(mood.mood_level) }} />
      {footer}
    </article>
  );
}
