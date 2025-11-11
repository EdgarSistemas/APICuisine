"""
Asistencia - Modelo para registro de check-in/check-out
Mapea tabla rrhh.Asistencia
"""

from sqlalchemy import Column, Integer, SmallInteger, String, DateTime, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import BaseModel


class Asistencia(BaseModel):
    """Modelo para Asistencias (check-in/out)"""
    __tablename__ = 'Asistencia'
    __table_args__ = {'schema': 'rrhh'}
    
    id_asistencia = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey('seguridad.Usuario.id_usuario'), nullable=False)
    usuario_horario_id = Column(Integer, ForeignKey('rrhh.UsuarioHorario.id_usuario_horario'), nullable=True)
    tipo_evento = Column(SmallInteger, nullable=False)  # 1=Entrada, 2=Salida
    evento_ts = Column(DateTime, nullable=False)
    origen = Column(String(20), nullable=True)  # 'movil', 'pwa', 'kiosk', 'api'
    device_info = Column(String(300), nullable=True)
    lat = Column(Numeric(9, 6), nullable=True)
    lng = Column(Numeric(9, 6), nullable=True)
    turno_clave_id = Column(Integer, ForeignKey('rrhh.TurnoClave.id_turno_clave'), nullable=True)
    codigo_usuario = Column(String(32), nullable=True)
    codigo_validado = Column(Boolean, nullable=False, default=False)
    observaciones = Column(String(300), nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.getdate())
    
    # Relaciones
    usuario = relationship("Usuario")
    usuario_horario = relationship("UsuarioHorario")
    turno_clave = relationship("TurnoClave")
    
    def __repr__(self):
        return f"<Asistencia usuario={self.usuario_id} tipo={self.tipo_evento} fecha={self.evento_ts}>"
