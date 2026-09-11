# Timetable Generator

A full-stack university timetable optimizer using **FastAPI**, **Google OR-Tools CP-SAT**, **SQLAlchemy**, and **React**. Compresses student schedules into the fewest possible days per week using Constraint Programming.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI 0.115 + Uvicorn |
| Solver | OR-Tools CP-SAT 9.12 |
| Database | SQLite via SQLAlchemy 2.0 async |
| Frontend | React 18 + Vite + Custom CSS |

---

## Project Structure

```
Timetable_Generator/
├── backend/
│   ├── venv/                    # Python virtual environment
│   ├── app/
│   │   ├── main.py              # FastAPI app + lifespan
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   ├── database.py          # Async SQLAlchemy engine
│   │   ├── models.py            # ORM models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── crud.py              # DB operations
│   │   ├── solver.py            # OR-Tools CP-SAT engine
│   │   └── routers/
│   │       ├── divisions.py
│   │       ├── subjects.py
│   │       ├── faculty.py
│   │       ├── rooms.py
│   │       └── timetable.py
│   ├── seed.py                  # Sample data seeder
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── api/client.js        # Axios API wrapper
    │   ├── components/
    │   │   ├── Layout.jsx
    │   │   └── TimetableGrid.jsx
    │   └── pages/
    │       ├── Dashboard.jsx
    │       ├── DataEntry.jsx
    │       └── Timetable.jsx
    └── package.json
```

---

## Quick Start

### 1. Start Backend

```powershell
cd backend
venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend API: http://localhost:8000  
Swagger Docs: http://localhost:8000/docs

### 2. Seed Sample Data (first time only)

```powershell
cd backend
venv\Scripts\python seed.py
```

Creates: 8 subjects, 4 divisions (CS-A, CS-B, IT-A, IT-B), 10 faculty, 6 rooms (4 theory + 2 labs).

### 3. Start Frontend

```powershell
cd frontend
npm run dev
```

Frontend: http://localhost:5173

---

## Constraints Implemented

### Hard Constraints (CP-SAT enforced)
| # | Constraint |
|---|-----------|
| C1 | Faculty clash: max 1 class per timeslot per faculty |
| C2 | Division clash: max 1 class per timeslot per division |
| C3 | Room clash: max 1 class per timeslot per room |
| C4 | Room-type match: labs → lab rooms only, theory → theory rooms only |
| C5 | Curriculum: exact weekly theory + lab hours per subject per division |
| C6 | Daily workload: max 8 hours per division per day |
| C7 | Max 1-hour break: gap between first and last class ≤ 1 slot |
| C8a | Double-theory limit: max 1 subject with 2 theory classes per day |
| C8b | Non-consecutive doubles: two theory slots for same subject cannot be adjacent |

### Objective Function (Minimize)
```
Minimize Σ Y[d, day]  for all divisions d, days (0..4)
where Y[d, day] = 1 if division d has any class on that day
```
Goal: pack all classes into as few days as possible, freeing entire days.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/divisions/` | Create division |
| GET  | `/api/divisions/` | List divisions |
| POST | `/api/subjects/` | Create subject |
| GET  | `/api/subjects/` | List subjects |
| POST | `/api/faculty/` | Create faculty |
| PUT  | `/api/faculty/{id}/subjects` | Assign subjects |
| POST | `/api/rooms/` | Create room |
| POST | `/api/timetable/solve` | **Run solver** |
| GET  | `/api/timetable/latest` | Get latest timetable |
| GET  | `/api/timetable/{division_id}` | Get division timetable |
| GET  | `/api/timetable/stats/overview` | Dashboard stats |
