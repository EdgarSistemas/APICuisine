"""
TurnoClave - Modelo para códigos de check-in diarios
Mapea tabla rrhh.TurnoClave
"""

from sqlalchemy import Column, Integer, SmallInteger, String, Date, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import BaseModel


class TurnoClave(BaseModel):
    """Modelo para Códigos de Turno diarios"""
    __tablename__ = 'TurnoClave'
    __table_args__ = {'schema': 'rrhh'}
    
    id_turno_clave = Column(Integer, primary_key=True, autoincrement=True)
    horario_id = Column(Integer, ForeignKey('rrhh.Horario.id_horario'), nullable=False)
    horario_detalle_id = Column(Integer, ForeignKey('rrhh.HorarioDetalle.id_detalle'), nullable=True)
    sucursal_id = Column(Integer, ForeignKey('catalogos.Sucursal.id_sucursal'), nullable=False)
    fecha = Column(Date, nullable=False)
    turno_idx = Column(SmallInteger, nullable=False, default=1)
    codigo = Column(String(32), nullable=False)  # 6 dígitos generados
    hash_codigo = Column(String(128), nullable=True)
    es_activo = Column(Boolean, nullable=False, default=True)
    generado_por = Column(Integer, ForeignKey('seguridad.Usuario.id_usuario'), nullable=True)
    generado_en = Column(DateTime, nullable=False, default=func.getdate())
    expira_en = Column(DateTime, nullable=True)
    uso_maximo = Column(Integer, nullable=False, default=0)  # 0 = ilimitado
    usos_count = Column(Integer, nullable=False, default=0)
    notas = Column(String(300), nullable=True)
    
    # Relaciones
    horario = relationship("Horario")
    horario_detalle = relationship("HorarioDetalle")
    sucursal = relationship("Sucursal")
    generado_por_usuario = relationship("Usuario", foreign_keys=[generado_por])
    
    def __repr__(self):
        return f"<TurnoClave codigo={self.codigo} fecha={self.fecha}>"
