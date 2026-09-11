"""Subject CRUD API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.database import get_db
from app.schemas import SubjectCreate, SubjectRead

router = APIRouter(prefix="/subjects", tags=["Subjects"])


@router.post("/", response_model=SubjectRead, status_code=201)
async def create_subject(data: SubjectCreate, db: AsyncSession = Depends(get_db)):
    """Create a new subject."""
    return await crud.create_subject(
        db, data.name, data.code, data.theory_hours_per_week, data.lab_hours_per_week
    )


@router.get("/", response_model=list[SubjectRead])
async def list_subjects(db: AsyncSession = Depends(get_db)):
    """List all subjects."""
    return await crud.get_subjects(db)


@router.get("/{subject_id}", response_model=SubjectRead)
async def get_subject(subject_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single subject by ID."""
    subject = await crud.get_subject(db, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject


@router.delete("/{subject_id}", status_code=204)
async def delete_subject(subject_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a subject."""
    deleted = await crud.delete_subject(db, subject_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Subject not found")
