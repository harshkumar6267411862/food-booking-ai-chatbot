from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

from typing import Generator


DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{settings.DATABASE_USER}:"
    f"{settings.DATABASE_PASSWORD}@"
    f"{settings.DATABASE_HOST}:"
    f"{settings.DATABASE_PORT}/"
    f"{settings.DATABASE_NAME}"
)


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