"""
Modelo para la entidad Sucursal del esquema catalogos
Representa las sucursales del restaurante en el sistema multi-tenant
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Index, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.core.db_connection import Base

class Sucursal(Base):
    """
    Modelo para la tabla catalogos.Sucursal
    Representa una sucursal/sede del restaurante
    """
    __tablename__ = 'Sucursal'
    __table_args__ = (
        {'schema': 'catalogos'},
        Index('IX_Sucursal_Activa', 'es_activa'),
        Index('IX_Sucursal_Codigo', 'codigo_sucursal'),
    )
    
    # Columnas principales
    id_sucursal = Column(Integer, primary_key=True, autoincrement=True)
    codigo_sucursal = Column(String(20), nullable=False, unique=True, 
                           comment='Código único identificador de la sucursal')
    nombre = Column(String(100), nullable=False, 
                   comment='Nombre comercial de la sucursal')
    telefono = Column(String(15), nullable=True, 
                     comment='Teléfono de contacto de la sucursal')
    direccion = Column(String(100), nullable=True, 
                      comment='Dirección física de la sucursal')
    es_activa = Column(Boolean, nullable=False, default=True, 
                      comment='Indica si la sucursal está activa operativamente')
    
    # Campos de auditoría
    created_at = Column(DateTime, nullable=False, server_default=text('GETUTCDATE()'),
                       comment='Fecha de creación del registro')
    updated_at = Column(DateTime, nullable=True, 
                       comment='Fecha de última actualización')
    
    # Relaciones (se definen aquí pero se implementan cuando existan los modelos)
    # areas = relationship("Area", back_populates="sucursal", lazy="select")
    # usuarios = relationship("Usuario", secondary="seguridad.UsuarioSucursal", 
    #                       back_populates="sucursales")
    # pedidos = relationship("Pedido", back_populates="sucursal")
    # inventarios = relationship("Existencia", back_populates="sucursal")
    
    def __repr__(self):
        """Representación string del objeto"""
        return f"<Sucursal {self.codigo_sucursal}: {self.nombre}>"
    
    def to_dict(self):
        """
        Convierte el objeto a diccionario para serialización JSON
        """
        return {
            'id_sucursal': self.id_sucursal,
            'codigo_sucursal': self.codigo_sucursal,
            'nombre': self.nombre,
            'telefono': self.telefono,
            'direccion': self.direccion,
            'es_activa': self.es_activa,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_dict_simple(self):
        """
        Versión simplificada para listados o referencias
        """
        return {
            'id_sucursal': self.id_sucursal,
            'codigo_sucursal': self.codigo_sucursal,
            'nombre': self.nombre,
            'es_activa': self.es_activa
        }
    
    @classmethod
    def get_campos_actualizables(cls):
        """
        Retorna lista de campos que pueden ser actualizados
        """
        return ['nombre', 'telefono', 'direccion', 'es_activa']
    
    def es_valida_para_operaciones(self):
        """
        Verifica si la sucursal puede realizar operaciones
        """
        return self.es_activa and self.nombre and self.codigo_sucursal