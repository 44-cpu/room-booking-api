from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, and_, func
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, date, time
from typing import List, Optional, Union

from models import Base, User, Booking, Room
import schemas


DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/room_booking_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Room Booking API")


KNOWN_ROOM_IDS = [1, 2, 3, 4, 5, 6, 7]


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def home():
    return {"message": "Room Booking API is running"}


@app.post("/rooms", response_model=Union[schemas.RoomOut, List[schemas.RoomOut]])
def create_room(
    rooms: Union[schemas.RoomCreate, List[schemas.RoomCreate]],
    db: Session = Depends(get_db)
):
    
    if isinstance(rooms, schemas.RoomCreate):
        new = Room(
            name=rooms.name,
            type=rooms.type,
            capacity=rooms.capacity,
            full_day_allowed=rooms.full_day_allowed,
        )
        db.add(new)
        db.commit()
        db.refresh(new)
        return new

    
    created_rooms = []
    for room in rooms:
        new = Room(
            name=room.name,
            type=room.type,
            capacity=room.capacity,
            full_day_allowed=room.full_day_allowed,
        )
        db.add(new)
        db.commit()
        db.refresh(new)
        created_rooms.append(new)
    return created_rooms

    
@app.get("/rooms", response_model=List[schemas.RoomOut])
def list_rooms(db: Session = Depends(get_db)):
    return db.query(Room).all()


@app.post("/users", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(func.lower(User.email) == user.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

   
    new_user = User(name=user.name, email=user.email, password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/users", response_model=List[schemas.UserOut])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()


def overlap_filter(start_field, end_field, start_time, end_time):
    """Check if two time ranges overlap"""
    return and_(start_field < end_time, end_field > start_time)

def find_available_rooms(db: Session, start_time: datetime, end_time: datetime) -> List[int]:
    """Find rooms that are free in the given time slot"""
    rooms = db.query(Room).filter(Room.id.in_(KNOWN_ROOM_IDS)).all()
    all_room_ids = {r.id for r in rooms}

    overlapping = (
        db.query(Booking.room_id)
        .filter(
            Booking.room_id.in_(all_room_ids),
            overlap_filter(Booking.start_time, Booking.end_time, start_time, end_time),
        )
        .all()
    )

    booked_ids = {row[0] for row in overlapping}
    return list(all_room_ids - booked_ids)

def compute_next_available(db: Session, requested_start: datetime) -> Optional[dict]:
    """Find the earliest room that will become available after requested_start"""
    row = (
        db.query(Booking.room_id, func.min(Booking.end_time).label("free_at"))
        .filter(Booking.end_time > requested_start)
        .group_by(Booking.room_id)
        .order_by(func.min(Booking.end_time))
        .first()
    )
    if not row:
        return None
    return {"room_id": row[0], "available_at": row[1].isoformat()}


@app.post("/bookings", response_model=schemas.BookingOut)
def create_booking(payload: schemas.BookingCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    
    if payload.full_day:
        if not payload.start_time:
            raise HTTPException(status_code=400, detail="start_time (date) required for full_day booking")
        d: date = payload.start_time.date()
        start_time = datetime.combine(d, time.min)
        end_time = datetime.combine(d, time.max.replace(microsecond=0))
    else:
        if not payload.start_time or not payload.end_time:
            raise HTTPException(status_code=400, detail="start_time and end_time are required for hourly bookings")
        start_time = payload.start_time
        end_time = payload.end_time

    now = datetime.utcnow()
    if start_time >= end_time:
        raise HTTPException(status_code=400, detail="start_time must be before end_time")
    if end_time <= now:
        raise HTTPException(status_code=400, detail="Cannot create booking in the past")

    
    if payload.room_id:
        if payload.room_id not in KNOWN_ROOM_IDS:
            raise HTTPException(status_code=404, detail="Requested room not found")

        conflict = (
            db.query(Booking)
            .filter(
                Booking.room_id == payload.room_id,
                overlap_filter(Booking.start_time, Booking.end_time, start_time, end_time),
            )
            .first()
        )

        if conflict:
            raise HTTPException(
                status_code=409,
                detail=f"Room {payload.room_id} is already booked from {conflict.start_time} to {conflict.end_time}",
            )

        new_booking = Booking(
            user_id=payload.user_id,
            room_id=payload.room_id,
            start_time=start_time,
            end_time=end_time,
            full_day=payload.full_day,
        )
        db.add(new_booking)
        db.commit()
        db.refresh(new_booking)
        return new_booking

    
    rooms_query = db.query(Room).filter(Room.id.in_(KNOWN_ROOM_IDS))
    if payload.full_day:
        rooms_query = rooms_query.filter(Room.full_day_allowed == True)
    rooms = rooms_query.all()
    if not rooms:
        raise HTTPException(status_code=404, detail="No rooms available that support full-day booking")

    all_room_ids = [r.id for r in rooms]
    free_ids = find_available_rooms(db, start_time, end_time)
    free_ids = [rid for rid in all_room_ids if rid in free_ids]

    if free_ids:
        chosen_room_id = free_ids[0]
        new_booking = Booking(
            user_id=payload.user_id,
            room_id=chosen_room_id,
            start_time=start_time,
            end_time=end_time,
            full_day=payload.full_day,
        )
        db.add(new_booking)
        db.commit()
        db.refresh(new_booking)
        return new_booking

    
    next_info = compute_next_available(db, start_time)
    if next_info:
        raise HTTPException(
            status_code=409,
            detail=(
                f"All rooms are booked for the requested slot. "
                f"Earliest available: Room {next_info['room_id']} at {next_info['available_at']}."
            ),
        )
    raise HTTPException(
        status_code=409,
        detail="All rooms are booked for the requested slot, no upcoming availability found.",
    )

@app.get("/bookings", response_model=List[schemas.BookingOut])
def get_bookings(db: Session = Depends(get_db)):
    return db.query(Booking).all()


@app.get("/available-rooms")
def get_available_rooms(start_time: datetime, end_time: datetime, db: Session = Depends(get_db)):
    if start_time >= end_time:
        raise HTTPException(status_code=400, detail="start_time must be before end_time")

    available = find_available_rooms(db, start_time, end_time)
    if available:
        return {"available_rooms": available, "message": None, "next_available": None}

    next_info = compute_next_available(db, start_time)
    if next_info:
        return {
            "available_rooms": [],
            "message": (
                f"All rooms are booked for this slot. "
                f"Earliest available: Room {next_info['room_id']} at {next_info['available_at']}."
            ),
            "next_available": next_info,
        }
    return {
        "available_rooms": [],
        "message": "All rooms are booked for this slot, no upcoming availability found.",
        "next_available": None,
    }
