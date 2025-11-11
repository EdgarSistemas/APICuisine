"""
Calificacion - Modelo para calificaciones de servicio
Mapea tabla servicio.Calificacion
"""

from sqlalchemy import Column, Integer, SmallInteger, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import BaseModel


class Calificacion(BaseModel):
    """Modelo para Calificaciones de servicio"""
    __tablename__ = 'Calificacion'
    __table_args__ = {'schema': 'servicio'}
    
    id_calificacion = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey('operaciones.Pedido.id_pedido'), nullable=False)
    cliente_id = Column(Integer, ForeignKey('seguridad.Usuario.id_usuario'), nullable=False)
    empleado_id = Column(Integer, ForeignKey('seguridad.Usuario.id_usuario'), nullable=False)
    notas = Column(String(300), nullable=True)
    calificacion = Column(SmallInteger, nullable=False)  # 1-10
    created_at = Column(DateTime, nullable=False, default=func.getdate())
    es_activo = Column(SmallInteger, nullable=False, default=1)  # 1=Registrada, 2=Cancelada
    
    # Relaciones
    pedido = relationship("Pedido", foreign_keys=[pedido_id])
    cliente = relationship("Usuario", foreign_keys=[cliente_id])
    empleado = relationship("Usuario", foreign_keys=[empleado_id])
    
    def __repr__(self):
        return f"<Calificacion id={self.id_calificacion} pedido={self.pedido_id} calificacion={self.calificacion}>"
