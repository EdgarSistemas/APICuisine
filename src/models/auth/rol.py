"""
Modelo declarativo para Rol
"""
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from src.models.base import BaseModel

class Rol(BaseModel):
    """
    Modelo declarativo para la tabla Rol del esquema seguridad
    """
    __tablename__ = 'Rol'
    __table_args__ = {'schema': 'seguridad'}
    
    # Campos principales - Nombres exactos de la BD
    id_rol = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(30), nullable=False, unique=True)
    descripcion = Column(String(100), nullable=True)
    # Relaciones
    usuarios = relationship(
        "Usuario", 
        secondary="seguridad.UsuarioRol",
        back_populates="roles",
        lazy="select"
    )
    
    modulos = relationship(
        "Modulo",
        secondary="seguridad.RolModulo", 
        back_populates="roles",
        lazy="select"
    )
    
    def __repr__(self):
        return f"<Rol(id={self.id_rol}, nombre='{self.nombre}')>"
    
    def has_module(self, modulo_nombre):
        """Verificar si el rol tiene acceso a un módulo específico"""
        return any(modulo.nombre == modulo_nombre for modulo in self.modulos)
    
    def get_permissions(self):
        """Obtener todos los módulos/permisos del rol"""
        return [modulo.nombre for modulo in self.modulos]