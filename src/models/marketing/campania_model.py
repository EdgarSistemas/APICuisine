"""
Campania Model
marketing.Campania - Gestión de campañas promocionales y cupones
"""

from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, Index, text, SMALLINT
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import Base, BaseModel


class Campania(BaseModel):
    """
    Modelo para Campaña de Marketing.
    Representa campañas promocionales con cupones de descuento.
    
    Estatus:
        0 = Inactiva
        1 = Activa
    """
    __tablename__ = 'Campania'
    __table_args__ = (
        Index('IX_Campania_Codigo', 'codigo'),
        Index('IX_Campania_Estatus', 'estatus'),
        {'schema': 'marketing'}
    )
    
    id_campania = Column(Integer, primary_key=True)
    usuario_crea_id = Column(Integer, ForeignKey('seguridad.Usuario.id_usuario'), nullable=False)
    codigo = Column(String(50), nullable=True, unique=True)  # Código del cupón
    nombre_campania = Column(String(100), nullable=False)
    porcentaje_desc = Column(Numeric(10, 2), nullable=False)  # Porcentaje de descuento (ej: 10.00 = 10%)
    estatus = Column(SMALLINT, nullable=False, default=1)  # 0=Inactiva, 1=Activa
    created_at = Column(DateTime, server_default=text('SYSUTCDATETIME()'), nullable=False)
    
    # Relaciones
    usuario_crea = relationship("Usuario", backref="campanias_creadas")
    usuarios_asignados = relationship("CampaniaUsuario", back_populates="campania", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Campania {self.id_campania}: {self.nombre_campania} ({self.porcentaje_desc}% desc)>"
    
    def to_dict(self):
        """Serializa el modelo a diccionario"""
        return {
            'id_campania': self.id_campania,
            'usuario_crea_id': self.usuario_crea_id,
            'codigo': self.codigo,
            'nombre_campania': self.nombre_campania,
            'porcentaje_desc': float(self.porcentaje_desc) if self.porcentaje_desc else 0,
            'estatus': self.estatus,
            'estatus_display': 'Activa' if self.estatus == 1 else 'Inactiva',
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
