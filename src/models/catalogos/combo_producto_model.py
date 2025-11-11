"""
ComboProducto Model
catalogos.ComboProducto - Items/líneas de productos en un combo
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, text, UniqueConstraint
from sqlalchemy.orm import relationship
from src.models.base import Base, BaseModel


class ComboProducto(BaseModel):
    __tablename__ = 'ComboProducto'
    __table_args__ = (
        UniqueConstraint('combo_id', 'producto_id', name='UX_Combo_Producto_Unico'),
        {'schema': 'catalogos'}
    )
    
    id_combo_producto = Column(Integer, primary_key=True)
    combo_id = Column(Integer, ForeignKey('catalogos.Combo.id_combo'), nullable=False)
    producto_id = Column(Integer, ForeignKey('catalogos.Producto.id_producto'), nullable=False)
    cantidad = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, server_default=text('GETUTCDATE()'), nullable=False)
    updated_at = Column(DateTime)
    
    # Relaciones
    producto = relationship("Producto")
    # combo: definida en Combo como backref
    
    def __repr__(self):
        return f"<ComboProducto {self.combo_id} - Producto {self.producto_id} x{self.cantidad}>"
