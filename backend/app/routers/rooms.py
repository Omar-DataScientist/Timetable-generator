"""Room CRUD API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.database import get_db
from app.models import RoomType
from app.schemas import RoomCreate, RoomRead

router = APIRouter(prefix="/rooms", tags=["Rooms"])


@router.post("/", response_model=RoomRead, status_code=201)
async def create_room(data: RoomCreate, db: AsyncSession = Depends(get_db)):
    """Create a new room."""
    return await crud.create_room(db, data.name, RoomType(data.room_type.value), data.capacity)


@router.get("/", response_model=list[RoomRead])
async def list_rooms(db: AsyncSession = Depends(get_db)):
    """List all rooms."""
    return await crud.get_rooms(db)


@router.get("/{room_id}", response_model=RoomRead)
async def get_room(room_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single room by ID."""
    room = await crud.get_room(db, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@router.delete("/{room_id}", status_code=204)
async def delete_room(room_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a room."""
    deleted = await crud.delete_room(db, room_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Room not found")
