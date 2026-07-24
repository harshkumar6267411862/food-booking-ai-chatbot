from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

from typing import Generator


from app.config import settings

DATABASE_URL = settings.DATABASE_URL


engine = create_engine(
    DATABASE_URL,
    echo=True
)

#A session is a conversation with the database..
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False #To prevent sqlalchemy to auto push the changes into the databse...
)


class Base(DeclarativeBase):
    pass



def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db #yield pauses the funciton...
    finally:
        db.close()