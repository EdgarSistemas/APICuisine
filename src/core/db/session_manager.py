from contextlib import contextmanager
from src.core.db.pool_manager import pool_manager
import logging

logger = logging.getLogger(__name__)

@contextmanager
def get_db_session():
    """
    Context manager para sesiones de SQLAlchemy con commit automático
    """
    session = pool_manager.session_factory()
    try:
        logger.debug("Session opened")
        yield session
        session.commit()
        logger.debug("Session committed")
    except Exception as e:
        session.rollback()
        logger.error(f"Session rolled back due to error: {e}")
        raise
    finally:
        session.close()
        logger.debug("Session closed")

@contextmanager
def get_read_only_session():
    """
    Context manager para sesiones de solo lectura (sin commit automático)
    """
    session = pool_manager.session_factory()
    try:
        logger.debug("Read-only session opened")
        yield session
        # No commit en sesiones de solo lectura
    finally:
        session.close()
        logger.debug("Read-only session closed")

@contextmanager
def get_db_connection():
    """
    Context manager para conexiones raw (equivale exacto a tu open_db_connection)
    """
    connection = pool_manager.engine.connect()
    try:
        logger.debug("Raw connection opened")
        yield connection
    finally:
        connection.close()
        logger.debug("Raw connection closed")

def get_model(table_name):
    """
    Función helper para obtener modelos
    Equivale a tu get_model pero simplificado
    """
    return pool_manager.get_model(table_name)

def execute_query(query, params=None):
    """
    Ejecutar query raw con context manager automático
    """
    with get_db_connection() as conn:
        result = conn.execute(query, params or {})
        return result.fetchall()

def execute_stored_procedure(sp_name, params=None):
    """
    Ejecutar stored procedure (equivale a tu exec_store_procedure)
    """
    with get_db_connection() as conn:
        result = conn.execute(f"EXEC {sp_name}", params or {})
        return result.fetchall()

def initialize_db():
    """
    Función helper para inicializar el pool desde la app
    """
    pool_manager.initialize()
    logger.info("Database pool initialized successfully")

def get_pool_status():
    """
    Función helper para obtener el estado del pool
    """
    return pool_manager.get_pool_status()