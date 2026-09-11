"""Pydantic schemas for request/response validation."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums (mirroring SQLAlchemy enums for Pydantic)
# ---------------------------------------------------------------------------

class RoomTypeEnum(str, Enum):
    THEORY = "THEORY"
    LAB = "LAB"


class ClassTypeEnum(str, Enum):
    THEORY = "THEORY"
    LAB = "LAB"


class SolveStatusEnum(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    OPTIMAL = "OPTIMAL"
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"
    ERROR = "ERROR"


# ---------------------------------------------------------------------------
# Division
# ---------------------------------------------------------------------------

class DivisionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=20)


class DivisionCreate(DivisionBase):
    subject_ids: list[int] = Field(default_factory=list, description="IDs of subjects in this division's curriculum")


class DivisionRead(DivisionBase):
    id: int
    subjects: list[SubjectRead] = []

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Subject
# ---------------------------------------------------------------------------

class SubjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=20)
    theory_hours_per_week: int = Field(..., ge=0, le=10)
    lab_hours_per_week: int = Field(..., ge=0, le=10)


class SubjectCreate(SubjectBase):
    pass


class SubjectRead(SubjectBase):
    id: int

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Faculty
# ---------------------------------------------------------------------------

class FacultyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    employee_id: str = Field(..., min_length=1, max_length=50)


class FacultyCreate(FacultyBase):
    subject_ids: list[int] = Field(default_factory=list, description="IDs of subjects this faculty can teach")


class FacultyRead(FacultyBase):
    id: int
    subjects: list[SubjectRead] = []

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Room
# ---------------------------------------------------------------------------

class RoomBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    room_type: RoomTypeEnum
    capacity: int = Field(60, ge=1)


class RoomCreate(RoomBase):
    pass


class RoomRead(RoomBase):
    id: int

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Timetable Entry
# ---------------------------------------------------------------------------

class TimetableEntryRead(BaseModel):
    id: int
    division_id: int
    division_name: str = ""
    division_code: str = ""
    subject_id: int
    subject_name: str = ""
    subject_code: str = ""
    class_type: ClassTypeEnum
    faculty_id: int
    faculty_name: str = ""
    room_id: int
    room_name: str = ""
    day: int = Field(..., ge=0, le=4, description="0=Monday, 4=Friday")
    slot: int = Field(..., ge=0, le=9, description="0=8AM, 9=5PM")

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Solve Run
# ---------------------------------------------------------------------------

class SolveRunRead(BaseModel):
    id: int
    status: SolveStatusEnum
    created_at: datetime
    completed_at: datetime | None = None
    objective_value: int | None = None
    total_active_days: int | None = None
    solver_log: str | None = None

    model_config = {"from_attributes": True}


class SolveRunWithEntries(SolveRunRead):
    entries: list[TimetableEntryRead] = []


# ---------------------------------------------------------------------------
# Timetable response (structured by division → day → slot)
# ---------------------------------------------------------------------------

class SlotEntry(BaseModel):
    """A single slot in the timetable grid."""
    slot: int
    time_label: str
    subject_name: str | None = None
    subject_code: str | None = None
    class_type: ClassTypeEnum | None = None
    faculty_name: str | None = None
    room_name: str | None = None


class DaySchedule(BaseModel):
    """All slots for a single day."""
    day: int
    day_name: str
    slots: list[SlotEntry]
    is_free: bool = False


class DivisionTimetable(BaseModel):
    """Complete weekly timetable for one division."""
    division_id: int
    division_name: str
    division_code: str
    active_days: int
    total_hours: int
    schedule: list[DaySchedule]


class TimetableResponse(BaseModel):
    """Full timetable response with metadata."""
    solve_run_id: int
    status: SolveStatusEnum
    objective_value: int | None = None
    divisions: list[DivisionTimetable]


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

class StatsResponse(BaseModel):
    total_divisions: int
    total_subjects: int
    total_faculty: int
    total_rooms: int
    total_theory_rooms: int
    total_lab_rooms: int
    latest_solve_status: SolveStatusEnum | None = None


# ---------------------------------------------------------------------------
# Rebuild forward references for circular deps
# ---------------------------------------------------------------------------

DivisionRead.model_rebuild()
FacultyRead.model_rebuild()
