"""Timetable generation and retrieval API endpoints."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from functools import partial

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.config import settings
from app.database import get_db
from app.models import ClassType, SolveStatus, TimetableEntry
from app.schemas import (
    ClassTypeEnum,
    DaySchedule,
    DivisionTimetable,
    SlotEntry,
    SolveRunRead,
    SolveStatusEnum,
    StatsResponse,
    TimetableResponse,
)
from app.solver import (
    DivisionData,
    FacultyData,
    RoomData,
    SolverInput,
    SubjectData,
    TimetableSolver,
)

router = APIRouter(prefix="/timetable", tags=["Timetable"])
logger = logging.getLogger(__name__)

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
SLOT_TIMES = [
    "8:00–9:00 AM", "9:00–10:00 AM", "10:00–11:00 AM", "11:00 AM–12:00 PM",
    "12:00–1:00 PM", "1:00–2:00 PM", "2:00–3:00 PM", "3:00–4:00 PM",
    "4:00–5:00 PM", "5:00–6:00 PM",
]


# ---------------------------------------------------------------------------
# Helper: build structured timetable response
# ---------------------------------------------------------------------------

def _build_division_timetable(
    division_id: int,
    division_name: str,
    division_code: str,
    entries: list[TimetableEntry],
) -> DivisionTimetable:
    """Convert flat TimetableEntry list into a structured grid for one division."""
    # Index entries by (day, slot)
    lookup: dict[tuple[int, int], TimetableEntry] = {}
    for e in entries:
        lookup[(e.day, e.slot)] = e

    active_days = len({e.day for e in entries})
    total_hours = len(entries)

    schedule = []
    for day in range(5):
        day_entries = [e for e in entries if e.day == day]
        is_free = len(day_entries) == 0
        slots = []
        for slot in range(10):
            e = lookup.get((day, slot))
            if e:
                slots.append(SlotEntry(
                    slot=slot,
                    time_label=SLOT_TIMES[slot],
                    subject_name=e.subject.name,
                    subject_code=e.subject.code,
                    class_type=ClassTypeEnum(e.class_type.value),
                    faculty_name=e.faculty_rel.name,
                    room_name=e.room.name,
                ))
            else:
                slots.append(SlotEntry(slot=slot, time_label=SLOT_TIMES[slot]))

        schedule.append(DaySchedule(
            day=day,
            day_name=DAY_NAMES[day],
            slots=slots,
            is_free=is_free,
        ))

    return DivisionTimetable(
        division_id=division_id,
        division_name=division_name,
        division_code=division_code,
        active_days=active_days,
        total_hours=total_hours,
        schedule=schedule,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/solve", response_model=SolveRunRead)
async def solve_timetable(db: AsyncSession = Depends(get_db)):
    """
    Trigger the CP-SAT solver to generate a new optimized timetable.
    Runs synchronously (blocks until completion or time limit).
    Returns the SolveRun record with status and metrics.
    """
    # Load all data
    divisions = await crud.get_divisions(db)
    subjects = await crud.get_subjects(db)
    faculty = await crud.get_all_faculty(db)
    rooms = await crud.get_rooms(db)

    if not divisions:
        raise HTTPException(status_code=400, detail="No divisions found. Please add divisions first.")
    if not subjects:
        raise HTTPException(status_code=400, detail="No subjects found. Please add subjects first.")
    if not faculty:
        raise HTTPException(status_code=400, detail="No faculty found. Please add faculty first.")
    if not rooms:
        raise HTTPException(status_code=400, detail="No rooms found. Please add rooms first.")

    # Check for theory/lab room availability
    theory_rooms = [r for r in rooms if r.room_type.value == "THEORY"]
    lab_rooms = [r for r in rooms if r.room_type.value == "LAB"]

    has_lab_requirements = any(
        s.lab_hours_per_week > 0 for s in subjects
    )
    if has_lab_requirements and not lab_rooms:
        raise HTTPException(
            status_code=400,
            detail="Subjects require lab hours but no lab rooms are defined."
        )

    # Create a SolveRun record
    run = await crud.create_solve_run(db)
    run.status = SolveStatus.RUNNING
    await db.flush()
    run_id = run.id

    # Build solver input
    div_data = [
        DivisionData(
            id=d.id,
            name=d.name,
            code=d.code,
            subject_ids=[s.id for s in d.subjects],
        )
        for d in divisions
    ]

    subj_data = [
        SubjectData(
            id=s.id,
            name=s.name,
            code=s.code,
            theory_hours=s.theory_hours_per_week,
            lab_hours=s.lab_hours_per_week,
        )
        for s in subjects
    ]

    fac_data = [
        FacultyData(id=f.id, name=f.name, subject_ids=[s.id for s in f.subjects])
        for f in faculty
    ]

    room_data = [
        RoomData(id=r.id, name=r.name, room_type=r.room_type.value)
        for r in rooms
    ]

    solver_input = SolverInput(
        divisions=div_data,
        subjects=subj_data,
        faculty=fac_data,
        rooms=room_data,
    )

    # Run solver in a thread to avoid blocking the event loop
    solver = TimetableSolver(
        data=solver_input,
        time_limit=settings.SOLVER_TIME_LIMIT_SECONDS,
        num_workers=settings.SOLVER_NUM_WORKERS,
    )

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, solver.solve)

    # Persist results
    run.completed_at = datetime.utcnow()
    run.solver_log = result.log
    run.status = SolveStatus(result.status) if result.status in SolveStatus.__members__ else SolveStatus.ERROR
    run.objective_value = result.objective_value
    run.total_active_days = result.total_active_days

    if result.status in ("OPTIMAL", "FEASIBLE"):
        for a in result.assignments:
            entry = TimetableEntry(
                solve_run_id=run_id,
                division_id=a.division_id,
                subject_id=a.subject_id,
                class_type=ClassType(a.class_type),
                faculty_id=a.faculty_id,
                room_id=a.room_id,
                day=a.day,
                slot=a.slot,
            )
            db.add(entry)

    await db.flush()
    return run


@router.get("/runs", response_model=list[SolveRunRead])
async def list_solve_runs(db: AsyncSession = Depends(get_db)):
    """List all solver runs, newest first."""
    return await crud.get_solve_runs(db)


@router.get("/latest", response_model=TimetableResponse)
async def get_latest_timetable(db: AsyncSession = Depends(get_db)):
    """Get the structured timetable from the latest successful solve run."""
    run = await crud.get_latest_successful_run(db)
    if not run:
        raise HTTPException(
            status_code=404,
            detail="No successful timetable found. Please run the solver first."
        )
    entries = await crud.get_entries_for_run(db, run.id)

    # Group entries by division
    division_entries: dict[int, list[TimetableEntry]] = {}
    for e in entries:
        division_entries.setdefault(e.division_id, []).append(e)

    divisions_data = await crud.get_divisions(db)
    div_map = {d.id: d for d in divisions_data}

    division_timetables = []
    for div_id, div_entries in division_entries.items():
        div = div_map.get(div_id)
        if div:
            division_timetables.append(_build_division_timetable(
                div_id, div.name, div.code, div_entries
            ))

    return TimetableResponse(
        solve_run_id=run.id,
        status=SolveStatusEnum(run.status.value),
        objective_value=run.objective_value,
        divisions=division_timetables,
    )


@router.get("/{division_id}", response_model=DivisionTimetable)
async def get_division_timetable(
    division_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get the timetable for a specific division from the latest successful run."""
    run = await crud.get_latest_successful_run(db)
    if not run:
        raise HTTPException(
            status_code=404,
            detail="No successful timetable found. Please run the solver first."
        )

    division = await crud.get_division(db, division_id)
    if not division:
        raise HTTPException(status_code=404, detail="Division not found")

    entries = await crud.get_entries_for_division(db, run.id, division_id)
    return _build_division_timetable(division_id, division.name, division.code, entries)


@router.get("/stats/overview", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get dashboard overview stats."""
    stats = await crud.get_stats(db)
    return StatsResponse(**stats)
