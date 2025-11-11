"""
Producto Model
catalogos.Producto - Productos del menú del restaurante
"""

from sqlalchemy import Column, Integer, String, Boolean, Numeric, ForeignKey, DateTime, text
from sqlalchemy.orm import relationship
from src.models.base import Base, BaseModel


class Producto(BaseModel):
    __tablename__ = 'Producto'
    __table_args__ = (
        {'schema': 'catalogos'}
    )
    
    id_producto = Column(Integer, primary_key=True)
    categoria_id = Column(Integer, ForeignKey('catalogos.CategoriaMenu.id_categoria'), nullable=False)
    codigo = Column(String(20), unique=True)
    nombre = Column(String(50), nullable=False)
    descripcion = Column(String(100))
    imagen_url = Column(String)
    precio = Column(Numeric(12, 2), nullable=False)
    es_activo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=text('GETUTCDATE()'), nullable=False)
    updated_at = Column(DateTime)
    
    # Relaciones
    # categoria: definida en CategoriaMenu como backref
    
    def __repr__(self):
        return f"<Producto {self.id_producto}: {self.nombre} - ${self.precio}>"
