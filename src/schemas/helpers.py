"""
Helpers para Schemas - Funciones y clases reutilizables
"""

from marshmallow import fields
from datetime import datetime
import pytz

# Zona horaria de México
TZ_MEXICO = pytz.timezone('America/Mexico_City')


class FormattedDateTime(fields.DateTime):
    """Campo DateTime personalizado que retorna fechas en formato legible sin 'T'
    
    Formato retornado: YYYY-MM-DD HH:MM:SS
    
    Características:
    - Maneja strings con 'Z' (ISO 8601 con UTC)
    - Maneja datetime objects con timezone
    - Convierte a timezone de México
    - Retorna en formato legible humano sin 'T'
    """
    
    def _serialize(self, value, attr, obj, **kwargs):
        """Serializa datetime a formato: YYYY-MM-DD HH:MM:SS"""
        if value is None:
            return None
        
        # Si es string, convertir a datetime
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return value
        
        # Si tiene timezone, convertir a Mexico timezone
        if hasattr(value, 'tzinfo') and value.tzinfo:
            value = value.astimezone(TZ_MEXICO)
        
        # Retornar en formato legible
        return value.strftime('%Y-%m-%d %H:%M:%S') if hasattr(value, 'strftime') else str(value)
