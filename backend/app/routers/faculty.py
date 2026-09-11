"""Faculty CRUD API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.database import get_db
from app.schemas import FacultyCreate, FacultyRead

router = APIRouter(prefix="/faculty", tags=["Faculty"])


class SubjectAssignment(BaseModel):
    subject_ids: list[int]


@router.post("/", response_model=FacultyRead, status_code=201)
async def create_faculty(data: FacultyCreate, db: AsyncSession = Depends(get_db)):
    """Create a new faculty member with optional subject assignments."""
    return await crud.create_faculty(db, data.name, data.employee_id, data.subject_ids)


@router.get("/", response_model=list[FacultyRead])
async def list_faculty(db: AsyncSession = Depends(get_db)):
    """List all faculty members with their subjects."""
    return await crud.get_all_faculty(db)


@router.get("/{faculty_id}", response_model=FacultyRead)
async def get_faculty(faculty_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single faculty member by ID."""
    faculty = await crud.get_faculty(db, faculty_id)
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty not found")
    return faculty


@router.put("/{faculty_id}/subjects", response_model=FacultyRead)
async def assign_subjects(
    faculty_id: int,
    data: SubjectAssignment,
    db: AsyncSession = Depends(get_db),
):
    """Assign subjects to a faculty member (replaces existing assignments)."""
    faculty = await crud.assign_subjects_to_faculty(db, faculty_id, data.subject_ids)
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty not found")
    return faculty


@router.delete("/{faculty_id}", status_code=204)
async def delete_faculty(faculty_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a faculty member."""
    deleted = await crud.delete_faculty(db, faculty_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Faculty not found")
