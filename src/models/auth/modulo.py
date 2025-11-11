"""
Modelo declarativo para Modulo
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import BaseModel, TimestampMixin

class Modulo(BaseModel, TimestampMixin):
    """
    Modelo declarativo para la tabla Modulo del esquema seguridad
    """
    __tablename__ = 'Modulo'
    __table_args__ = {'schema': 'seguridad'}
    
    # Campos principales - Nombres exactos de la BD
    id_modulo = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(30), nullable=False)
    clave = Column(String(20), nullable=False, unique=True)
    descripcion = Column(String(100))
    es_activo = Column(Boolean, default=True, nullable=False)
    # Relaciones
    roles = relationship(
        "Rol",
        secondary="seguridad.RolModulo",
        back_populates="modulos",
        lazy="select"
    )
    
    def __repr__(self):
        return f"<Modulo(id={self.id_modulo}, nombre='{self.nombre}', activo={self.es_activo})>"
    
    def is_active(self):
        """Verificar si el módulo está activo"""
        return self.es_activo