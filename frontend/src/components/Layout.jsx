import { NavLink } from 'react-router-dom';

const navItems = [
  { to: '/',         icon: '📊', label: 'Dashboard' },
  { to: '/data',     icon: '🗂️', label: 'Data Entry' },
  { to: '/timetable',icon: '📅', label: 'Timetable' },
];

export default function Layout({ children, title }) {
  return (
    <div className="app-shell">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <h1>⚡ TimetableGen</h1>
          <p>OR-Tools CP-SAT Optimizer</p>
        </div>
        <nav className="sidebar-nav">
          {navItems.map(({ to, icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            >
              <span className="nav-icon">{icon}</span>
              {label}
            </NavLink>
          ))}
        </nav>
        <div style={{ padding: '16px 20px', borderTop: '1px solid var(--border)' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            <div style={{ marginBottom: 4 }}>Backend: <span style={{ color: 'var(--cyan)' }}>FastAPI</span></div>
            <div style={{ marginBottom: 4 }}>Solver: <span style={{ color: 'var(--violet)' }}>OR-Tools CP-SAT</span></div>
            <div>DB: <span style={{ color: 'var(--emerald)' }}>SQLite</span></div>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="main-content">
        <div className="topbar">
          <h2 className="topbar-title">{title}</h2>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="btn btn-secondary"
            style={{ fontSize: 13 }}
          >
            📖 API Docs
          </a>
        </div>
        <div className="page-body">{children}</div>
      </main>
    </div>
  );
}
