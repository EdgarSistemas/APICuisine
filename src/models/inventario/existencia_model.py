"""
Existencia - Modelo para existencias de inventario por sucursal
Mapea tabla inventario.Existencia
"""

from sqlalchemy import Column, Integer, BigInteger, DateTime, ForeignKey, Numeric, LargeBinary
from sqlalchemy.orm import relationship
from src.models.base import BaseModel
from sqlalchemy.sql import func


class Existencia(BaseModel):
    """Modelo para Existencias de inventario (snapshot en tiempo real)"""
    __tablename__ = 'Existencia'
    __table_args__ = {'schema': 'inventario'}
    
    id_existencia = Column(Integer, primary_key=True, autoincrement=True)
    sucursal_id = Column(Integer, ForeignKey('catalogos.Sucursal.id_sucursal'), nullable=False)
    insumo_id = Column(BigInteger, ForeignKey('inventario.Insumo.id_insumo'), nullable=False)
    cantidad = Column(Numeric(10, 2), nullable=False, default=0)
    costo_promedio = Column(Numeric(10, 2), nullable=False, default=0)
    updated_at = Column(DateTime, nullable=False, default=func.getdate(), onupdate=func.getdate())
    rowversion = Column(LargeBinary(8), nullable=False, server_default=func.current_timestamp())  # Auto-generado por SQL Server
    
    # Relaciones
    sucursal = relationship("Sucursal")
    insumo = relationship("Insumo")
    
    def __repr__(self):
        return f"<Existencia sucursal={self.sucursal_id} insumo={self.insumo_id} cantidad={self.cantidad}>"
