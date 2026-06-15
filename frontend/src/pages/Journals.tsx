import { Button, Form, Input, Select, Switch, Tag } from 'antd';
import { useEffect, useState } from 'react';
import { createJournal, getJournals } from '../api/journal';
import { EmptyState } from '../components/common/EmptyState';
import { MoodCard } from '../components/common/MoodCard';
import { MOOD_LEVEL_LABELS, MOOD_TAG_LABELS, MoodTag } from '../constants/mood';
import { useAuth } from '../hooks/useAuth';
import { useMoodStore } from '../stores/moodStore';
import type { Journal, JournalPayload, Mood } from '../types';
import { MOOD_TAG_COLORS } from '../utils/moodColor';

export function Journals() {
  const { token, user } = useAuth();
  const { todayMood, loadTodayMood, loadMoods } = useMoodStore();
  const [journals, setJournals] = useState<Journal[]>([]);
  const [form] = Form.useForm<JournalPayload>();
  const [moodTags, setMoodTags] = useState<MoodTag[]>([]);
  const [autoFilled, setAutoFilled] = useState(false);

  const load = () => getJournals().then(setJournals).catch(() => setJournals([]));

  useEffect(() => {
    if (token) {
      load();
      loadTodayMood();
    }
  }, [token, loadTodayMood]);

  useEffect(() => {
    if (todayMood && !autoFilled) {
      form.setFieldsValue({
        mood_level: todayMood.mood_level,
      });
      setMoodTags(todayMood.mood_tags || []);
      setAutoFilled(true);
    }
  }, [todayMood, autoFilled, form]);

  const toggleTag = (tag: MoodTag) => {
    setMoodTags((current) =>
      current.includes(tag) ? current.filter((item) => item !== tag) : [...current, tag],
    );
  };

  const handleFinish = async (payload: JournalPayload) => {
    await createJournal({ ...payload, mood_tags: moodTags });
    form.resetFields();
    setMoodTags([]);
    setAutoFilled(false);
    load();
    loadMoods();
  };

  const journalAsMood = (journal: Journal): Mood => ({
    id: journal.id,
    user_id: journal.user_id,
    mood_level: journal.mood_level,
    mood_tags: journal.mood_tags && journal.mood_tags.length ? journal.mood_tags : (journal.mood_level >= 7 ? [MoodTag.CALM] : journal.mood_level <= 3 ? [MoodTag.ANXIOUS] : [MoodTag.TIRED]),
    note: journal.title,
    record_date: journal.created_at.slice(0, 10),
    created_at: journal.created_at,
  });

  return (
    <main className="page">
      <h1 className="page-title">日记本</h1>
      <p className="page-kicker">用更长文本记录情绪背后的事件、身体感受和自我照顾方案。</p>

      <section className="grid two">
        <div className="panel">
          <h2>富文本日记</h2>
          <Form
            form={form}
            layout="vertical"
            className="journal-editor"
            initialValues={{ mood_level: 7, weather: 'cloudy', is_private: true }}
            onFinish={handleFinish}
          >
            <Form.Item name="title" label="标题" rules={[{ required: true }]}>
              <Input placeholder={`${user?.nickname || '我'}的今日观察`} />
            </Form.Item>
            <Form.Item name="content" label="内容" rules={[{ required: true }]}>
              <Input.TextArea rows={8} placeholder="写下事件、想法、身体信号和下一步照顾自己的方式。" />
            </Form.Item>
            <Form.Item name="mood_level" label="关联心情">
              <Select options={Object.entries(MOOD_LEVEL_LABELS).map(([value, label]) => ({ value: Number(value), label: `${value} · ${label}` }))} />
            </Form.Item>
            <Form.Item label="情绪标签">
              <div className="mood-tag-row">
                {Object.values(MoodTag).map((tag) => (
                  <Tag.CheckableTag
                    key={tag}
                    checked={moodTags.includes(tag)}
                    onChange={() => toggleTag(tag)}
                    style={{
                      borderColor: MOOD_TAG_COLORS[tag],
                      color: moodTags.includes(tag) ? '#fff' : MOOD_TAG_COLORS[tag],
                      background: moodTags.includes(tag) ? MOOD_TAG_COLORS[tag] : 'transparent',
                      padding: '6px 10px',
                    }}
                  >
                    {MOOD_TAG_LABELS[tag]}
                  </Tag.CheckableTag>
                ))}
              </div>
              {todayMood && (
                <p className="muted" style={{ marginTop: 8, marginBottom: 0 }}>
                  已自动带入今日情绪记录。
                </p>
              )}
            </Form.Item>
            <Form.Item name="weather" label="天气">
              <Select options={['sunny', 'cloudy', 'rainy', 'windy'].map((value) => ({ value, label: value }))} />
            </Form.Item>
            <Form.Item name="is_private" label="私密" valuePropName="checked">
              <Switch />
            </Form.Item>
            <Button type="primary" htmlType="submit">保存日记</Button>
          </Form>
        </div>
        <div className="panel">
          <h2>按心情筛选</h2>
          <Select
            allowClear
            placeholder="选择心情等级"
            style={{ width: '100%' }}
            onChange={(value?: number) => getJournals(value).then(setJournals)}
            options={Object.entries(MOOD_LEVEL_LABELS).map(([value, label]) => ({ value: Number(value), label: `${value} · ${label}` }))}
          />
        </div>
      </section>

      <section style={{ marginTop: 18 }} className="timeline-list">
        {journals.length ? (
          journals.map((journal) => (
            <MoodCard
              key={journal.id}
              mood={journalAsMood(journal)}
              showJournalBadge={false}
              footer={<p className="muted">{journal.content}</p>}
            />
          ))
        ) : (
          <EmptyState title="还没有日记" description="写一篇日记后会按时间线展示。" />
        )}
      </section>
    </main>
  );
}
