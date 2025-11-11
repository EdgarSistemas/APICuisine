"""
Recepcion - Modelo para recepción de compras
Mapea tabla inventario.Recepcion
"""

from sqlalchemy import Column, Integer, BigInteger, DateTime, String, ForeignKey, Text, text
from sqlalchemy.orm import relationship
from src.models.base import BaseModel
from sqlalchemy.sql import func


class Recepcion(BaseModel):
    """Modelo para Recepcion de Compras"""
    __tablename__ = 'Recepcion'
    __table_args__ = {'schema': 'inventario'}
    
    id_recepcion = Column(Integer, primary_key=True, autoincrement=True)
    compra_id = Column(Integer, ForeignKey('inventario.Compra.id_compra'), nullable=True)
    recibido_por = Column(Integer, ForeignKey('seguridad.Usuario.id_usuario'), nullable=True)
    fecha_recepcion = Column(DateTime, nullable=False, default=func.getdate())
    notas = Column(String(200), nullable=True)
    estatus = Column(Integer, nullable=False, default=1)  # 1=Registrada
    created_at = Column(DateTime, nullable=False, default=func.getdate())
    
    # Relaciones
    compra = relationship("Compra", back_populates="recepciones")
    usuario = relationship("Usuario")
    detalles = relationship("RecepcionDetalle", back_populates="recepcion", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Recepcion id={self.id_recepcion} compra={self.compra_id}>"
