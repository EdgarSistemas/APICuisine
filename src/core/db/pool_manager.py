from src.core.config import get_config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
import threading
import logging

# Importar modelos declarativos
from src.models.auth import Base

logger = logging.getLogger(__name__)

class DatabasePoolManager:
    """
    Singleton que gestiona el pool de conexiones con modelos declarativos
    Optimizado para performance - Sin automap
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._engine = None
            self._session_factory = None
            self._initialized = True
    
    def initialize(self):
        """
        Inicializar el pool con modelos declarativos (SIN AUTOMAP)
        """
        if self._engine is not None:
            logger.info("Pool already initialized")
            return
        
        logger.info("Initializing database pool with declarative models...")
        
        # Obtener configuración
        config = get_config()
        
        # Crear engine con pool de conexiones
        self._engine = create_engine(
            config.SQLALCHEMY_DATABASE_URI,
            poolclass=QueuePool,
            pool_size=config.POOL_SIZE,              # Pool base desde config
            max_overflow=config.POOL_MAX_OVERFLOW,   # Conexiones adicionales desde config
            pool_timeout=config.POOL_TIMEOUT,        # Timeout desde config
            pool_recycle=config.POOL_RECYCLE,        # Reciclar desde config
            pool_pre_ping=True,                      # Verificar conexiones antes de usar
            echo=config.SQLALCHEMY_ECHO              # Debug SQL desde config
        )
        
        # Crear session factory
        self._session_factory = sessionmaker(bind=self._engine)
        
        # Inicializar modelos declarativos (crear tablas si no existen)
        try:
            Base.metadata.create_all(self._engine)
            logger.info("Declarative models initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing declarative models: {e}")
            raise
        
        logger.info(f"Pool initialized with {config.POOL_SIZE} base connections + {config.POOL_MAX_OVERFLOW} overflow")
        logger.info(f"Pool timeout: {config.POOL_TIMEOUT}s, recycle: {config.POOL_RECYCLE}s")
    
    @property
    def engine(self):
        """Obtener engine"""
        if self._engine is None:
            raise RuntimeError("Pool not initialized. Call initialize() first.")
        return self._engine
    
    def get_engine(self):
        """Método de conveniencia para obtener engine"""
        return self.engine
    
    @property
    def session_factory(self):
        """Obtener session factory"""
        if self._session_factory is None:
            raise RuntimeError("Pool not initialized. Call initialize() first.")
        return self._session_factory
    
    @property
    def base(self):
        """Obtener base declarativa"""
        return Base
    
    def get_pool_status(self):
        """
        Obtener estado del pool para monitoring
        """
        if self._engine is None:
            return {"status": "not_initialized"}
        
        pool = self._engine.pool
        return {
            "status": "active",
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "total_connections": pool.size() + pool.overflow(),
            "model_type": "declarative"  # Indicador del tipo de modelo
        }

pool_manager = DatabasePoolManager()