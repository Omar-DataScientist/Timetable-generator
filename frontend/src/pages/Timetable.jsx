import { useState, useEffect } from 'react';
import { getLatestTimetable, getDivisions } from '../api/client';
import TimetableGrid from '../components/TimetableGrid';
import { useNavigate } from 'react-router-dom';

export default function TimetablePage() {
  const [timetable, setTimetable] = useState(null);
  const [selectedDivision, setSelectedDivision] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    loadTimetable();
  }, []);

  async function loadTimetable() {
    setLoading(true);
    setError('');
    try {
      const res = await getLatestTimetable();
      setTimetable(res.data);
      if (res.data.divisions.length > 0) {
        setSelectedDivision(res.data.divisions[0].division_id);
      }
    } catch (e) {
      if (e.response?.status === 404) {
        setError('No timetable generated yet. Go to Dashboard and run the optimizer.');
      } else {
        setError('Failed to load timetable. Make sure the backend is running.');
      }
    } finally {
      setLoading(false);
    }
  }

  const currentDivision = timetable?.divisions?.find(d => d.division_id === selectedDivision);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 80 }}>
        <div>
          <div className="spinner" style={{ width: 48, height: 48, borderWidth: 4 }} />
          <p style={{ color: 'var(--text-secondary)', textAlign: 'center', marginTop: 16 }}>Loading timetable…</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">📅</div>
        <h3>No Timetable Available</h3>
        <p style={{ marginBottom: 24 }}>{error}</p>
        <button className="btn btn-primary" onClick={() => navigate('/')}>
          → Go to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* Meta banner */}
      <div className="card" style={{ marginBottom: 24, display: 'flex', alignItems: 'center', gap: 20, flexWrap: 'wrap' }}>
        <div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>Solve Run #{timetable?.solve_run_id}</div>
          <span className={`badge ${timetable?.status === 'OPTIMAL' ? 'badge-optimal' : 'badge-feasible'}`} style={{ fontSize: 13, padding: '5px 12px' }}>
            {timetable?.status === 'OPTIMAL' ? '⭐ OPTIMAL' : '✅ FEASIBLE'}
          </span>
        </div>
        <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
          Total active division-days: <strong style={{ color: 'var(--cyan)' }}>{timetable?.objective_value}</strong>
        </div>
        <div style={{ marginLeft: 'auto' }}>
          <button className="btn btn-secondary" onClick={loadTimetable} style={{ fontSize: 13 }}>
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Division selector */}
      <div className="division-selector">
        <span style={{ fontSize: 13, color: 'var(--text-muted)', fontWeight: 500 }}>Division:</span>
        {timetable?.divisions?.map(d => (
          <button
            key={d.division_id}
            className={`division-chip${selectedDivision === d.division_id ? ' active' : ''}`}
            onClick={() => setSelectedDivision(d.division_id)}
          >
            {d.division_code}
            <span style={{ marginLeft: 6, fontSize: 11, opacity: 0.7 }}>
              {d.active_days}d
            </span>
          </button>
        ))}
      </div>

      {/* Timetable Grid */}
      {currentDivision && (
        <div>
          <div style={{ marginBottom: 16 }}>
            <h2 style={{ fontSize: 20, fontWeight: 700, letterSpacing: '-0.4px' }}>
              {currentDivision.division_name}
            </h2>
          </div>
          <TimetableGrid timetableData={currentDivision} />
        </div>
      )}
    </div>
  );
}
