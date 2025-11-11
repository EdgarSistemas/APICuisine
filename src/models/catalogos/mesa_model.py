"""
Mesa Model
catalogos.Mesa - Tablas del restaurante
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Index, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import Base, BaseModel


class Mesa(BaseModel):
    __tablename__ = 'Mesa'
    __table_args__ = (
        Index('IX_Mesa_Area', 'area_id'),
        Index('IX_Mesa_Activa', 'es_activa'),
        {'schema': 'catalogos'}
    )
    
    id_mesa = Column(Integer, primary_key=True)
    area_id = Column(Integer, ForeignKey('catalogos.Area.id_area'), nullable=False)
    codigo_mesa = Column(String(20), nullable=False)
    capacidad = Column(Integer, nullable=False)
    es_activa = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=text('GETUTCDATE()'), nullable=False)
    updated_at = Column(DateTime)
    
    # Relaciones
    area = relationship("Area", backref="mesas")
    
    def __repr__(self):
        return f"<Mesa {self.id_mesa}: {self.codigo_mesa} (Area {self.area_id})>"
