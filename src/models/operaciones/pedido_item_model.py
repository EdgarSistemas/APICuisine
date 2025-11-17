"""
PedidoItem Model
operaciones.PedidoItem - Items (productos/combos) dentro de pedidos
"""

from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, Index, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import Base, BaseModel


class PedidoItem(BaseModel):
    __tablename__ = 'PedidoItem'
    __table_args__ = (
        Index('IX_PedidoItem_Pedido', 'pedido_id'),
        Index('IX_PedidoItem_PedidoEstatus', 'pedido_id', 'estatus'),
        Index('IX_PedidoItem_Producto', 'producto_id'),
        Index('IX_PedidoItem_Combo', 'combo_id'),
        {'schema': 'operaciones'}
    )
    
    id_pedido_item = Column(Integer, primary_key=True)
    pedido_id = Column(Integer, ForeignKey('operaciones.Pedido.id_pedido'), nullable=False)
    producto_id = Column(Integer, ForeignKey('catalogos.Producto.id_producto'), nullable=True)
    combo_id = Column(Integer, ForeignKey('catalogos.Combo.id_combo'), nullable=True)
    cantidad = Column(Integer, nullable=False)  # Cantidad ordenada
    precio_unitario = Column(Numeric(10, 2), nullable=False)  # Precio al momento del pedido
    estatus = Column(Integer, nullable=False, default=1)  # 1=Agregado, 2=Confirmado, 3=EnCocina, 4=Listo, 5=Servido
    notas = Column(String(200), nullable=True)  # Notas especiales (sin picante, etc)
    created_at = Column(DateTime, server_default=text('GETUTCDATE()'), nullable=False)
    updated_at = Column(DateTime, nullable=True)
    
    # Relaciones
    pedido = relationship("Pedido", backref="items")
    producto = relationship("Producto", backref="items_pedidos")
    combo = relationship("Combo", backref="items_pedidos")
    
    def __repr__(self):
        prod_name = f"Producto {self.producto_id}" if self.producto_id else f"Combo {self.combo_id}"
        return f"<PedidoItem {self.id_pedido_item}: {prod_name} x{self.cantidad} (Estatus {self.estatus})>"
