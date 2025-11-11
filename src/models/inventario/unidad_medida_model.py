"""
UnidadMedida Model
inventario.UnidadMedida - Unidades de medida para insumos (kg, g, l, ml, pz, etc)
"""

from sqlalchemy import Column, Integer, String, DateTime, text
from sqlalchemy.orm import relationship
from src.models.base import Base, BaseModel


class UnidadMedida(BaseModel):
    __tablename__ = 'UnidadMedida'
    __table_args__ = (
        {'schema': 'inventario'}
    )
    
    id_unidad = Column(Integer, primary_key=True)
    clave = Column(String(20), unique=True, nullable=False)  # kg, g, l, ml, pz
    nombre = Column(String(30), nullable=False)
    created_at = Column(DateTime, server_default=text('GETUTCDATE()'), nullable=False)
    updated_at = Column(DateTime)
    
    # Relaciones
    insumos = relationship("Insumo", backref="unidad_medida")
    
    def __repr__(self):
        return f"<UnidadMedida {self.clave}: {self.nombre}>"
