"""
models.py — ORM models untuk Dynamic Message Mapper
"""
import json
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, Text, DateTime, ForeignKey, Float
)
from sqlalchemy.orm import relationship
from database import Base


class Partner(Base):
    """Tabel partner eksternal."""
    __tablename__ = "partners"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    base_url = Column(String(255), nullable=True)
    api_key = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    endpoints = relationship("PartnerEndpoint", back_populates="partner", cascade="all,delete")
    logs = relationship("TransformLog", back_populates="partner", cascade="all,delete")


class PartnerEndpoint(Base):
    """Tabel endpoint partner beserta konfigurasi mapping field."""
    __tablename__ = "partner_endpoints"

    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False)
    name = Column(String(100), nullable=False)
    path = Column(String(255), nullable=False)
    method = Column(String(10), default="POST")
    description = Column(Text, nullable=True)
    _mapping_rules = Column("mapping_rules", Text, default="[]")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    partner = relationship("Partner", back_populates="endpoints")

    @property
    def mapping_rules(self):
        return json.loads(self._mapping_rules or "[]")

    @mapping_rules.setter
    def mapping_rules(self, value):
        self._mapping_rules = json.dumps(value, ensure_ascii=False)


class TransformLog(Base):
    """Tabel log transformasi request/response."""
    __tablename__ = "transform_logs"

    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=True)
    endpoint_id = Column(Integer, ForeignKey("partner_endpoints.id"), nullable=True)
    _input_payload = Column("input_payload", Text, nullable=True)
    _output_payload = Column("output_payload", Text, nullable=True)
    _validation_errors = Column("validation_errors", Text, default="[]")
    _mapping_errors = Column("mapping_errors", Text, default="[]")
    is_success = Column(Boolean, default=True)
    transform_latency_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    partner = relationship("Partner", back_populates="logs")

    @property
    def input_payload(self):
        return json.loads(self._input_payload or "{}")

    @input_payload.setter
    def input_payload(self, value):
        self._input_payload = json.dumps(value, ensure_ascii=False)

    @property
    def output_payload(self):
        return json.loads(self._output_payload or "{}")

    @output_payload.setter
    def output_payload(self, value):
        self._output_payload = json.dumps(value, ensure_ascii=False)

    @property
    def validation_errors(self):
        return json.loads(self._validation_errors or "[]")

    @validation_errors.setter
    def validation_errors(self, value):
        self._validation_errors = json.dumps(value, ensure_ascii=False)

    @property
    def mapping_errors(self):
        return json.loads(self._mapping_errors or "[]")

    @mapping_errors.setter
    def mapping_errors(self, value):
        self._mapping_errors = json.dumps(value, ensure_ascii=False)
