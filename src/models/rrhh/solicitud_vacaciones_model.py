"""
SolicitudVacaciones - Modelo para peticiones de vacaciones
Mapea tabla rrhh.SolicitudVacaciones
"""

from sqlalchemy import Column, Integer, SmallInteger, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import BaseModel


class SolicitudVacaciones(BaseModel):
    """Modelo para Solicitudes de Vacaciones"""
    __tablename__ = 'SolicitudVacaciones'
    __table_args__ = {'schema': 'rrhh'}
    
    id_solicitud = Column(Integer, primary_key=True, autoincrement=True)
    horario_usuario_id = Column(Integer, ForeignKey('rrhh.UsuarioHorario.id_usuario_horario'), nullable=False)
    motivo = Column(String(300), nullable=True)
    estatus = Column(SmallInteger, nullable=False, default=1)  # 1=Registrada, 2=Aprobada, 3=Cancelada
    created_at = Column(DateTime, nullable=False, default=func.getdate())
    
    # Relaciones
    usuario_horario = relationship("UsuarioHorario")
    
    def __repr__(self):
        return f"<SolicitudVacaciones id={self.id_solicitud} estatus={self.estatus}>"
