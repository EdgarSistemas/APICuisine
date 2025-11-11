"""
CategoriaMenu Model
catalogos.CategoriaMenu - Categorías de productos en el menú
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, text
from sqlalchemy.orm import relationship
from src.models.base import Base, BaseModel


class CategoriaMenu(BaseModel):
    __tablename__ = 'CategoriaMenu'
    __table_args__ = (
        {'schema': 'catalogos'}
    )
    
    id_categoria = Column(Integer, primary_key=True)
    nombre = Column(String(30), nullable=False)
    descripcion = Column(String(100))
    es_activa = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=text('GETUTCDATE()'), nullable=False)
    updated_at = Column(DateTime)
    
    # Relaciones
    productos = relationship("Producto", backref="categoria")
    
    def __repr__(self):
        return f"<CategoriaMenu {self.id_categoria}: {self.nombre}>"
