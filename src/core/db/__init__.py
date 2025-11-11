"""
Database Layer - Gestión de conexiones y pool de base de datos
Contiene el pool manager singleton y context managers para sesiones.
"""

from .pool_manager import pool_manager
from .session_manager import (
    get_db_session, 
    get_read_only_session, 
    get_db_connection,
    get_pool_status
)
from .base import (
    get_automap_base,
    get_model_class,
    list_available_tables,
    get_tables_by_schema,
    get_table_info,
    DatabaseReflection,
    AutomapBase,
    DeclarativeBase
)

__all__ = [
    'pool_manager',
    'get_db_session',
    'get_read_only_session', 
    'get_db_connection',
    'get_pool_status',
    'get_automap_base',
    'get_model_class',
    'list_available_tables',
    'get_tables_by_schema',
    'get_table_info',
    'DatabaseReflection',
    'AutomapBase',
    'DeclarativeBase',
    'initialize_pool',
    'get_engine'
]

def initialize_pool():
    """Inicializa el pool de conexiones si no está inicializado"""
    try:
        return pool_manager.get_engine()
    except RuntimeError:
        pool_manager.initialize()
        return pool_manager.get_engine()

def get_engine():
    """Obtiene el engine, inicializando el pool si es necesario"""
    return initialize_pool()