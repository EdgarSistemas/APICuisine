"""
CampaniaUsuario Model
marketing.CampaniaUsuario - Asignación de cupones a clientes
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, Index, text, SMALLINT
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import Base, BaseModel


class CampaniaUsuario(BaseModel):
    """
    Modelo para asignación de cupones a usuarios/clientes.
    
    Estatus:
        0 = No usado (cupón disponible)
        1 = Usado (cupón canjeado)
    
    Validación de cupón:
        1. Campaña existe y está activa (Campania.estatus = 1)
        2. CampaniaUsuario existe para el cliente
        3. CampaniaUsuario.estatus = 0 (no usado)
        4. CampaniaUsuario.fecha_vigencia >= NOW() (timezone America/Mexico_City)
    """
    __tablename__ = 'CampaniaUsuario'
    __table_args__ = (
        Index('IX_CampaniaUsuario_Cliente', 'cliente_id'),
        Index('IX_CampaniaUsuario_Campania', 'campania_id'),
        Index('IX_CampaniaUsuario_ClienteCampaniaEstatus', 'cliente_id', 'campania_id', 'estatus'),
        {'schema': 'marketing'}
    )
    
    id_campania_usuario = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey('seguridad.Usuario.id_usuario'), nullable=False)
    campania_id = Column(Integer, ForeignKey('marketing.Campania.id_campania'), nullable=False)
    fecha_vigencia = Column(DateTime, nullable=True)  # Hasta cuándo es válido el cupón
    estatus = Column(SMALLINT, nullable=False, default=0)  # 0=NoUsado, 1=Usado
    created_at = Column(DateTime, server_default=text('SYSUTCDATETIME()'), nullable=False)
    
    # Relaciones
    cliente = relationship("Usuario", backref="cupones_asignados")
    campania = relationship("Campania", back_populates="usuarios_asignados")
    
    def __repr__(self):
        estado = "Usado" if self.estatus == 1 else "Disponible"
        return f"<CampaniaUsuario {self.id_campania_usuario}: Cliente {self.cliente_id} - Campaña {self.campania_id} ({estado})>"
    
    def to_dict(self):
        """Serializa el modelo a diccionario"""
        return {
            'id_campania_usuario': self.id_campania_usuario,
            'cliente_id': self.cliente_id,
            'campania_id': self.campania_id,
            'fecha_vigencia': self.fecha_vigencia.isoformat() if self.fecha_vigencia else None,
            'estatus': self.estatus,
            'estatus_display': 'Usado' if self.estatus == 1 else 'Disponible',
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
