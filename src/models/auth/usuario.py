"""
Modelo declarativo para Usuario
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from src.models.base import BaseModel, TimestampMixin

class Usuario(BaseModel, TimestampMixin):
    """
    Modelo declarativo para la tabla Usuario del esquema seguridad
    """
    __tablename__ = 'Usuario'
    __table_args__ = {'schema': 'seguridad'}
    
    # Campos principales
    id_usuario = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(50), nullable=False)
    hash_password = Column(Text, nullable=True)  # NVARCHAR(MAX) 
    nombre = Column(String(50), nullable=False)
    apellido = Column(String(30), nullable=True)
    telefono = Column(String(30), nullable=True)
    es_activo = Column(Boolean, default=True, nullable=False)
    es_cliente = Column(Boolean, default=False, nullable=False)
    acepta_marketing = Column(Boolean, default=False, nullable=False)
    tipo_acceso = Column(String(5), nullable=True)
    # Relaciones
    roles = relationship(
        "Rol", 
        secondary="seguridad.UsuarioRol",
        back_populates="usuarios",
        lazy="select"
    )
    
    sucursales = relationship(
        "UsuarioSucursal",
        back_populates="usuario",
        lazy="select"
    )
    
    push_tokens = relationship(
        "PushToken",
        back_populates="usuario",
        lazy="select"
    )
    
    codigos_reset = relationship(
        "CodigoReset",
        back_populates="usuario",
        lazy="select"
    )
    
    logs = relationship(
        "LogAccion",
        back_populates="usuario",
        lazy="select"
    ) 
    
    def __repr__(self):
        return f"<Usuario(id={self.id_usuario}, email='{self.email}', activo={self.es_activo})>"
    
    def to_dict(self, include_password=False):
        """
        Convertir a diccionario con opción de excluir password
        """
        result = super().to_dict()
        if not include_password and 'hash_password' in result:
            del result['hash_password']
        return result
    
    def is_active(self):
        """Verificar si el usuario está activo"""
        return self.es_activo
    
    def has_role(self, rol_nombre):
        """Verificar si el usuario tiene un rol específico"""
        return any(rol.nombre == rol_nombre for rol in self.roles)