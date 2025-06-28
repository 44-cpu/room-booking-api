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

@app.get("/")
def home():
    return {"message": "Room Booking System is running"}

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@app.get("/bookings")
def get_bookings(db: Session = Depends(get_db)):
    return db.query(Booking).all()

