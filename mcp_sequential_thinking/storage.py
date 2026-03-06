import json
from typing import List, Optional
from pathlib import Path
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Text, Table, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

from .models import ThoughtData
from .logging_conf import configure_logging

logger = configure_logging("sequential-thinking.database-storage")

Base = declarative_base()

# Association Tables for Many-to-Many relationships
thought_tags_association = Table(
    'thought_tags',
    Base.metadata,
    Column('thought_id', String, ForeignKey('thoughts.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

thought_axioms_association = Table(
    'thought_axioms',
    Base.metadata,
    Column('thought_id', String, ForeignKey('thoughts.id')),
    Column('axiom_id', Integer, ForeignKey('axioms.id'))
)

thought_assumptions_association = Table(
    'thought_assumptions',
    Base.metadata,
    Column('thought_id', String, ForeignKey('thoughts.id')),
    Column('assumption_id', Integer, ForeignKey('assumptions.id'))
)

thought_evidence_association = Table(
    'thought_evidence',
    Base.metadata,
    Column('thought_id', String, ForeignKey('thoughts.id')),
    Column('evidence_id', Integer, ForeignKey('supporting_evidence.id'))
)

thought_counters_association = Table(
    'thought_counters',
    Base.metadata,
    Column('thought_id', String, ForeignKey('thoughts.id')),
    Column('counter_id', Integer, ForeignKey('counter_arguments.id'))
)

class ThoughtModel(Base):
    __tablename__ = 'thoughts'
    id = Column(String, primary_key=True)
    thought = Column(Text, nullable=False)
    thought_number = Column(Integer, nullable=False)
    total_thoughts = Column(Integer, nullable=False)
    next_thought_needed = Column(Boolean, nullable=False)
    thought_type = Column(String, nullable=False, default='analysis')
    stage = Column(String, nullable=False)
    parent_thought_id = Column(String, nullable=True)
    revises_thought_id = Column(String, nullable=True)
    branch_label = Column(String, nullable=True)
    confidence_level = Column(Float, default=0.5)
    timestamp = Column(String, nullable=False)

    tags = relationship("TagModel", secondary=thought_tags_association, back_populates="thoughts")
    axioms_used = relationship("AxiomModel", secondary=thought_axioms_association, back_populates="thoughts")
    assumptions_challenged = relationship("AssumptionModel", secondary=thought_assumptions_association, back_populates="thoughts")
    supporting_evidence = relationship("EvidenceModel", secondary=thought_evidence_association, back_populates="thoughts")
    counter_arguments = relationship("CounterArgumentModel", secondary=thought_counters_association, back_populates="thoughts")

class TagModel(Base):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    thoughts = relationship("ThoughtModel", secondary=thought_tags_association, back_populates="tags")

class AxiomModel(Base):
    __tablename__ = 'axioms'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    thoughts = relationship("ThoughtModel", secondary=thought_axioms_association, back_populates="axioms_used")

class AssumptionModel(Base):
    __tablename__ = 'assumptions'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    thoughts = relationship("ThoughtModel", secondary=thought_assumptions_association, back_populates="assumptions_challenged")

class EvidenceModel(Base):
    __tablename__ = 'supporting_evidence'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    thoughts = relationship("ThoughtModel", secondary=thought_evidence_association, back_populates="supporting_evidence")

class CounterArgumentModel(Base):
    __tablename__ = 'counter_arguments'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    thoughts = relationship("ThoughtModel", secondary=thought_counters_association, back_populates="counter_arguments")


class ThoughtStorage:
    """Database-backed storage manager for thought data."""

    def __init__(self, db_url: str):
        logger.info(f"--- ENTERING ThoughtStorage __init__ ---")
        logger.info(f"Initializing database storage with URL: {db_url}")
        self.engine = create_engine(db_url)
        logger.info(f"--- DATABASE ENGINE CREATED ---")
        Base.metadata.create_all(self.engine)
        logger.info(f"--- METADATA.CREATE_ALL CALLED ---")
        self.Session = sessionmaker(bind=self.engine)
        logger.info(f"--- ThoughtStorage INITIALIZED SUCCESSFULLY ---")

    def _get_or_create(self, session, model, name):
        instance = session.query(model).filter_by(name=name).first()
        if not instance:
            instance = model(name=name)
            session.add(instance)
            session.flush() # Flush to get the ID without committing
        return instance

    def add_thought(self, thought_data: ThoughtData) -> None:
        with self.Session() as session:
            thought_model = ThoughtModel(
                id=str(thought_data.id),
                thought=thought_data.thought,
                thought_number=thought_data.thought_number,
                total_thoughts=thought_data.total_thoughts,
                next_thought_needed=thought_data.next_thought_needed,
                thought_type=thought_data.thought_type,
                stage=thought_data.stage,
                parent_thought_id=thought_data.parent_thought_id,
                revises_thought_id=thought_data.revises_thought_id,
                branch_label=thought_data.branch_label,
                confidence_level=thought_data.confidence_level,
                timestamp=thought_data.timestamp
            )

            thought_model.tags = [self._get_or_create(session, TagModel, name) for name in thought_data.tags]
            thought_model.axioms_used = [self._get_or_create(session, AxiomModel, name) for name in thought_data.axioms_used]
            thought_model.assumptions_challenged = [self._get_or_create(session, AssumptionModel, name) for name in thought_data.assumptions_challenged]
            thought_model.supporting_evidence = [self._get_or_create(session, EvidenceModel, name) for name in thought_data.supporting_evidence]
            thought_model.counter_arguments = [self._get_or_create(session, CounterArgumentModel, name) for name in thought_data.counter_arguments]

            session.add(thought_model)
            session.commit()
        logger.info(f"Added thought #{thought_data.thought_number} to the database.")

    def get_all_thoughts(self) -> List[ThoughtData]:
        with self.Session() as session:
            all_thought_models = session.query(ThoughtModel).order_by(ThoughtModel.thought_number).all()
            result = []
            for tm in all_thought_models:
                thought_data = ThoughtData(
                    id=tm.id,
                    thought=tm.thought,
                    thought_number=tm.thought_number,
                    total_thoughts=tm.total_thoughts,
                    next_thought_needed=tm.next_thought_needed,
                    thought_type=tm.thought_type or 'analysis',
                    stage=tm.stage,
                    parent_thought_id=tm.parent_thought_id,
                    revises_thought_id=tm.revises_thought_id,
                    branch_label=tm.branch_label,
                    confidence_level=tm.confidence_level,
                    timestamp=tm.timestamp,
                    tags=[tag.name for tag in tm.tags],
                    axioms_used=[axiom.name for axiom in tm.axioms_used],
                    assumptions_challenged=[assumption.name for assumption in tm.assumptions_challenged],
                    supporting_evidence=[evidence.name for evidence in tm.supporting_evidence],
                    counter_arguments=[counter.name for counter in tm.counter_arguments]
                )
                result.append(thought_data)
        return result

    def clear_history(self) -> None:
        """Clear all thought data from the database."""
        logger.info("Clearing all thought data from the database.")
        with self.Session() as session:
            # Delete in correct order to respect foreign key constraints
            session.execute(thought_tags_association.delete())
            session.execute(thought_axioms_association.delete())
            session.execute(thought_assumptions_association.delete())
            session.execute(thought_evidence_association.delete())
            session.execute(thought_counters_association.delete())
            session.query(ThoughtModel).delete()
            session.query(TagModel).delete()
            session.query(AxiomModel).delete()
            session.query(AssumptionModel).delete()
            session.query(EvidenceModel).delete()
            session.query(CounterArgumentModel).delete()
            session.commit()
        logger.info("Database cleared.")

    def export_session(self, file_path: str) -> None:
        logger.info(f"Starting session export to {file_path}")
        all_thoughts = self.get_all_thoughts()
        thoughts_as_dicts = [t.to_dict(include_id=True) for t in all_thoughts]
        
        export_data = {
            "exportedAt": datetime.now().isoformat(),
            "thoughts": thoughts_as_dicts
        }

        try:
            p = Path(file_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured directory exists: {p.parent}")

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Session successfully exported to {file_path}")

        except Exception as e:
            logger.error(f"Failed to export session to {file_path}: {e}")
            raise

    def import_session(self, file_path: str) -> None:
        logger.info(f"Starting session import from {file_path}")
        
        p = Path(file_path)
        if not p.exists():
            logger.error(f"Import file not found at {file_path}")
            raise FileNotFoundError(f"Import file not found: {file_path}")
        
        if not p.is_file():
            logger.error(f"Import path is not a file: {file_path}")
            raise ValueError(f"Import path is not a file: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            thoughts_to_import = import_data.get("thoughts", [])
            
            self.clear_history() # Clear existing data before import

            for thought_dict in thoughts_to_import:
                thought_data = ThoughtData.from_dict(thought_dict)
                self.add_thought(thought_data)
            
            logger.info(f"Successfully imported {len(thoughts_to_import)} thoughts from {file_path}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to import session from {file_path}: {e}")
            raise