"""
Mejora - Modelo para sugerencias de mejora
Mapea tabla servicio.Mejoras
"""

from sqlalchemy import Column, Integer, SmallInteger, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import BaseModel


class Mejora(BaseModel):
    """Modelo para Mejoras/Sugerencias"""
    __tablename__ = 'Mejoras'
    __table_args__ = {'schema': 'servicio'}
    
    id_mejora = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey('seguridad.Usuario.id_usuario'), nullable=False)
    notas = Column(String(300), nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.getdate())
    estatus = Column(SmallInteger, nullable=False, default=1)  # 1=Registrada, 2=En proceso, 3=Completada
    
    # Relaciones
    cliente = relationship("Usuario")
    
    def __repr__(self):
        return f"<Mejora id={self.id_mejora} cliente={self.cliente_id}>"
