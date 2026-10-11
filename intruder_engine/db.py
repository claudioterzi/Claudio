"""Database layer — SQLite + SQLAlchemy."""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import (
    Column, Float, ForeignKey, Integer, Text,
    create_engine, event,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

DEFAULT_DB_PATH = Path.home() / ".intruder" / "data.db"


class Base(DeclarativeBase):
    pass


class Event(Base):
    __tablename__ = "events"

    id        = Column(Integer, primary_key=True)
    timestamp = Column(Text, nullable=False)
    source    = Column(Text, nullable=False)   # diary, email, calendar, chat…
    content   = Column(Text, nullable=False)
    _embedding = Column("embedding", Text)     # JSON-serialised list[float]

    @property
    def embedding(self) -> list[float] | None:
        return json.loads(self._embedding) if self._embedding else None

    @embedding.setter
    def embedding(self, vec: list[float] | None) -> None:
        self._embedding = json.dumps(vec) if vec is not None else None


class Entity(Base):
    __tablename__ = "entities"

    id   = Column(Integer, primary_key=True)
    type = Column(Text, nullable=False)   # person, place, idea, project, emotion
    name = Column(Text, nullable=False, unique=True)


class Relationship(Base):
    __tablename__ = "relationships"

    source_id = Column(Integer, ForeignKey("entities.id"), primary_key=True)
    target_id = Column(Integer, ForeignKey("entities.id"), primary_key=True)
    weight    = Column(Float, default=1.0)

    source = relationship("Entity", foreign_keys=[source_id])
    target = relationship("Entity", foreign_keys=[target_id])


class Trace(Base):
    __tablename__ = "traces"

    id          = Column(Integer, primary_key=True)
    trace_type  = Column(Text, nullable=False)  # recurrence, convergence, anomaly, acceleration, absence
    score       = Column(Float, nullable=False)
    description = Column(Text)
    timestamp   = Column(Text, nullable=False)


def make_engine(db_path: Path = DEFAULT_DB_PATH):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    return engine


def make_session(db_path: Path = DEFAULT_DB_PATH) -> Session:
    engine = make_engine(db_path)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
