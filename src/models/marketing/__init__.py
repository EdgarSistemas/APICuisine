"""
Models Marketing - Entidades del esquema marketing
CRM: Campañas y cupones de descuento
"""
from .campania_model import Campania
from .campania_usuario_model import CampaniaUsuario

__all__ = [
    'Campania',
    'CampaniaUsuario'
]
