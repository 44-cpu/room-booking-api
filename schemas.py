from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class BookingBase(BaseModel):
    room_id: Optional[int] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    full_day: bool = False

class BookingCreate(BookingBase):
    user_id: int

class BookingOut(BaseModel):
    id: int
    user_id: int
    room_id: int
    start_time: datetime
    end_time: datetime
    full_day: bool
    created_at: datetime

    class Config:
        from_attributes = True  



class RoomCreate(BaseModel):
    name: str
    type: str
    capacity: int
    full_day_allowed: bool

class RoomOut(BaseModel):
    id: int
    name: str
    type: str
    capacity: int
    full_day_allowed: bool

    class Config:
        from_attributes = True



class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True
