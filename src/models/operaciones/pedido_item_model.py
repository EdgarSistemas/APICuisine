"""
PedidoItem Model
operaciones.PedidoItem - Items (productos/combos) dentro de pedidos

Sistema de Estados (estatus_detalle):
    1 = EnCocina (item creado, inventario consumido)
    2 = Listo (preparación completada por cocina)
    3 = Completo (servido/entregado)
    4 = Cancelado
    5 = Pagado

Flujo Items: 1 (crear+inventario) → 2 (cocina listo) → 3 (cerrar) → 5 (pagar)
Takeaway: Cuando todos items = 2 (Listo), auto-pagar a 5
"""

from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, Index, text, SMALLINT
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import Base, BaseModel

# Constantes de estatus de PedidoItem
ESTATUS_ITEM_EN_COCINA = 1
ESTATUS_ITEM_LISTO = 2
ESTATUS_ITEM_COMPLETO = 3
ESTATUS_ITEM_CANCELADO = 4
ESTATUS_ITEM_PAGADO = 5

# Mapa de estados para display
ESTATUS_ITEM_MAP = {
    1: 'EnCocina',
    2: 'Listo',
    3: 'Completo',
    4: 'Cancelado',
    5: 'Pagado'
}


class PedidoItem(BaseModel):
    """
    Modelo para Items de Pedido con estatus de preparación.
    
    estatus_detalle (sistema 1-5):
        1 = EnCocina (inventario consumido)
        2 = Listo (preparado)
        3 = Completo (entregado)
        4 = Cancelado
        5 = Pagado
    """
    __tablename__ = 'PedidoItem'
    __table_args__ = (
        Index('IX_PedidoItem_Pedido', 'pedido_id'),
        Index('IX_PedidoItem_PedidoEstatus', 'pedido_id', 'estatus_detalle'),
        Index('IX_PedidoItem_Producto', 'producto_id'),
        Index('IX_PedidoItem_Combo', 'combo_id'),
        {'schema': 'operaciones'}
    )
    
    id_pedido_item = Column(Integer, primary_key=True)
    pedido_id = Column(Integer, ForeignKey('operaciones.Pedido.id_pedido'), nullable=False)
    producto_id = Column(Integer, ForeignKey('catalogos.Producto.id_producto'), nullable=True)
    combo_id = Column(Integer, ForeignKey('catalogos.Combo.id_combo'), nullable=True)
    cantidad = Column(Integer, nullable=False)  # Cantidad ordenada
    precio_unit = Column(Numeric(12, 2), nullable=False)  # Precio al momento del pedido
    estatus_detalle = Column(SMALLINT, nullable=False, default=0)  # 0=Iniciado, 1=EnCocina, 2=Listo, 3=Completo, 4=Cancelado, 5=Pagado
    notas = Column(String(200), nullable=True)  # Notas especiales (sin picante, etc)
    created_at = Column(DateTime, server_default=text('SYSUTCDATETIME()'), nullable=False)
    updated_at = Column(DateTime, nullable=True)
    
    # Relaciones - usar back_populates para sincronizar con pedido_model.py
    pedido = relationship("Pedido", back_populates="items")
    producto = relationship("Producto", backref="items_pedidos")
    combo = relationship("Combo", backref="items_pedidos")
    
    # Mapeo de estados
    ESTATUS_MAP = {
        0: 'Iniciado',
        1: 'EnCocina',
        2: 'Listo',
        3: 'Completo',
        4: 'Cancelado',
        5: 'Pagado'
    }
    
    def __repr__(self):
        prod_name = f"Producto {self.producto_id}" if self.producto_id else f"Combo {self.combo_id}"
        estatus_str = self.ESTATUS_MAP.get(self.estatus_detalle, 'Desconocido')
        return f"<PedidoItem {self.id_pedido_item}: {prod_name} x{self.cantidad} ({estatus_str})>"
    
    def to_dict(self):
        """Serializa el modelo a diccionario"""
        return {
            'id_pedido_item': self.id_pedido_item,
            'pedido_id': self.pedido_id,
            'producto_id': self.producto_id,
            'combo_id': self.combo_id,
            'cantidad': self.cantidad,
            'precio_unit': float(self.precio_unit) if self.precio_unit else 0,
            'subtotal': float(self.precio_unit * self.cantidad) if self.precio_unit else 0,
            'estatus_detalle': self.estatus_detalle,
            'estatus_display': self.ESTATUS_MAP.get(self.estatus_detalle, 'Desconocido'),
            'notas': self.notas,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
