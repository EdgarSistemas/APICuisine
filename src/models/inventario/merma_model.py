"""
Merma - Modelo para mermas de inventario
Mapea tabla inventario.Merma
"""

from sqlalchemy import Column, Integer, BigInteger, DateTime, ForeignKey, func, Numeric, Text
from sqlalchemy.orm import relationship
from src.models.base import BaseModel


class Merma(BaseModel):
    """Modelo para Mermas de inventario"""
    __tablename__ = 'Merma'
    __table_args__ = {'schema': 'inventario'}
    
    id_merma = Column(Integer, primary_key=True, autoincrement=True)
    sucursal_id = Column(Integer, ForeignKey('catalogos.Sucursal.id_sucursal'), nullable=False)
    insumo_id = Column(BigInteger, ForeignKey('inventario.Insumo.id_insumo'), nullable=False)
    cantidad = Column(Numeric(10, 2), nullable=False)
    motivo = Column(Text)
    created_at = Column(DateTime, nullable=False, default=func.getdate())
    
    # Relaciones
    sucursal = relationship("Sucursal")
    insumo = relationship("Insumo")
    
    def __repr__(self):
        return f"<Merma id={self.id_merma} insumo={self.insumo_id} cantidad={self.cantidad}>"
