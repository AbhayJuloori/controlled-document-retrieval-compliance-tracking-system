from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from controlled_docs.config import AppConfig
from controlled_docs.models import AccessPolicy, Base


DEFAULT_ACCESS_POLICIES = (
    AccessPolicy(
        role="Analyst",
        allowed_jurisdictions=["US-FDA", "EU-MDR", "ISO13485"],
        allowed_doc_types=["SOP", "WI", "POLICY", "TRAINING", "CAPA"],
    ),
    AccessPolicy(
        role="Auditor",
        allowed_jurisdictions=["US-FDA", "EU-MDR", "ISO13485"],
        allowed_doc_types=["SOP", "WI", "POLICY", "TRAINING", "CAPA"],
    ),
    AccessPolicy(
        role="QualityLead",
        allowed_jurisdictions=["US-FDA", "EU-MDR", "ISO13485"],
        allowed_doc_types=["SOP", "WI", "POLICY", "TRAINING", "CAPA"],
    ),
)


def build_engine(config: AppConfig):
    return create_engine(config.database_url, future=True)


def initialize_database(config: AppConfig) -> sessionmaker[Session]:
    engine = build_engine(config)
    if engine.dialect.name == "postgresql":
        with engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=True, expire_on_commit=False)
    with session_factory() as session:
        for policy in DEFAULT_ACCESS_POLICIES:
            if session.get(AccessPolicy, policy.role) is None:
                session.add(
                    AccessPolicy(
                        role=policy.role,
                        allowed_jurisdictions=policy.allowed_jurisdictions,
                        allowed_doc_types=policy.allowed_doc_types,
                    )
                )
        session.commit()
    return session_factory


@contextmanager
def session_scope(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
