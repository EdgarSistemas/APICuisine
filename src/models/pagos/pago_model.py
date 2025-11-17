"""
Pago Model
pagos.Pago - Gestión de pagos
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, Numeric, String, Index, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import Base, BaseModel


class Pago(BaseModel):
    __tablename__ = 'Pago'
    __table_args__ = (
        Index('IX_Pago_Pedido', 'pedido_id'),
        Index('IX_Pago_PedidoEstatus', 'pedido_id', 'estatus'),
        Index('IX_Pago_Sucursal', 'sucursal_id'),
        Index('IX_Pago_SucursalFecha', 'sucursal_id', 'created_at'),
        {'schema': 'pagos'}
    )
    
    id_pago = Column(Integer, primary_key=True)
    pedido_id = Column(Integer, ForeignKey('operaciones.Pedido.id_pedido'), nullable=False)
    sucursal_id = Column(Integer, ForeignKey('catalogos.Sucursal.id_sucursal'), nullable=False)
    monto = Column(Numeric(12, 2), nullable=False)
    propina = Column(Numeric(12, 2), default=0, nullable=False)
    moneda = Column(String(5), default='MXN', nullable=False)
    metodo_pago = Column(String(50), nullable=True)  # Efectivo, Tarjeta, QR, Transferencia
    referencia = Column(String(100), nullable=True)  # Número de transacción
    estatus = Column(Integer, nullable=False, default=1)  # 1=Pagado, 2=Pendiente, 3=Anulado
    usuario_id = Column(Integer, ForeignKey('seguridad.Usuario.id_usuario'))
    fecha_pago = Column(DateTime, nullable=True)  # Fecha cuando se confirma pago
    created_at = Column(DateTime, server_default=text('GETUTCDATE()'), nullable=False)
    updated_at = Column(DateTime)
    
    # Relaciones
    pedido = relationship("Pedido", backref="pagos")
    sucursal = relationship("Sucursal", backref="pagos")
    usuario = relationship("Usuario", backref="pagos")
    
    def __repr__(self):
        return f"<Pago {self.id_pago}: ${self.monto} (Pedido {self.pedido_id})>"
