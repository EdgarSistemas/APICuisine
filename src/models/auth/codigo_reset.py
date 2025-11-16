"""
Modelo para códigos de reset de contraseña
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from ..base import BaseModel

class CodigoReset(BaseModel):
    """Modelo para códigos de verificación de reset de contraseña"""
    
    __tablename__ = 'codigo_reset'
    __table_args__ = {'schema': 'seguridad'}
    
    # Campos principales - exactos a la tabla SQL
    id_codigo = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey('seguridad.Usuario.id_usuario'), nullable=False)
    codigo = Column(String(6), nullable=False)
    expiracion = Column(DateTime, nullable=False)
    usado = Column(Boolean, default=False, nullable=False)
    
    # Timestamps automáticos
    created_at = Column(DateTime, default=lambda: datetime.now(ZoneInfo("America/Mexico_City")), nullable=False)
    used_at = Column(DateTime, nullable=True)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="codigos_reset")
    
    def __repr__(self):
        return f"<CodigoReset(id={self.id_codigo}, usuario_id={self.usuario_id}, usado={self.usado})>"
    
    def esta_vigente(self) -> bool:
        """Verificar si el código está vigente (no usado y no expirado) usando timezone de México"""
        tz_mexico = ZoneInfo("America/Mexico_City")
        ahora_mexico = datetime.now(tz_mexico)
        return not self.usado and self.expiracion > ahora_mexico
    
    def marcar_como_usado(self):
        """Marcar el código como usado con hora de México"""
        tz_mexico = ZoneInfo("America/Mexico_City")
        self.usado = True
        self.used_at = datetime.now(tz_mexico)