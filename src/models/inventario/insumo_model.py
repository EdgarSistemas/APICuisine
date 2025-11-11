"""
Insumo Model
inventario.Insumo - Materias primas e ingredientes para la cocina
"""

from sqlalchemy import Column, Integer, String, Boolean, Numeric, ForeignKey, DateTime, text
from sqlalchemy.orm import relationship
from src.models.base import Base, BaseModel


class Insumo(BaseModel):
    __tablename__ = 'Insumo'
    __table_args__ = (
        {'schema': 'inventario'}
    )
    
    id_insumo = Column(Integer, primary_key=True)
    nombre = Column(String(30), nullable=False)
    unidad_id = Column(Integer, ForeignKey('inventario.UnidadMedida.id_unidad'), nullable=False)
    es_activo = Column(Boolean, default=True, nullable=False)
    minimo_stock = Column(Numeric(10, 2), default=0, nullable=False)
    created_at = Column(DateTime, server_default=text('GETUTCDATE()'), nullable=False)
    updated_at = Column(DateTime)
    
    # Relaciones
    # unidad_medida: definida en UnidadMedida como backref
    
    def __repr__(self):
        return f"<Insumo {self.id_insumo}: {self.nombre}>"
