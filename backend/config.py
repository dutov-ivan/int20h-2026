from sqlmodel import SQLModel, create_engine, Session
from typing import Generator

# Postgres Connection String
# Format: postgresql://<username>:<password>@<host>:<port>/<db_name>
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/int20h_db"

# create_engine handles the connection pool
engine = create_engine(DATABASE_URL, echo=True)  # echo=True logs SQL for debugging


def create_db_and_tables():
    """Creates tables if they don't exist (useful for dev/prototyping)"""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Dependency to provide a DB session for each request"""
    with Session(engine) as session:
        yield session
