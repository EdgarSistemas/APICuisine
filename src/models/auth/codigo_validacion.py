from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from ..base import Base

class CodigoValidacion(Base):
    __tablename__ = 'codigo_validacion'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False)
    codigo = Column(String(6), nullable=False)
    creado_en = Column(DateTime, nullable=False)
    expira_en = Column(DateTime, nullable=False)
    estatus = Column(Integer, default=1)  # 1=Activo, 0=Inactivo

    def __init__(self, email, codigo, creado_en, duracion_minutos=10):
        self.email = email
        self.codigo = codigo
        self.creado_en = creado_en
        self.expira_en = self.creado_en + timedelta(minutes=duracion_minutos)
        self.estatus = 1

    def es_valido(self):
        """Verificar si el código está vigente usando timezone de México"""
        tz_mexico = ZoneInfo("America/Mexico_City")
        ahora_mexico = datetime.now(tz_mexico)
        return ahora_mexico <= self.expira_en
    
    def invalidar(self):
        self.estatus = 0