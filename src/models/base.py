"""
Base declarativa común para todos los modelos
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime, String
from datetime import datetime
import pytz

# Base declarativa compartida
Base = declarative_base()

# Zona horaria de México
TZ_MEXICO = pytz.timezone('America/Mexico_City')

def get_mexico_now():
    """Obtiene la hora actual en zona de México (sin timezone info para SQL Server)"""
    return datetime.now(TZ_MEXICO).replace(tzinfo=None)

class TimestampMixin:
    """
    Mixin para campos de auditoría comunes (nombres exactos del schema)
    """
    created_at = Column(DateTime, default=get_mexico_now, nullable=False)
    updated_at = Column(DateTime, default=get_mexico_now, onupdate=get_mexico_now)

class BaseModel(Base):
    """
    Modelo base abstracto con campos comunes
    """
    __abstract__ = True
    
    def to_dict(self):
        """Convertir modelo a diccionario"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result
    
    def __repr__(self):
        return f"<{self.__class__.__name__}({self.to_dict()})>"