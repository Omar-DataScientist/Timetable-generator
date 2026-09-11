"""Division CRUD API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.database import get_db
from app.schemas import DivisionCreate, DivisionRead

router = APIRouter(prefix="/divisions", tags=["Divisions"])


@router.post("/", response_model=DivisionRead, status_code=201)
async def create_division(data: DivisionCreate, db: AsyncSession = Depends(get_db)):
    """Create a new division with optional subject mappings."""
    division = await crud.create_division(db, data.name, data.code, data.subject_ids)
    return division


@router.get("/", response_model=list[DivisionRead])
async def list_divisions(db: AsyncSession = Depends(get_db)):
    """List all divisions with their subjects."""
    return await crud.get_divisions(db)


@router.get("/{division_id}", response_model=DivisionRead)
async def get_division(division_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single division by ID."""
    division = await crud.get_division(db, division_id)
    if not division:
        raise HTTPException(status_code=404, detail="Division not found")
    return division


@router.delete("/{division_id}", status_code=204)
async def delete_division(division_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a division."""
    deleted = await crud.delete_division(db, division_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Division not found")
