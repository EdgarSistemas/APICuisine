"""
Modelo para la entidad Area del esquema catalogos
Representa las áreas de una sucursal (salón, terraza, VIP, etc.)
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import Base

class Area(Base):
    """
    Modelo para la tabla catalogos.Area
    Representa un área dentro de una sucursal del restaurante
    """
    __tablename__ = 'Area'
    __table_args__ = (
        Index('IX_Area_Sucursal', 'sucursal_id'),
        Index('IX_Area_Activa', 'es_activa'),
        Index('IX_Area_SucursalActiva', 'sucursal_id', 'es_activa'),
        {'schema': 'catalogos'}
    )
    
    # Columnas principales
    id_area = Column(Integer, primary_key=True, autoincrement=True)
    sucursal_id = Column(Integer, ForeignKey('catalogos.Sucursal.id_sucursal'), 
                        nullable=False, comment='FK a la sucursal propietaria')
    nombre = Column(String(50), nullable=False, 
                   comment='Nombre del área (Salón, Terraza, VIP, etc.)')
    descripcion = Column(String(100), nullable=True, 
                        comment='Descripción opcional del área')
    es_activa = Column(Boolean, nullable=False, default=True, 
                      comment='Indica si el área está activa operativamente')
    
    # Campos de auditoría
    created_at = Column(DateTime, nullable=False, server_default=text('GETUTCDATE()'),
                       comment='Fecha de creación del registro')
    # Nota: Area NO tiene updated_at según el schema
    
    # Relaciones (se definen aquí pero se implementan cuando existan los modelos)
    # sucursal = relationship("Sucursal", back_populates="areas")
    # mesas = relationship("Mesa", back_populates="area", lazy="select")
    # asignaciones = relationship("AsignacionMesa", back_populates="area")
    
    def __repr__(self):
        """Representación string del objeto"""
        return f"<Area {self.id_area}: {self.nombre} (Sucursal {self.sucursal_id})>"
    
    def to_dict(self):
        """
        Convierte el objeto a diccionario para serialización JSON
        """
        return {
            'id_area': self.id_area,
            'sucursal_id': self.sucursal_id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'es_activa': self.es_activa,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def to_dict_simple(self):
        """
        Versión simplificada para listados o referencias
        """
        return {
            'id_area': self.id_area,
            'sucursal_id': self.sucursal_id,
            'nombre': self.nombre,
            'es_activa': self.es_activa
        }
    
    @classmethod
    def get_campos_actualizables(cls):
        """
        Retorna lista de campos que pueden ser actualizados
        """
        return ['nombre', 'descripcion', 'es_activa']
    
    def es_valida_para_operaciones(self):
        """
        Verifica si el área puede realizar operaciones
        """
        return self.es_activa and self.nombre and self.sucursal_id
    
    def get_nombre_completo(self):
        """
        Retorna nombre completo del área incluyendo referencia a sucursal
        """
        return f"{self.nombre} (Sucursal ID: {self.sucursal_id})"