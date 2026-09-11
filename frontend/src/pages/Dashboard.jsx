import { useState, useEffect } from 'react';
import { getStats, solveTimetable, getSolveRuns } from '../api/client';
import { useNavigate } from 'react-router-dom';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [runs, setRuns] = useState([]);
  const [solving, setSolving] = useState(false);
  const [solveResult, setSolveResult] = useState(null);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [statsRes, runsRes] = await Promise.all([getStats(), getSolveRuns()]);
      setStats(statsRes.data);
      setRuns(runsRes.data.slice(0, 5));
    } catch {
      // backend may not be running yet
    }
  }

  async function handleSolve() {
    setSolving(true);
    setError('');
    setSolveResult(null);
    try {
      const res = await solveTimetable();
      setSolveResult(res.data);
      await loadData();
      if (res.data.status === 'OPTIMAL' || res.data.status === 'FEASIBLE') {
        setTimeout(() => navigate('/timetable'), 1500);
      }
    } catch (e) {
      setError(e.response?.data?.detail || 'Solver failed. Check that the backend is running.');
    } finally {
      setSolving(false);
    }
  }

  const statusColor = {
    OPTIMAL: 'var(--emerald)',
    FEASIBLE: 'var(--amber)',
    INFEASIBLE: 'var(--rose)',
    ERROR: 'var(--rose)',
    PENDING: 'var(--text-muted)',
    RUNNING: 'var(--cyan)',
  };

  return (
    <div>
      {/* Stats */}
      <div className="stats-grid">
        {[
          { label: 'Divisions', value: stats?.total_divisions ?? '—', icon: '🎓', color: 'cyan' },
          { label: 'Subjects', value: stats?.total_subjects ?? '—', icon: '📚', color: 'violet' },
          { label: 'Faculty', value: stats?.total_faculty ?? '—', icon: '👨‍🏫', color: 'amber' },
          { label: 'Rooms', value: stats?.total_rooms ?? '—', icon: '🏫', color: 'emerald' },
          { label: 'Lab Rooms', value: stats?.total_lab_rooms ?? '—', icon: '🔬', color: 'rose' },
        ].map(({ label, value, icon, color }) => (
          <div key={label} className={`stat-card ${color}`}>
            <div className="stat-icon">{icon}</div>
            <div className="stat-label">{label}</div>
            <div className="stat-value">{value}</div>
          </div>
        ))}
      </div>

      {/* Solve Panel */}
      <div className="solve-panel">
        <h2>Generate Timetable</h2>
        <p>
          CP-SAT solver will optimize your schedule to minimize active days per division,
          packing classes into compact blocks and freeing up entire days.
        </p>

        {error && <div className="alert alert-error" style={{ textAlign: 'left' }}>⚠️ {error}</div>}

        {solveResult && (
          <div className={`alert ${solveResult.status === 'OPTIMAL' || solveResult.status === 'FEASIBLE' ? 'alert-success' : 'alert-error'}`}
            style={{ textAlign: 'left', marginBottom: 20 }}>
            {solveResult.status === 'OPTIMAL' && '✅ Optimal solution found!'}
            {solveResult.status === 'FEASIBLE' && '✅ Feasible solution found!'}
            {solveResult.status === 'INFEASIBLE' && '❌ No feasible solution. Check constraints.'}
            {solveResult.status === 'ERROR' && '❌ Solver error.'}
            {solveResult.objective_value != null && (
              <div style={{ marginTop: 8, fontSize: 13 }}>
                Total active division-days: <strong>{solveResult.objective_value}</strong>
              </div>
            )}
          </div>
        )}

        {solving ? (
          <div>
            <div className="spinner" />
            <p style={{ color: 'var(--cyan)', fontSize: 14 }}>Solving… this may take up to 120 seconds</p>
          </div>
        ) : (
          <button className="btn-solve" onClick={handleSolve}>
            ⚡ Run Optimizer
          </button>
        )}
      </div>

      {/* Recent Runs */}
      {runs.length > 0 && (
        <div className="card">
          <div className="section-title" style={{ fontSize: 16, marginBottom: 16 }}>Recent Solver Runs</div>
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Run #</th>
                  <th>Status</th>
                  <th>Objective</th>
                  <th>Active Days</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {runs.map(run => (
                  <tr key={run.id}>
                    <td style={{ color: 'var(--text-muted)' }}>#{run.id}</td>
                    <td>
                      <span style={{ color: statusColor[run.status] || 'var(--text-muted)', fontWeight: 600 }}>
                        {run.status}
                      </span>
                    </td>
                    <td>{run.objective_value ?? '—'}</td>
                    <td>{run.total_active_days ?? '—'}</td>
                    <td style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                      {new Date(run.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
