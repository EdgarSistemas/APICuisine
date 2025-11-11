"""
Combo Model
catalogos.Combo - Combos/paquetes de productos con precio especial
"""

from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime, text
from sqlalchemy.orm import relationship
from src.models.base import Base, BaseModel


class Combo(BaseModel):
    __tablename__ = 'Combo'
    __table_args__ = (
        {'schema': 'catalogos'}
    )
    
    id_combo = Column(Integer, primary_key=True)
    nombre = Column(String(50), nullable=False)
    descripcion = Column(String(100))
    imagen_url = Column(String)
    precio = Column(Numeric(12, 2), nullable=False)
    es_activo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=text('GETUTCDATE()'), nullable=False)
    updated_at = Column(DateTime)
    
    # Relaciones
    combo_productos = relationship("ComboProducto", backref="combo", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Combo {self.id_combo}: {self.nombre} - ${self.precio}>"
