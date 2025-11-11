"""
Core - Infraestructura y configuración base del proyecto
Contiene configuración, utilidades y componentes de infraestructura.
"""

from .config import get_config

__all__ = [
    'get_config'
]

# Configuración disponible globalmente
config = get_config()