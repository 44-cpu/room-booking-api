from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

POSTGRES_USERNAME = "postgres"
POSTGRES_PASSWORD = "postgres"
POSTGRES_HOST = "127.0.0.1"
POSTGRES_DB = "room_booking_db"

#master database
DATABASE_URL = f"postgresql://{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DB}"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()