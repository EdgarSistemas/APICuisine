from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from ..base import Base

class CodigoValidacion(Base):
    __tablename__ = 'codigo_validacion'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True)
    codigo = Column(String(6), nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow)
    expira_en = Column(DateTime, nullable=False)

    def __init__(self, email, codigo, duracion_minutos=10):
        self.email = email
        self.codigo = codigo
        self.creado_en = datetime.utcnow()
        self.expira_en = self.creado_en + timedelta(minutes=duracion_minutos)

    def es_valido(self):
        return datetime.utcnow() <= self.expira_en