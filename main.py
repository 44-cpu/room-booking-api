from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, TIMESTAMP, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from datetime import datetime

# FastAPI app
app = FastAPI()

# Database config
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/room_booking_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# SQLAlchemy Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(150), unique=True, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    bookings = relationship("Booking", back_populates="user")

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    room_id = Column(Integer)
    start_time = Column(TIMESTAMP)
    end_time = Column(TIMESTAMP)

    user = relationship("User", back_populates="bookings")

# Pydantic Models
class UserCreate(BaseModel):
    name: str
    email: str

class BookingCreate(BaseModel):
    user_id: int
    room_id: int
    start_time: datetime
    end_time: datetime

# Routes
@app.get("/")
def home():
    return {"message": "Room Booking API is running"}

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@app.post("/users")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = User(name=user.name, email=user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/bookings")
def get_bookings(db: Session = Depends(get_db)):
    return db.query(Booking).all()

@app.post("/bookings")
def create_booking(booking: BookingCreate, db: Session = Depends(get_db)):
    new_booking = Booking(
        user_id=booking.user_id,
        room_id=booking.room_id,
        start_time=booking.start_time,
        end_time=booking.end_time
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    return new_booking
