import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE_URL = f'sqlite:///{os.path.join(basedir, "data", "selltrack.db")}'

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    os.makedirs(os.path.join(basedir, 'data'), exist_ok=True)
    Base.metadata.create_all(bind=engine)
