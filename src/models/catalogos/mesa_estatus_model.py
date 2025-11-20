"""
MesaEstatus Model
catalogos.MesaEstatus - Estados de las mesas (disponible, ocupada, en limpieza, etc)

Estatus:
- 1 = Disponible (mesa libre, lista para ser reservada/ocupada)
- 2 = Ocupada (cliente está en la mesa)
- 3 = En Limpieza (en proceso de limpieza, no disponible)
- 4 = Fuera de Servicio (mantenimiento)
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import BaseModel


class MesaEstatus(BaseModel):
    """Modelo para controlar el estatus de las mesas"""
    __tablename__ = 'MesaEstatus'
    __table_args__ = {'schema': 'catalogos'}
    
    id_mesa_estatus = Column(Integer, primary_key=True, autoincrement=True)
    mesa_id = Column(Integer, ForeignKey('catalogos.Mesa.id_mesa'), nullable=False, unique=True)
    estatus = Column(Integer, nullable=False, default=1)  # 1=Disponible, 2=Ocupada, 3=En Limpieza, 4=Fuera de Servicio
    cambio_por = Column(Integer, ForeignKey('seguridad.Usuario.id_usuario'), nullable=True)  # Quién hizo el cambio
    notas = Column(String(200), nullable=True)
    created_at = Column(DateTime, server_default=text('GETUTCDATE()'), nullable=False)
    updated_at = Column(DateTime)
    
    # Relaciones
    mesa = relationship("Mesa", backref="mesa_estatus")
    usuario = relationship("Usuario", foreign_keys=[cambio_por], backref="cambios_mesa_estatus")
    
    def __repr__(self):
        estatus_map = {1: "Disponible", 2: "Ocupada", 3: "En Limpieza", 4: "Fuera de Servicio"}
        return f"<MesaEstatus Mesa {self.mesa_id}: {estatus_map.get(self.estatus, 'Desconocido')}>"
