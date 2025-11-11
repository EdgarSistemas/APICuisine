"""
UsuarioHorario - Modelo para asignación de horarios a empleados
Mapea tabla rrhh.UsuarioHorario
"""

from sqlalchemy import Column, Integer, Date, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import BaseModel


class UsuarioHorario(BaseModel):
    """Modelo para asignación de Horarios a Usuarios"""
    __tablename__ = 'UsuarioHorario'
    __table_args__ = {'schema': 'rrhh'}
    
    id_usuario_horario = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey('seguridad.Usuario.id_usuario'), nullable=False)
    horario_id = Column(Integer, ForeignKey('rrhh.Horario.id_horario'), nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=True)  # NULL = indefinido
    es_recurring = Column(Boolean, nullable=False, default=True)
    es_activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=func.getdate())
    updated_at = Column(DateTime, nullable=True, onupdate=func.getdate())
    
    # Relaciones
    usuario = relationship("Usuario")
    horario = relationship("Horario")
    
    def __repr__(self):
        return f"<UsuarioHorario usuario={self.usuario_id} horario={self.horario_id}>"
