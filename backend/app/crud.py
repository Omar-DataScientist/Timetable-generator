"""CRUD operations for all entities using async SQLAlchemy 2.0 syntax."""

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Division,
    DivisionSubject,
    Faculty,
    FacultySubject,
    Room,
    RoomType,
    SolveRun,
    SolveStatus,
    Subject,
    TimetableEntry,
)


# ---------------------------------------------------------------------------
# Division CRUD
# ---------------------------------------------------------------------------

async def create_division(db: AsyncSession, name: str, code: str, subject_ids: list[int] = None) -> Division:
    division = Division(name=name, code=code)
    db.add(division)
    await db.flush()  # get the id

    if subject_ids:
        for sid in subject_ids:
            db.add(DivisionSubject(division_id=division.id, subject_id=sid))
        await db.flush()

    # Reload with relationships
    result = await db.execute(
        select(Division).options(selectinload(Division.subjects)).where(Division.id == division.id)
    )
    return result.scalar_one()


async def get_divisions(db: AsyncSession) -> list[Division]:
    result = await db.execute(
        select(Division).options(selectinload(Division.subjects)).order_by(Division.id)
    )
    return list(result.scalars().all())


async def get_division(db: AsyncSession, division_id: int) -> Division | None:
    result = await db.execute(
        select(Division).options(selectinload(Division.subjects)).where(Division.id == division_id)
    )
    return result.scalar_one_or_none()


async def delete_division(db: AsyncSession, division_id: int) -> bool:
    result = await db.execute(delete(Division).where(Division.id == division_id))
    return result.rowcount > 0


# ---------------------------------------------------------------------------
# Subject CRUD
# ---------------------------------------------------------------------------

async def create_subject(db: AsyncSession, name: str, code: str, theory_hours: int, lab_hours: int) -> Subject:
    subject = Subject(name=name, code=code, theory_hours_per_week=theory_hours, lab_hours_per_week=lab_hours)
    db.add(subject)
    await db.flush()
    return subject


async def get_subjects(db: AsyncSession) -> list[Subject]:
    result = await db.execute(select(Subject).order_by(Subject.id))
    return list(result.scalars().all())


async def get_subject(db: AsyncSession, subject_id: int) -> Subject | None:
    result = await db.execute(select(Subject).where(Subject.id == subject_id))
    return result.scalar_one_or_none()


async def delete_subject(db: AsyncSession, subject_id: int) -> bool:
    result = await db.execute(delete(Subject).where(Subject.id == subject_id))
    return result.rowcount > 0


# ---------------------------------------------------------------------------
# Faculty CRUD
# ---------------------------------------------------------------------------

async def create_faculty(db: AsyncSession, name: str, employee_id: str, subject_ids: list[int] = None) -> Faculty:
    faculty = Faculty(name=name, employee_id=employee_id)
    db.add(faculty)
    await db.flush()

    if subject_ids:
        for sid in subject_ids:
            db.add(FacultySubject(faculty_id=faculty.id, subject_id=sid))
        await db.flush()

    result = await db.execute(
        select(Faculty).options(selectinload(Faculty.subjects)).where(Faculty.id == faculty.id)
    )
    return result.scalar_one()


async def get_all_faculty(db: AsyncSession) -> list[Faculty]:
    result = await db.execute(
        select(Faculty).options(selectinload(Faculty.subjects)).order_by(Faculty.id)
    )
    return list(result.scalars().all())


async def get_faculty(db: AsyncSession, faculty_id: int) -> Faculty | None:
    result = await db.execute(
        select(Faculty).options(selectinload(Faculty.subjects)).where(Faculty.id == faculty_id)
    )
    return result.scalar_one_or_none()


async def assign_subjects_to_faculty(db: AsyncSession, faculty_id: int, subject_ids: list[int]) -> Faculty | None:
    # Clear existing
    await db.execute(delete(FacultySubject).where(FacultySubject.faculty_id == faculty_id))
    for sid in subject_ids:
        db.add(FacultySubject(faculty_id=faculty_id, subject_id=sid))
    await db.flush()
    return await get_faculty(db, faculty_id)


async def delete_faculty(db: AsyncSession, faculty_id: int) -> bool:
    result = await db.execute(delete(Faculty).where(Faculty.id == faculty_id))
    return result.rowcount > 0


# ---------------------------------------------------------------------------
# Room CRUD
# ---------------------------------------------------------------------------

async def create_room(db: AsyncSession, name: str, room_type: RoomType, capacity: int = 60) -> Room:
    room = Room(name=name, room_type=room_type, capacity=capacity)
    db.add(room)
    await db.flush()
    return room


async def get_rooms(db: AsyncSession) -> list[Room]:
    result = await db.execute(select(Room).order_by(Room.id))
    return list(result.scalars().all())


async def get_room(db: AsyncSession, room_id: int) -> Room | None:
    result = await db.execute(select(Room).where(Room.id == room_id))
    return result.scalar_one_or_none()


async def delete_room(db: AsyncSession, room_id: int) -> bool:
    result = await db.execute(delete(Room).where(Room.id == room_id))
    return result.rowcount > 0


# ---------------------------------------------------------------------------
# Faculty-Subject mapping queries
# ---------------------------------------------------------------------------

async def get_faculty_subject_mappings(db: AsyncSession) -> list[FacultySubject]:
    result = await db.execute(select(FacultySubject))
    return list(result.scalars().all())


async def get_division_subject_mappings(db: AsyncSession) -> list[DivisionSubject]:
    result = await db.execute(select(DivisionSubject))
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# SolveRun CRUD
# ---------------------------------------------------------------------------

async def create_solve_run(db: AsyncSession) -> SolveRun:
    run = SolveRun(status=SolveStatus.PENDING)
    db.add(run)
    await db.flush()
    return run


async def get_solve_runs(db: AsyncSession) -> list[SolveRun]:
    result = await db.execute(select(SolveRun).order_by(SolveRun.created_at.desc()))
    return list(result.scalars().all())


async def get_latest_successful_run(db: AsyncSession) -> SolveRun | None:
    result = await db.execute(
        select(SolveRun)
        .options(selectinload(SolveRun.entries))
        .where(SolveRun.status.in_([SolveStatus.OPTIMAL, SolveStatus.FEASIBLE]))
        .order_by(SolveRun.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_solve_run(db: AsyncSession, run_id: int) -> SolveRun | None:
    result = await db.execute(
        select(SolveRun).options(selectinload(SolveRun.entries)).where(SolveRun.id == run_id)
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Timetable entries
# ---------------------------------------------------------------------------

async def get_entries_for_run(db: AsyncSession, run_id: int) -> list[TimetableEntry]:
    result = await db.execute(
        select(TimetableEntry)
        .options(
            selectinload(TimetableEntry.division),
            selectinload(TimetableEntry.subject),
            selectinload(TimetableEntry.faculty_rel),
            selectinload(TimetableEntry.room),
        )
        .where(TimetableEntry.solve_run_id == run_id)
        .order_by(TimetableEntry.division_id, TimetableEntry.day, TimetableEntry.slot)
    )
    return list(result.scalars().all())


async def get_entries_for_division(db: AsyncSession, run_id: int, division_id: int) -> list[TimetableEntry]:
    result = await db.execute(
        select(TimetableEntry)
        .options(
            selectinload(TimetableEntry.division),
            selectinload(TimetableEntry.subject),
            selectinload(TimetableEntry.faculty_rel),
            selectinload(TimetableEntry.room),
        )
        .where(
            TimetableEntry.solve_run_id == run_id,
            TimetableEntry.division_id == division_id,
        )
        .order_by(TimetableEntry.day, TimetableEntry.slot)
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

async def get_stats(db: AsyncSession) -> dict:
    divisions_count = (await db.execute(select(func.count(Division.id)))).scalar() or 0
    subjects_count = (await db.execute(select(func.count(Subject.id)))).scalar() or 0
    faculty_count = (await db.execute(select(func.count(Faculty.id)))).scalar() or 0
    rooms_count = (await db.execute(select(func.count(Room.id)))).scalar() or 0
    theory_rooms = (await db.execute(
        select(func.count(Room.id)).where(Room.room_type == RoomType.THEORY)
    )).scalar() or 0
    lab_rooms = (await db.execute(
        select(func.count(Room.id)).where(Room.room_type == RoomType.LAB)
    )).scalar() or 0

    latest_run = await db.execute(select(SolveRun).order_by(SolveRun.created_at.desc()).limit(1))
    latest = latest_run.scalar_one_or_none()

    return {
        "total_divisions": divisions_count,
        "total_subjects": subjects_count,
        "total_faculty": faculty_count,
        "total_rooms": rooms_count,
        "total_theory_rooms": theory_rooms,
        "total_lab_rooms": lab_rooms,
        "latest_solve_status": latest.status.value if latest else None,
    }
