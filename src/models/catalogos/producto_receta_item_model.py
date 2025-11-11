"""
ProductoRecetaItem Model
catalogos.ProductoRecetaItem - Items (insumos) de una receta
"""

from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger, Numeric, DateTime, text, UniqueConstraint
from sqlalchemy.orm import relationship
from src.models.base import Base, BaseModel


class ProductoRecetaItem(BaseModel):
    __tablename__ = 'ProductoRecetaItem'
    __table_args__ = (
        UniqueConstraint('receta_id', 'insumo_id', name='UX_Receta_Insumo'),
        {'schema': 'catalogos'}
    )
    
    id_receta_item = Column(BigInteger, primary_key=True)
    receta_id = Column(BigInteger, ForeignKey('catalogos.ProductoReceta.id_receta'), nullable=False)
    insumo_id = Column(BigInteger, ForeignKey('inventario.Insumo.id_insumo'), nullable=False)
    cantidad = Column(Numeric(10, 2), nullable=False)
    
    # Relaciones
    insumo = relationship("Insumo", backref="receta_items")
    
    def __repr__(self):
        return f"<ProductoRecetaItem {self.id_receta_item}: receta={self.receta_id}, insumo={self.insumo_id}, qty={self.cantidad}>"
