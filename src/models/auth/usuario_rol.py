"""
Modelo declarativo para la tabla intermedia Usuario-Rol
"""
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import BaseModel

class UsuarioRol(BaseModel):
    """
    Modelo declarativo para la tabla UsuarioRol del esquema seguridad
    Tabla intermedia para la relación many-to-many entre Usuario y Rol
    """
    __tablename__ = 'UsuarioRol'
    __table_args__ = {'schema': 'seguridad'}
    
    # Campos principales - Nombres exactos del schema
    id_usuario_rol = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey('seguridad.Usuario.id_usuario'), nullable=False)
    rol_id = Column(Integer, ForeignKey('seguridad.Rol.id_rol'), nullable=False)
    
    # Relaciones
    usuario = relationship("Usuario", overlaps="roles,usuarios")
    rol = relationship("Rol", overlaps="roles,usuarios")
    
    def __repr__(self):
        return f"<UsuarioRol(id={self.id_usuario_rol}, usuario_id={self.usuario_id}, rol_id={self.rol_id})>"