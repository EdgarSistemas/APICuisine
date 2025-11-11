"""
Compra Model
inventario.Compra - Gestión de compras
"""

from sqlalchemy import Column, Integer, BigInteger, String, ForeignKey, DateTime, Index, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import Base, BaseModel


class Compra(BaseModel):
    __tablename__ = 'Compra'
    __table_args__ = (
        Index('IX_Compra_Sucursal', 'sucursal_id'),
        Index('IX_Compra_SucursalFecha', 'sucursal_id', 'fecha_compra'),
        Index('IX_Compra_Usuario', 'usuario_id'),
        {'schema': 'inventario'}
    )
    
    id_compra = Column(BigInteger, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('seguridad.Usuario.id_usuario'), nullable=False)
    sucursal_id = Column(Integer, ForeignKey('catalogos.Sucursal.id_sucursal'), nullable=False)
    proveedor_id = Column(Integer, ForeignKey('inventario.Proveedor.id_proveedor'), nullable=False)
    folio = Column(String(20), nullable=False)
    fecha_compra = Column(DateTime, server_default=text('GETUTCDATE()'), nullable=False)
    estatus = Column(Integer, nullable=False, default=1)  # 1=Pendiente, 2=Recibida, 3=Cancelada
    created_at = Column(DateTime, server_default=text('GETUTCDATE()'), nullable=False)
    updated_at = Column(DateTime)
    
    # Relaciones
    usuario = relationship("Usuario", backref="compras")
    sucursal = relationship("Sucursal", backref="compras")
    proveedor = relationship("Proveedor", backref="compras")
    recepciones = relationship("Recepcion", back_populates="compra", cascade="all, delete-orphan")
    detalles = relationship("CompraDetalle", back_populates="compra", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Compra {self.id_compra}: {self.folio} (Sucursal {self.sucursal_id})>"
