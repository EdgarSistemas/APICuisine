"""
ConfigSucursalDAO - Data Access Object para config.ConfigSucursal
"""

from src.models import ConfigSucursal
from src.core.db.session_manager import get_db_session
from src.schemas.config_sucursal_schema import ConfigSucursalResponseSchema
import logging

logger = logging.getLogger(__name__)


class ConfigSucursalDAO:
    """Data Access Object para ConfigSucursal"""
    
    @staticmethod
    def crear_o_actualizar_config(sucursal_id: int, clave: str, valor_string: str = None) -> dict:
        """
        Crear o actualizar configuración (upsert).
        Si ya existe la clave para la sucursal, actualiza el valor.
        
        Args:
            sucursal_id: ID de la sucursal
            clave: Clave de configuración
            valor_string: Valor de la configuración
            
        Returns:
            Dict serializado de la configuración
        """
        schema = ConfigSucursalResponseSchema()
        with get_db_session() as session:
            # Buscar si ya existe
            config_existente = session.query(ConfigSucursal).filter(
                ConfigSucursal.sucursal_id == sucursal_id,
                ConfigSucursal.clave == clave
            ).first()
            
            if config_existente:
                # Actualizar
                config_existente.valor_string = valor_string
                session.commit()
                logger.info(f"Configuración actualizada: sucursal={sucursal_id}, clave={clave}")
                return schema.dump(config_existente)
            else:
                # Crear nueva
                nueva_config = ConfigSucursal(
                    sucursal_id=sucursal_id,
                    clave=clave,
                    valor_string=valor_string
                )
                session.add(nueva_config)
                session.commit()
                logger.info(f"Configuración creada: sucursal={sucursal_id}, clave={clave}")
                return schema.dump(nueva_config)
    
    
    @staticmethod
    def obtener_config_por_clave(sucursal_id: int, clave: str) -> dict:
        """
        Obtener configuración por sucursal y clave.
        
        Args:
            sucursal_id: ID de la sucursal
            clave: Clave de configuración
            
        Returns:
            Dict de la configuración o None
        """
        schema = ConfigSucursalResponseSchema()
        with get_db_session() as session:
            config = session.query(ConfigSucursal).filter(
                ConfigSucursal.sucursal_id == sucursal_id,
                ConfigSucursal.clave == clave
            ).first()
            return schema.dump(config) if config else None
    
    
    @staticmethod
    def listar_configs_por_sucursal(sucursal_id: int) -> list:
        """
        Listar todas las configuraciones de una sucursal.
        
        Args:
            sucursal_id: ID de la sucursal
            
        Returns:
            Lista de dicts de configuraciones
        """
        schema = ConfigSucursalResponseSchema()
        with get_db_session() as session:
            configs = session.query(ConfigSucursal).filter(
                ConfigSucursal.sucursal_id == sucursal_id
            ).order_by(ConfigSucursal.clave).all()
            return [schema.dump(c) for c in configs]
    
    
    @staticmethod
    def eliminar_config(sucursal_id: int, clave: str) -> bool:
        """
        Eliminar configuración por sucursal y clave.
        
        Args:
            sucursal_id: ID de la sucursal
            clave: Clave de configuración
            
        Returns:
            True si se eliminó, False si no existía
        """
        with get_db_session() as session:
            config = session.query(ConfigSucursal).filter(
                ConfigSucursal.sucursal_id == sucursal_id,
                ConfigSucursal.clave == clave
            ).first()
            
            if config:
                session.delete(config)
                session.commit()
                logger.info(f"Configuración eliminada: sucursal={sucursal_id}, clave={clave}")
                return True
            return False
    
    
    @staticmethod
    def sucursal_existe(sucursal_id: int) -> bool:
        """
        Verificar si una sucursal existe.
        
        Args:
            sucursal_id: ID de la sucursal
            
        Returns:
            True si existe
        """
        from src.models import Sucursal
        with get_db_session() as session:
            existe = session.query(Sucursal).filter(
                Sucursal.id_sucursal == sucursal_id
            ).first()
            return existe is not None
