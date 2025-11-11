"""
CompraDetalle Model
inventario.CompraDetalle - Detalles de compras
"""

from sqlalchemy import Column, Integer, BigInteger, ForeignKey, Numeric, DateTime, Index, text, String
from sqlalchemy.orm import relationship
from src.models.base import Base, BaseModel


class CompraDetalle(BaseModel):
    __tablename__ = 'CompraDetalle'
    __table_args__ = (
        Index('IX_CompraDetalle_Compra', 'compra_id'),
        Index('IX_CompraDetalle_Insumo', 'insumo_id'),
        {'schema': 'inventario'}
    )
    
    id_compra_detalle = Column(Integer, primary_key=True)
    compra_id = Column(BigInteger, ForeignKey('inventario.Compra.id_compra'), nullable=False)
    insumo_id = Column(Integer, ForeignKey('inventario.Insumo.id_insumo'), nullable=False)
    cant_presentacion = Column(Numeric(10, 2), nullable=False)  # ej: 5 costales
    costo_unit_present = Column(Numeric(10, 2), nullable=False)  # MXN por presentación
    created_at = Column(DateTime, server_default=text('GETUTCDATE()'), nullable=False)
    updated_at = Column(DateTime)
    presentacion = Column(String(50), nullable=False)  # ej: 'costal', 'litro', etc.
    
    # Relaciones
    compra = relationship("Compra", back_populates="detalles")
    insumo = relationship("Insumo", backref="detalles_compra")
    
    def __repr__(self):
        return f"<CompraDetalle {self.id_compra_detalle}: Compra {self.compra_id}, Insumo {self.insumo_id}>"
