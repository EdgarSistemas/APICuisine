"""
Modelo para logs de auditoría
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from ..base import BaseModel

class LogAccion(BaseModel):
    """Modelo para auditoría de acciones en el sistema"""
    
    __tablename__ = 'LogAccion'
    __table_args__ = {'schema': 'auditoria'}
    
    # Campos principales
    id_log_accion = Column(Integer, primary_key=True, autoincrement=True)
    origen = Column(String(40), nullable=False)  # API, WEB, MOBILE, etc.
    entidad = Column(String(120), nullable=False)  # Usuario, Producto, Pedido, etc.
    entidad_id = Column(String(80), nullable=True)  # ID del registro afectado
    accion = Column(String(40), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN, etc.
    usuario_id = Column(Integer, ForeignKey('seguridad.Usuario.id_usuario'), nullable=True)
    detalle_json = Column(Text, nullable=True)  # Detalles adicionales en JSON
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="logs")
    
    def __repr__(self):
        return f"<LogAccion(id={self.id_log_accion}, entidad='{self.entidad}', accion='{self.accion}')>"
    
    def to_dict(self):
        """Convertir a diccionario"""
        return {
            'id_log_accion': self.id_log_accion,
            'origen': self.origen,
            'entidad': self.entidad,
            'entidad_id': self.entidad_id,
            'accion': self.accion,
            'usuario_id': self.usuario_id,
            'detalle_json': self.detalle_json,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }