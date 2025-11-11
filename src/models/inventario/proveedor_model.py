"""
Proveedor Model
inventario.Proveedor - Gestión de proveedores
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Index, text
from sqlalchemy.sql import func
from src.models.base import Base, BaseModel


class Proveedor(BaseModel):
    __tablename__ = 'Proveedor'
    __table_args__ = (
        Index('IX_Proveedor_Nombre', 'nombre'),
        {'schema': 'inventario'}
    )
    
    id_proveedor = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100))
    telefono = Column(String(20))
    es_activo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=text('GETUTCDATE()'), nullable=False)
    updated_at = Column(DateTime)
    
    def __repr__(self):
        return f"<Proveedor {self.id_proveedor}: {self.nombre}>"
