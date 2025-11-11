"""
Horario - Modelo para plantillas de horarios
Mapea tabla rrhh.Horario
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import BaseModel


class Horario(BaseModel):
    """Modelo para Horarios (plantillas)"""
    __tablename__ = 'Horario'
    __table_args__ = {'schema': 'rrhh'}
    
    id_horario = Column(Integer, primary_key=True, autoincrement=True)
    sucursal_id = Column(Integer, ForeignKey('catalogos.Sucursal.id_sucursal'), nullable=True)  # NULL = global
    clave = Column(String(60), unique=True, nullable=False)
    nombre = Column(String(120), nullable=False)
    descripcion = Column(String(300), nullable=True)
    es_activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=func.getdate())
    updated_at = Column(DateTime, nullable=True, onupdate=func.getdate())
    
    # Relaciones
    sucursal = relationship("Sucursal")
    detalles = relationship("HorarioDetalle", back_populates="horario")
    
    def __repr__(self):
        return f"<Horario id={self.id_horario} clave={self.clave}>"
