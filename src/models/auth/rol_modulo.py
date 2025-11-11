"""
Modelo declarativo para la tabla intermedia Rol-Modulo
"""
from sqlalchemy import Column, Integer, ForeignKey, Boolean, SmallInteger
from sqlalchemy.orm import relationship
from src.models.base import BaseModel

class RolModulo(BaseModel):
    """
    Modelo declarativo para la tabla RolModulo del esquema seguridad
    Tabla intermedia para la relación many-to-many entre Rol y Modulo
    """
    __tablename__ = 'RolModulo'
    __table_args__ = {'schema': 'seguridad'}
    
    # Campos principales - Nombres exactos del schema
    id_rol_modulo = Column(Integer, primary_key=True, autoincrement=True)
    rol_id = Column(Integer, ForeignKey('seguridad.Rol.id_rol'), nullable=False)
    modulo_id = Column(Integer, ForeignKey('seguridad.Modulo.id_modulo'), nullable=False)
    habilitado = Column(Boolean, default=True, nullable=False)
    plataforma = Column(SmallInteger, nullable=True)  # TINYINT
    
    # Relaciones
    rol = relationship("Rol", overlaps="modulos,roles")
    modulo = relationship("Modulo", overlaps="modulos,roles")
    
    def __repr__(self):
        return f"<RolModulo(id={self.id_rol_modulo}, rol_id={self.rol_id}, modulo_id={self.modulo_id}, habilitado={self.habilitado})>"
    
    def is_enabled(self):
        """Verificar si la relación rol-módulo está habilitada"""
        return self.habilitado