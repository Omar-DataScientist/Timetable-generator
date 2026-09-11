import { useState, useEffect } from 'react';
import {
  getSubjects, createSubject, deleteSubject,
  getDivisions, createDivision, deleteDivision,
  getFaculty, createFaculty, deleteFaculty,
  getRooms, createRoom, deleteRoom,
} from '../api/client';

// ── Generic delete button ──────────────────────────────────────────────────
function DeleteBtn({ onClick }) {
  return (
    <button className="btn btn-danger" style={{ padding: '5px 12px', fontSize: 12 }} onClick={onClick}>
      🗑️
    </button>
  );
}

// ── Subjects Tab ───────────────────────────────────────────────────────────
function SubjectsTab() {
  const [subjects, setSubjects] = useState([]);
  const [form, setForm] = useState({ name: '', code: '', theory_hours_per_week: 3, lab_hours_per_week: 0 });
  const [err, setErr] = useState('');

  useEffect(() => { load(); }, []);
  async function load() { const r = await getSubjects(); setSubjects(r.data); }

  async function handleAdd(e) {
    e.preventDefault(); setErr('');
    try {
      await createSubject({ ...form, theory_hours_per_week: +form.theory_hours_per_week, lab_hours_per_week: +form.lab_hours_per_week });
      setForm({ name: '', code: '', theory_hours_per_week: 3, lab_hours_per_week: 0 });
      await load();
    } catch (ex) { setErr(ex.response?.data?.detail || 'Error'); }
  }

  async function handleDelete(id) { await deleteSubject(id); await load(); }

  return (
    <div>
      {/* Add form */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="section-title" style={{ fontSize: 16, marginBottom: 16 }}>Add Subject</div>
        {err && <div className="alert alert-error">{err}</div>}
        <form onSubmit={handleAdd}>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Subject Name</label>
              <input className="form-input" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required placeholder="e.g. Data Structures" />
            </div>
            <div className="form-group">
              <label className="form-label">Code</label>
              <input className="form-input" value={form.code} onChange={e => setForm({ ...form, code: e.target.value })} required placeholder="e.g. DSA" />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Theory Hours/Week</label>
              <input className="form-input" type="number" min="0" max="10" value={form.theory_hours_per_week} onChange={e => setForm({ ...form, theory_hours_per_week: e.target.value })} />
            </div>
            <div className="form-group">
              <label className="form-label">Lab Hours/Week</label>
              <input className="form-input" type="number" min="0" max="10" value={form.lab_hours_per_week} onChange={e => setForm({ ...form, lab_hours_per_week: e.target.value })} />
            </div>
          </div>
          <button className="btn btn-primary" type="submit">+ Add Subject</button>
        </form>
      </div>

      {/* List */}
      <div className="table-wrapper">
        <table>
          <thead><tr><th>#</th><th>Name</th><th>Code</th><th>Theory hrs</th><th>Lab hrs</th><th></th></tr></thead>
          <tbody>
            {subjects.map(s => (
              <tr key={s.id}>
                <td style={{ color: 'var(--text-muted)' }}>{s.id}</td>
                <td>{s.name}</td>
                <td><span className="badge badge-theory">{s.code}</span></td>
                <td>{s.theory_hours_per_week}</td>
                <td>{s.lab_hours_per_week}</td>
                <td><DeleteBtn onClick={() => handleDelete(s.id)} /></td>
              </tr>
            ))}
            {subjects.length === 0 && <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 32 }}>No subjects yet</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Divisions Tab ──────────────────────────────────────────────────────────
function DivisionsTab() {
  const [divisions, setDivisions] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [form, setForm] = useState({ name: '', code: '', subject_ids: [] });
  const [err, setErr] = useState('');

  useEffect(() => { load(); }, []);
  async function load() {
    const [dr, sr] = await Promise.all([getDivisions(), getSubjects()]);
    setDivisions(dr.data); setSubjects(sr.data);
  }

  function toggleSubject(id) {
    setForm(f => ({
      ...f,
      subject_ids: f.subject_ids.includes(id) ? f.subject_ids.filter(x => x !== id) : [...f.subject_ids, id],
    }));
  }

  async function handleAdd(e) {
    e.preventDefault(); setErr('');
    try {
      await createDivision(form);
      setForm({ name: '', code: '', subject_ids: [] });
      await load();
    } catch (ex) { setErr(ex.response?.data?.detail || 'Error'); }
  }

  async function handleDelete(id) { await deleteDivision(id); await load(); }

  return (
    <div>
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="section-title" style={{ fontSize: 16, marginBottom: 16 }}>Add Division</div>
        {err && <div className="alert alert-error">{err}</div>}
        <form onSubmit={handleAdd}>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Division Name</label>
              <input className="form-input" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required placeholder="e.g. CS Division A" />
            </div>
            <div className="form-group">
              <label className="form-label">Code</label>
              <input className="form-input" value={form.code} onChange={e => setForm({ ...form, code: e.target.value })} required placeholder="e.g. CS-A" />
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Subjects (select all that apply)</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {subjects.map(s => (
                <button
                  key={s.id}
                  type="button"
                  className={`division-chip${form.subject_ids.includes(s.id) ? ' active' : ''}`}
                  onClick={() => toggleSubject(s.id)}
                >
                  {s.code}
                </button>
              ))}
            </div>
          </div>
          <button className="btn btn-primary" type="submit">+ Add Division</button>
        </form>
      </div>

      <div className="table-wrapper">
        <table>
          <thead><tr><th>#</th><th>Name</th><th>Code</th><th>Subjects</th><th></th></tr></thead>
          <tbody>
            {divisions.map(d => (
              <tr key={d.id}>
                <td style={{ color: 'var(--text-muted)' }}>{d.id}</td>
                <td>{d.name}</td>
                <td><span className="badge badge-lab">{d.code}</span></td>
                <td style={{ display: 'flex', flexWrap: 'wrap', gap: 4, paddingTop: 12 }}>
                  {d.subjects.map(s => <span key={s.id} className="badge badge-theory">{s.code}</span>)}
                </td>
                <td><DeleteBtn onClick={() => handleDelete(d.id)} /></td>
              </tr>
            ))}
            {divisions.length === 0 && <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 32 }}>No divisions yet</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Faculty Tab ────────────────────────────────────────────────────────────
function FacultyTab() {
  const [faculty, setFaculty] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [form, setForm] = useState({ name: '', employee_id: '', subject_ids: [] });
  const [err, setErr] = useState('');

  useEffect(() => { load(); }, []);
  async function load() {
    const [fr, sr] = await Promise.all([getFaculty(), getSubjects()]);
    setFaculty(fr.data); setSubjects(sr.data);
  }

  function toggleSubject(id) {
    setForm(f => ({
      ...f,
      subject_ids: f.subject_ids.includes(id) ? f.subject_ids.filter(x => x !== id) : [...f.subject_ids, id],
    }));
  }

  async function handleAdd(e) {
    e.preventDefault(); setErr('');
    try {
      await createFaculty(form);
      setForm({ name: '', employee_id: '', subject_ids: [] });
      await load();
    } catch (ex) { setErr(ex.response?.data?.detail || 'Error'); }
  }

  async function handleDelete(id) { await deleteFaculty(id); await load(); }

  return (
    <div>
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="section-title" style={{ fontSize: 16, marginBottom: 16 }}>Add Faculty</div>
        {err && <div className="alert alert-error">{err}</div>}
        <form onSubmit={handleAdd}>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Full Name</label>
              <input className="form-input" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required placeholder="e.g. Dr. Alice Sharma" />
            </div>
            <div className="form-group">
              <label className="form-label">Employee ID</label>
              <input className="form-input" value={form.employee_id} onChange={e => setForm({ ...form, employee_id: e.target.value })} required placeholder="e.g. FAC001" />
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Can Teach (subjects)</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {subjects.map(s => (
                <button
                  key={s.id}
                  type="button"
                  className={`division-chip${form.subject_ids.includes(s.id) ? ' active' : ''}`}
                  onClick={() => toggleSubject(s.id)}
                >
                  {s.code}
                </button>
              ))}
            </div>
          </div>
          <button className="btn btn-primary" type="submit">+ Add Faculty</button>
        </form>
      </div>

      <div className="table-wrapper">
        <table>
          <thead><tr><th>#</th><th>Name</th><th>Emp ID</th><th>Teaches</th><th></th></tr></thead>
          <tbody>
            {faculty.map(f => (
              <tr key={f.id}>
                <td style={{ color: 'var(--text-muted)' }}>{f.id}</td>
                <td>{f.name}</td>
                <td style={{ color: 'var(--text-muted)', fontSize: 13 }}>{f.employee_id}</td>
                <td style={{ display: 'flex', flexWrap: 'wrap', gap: 4, paddingTop: 12 }}>
                  {f.subjects.map(s => <span key={s.id} className="badge badge-theory">{s.code}</span>)}
                </td>
                <td><DeleteBtn onClick={() => handleDelete(f.id)} /></td>
              </tr>
            ))}
            {faculty.length === 0 && <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 32 }}>No faculty yet</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Rooms Tab ──────────────────────────────────────────────────────────────
function RoomsTab() {
  const [rooms, setRooms] = useState([]);
  const [form, setForm] = useState({ name: '', room_type: 'THEORY', capacity: 60 });
  const [err, setErr] = useState('');

  useEffect(() => { load(); }, []);
  async function load() { const r = await getRooms(); setRooms(r.data); }

  async function handleAdd(e) {
    e.preventDefault(); setErr('');
    try {
      await createRoom({ ...form, capacity: +form.capacity });
      setForm({ name: '', room_type: 'THEORY', capacity: 60 });
      await load();
    } catch (ex) { setErr(ex.response?.data?.detail || 'Error'); }
  }

  async function handleDelete(id) { await deleteRoom(id); await load(); }

  return (
    <div>
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="section-title" style={{ fontSize: 16, marginBottom: 16 }}>Add Room</div>
        {err && <div className="alert alert-error">{err}</div>}
        <form onSubmit={handleAdd}>
          <div className="form-row" style={{ gridTemplateColumns: '1fr 1fr 1fr' }}>
            <div className="form-group">
              <label className="form-label">Room Name</label>
              <input className="form-input" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required placeholder="e.g. Room 101" />
            </div>
            <div className="form-group">
              <label className="form-label">Type</label>
              <select className="form-select" value={form.room_type} onChange={e => setForm({ ...form, room_type: e.target.value })}>
                <option value="THEORY">Theory</option>
                <option value="LAB">Lab</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Capacity</label>
              <input className="form-input" type="number" min="1" value={form.capacity} onChange={e => setForm({ ...form, capacity: e.target.value })} />
            </div>
          </div>
          <button className="btn btn-primary" type="submit">+ Add Room</button>
        </form>
      </div>

      <div className="table-wrapper">
        <table>
          <thead><tr><th>#</th><th>Name</th><th>Type</th><th>Capacity</th><th></th></tr></thead>
          <tbody>
            {rooms.map(r => (
              <tr key={r.id}>
                <td style={{ color: 'var(--text-muted)' }}>{r.id}</td>
                <td>{r.name}</td>
                <td><span className={`badge ${r.room_type === 'THEORY' ? 'badge-theory' : 'badge-lab'}`}>{r.room_type}</span></td>
                <td>{r.capacity}</td>
                <td><DeleteBtn onClick={() => handleDelete(r.id)} /></td>
              </tr>
            ))}
            {rooms.length === 0 && <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 32 }}>No rooms yet</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Main DataEntry page ────────────────────────────────────────────────────
const TABS = [
  { id: 'subjects',   label: '📚 Subjects',  Component: SubjectsTab },
  { id: 'divisions',  label: '🎓 Divisions', Component: DivisionsTab },
  { id: 'faculty',    label: '👨‍🏫 Faculty',   Component: FacultyTab },
  { id: 'rooms',      label: '🏫 Rooms',     Component: RoomsTab },
];

export default function DataEntry() {
  const [activeTab, setActiveTab] = useState('subjects');
  const ActiveComp = TABS.find(t => t.id === activeTab)?.Component;

  return (
    <div>
      <p className="section-subtitle">
        Manage all constraint data. Add subjects, assign curricula to divisions, map faculty, and configure rooms.
      </p>

      <div className="tabs-nav">
        {TABS.map(t => (
          <button
            key={t.id}
            className={`tab-btn${activeTab === t.id ? ' active' : ''}`}
            onClick={() => setActiveTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {ActiveComp && <ActiveComp />}
    </div>
  );
}
