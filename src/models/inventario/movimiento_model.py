"""
Movimiento - Modelo para auditoría de movimientos de inventario
Mapea tabla inventario.Movimiento
"""

from sqlalchemy import Column, Integer, BigInteger, DateTime, ForeignKey, func, Numeric
from sqlalchemy.orm import relationship
from src.models.base import BaseModel


class Movimiento(BaseModel):
    """Modelo para Movimientos de inventario (auditoría)"""
    __tablename__ = 'Movimiento'
    __table_args__ = {'schema': 'inventario'}
    
    id_movimiento = Column(Integer, primary_key=True, autoincrement=True)
    sucursal_id = Column(Integer, ForeignKey('catalogos.Sucursal.id_sucursal'), nullable=False)
    insumo_id = Column(BigInteger, ForeignKey('inventario.Insumo.id_insumo'), nullable=False)
    lote_id = Column(Integer, ForeignKey('inventario.Lote.id_lote'))
    tipo_mov = Column(Integer, nullable=False)  # 1=Entrada, 2=Salida
    motivo = Column(Integer, nullable=False)  # 1=Recepción, 2=Pedido, 3=Merma
    cantidad = Column(Numeric(10, 2), nullable=False)  # En unidad base
    pedido_id = Column(Integer, ForeignKey('operaciones.Pedido.id_pedido'))
    det_recepcion_id = Column(Integer, ForeignKey('inventario.RecepcionDetalle.id_recepcion_det'))
    compra_id = Column(Integer, ForeignKey('inventario.Compra.id_compra'))
    merma_id = Column(Integer, ForeignKey('inventario.Merma.id_merma'))
    usuario_id = Column(Integer, ForeignKey('seguridad.Usuario.id_usuario'))
    created_at = Column(DateTime, nullable=False, default=func.getdate())
    
    # Relaciones
    sucursal = relationship("Sucursal")
    insumo = relationship("Insumo")
    lote = relationship("Lote")
    usuario = relationship("Usuario")
    
    def __repr__(self):
        return f"<Movimiento id={self.id_movimiento} tipo={self.tipo_mov} cantidad={self.cantidad}>"
