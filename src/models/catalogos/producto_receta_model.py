"""
ProductoReceta Model
catalogos.ProductoReceta - Recetas de preparación para productos
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, BigInteger, DateTime, text
from sqlalchemy.orm import relationship
from src.models.base import Base, BaseModel


class ProductoReceta(BaseModel):
    __tablename__ = 'ProductoReceta'
    __table_args__ = (
        {'schema': 'catalogos'}
    )
    
    id_receta = Column(BigInteger, primary_key=True)
    producto_id = Column(BigInteger, ForeignKey('catalogos.Producto.id_producto'), nullable=False)
    nombre = Column(String(120))
    es_activa = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=text('GETUTCDATE()'), nullable=False)
    updated_at = Column(DateTime)
    
    # Relaciones
    producto = relationship("Producto", backref="recetas")
    items = relationship("ProductoRecetaItem", backref="receta", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ProductoReceta {self.id_receta}: {self.nombre}>"
