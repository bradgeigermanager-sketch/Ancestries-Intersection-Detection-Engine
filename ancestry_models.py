"""
MODULE: ancestry_schema_models
VERSION: 1.0.0
TYPE: Database Object Mapping (SQLAlchemy ORM)
USE: Establishes person nodes and explicit ancestral lineage links.
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import declarative_base, relationship
import uuid

Base = declarative_base()

class PersonNode(Base):
    """
    [SLOT: GENEALOGY_NODE_REGISTRY]
    Represents an individual within the global ancestral registry.
    """
    __tablename__ = "person_nodes"

    person_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name = Column(String(150), nullable=False)
    birth_year = Column(Integer, nullable=True)
    birth_place = Column(String(150), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Self-referential links to model parental paths directly
    father_id = Column(String(36), ForeignKey("person_nodes.person_id"), nullable=True)
    mother_id = Column(String(36), ForeignKey("person_nodes.person_id"), nullable=True)

    # ORM mappings for traversal
    father = relationship("PersonNode", remote_side=[person_id], foreign_keys=[father_id])
    mother = relationship("PersonNode", remote_side=[person_id], foreign_keys=[mother_id])
  
