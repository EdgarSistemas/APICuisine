"""
ConfigSucursal - Modelo para configuraciones por sucursal
Mapea tabla config.ConfigSucursal
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import BaseModel


class ConfigSucursal(BaseModel):
    """Modelo para configuraciones clave-valor por sucursal"""
    __tablename__ = 'ConfigSucursal'
    __table_args__ = {'schema': 'config'}
    
    id_config = Column(Integer, primary_key=True, autoincrement=True)
    sucursal_id = Column(Integer, ForeignKey('catalogos.Sucursal.id_sucursal'), nullable=False)
    clave = Column(String(30), nullable=False)
    valor_string = Column(String(300), nullable=True)
    updated_at = Column(DateTime, nullable=False, default=func.getdate(), onupdate=func.getdate())
    rowversion = Column(LargeBinary(8), nullable=False, server_default=func.current_timestamp())
    
    # Relaciones
    sucursal = relationship("Sucursal")
    
    def __repr__(self):
        return f"<ConfigSucursal sucursal={self.sucursal_id} clave={self.clave} valor={self.valor_string}>"
