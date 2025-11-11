from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import BaseModel, TimestampMixin

class PushToken(BaseModel):
    __tablename__ = 'PushToken'
    __table_args__ = {'schema': 'movil'}

    id_push_token = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey('seguridad.Usuario.id_usuario'), nullable=True)
    plataforma = Column(String(10), nullable=False)  # 'android', 'web'
    token = Column(String(255), nullable=False, unique=True)
    es_activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(DateTime, nullable=False, default=func.sysutcdatetime())
    actualizado_en = Column(DateTime, nullable=True)
    
    # Relación con Usuario
    usuario = relationship("Usuario", back_populates="push_tokens")

    def __repr__(self):
        return f"<PushToken(id={self.id_push_token}, usuario_id={self.usuario_id}, plataforma='{self.plataforma}', activo={self.es_activo})>"

    def to_dict(self):
        """Convierte el objeto a diccionario para serialización JSON"""
        return {
            'id_push_token': self.id_push_token,
            'usuario_id': self.usuario_id,
            'plataforma': self.plataforma,
            'token': self.token,
            'es_activo': self.es_activo,
            'creado_en': self.creado_en.isoformat() if self.creado_en else None,
            'actualizado_en': self.actualizado_en.isoformat() if self.actualizado_en else None
        }