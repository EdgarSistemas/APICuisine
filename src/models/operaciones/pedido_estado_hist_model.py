"""
PedidoEstadoHist Model
operaciones.PedidoEstadoHist - Historial de cambios de estado en pedidos
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Index, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import Base, BaseModel


class PedidoEstadoHist(BaseModel):
    __tablename__ = 'PedidoEstadoHist'
    __table_args__ = (
        Index('IX_PedidoEstadoHist_Pedido', 'pedido_id'),
        Index('IX_PedidoEstadoHist_PedidoFecha', 'pedido_id', 'created_at'),
        {'schema': 'operaciones'}
    )
    
    id_pedido_estado_hist = Column(Integer, primary_key=True)
    pedido_id = Column(Integer, ForeignKey('operaciones.Pedido.id_pedido'), nullable=False)
    estatus_anterior = Column(Integer, nullable=True)  # Estado anterior (NULL si es el primero)
    estatus_nuevo = Column(Integer, nullable=False)  # Nuevo estado
    usuario_id = Column(Integer, ForeignKey('seguridad.Usuario.id_usuario'), nullable=True)
    comentario = Column(Text, nullable=True)  # Razón del cambio
    created_at = Column(DateTime, server_default=text('GETUTCDATE()'), nullable=False)
    
    # Relaciones
    pedido = relationship("Pedido", backref="historial_estados")
    usuario = relationship("Usuario", backref="cambios_estado_pedido")
    
    def __repr__(self):
        return f"<PedidoEstadoHist {self.id_pedido_estado_hist}: Pedido {self.pedido_id} {self.estatus_anterior}→{self.estatus_nuevo}>"
