"""
AsignacionMesa Model
operaciones.AsignacionMesa - Asignaciones de meseros a mesas
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean, Index, UniqueConstraint, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import Base, BaseModel


class AsignacionMesa(BaseModel):
    __tablename__ = 'AsignacionMesa'
    __table_args__ = (
        Index('IX_AsignacionMesa_Mesa', 'mesa_id'),
        Index('IX_AsignacionMesa_Usuario', 'usuario_id'),
        Index('IX_AsignacionMesa_Activa', 'es_activa'),
        UniqueConstraint('mesa_id', 'usuario_id', 'es_activa', 
                        name='UX_AsigMesa_MesaUsuarioActiva'),
        {'schema': 'operaciones'}
    )
    
    id_asignacion_mesa = Column(Integer, primary_key=True)
    mesa_id = Column(Integer, ForeignKey('catalogos.Mesa.id_mesa'), nullable=False)
    usuario_id = Column(Integer, ForeignKey('seguridad.Usuario.id_usuario'), nullable=False)
    es_activa = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=text('GETUTCDATE()'), nullable=False)
    updated_at = Column(DateTime)
    
    # Relaciones
    mesa = relationship("Mesa", backref="asignaciones")
    usuario = relationship("Usuario", backref="asignaciones_mesa")
    
    def __repr__(self):
        return f"<AsignacionMesa {self.id_asignacion_mesa}: Mesa {self.mesa_id} - Usuario {self.usuario_id}>"
