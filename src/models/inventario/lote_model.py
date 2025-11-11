"""
Lote - Modelo para lotes de insumos
Mapea tabla inventario.Lote
"""

from sqlalchemy import Column, Integer, BigInteger, DateTime, String, ForeignKey, func, Numeric
from sqlalchemy.orm import relationship
from src.models.base import BaseModel


class Lote(BaseModel):
    """Modelo para Lotes de insumos"""
    __tablename__ = 'Lote'
    __table_args__ = {'schema': 'inventario'}
    
    id_lote = Column(Integer, primary_key=True, autoincrement=True)
    det_recepcion_id = Column(Integer, ForeignKey('inventario.RecepcionDetalle.id_recepcion_det'), nullable=False)
    lote = Column(String(20))  # numero de lote interno
    lote_proveedor = Column(String(100))  # numero de lote del proveedor
    cantidad_inicial = Column(Numeric(10, 2), nullable=False)
    cantidad_disponible = Column(Numeric(10, 2), nullable=False)
    costo_unitario = Column(Numeric(10, 2), nullable=False)  # MXN por unidad base
    fecha_caducidad = Column(DateTime)
    estado = Column(Integer, nullable=False, default=1)  # 1=Disponible, 2=Agotado
    created_at = Column(DateTime, nullable=False, default=func.getdate())
    
    # Relaciones
    recepcion_detalle = relationship("RecepcionDetalle", back_populates="lotes")
    
    def __repr__(self):
        return f"<Lote id={self.id_lote} cantidad={self.cantidad_disponible}>"
