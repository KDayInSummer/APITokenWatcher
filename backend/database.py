from sqlmodel import SQLModel, create_engine, Session
from backend.config import settings

engine = create_engine(f"sqlite:///{settings.db_path}", echo=False, connect_args={"check_same_thread": False})


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
