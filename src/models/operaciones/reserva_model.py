"""
Reserva - Modelo para reservaciones confirmadas de mesas
Mapea tabla operaciones.Reserva

Estatus:
- 1 = Programada (reserva confirmada, esperando fecha/hora)
- 2 = EnCurso (cliente llegó, está ocupando mesa)
- 3 = Completada (cliente terminó y se fue)
- 4 = NoShow (no llegó en tiempo de tolerancia)
- 5 = Cancelada (cliente o recepcionista canceló)
"""

from sqlalchemy import Column, BigInteger, Integer, SmallInteger, DateTime, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import BaseModel


class Reserva(BaseModel):
    """Modelo para Reservaciones confirmadas"""
    __tablename__ = 'Reserva'
    __table_args__ = {'schema': 'operaciones'}
    
    id_reserva = Column(BigInteger, primary_key=True, autoincrement=True)
    cliente_id = Column(BigInteger, nullable=True)  # FK -> seguridad.Usuario
    recepcionista_id = Column(BigInteger, nullable=True)  # FK -> seguridad.Usuario (quien confirma desde PWA)
    inicio = Column(DateTime, nullable=False)  # Fecha/hora inicio reserva
    fin_estimado = Column(DateTime, nullable=False)  # Fecha/hora fin estimado
    estatus = Column(SmallInteger, nullable=False, default=1)  # 1=Programada, 2=EnCurso, 3=Completada, 4=NoShow, 5=Cancelada
    tolerancia_min = Column(Integer, nullable=True)  # Minutos de tolerancia para NoShow (NULL = usar config)
    notas = Column(String(300), nullable=True)
    hold_id = Column(BigInteger, nullable=True)  # FK -> operaciones.HoldMesa (si se originó desde hold)
    created_at = Column(DateTime, nullable=False, default=func.getdate())
    updated_at = Column(DateTime, nullable=True, onupdate=func.getdate())
    
    def __repr__(self):
        return f"<Reserva id={self.id_reserva} cliente={self.cliente_id} inicio={self.inicio} estatus={self.estatus}>"
