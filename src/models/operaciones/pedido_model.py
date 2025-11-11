"""
Pedido Model
operaciones.Pedido - Centro de operaciones
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text, Index, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import Base, BaseModel


class Pedido(BaseModel):
    __tablename__ = 'Pedido'
    __table_args__ = (
        Index('IX_Pedido_Sucursal', 'sucursal_id'),
        Index('IX_Pedido_SucursalFecha', 'sucursal_id', 'created_at'),
        Index('IX_Pedido_Estado', 'estado_pedido'),
        Index('IX_Pedido_MesaEstado', 'sucursal_id', 'mesa_id', 'estado_pedido'),
        {'schema': 'operaciones'}
    )
    
    id_pedido = Column(Integer, primary_key=True)
    sucursal_id = Column(Integer, ForeignKey('catalogos.Sucursal.id_sucursal'), nullable=False)
    folio = Column(String(20), nullable=False)
    cliente_id = Column(Integer, ForeignKey('seguridad.Usuario.id_usuario'))
    tipo_pedido = Column(Integer, nullable=False)  # 1=Dine-in, 2=Pickup, 3=Delivery
    canal = Column(Integer, nullable=False)  # 1=Mesero, 2=Sistema, 3=App
    reserva_id = Column(Integer)
    mesa_id = Column(Integer, ForeignKey('catalogos.Mesa.id_mesa'))
    inicia_usuario_id = Column(Integer, ForeignKey('seguridad.Usuario.id_usuario'), nullable=False)
    estado_pedido = Column(Integer, nullable=False, default=1)  # 1=Abierto, 2=Enviado, 3=Entregado, 4=Cancelado
    notas = Column(String(100))
    created_at = Column(DateTime, server_default=text('GETUTCDATE()'), nullable=False)
    updated_at = Column(DateTime)
    
    # Relaciones
    sucursal = relationship("Sucursal", backref="pedidos")
    cliente = relationship("Usuario", foreign_keys=[cliente_id], backref="pedidos_como_cliente")
    usuario_inicia = relationship("Usuario", foreign_keys=[inicia_usuario_id], backref="pedidos_iniciados")
    mesa = relationship("Mesa", backref="pedidos")
    
    def __repr__(self):
        return f"<Pedido {self.id_pedido}: {self.folio} (Sucursal {self.sucursal_id})>"
