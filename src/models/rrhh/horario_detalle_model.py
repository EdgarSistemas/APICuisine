"""
HorarioDetalle - Modelo para franjas horarias por día
Mapea tabla rrhh.HorarioDetalle
"""

from sqlalchemy import Column, Integer, SmallInteger, Time, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import BaseModel


class HorarioDetalle(BaseModel):
    """Modelo para Detalles de Horario (franjas por día)"""
    __tablename__ = 'HorarioDetalle'
    __table_args__ = {'schema': 'rrhh'}
    
    id_detalle = Column(Integer, primary_key=True, autoincrement=True)
    horario_id = Column(Integer, ForeignKey('rrhh.Horario.id_horario'), nullable=False)
    dia_semana = Column(SmallInteger, nullable=False)  # 1=Lunes, 7=Domingo
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    turno_idx = Column(SmallInteger, nullable=False, default=1)  # Siempre 1 (un turno por día)
    tolerancia_min = Column(Integer, nullable=False, default=10)
    es_activo = Column(Boolean, nullable=False, default=True)
    
    # Relaciones
    horario = relationship("Horario", back_populates="detalles")
    
    def __repr__(self):
        return f"<HorarioDetalle horario={self.horario_id} dia={self.dia_semana}>"
