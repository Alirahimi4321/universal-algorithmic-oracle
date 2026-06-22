"""SQLAlchemy storage backend supporting SQLite and PostgreSQL.

Per design doc section 21.2: storage technologies for evolutionary memory.
"""
import json
import time
import hashlib
import logging
from typing import Optional, Any
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Text, Boolean,
    Index, MetaData, Table, JSON
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session

logger = logging.getLogger(__name__)
Base = declarative_base()


class ExperimentRecord(Base):
    __tablename__ = "experiments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String(255), unique=True, nullable=False)
    question_text = Column(Text, nullable=False)
    entropy_signature = Column(String(255))
    oracle_id = Column(String(255), nullable=False)
    oracle_version = Column(String(255), nullable=False)
    oracle_graph_hash = Column(String(255), nullable=False)
    prediction_payload = Column(Text, nullable=False)
    prediction_hash = Column(String(255), nullable=False)
    timestamp_created = Column(Float, nullable=False)
    time_horizon = Column(String(255), nullable=False)
    domain = Column(String(255), default="general")
    status = Column(String(50), default="registered")
    outcome = Column(String(50), default="pending")
    outcome_details = Column(Text)
    outcome_timestamp = Column(Float)
    content_hash = Column(String(255), nullable=False)

    __table_args__ = (
        Index("idx_exp_status", "status"),
        Index("idx_exp_outcome", "outcome"),
        Index("idx_exp_domain", "domain"),
    )


class LogEntryRecord(Base):
    __tablename__ = "immutable_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String(255), nullable=False)
    action = Column(String(100), nullable=False)
    timestamp = Column(Float, nullable=False)
    entry_data = Column(Text, nullable=False)
    entry_hash = Column(String(255), nullable=False)
    prev_hash = Column(String(255), nullable=False)
    chain_length = Column(Integer, nullable=False)


class ChromosomeRecord(Base):
    __tablename__ = "chromosomes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chromosome_id = Column(String(255), unique=True, nullable=False)
    generation = Column(Integer, nullable=False)
    fitness_score = Column(Float)
    fitness_data = Column(Text)
    chromosome_data = Column(Text, nullable=False)
    chromosome_hash = Column(String(255), nullable=False)
    lineage_id = Column(String(255))
    parent_ids = Column(Text)
    timestamp = Column(Float, nullable=False)


class VersionRecord(Base):
    __tablename__ = "oracle_versions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(String(255), unique=True, nullable=False)
    oracle_id = Column(String(255), nullable=False)
    chromosome_id = Column(String(255))
    chromosome_hash = Column(String(255))
    generation = Column(Integer, nullable=False)
    parent_id = Column(String(255))
    mutation_type = Column(String(100))
    systems = Column(Text)
    fitness = Column(Text)
    gene_count = Column(Integer)
    edge_count = Column(Integer)
    timestamp = Column(Float, nullable=False)


class StorageBackend:
    """SQLAlchemy-based storage supporting SQLite and PostgreSQL."""

    def __init__(self, url: str = "sqlite:///oracle_memory.db"):
        self.url = url
        self.engine = create_engine(url, echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionFactory = sessionmaker(bind=self.engine)

    def _session(self) -> Session:
        return self.SessionFactory()

    def store_experiment(self, data: dict) -> None:
        with self._session() as session:
            record = ExperimentRecord(**data)
            session.add(record)
            session.commit()

    def get_experiment(self, experiment_id: str) -> Optional[dict]:
        with self._session() as session:
            record = session.query(ExperimentRecord).filter_by(
                experiment_id=experiment_id
            ).first()
            if record:
                return {c.name: getattr(record, c.name) for c in ExperimentRecord.__table__.columns}
            return None

    def update_experiment(self, experiment_id: str, updates: dict) -> bool:
        with self._session() as session:
            record = session.query(ExperimentRecord).filter_by(
                experiment_id=experiment_id
            ).first()
            if not record:
                return False
            for key, value in updates.items():
                if hasattr(record, key):
                    setattr(record, key, value)
            session.commit()
            return True

    def list_experiments(self, status: str = None, domain: str = None) -> list[dict]:
        with self._session() as session:
            query = session.query(ExperimentRecord)
            if status:
                query = query.filter_by(status=status)
            if domain:
                query = query.filter_by(domain=domain)
            return [
                {c.name: getattr(r, c.name) for c in ExperimentRecord.__table__.columns}
                for r in query.order_by(ExperimentRecord.timestamp_created.desc()).all()
            ]

    def store_log_entry(self, data: dict) -> None:
        with self._session() as session:
            record = LogEntryRecord(**data)
            session.add(record)
            session.commit()

    def get_log_entries(self, experiment_id: str) -> list[dict]:
        with self._session() as session:
            records = session.query(LogEntryRecord).filter_by(
                experiment_id=experiment_id
            ).order_by(LogEntryRecord.id).all()
            return [{c.name: getattr(r, c.name) for c in LogEntryRecord.__table__.columns} for r in records]

    def store_chromosome(self, data: dict) -> None:
        with self._session() as session:
            record = ChromosomeRecord(**data)
            session.add(record)
            session.commit()

    def get_chromosome(self, chromosome_id: str) -> Optional[dict]:
        with self._session() as session:
            record = session.query(ChromosomeRecord).filter_by(
                chromosome_id=chromosome_id
            ).first()
            if record:
                return {c.name: getattr(record, c.name) for c in ChromosomeRecord.__table__.columns}
            return None

    def list_chromosomes(self, lineage_id: str = None, limit: int = 100) -> list[dict]:
        with self._session() as session:
            query = session.query(ChromosomeRecord)
            if lineage_id:
                query = query.filter_by(lineage_id=lineage_id)
            return [
                {c.name: getattr(r, c.name) for c in ChromosomeRecord.__table__.columns}
                for r in query.order_by(ChromosomeRecord.timestamp.desc()).limit(limit).all()
            ]

    def store_version(self, data: dict) -> None:
        with self._session() as session:
            record = VersionRecord(**data)
            session.add(record)
            session.commit()

    def get_versions(self, oracle_id: str) -> list[dict]:
        with self._session() as session:
            records = session.query(VersionRecord).filter_by(
                oracle_id=oracle_id
            ).order_by(VersionRecord.generation).all()
            return [{c.name: getattr(r, c.name) for c in VersionRecord.__table__.columns} for r in records]

    def get_stats(self) -> dict:
        with self._session() as session:
            return {
                "experiments": session.query(ExperimentRecord).count(),
                "log_entries": session.query(LogEntryRecord).count(),
                "chromosomes": session.query(ChromosomeRecord).count(),
                "versions": session.query(VersionRecord).count(),
            }
