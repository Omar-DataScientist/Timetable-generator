const SUBJECT_COLORS = [
  { bg: 'rgba(6,182,212,0.15)',   border: '#06b6d4', text: '#06b6d4' },   // cyan
  { bg: 'rgba(139,92,246,0.15)',  border: '#8b5cf6', text: '#8b5cf6' },   // violet
  { bg: 'rgba(245,158,11,0.15)',  border: '#f59e0b', text: '#f59e0b' },   // amber
  { bg: 'rgba(16,185,129,0.15)',  border: '#10b981', text: '#10b981' },   // emerald
  { bg: 'rgba(244,63,94,0.15)',   border: '#f43f5e', text: '#f43f5e' },   // rose
  { bg: 'rgba(249,115,22,0.15)',  border: '#f97316', text: '#f97316' },   // orange
  { bg: 'rgba(99,102,241,0.15)',  border: '#6366f1', text: '#6366f1' },   // indigo
  { bg: 'rgba(20,184,166,0.15)',  border: '#14b8a6', text: '#14b8a6' },   // teal
];

const DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
const SLOT_TIMES = [
  '8–9 AM', '9–10 AM', '10–11 AM', '11 AM–12 PM',
  '12–1 PM', '1–2 PM', '2–3 PM', '3–4 PM', '4–5 PM', '5–6 PM',
];

function getSubjectColor(subjectCode, subjectColorMap) {
  if (!subjectColorMap[subjectCode]) {
    const idx = Object.keys(subjectColorMap).length % SUBJECT_COLORS.length;
    subjectColorMap[subjectCode] = SUBJECT_COLORS[idx];
  }
  return subjectColorMap[subjectCode];
}

export default function TimetableGrid({ timetableData }) {
  if (!timetableData) return null;

  const { schedule, active_days, total_hours } = timetableData;
  const subjectColorMap = {};

  // Pre-assign colors
  schedule.forEach(day => {
    day.slots.forEach(slot => {
      if (slot.subject_code) getSubjectColor(slot.subject_code, subjectColorMap);
    });
  });

  return (
    <div>
      {/* Summary pills */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        <div className="badge badge-theory" style={{ fontSize: 13, padding: '6px 14px' }}>
          📅 {active_days} active days / week
        </div>
        <div className="badge badge-feasible" style={{ fontSize: 13, padding: '6px 14px' }}>
          ⏱️ {total_hours} total hours
        </div>
        <div className="badge badge-free" style={{ fontSize: 13, padding: '6px 14px' }}>
          🎉 {5 - active_days} free day{5 - active_days !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Grid */}
      <div className="timetable-wrapper">
        <div className="timetable-grid">
          {/* Header row */}
          <div className="timetable-header-cell" style={{ background: 'rgba(255,255,255,0.02)', color: 'var(--text-muted)', fontSize: 11 }}>
            TIME
          </div>
          {schedule.map(day => (
            <div
              key={day.day}
              className={`timetable-header-cell day-header${day.is_free ? ' free-day' : ''}`}
            >
              <div>{DAY_NAMES[day.day]}</div>
              {day.is_free && <div style={{ fontSize: 11, fontWeight: 400, marginTop: 2 }}>🎉 Free</div>}
            </div>
          ))}

          {/* Slot rows */}
          {SLOT_TIMES.map((time, slotIdx) => (
            <>
              {/* Time label */}
              <div key={`time-${slotIdx}`} className="timetable-time-cell">
                {time}
              </div>

              {/* Day cells */}
              {schedule.map(day => {
                const entry = day.slots[slotIdx];
                const hasClass = entry && entry.subject_code;
                const color = hasClass ? getSubjectColor(entry.subject_code, subjectColorMap) : null;

                return (
                  <div
                    key={`cell-${day.day}-${slotIdx}`}
                    className={`timetable-cell${day.is_free ? ' free-day-col' : ''}`}
                  >
                    {hasClass ? (
                      <div
                        className={`class-block ${entry.class_type === 'THEORY' ? 'theory' : 'lab'}`}
                        style={{
                          background: color.bg,
                          borderLeftColor: color.border,
                        }}
                        data-tooltip={`${entry.subject_name} • ${entry.faculty_name} • ${entry.room_name}`}
                      >
                        <div className="class-block-code" style={{ color: color.text }}>
                          {entry.subject_code}
                        </div>
                        <div className="class-block-name">{entry.subject_name}</div>
                        <div className="class-block-meta">
                          <span className={`badge ${entry.class_type === 'THEORY' ? 'badge-theory' : 'badge-lab'}`}
                            style={{ fontSize: 9, padding: '1px 6px' }}>
                            {entry.class_type}
                          </span>
                        </div>
                        <div className="class-block-meta" style={{ marginTop: 2 }}>
                          👤 {entry.faculty_name?.split(' ').slice(-1)[0]}
                        </div>
                        <div className="class-block-meta">
                          🚪 {entry.room_name}
                        </div>
                      </div>
                    ) : day.is_free && slotIdx === 4 ? (
                      <div className="free-day-banner">
                        <span>🏖️</span>
                        <span style={{ fontSize: 10 }}>Free Day</span>
                      </div>
                    ) : null}
                  </div>
                );
              })}
            </>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div style={{ marginTop: 16, display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Legend:</span>
        <span className="badge badge-theory">Theory Class</span>
        <span className="badge badge-lab">Lab / Tutorial</span>
        <span className="badge badge-free">Free Day</span>
      </div>
    </div>
  );
}
