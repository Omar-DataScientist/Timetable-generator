"""SQLAlchemy ORM models for all timetable entities."""

import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class RoomType(str, enum.Enum):
    """Room category."""
    THEORY = "THEORY"
    LAB = "LAB"


class ClassType(str, enum.Enum):
    """Class session type."""
    THEORY = "THEORY"
    LAB = "LAB"


class SolveStatus(str, enum.Enum):
    """Solver run status."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    OPTIMAL = "OPTIMAL"
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"
    ERROR = "ERROR"


# ---------------------------------------------------------------------------
# Association tables
# ---------------------------------------------------------------------------

class FacultySubject(Base):
    """Many-to-many: which faculty can teach which subjects."""
    __tablename__ = "faculty_subjects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    faculty_id = Column(Integer, ForeignKey("faculty.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        UniqueConstraint("faculty_id", "subject_id", name="uq_faculty_subject"),
    )


class DivisionSubject(Base):
    """Many-to-many: curriculum mapping — which divisions study which subjects."""
    __tablename__ = "division_subjects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    division_id = Column(Integer, ForeignKey("divisions.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        UniqueConstraint("division_id", "subject_id", name="uq_division_subject"),
    )


# ---------------------------------------------------------------------------
# Core entities
# ---------------------------------------------------------------------------

class Division(Base):
    """A target student group (e.g., CS-A, IT-B)."""
    __tablename__ = "divisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False)

    # Relationships
    subjects = relationship("Subject", secondary="division_subjects", back_populates="divisions", lazy="selectin")


class Subject(Base):
    """A course with specified weekly theory and lab hours."""
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    theory_hours_per_week = Column(Integer, nullable=False, default=0)
    lab_hours_per_week = Column(Integer, nullable=False, default=0)

    # Relationships
    divisions = relationship("Division", secondary="division_subjects", back_populates="subjects", lazy="selectin")
    faculty = relationship("Faculty", secondary="faculty_subjects", back_populates="subjects", lazy="selectin")


class Faculty(Base):
    """A teaching staff member."""
    __tablename__ = "faculty"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    employee_id = Column(String(50), unique=True, nullable=False)

    # Relationships
    subjects = relationship("Subject", secondary="faculty_subjects", back_populates="faculty", lazy="selectin")


class Room(Base):
    """A physical room categorized as Theory or Lab."""
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    room_type = Column(Enum(RoomType), nullable=False)
    capacity = Column(Integer, nullable=False, default=60)


# ---------------------------------------------------------------------------
# Timetable output
# ---------------------------------------------------------------------------

class SolveRun(Base):
    """Tracks each solver execution and its outcome."""
    __tablename__ = "solve_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(Enum(SolveStatus), nullable=False, default=SolveStatus.PENDING)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    objective_value = Column(Integer, nullable=True)
    total_active_days = Column(Integer, nullable=True)
    solver_log = Column(Text, nullable=True)

    # Relationships
    entries = relationship("TimetableEntry", back_populates="solve_run", lazy="selectin", cascade="all, delete-orphan")


class TimetableEntry(Base):
    """A single scheduled class in the generated timetable."""
    __tablename__ = "timetable_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    solve_run_id = Column(Integer, ForeignKey("solve_runs.id", ondelete="CASCADE"), nullable=False)
    division_id = Column(Integer, ForeignKey("divisions.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    class_type = Column(Enum(ClassType), nullable=False)
    faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    day = Column(Integer, nullable=False)   # 0=Monday .. 4=Friday
    slot = Column(Integer, nullable=False)  # 0=8:00 AM .. 9=5:00-6:00 PM

    # Relationships
    solve_run = relationship("SolveRun", back_populates="entries")
    division = relationship("Division", lazy="selectin")
    subject = relationship("Subject", lazy="selectin")
    faculty_rel = relationship("Faculty", lazy="selectin")
    room = relationship("Room", lazy="selectin")

    __table_args__ = (
        UniqueConstraint(
            "solve_run_id", "division_id", "day", "slot",
            name="uq_division_timeslot_per_run",
        ),
    )
