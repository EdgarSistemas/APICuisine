"""
RecepcionDetalle - Modelo para detalles de recepción
Mapea tabla inventario.RecepcionDetalle
"""

from sqlalchemy import Column, Integer, BigInteger, DateTime, String, ForeignKey, func, Numeric, Text
from sqlalchemy.orm import relationship
from src.models.base import BaseModel


class RecepcionDetalle(BaseModel):
    """Modelo para detalles de Recepcion"""
    __tablename__ = 'RecepcionDetalle'
    __table_args__ = {'schema': 'inventario'}
    
    id_recepcion_det = Column(Integer, primary_key=True, autoincrement=True)
    recepcion_id = Column(Integer, ForeignKey('inventario.Recepcion.id_recepcion'), nullable=False)
    insumo_id = Column(BigInteger, ForeignKey('inventario.Insumo.id_insumo'), nullable=False)
    cant_presentacion = Column(Numeric(10, 2), nullable=False)
    unidades_por_present = Column(Numeric(10, 2), nullable=False)
    cantidad_base = Column(Numeric(10, 4), nullable=False)  # cant_presentacion * unidades_por_present
    costo_unitario = Column(Numeric(10, 2), nullable=False)  # por unidad base
    notas = Column(Text)
    created_at = Column(DateTime, nullable=False, default=func.getdate())
    
    # Relaciones
    recepcion = relationship("Recepcion", back_populates="detalles")
    insumo = relationship("Insumo")
    lotes = relationship("Lote", back_populates="recepcion_detalle", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<RecepcionDetalle id={self.id_recepcion_det} insumo={self.insumo_id}>"
