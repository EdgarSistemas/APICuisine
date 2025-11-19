"""
HoldMesa - Modelo para apartado temporal de mesas durante proceso de reserva
Mapea tabla operaciones.HoldMesa

Estatus:
- 1 = Activo (hold activo, esperando confirmación)
- 2 = Confirmado (convertido a reserva)
- 3 = Expirado (TTL cumplido, no confirmó)
- 4 = Cancelado (usuario canceló antes de confirmar)

Actor_tipo:
- 1 = Cliente (desde móvil)
- 2 = Recepcionista (desde PWA)
"""

from sqlalchemy import Column, BigInteger, Integer, SmallInteger, DateTime, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import BaseModel, get_mexico_now


class HoldMesa(BaseModel):
    """Modelo para Hold temporal de mesas"""
    __tablename__ = 'HoldMesa'
    __table_args__ = {'schema': 'operaciones'}
    
    id_hold_mesa = Column(BigInteger, primary_key=True, autoincrement=True)
    mesa_id = Column(Integer, nullable=False)
    actor_tipo = Column(SmallInteger, nullable=False)  # 1=Cliente, 2=Recepcionista
    actor_usuario_id = Column(BigInteger, nullable=True)  # FK -> seguridad.Usuario
    inicio = Column(DateTime, nullable=False)  # Fecha/hora inicio deseada
    fin_estimado = Column(DateTime, nullable=False)  # Fecha/hora fin estimado
    expires_at = Column(DateTime, nullable=False)  # TTL: cuándo expira este hold
    estatus = Column(SmallInteger, nullable=False, default=1)  # 1=Activo, 2=Confirmado, 3=Expirado, 4=Cancelado
    notas = Column(String(300), nullable=True)
    created_at = Column(DateTime, nullable=False, default=get_mexico_now)
    updated_at = Column(DateTime, nullable=True, onupdate=get_mexico_now)
    horas = Column(Integer, nullable=False)
    
    def __repr__(self):
        return f"<HoldMesa id={self.id_hold_mesa} mesa={self.mesa_id} estatus={self.estatus} expires={self.expires_at}>"
