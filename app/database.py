from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Use directory-based path for Docker compatibility
SQLALCHEMY_DATABASE_URL = "sqlite:////app/data/medical_records.db"
#initialize the connection to database
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
#create a session for the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#create base class for all models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()