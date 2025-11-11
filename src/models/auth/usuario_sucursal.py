"""
Modelo declarativo para Usuario-Sucursal
"""
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import BaseModel

class UsuarioSucursal(BaseModel):
    """
    Modelo declarativo para la tabla UsuarioSucursal del esquema seguridad
    """
    __tablename__ = 'UsuarioSucursal'
    __table_args__ = {'schema': 'seguridad'}
    
    # Campos principales - Nombres exactos del schema
    id_usuario_sucursal = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey('seguridad.Usuario.id_usuario'), nullable=False)
    sucursal_id = Column(Integer, nullable=False)  # FK a catalogos.Sucursal.id_sucursal
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="sucursales")
    
    def __repr__(self):
        return f"<UsuarioSucursal(id={self.id_usuario_sucursal}, usuario_id={self.usuario_id}, sucursal_id={self.sucursal_id})>"