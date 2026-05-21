from sqlalchemy import create_engine, Column, String, Integer, DateTime, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from src.backend.app.core.config import settings

Base = declarative_base()

class Track(Base):
    __tablename__ = "tracks"

    id = Column(String, primary_key=True, index=True) # Usually the video ID
    title = Column(String)
    url = Column(String)
    duration = Column(Integer) # In seconds
    thumbnail = Column(String)
    file_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class DownloadTask(Base):
    __tablename__ = "download_tasks"

    id = Column(String, primary_key=True, index=True) # Unique task UUID
    url = Column(String)
    status = Column(String, default="pending") # pending, downloading, completed, failed
    progress = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    track_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})

# Habilitar modo WAL para suportar múltiplos acessos simultâneos sem travar o banco
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
