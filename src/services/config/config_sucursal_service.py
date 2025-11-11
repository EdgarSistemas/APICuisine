"""
ConfigSucursalService - Business Logic para Configuraciones por Sucursal
"""

from src.dao.config.config_sucursal_dao import ConfigSucursalDAO
from src.core.utils.multitenant import es_admin
import logging

logger = logging.getLogger(__name__)


class ConfigSucursalService:
    """Service para gestión de configuraciones por sucursal"""
    
    @staticmethod
    def crear_o_actualizar_config(usuario_id: int, sucursal_id: int, clave: str, valor_string: str = None) -> dict:
        """
        Crear o actualizar configuración.
        Solo ADMIN puede gestionar configuraciones.
        
        Args:
            usuario_id: ID del usuario autenticado
            sucursal_id: ID de la sucursal
            clave: Clave de configuración
            valor_string: Valor de la configuración
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó crear/actualizar config sin permisos")
                return {"success": False, "error": "Solo administradores pueden gestionar configuraciones"}
            
            # VALIDACIÓN 2: Sucursal existe
            if not ConfigSucursalDAO.sucursal_existe(sucursal_id):
                return {"success": False, "error": f"Sucursal {sucursal_id} no existe"}
            
            # Crear o actualizar
            config = ConfigSucursalDAO.crear_o_actualizar_config(sucursal_id, clave, valor_string)
            
            logger.info(f"Config guardada: sucursal={sucursal_id}, clave={clave} por usuario {usuario_id}")
            return {"success": True, "data": config}
            
        except Exception as e:
            logger.error(f"Error en ConfigSucursalService.crear_o_actualizar_config: {str(e)}")
            return {"success": False, "error": f"Error al guardar configuración: {str(e)}"}
    
    
    @staticmethod
    def obtener_config(sucursal_id: int, clave: str) -> dict:
        """
        Obtener configuración por sucursal y clave.
        
        Args:
            sucursal_id: ID de la sucursal
            clave: Clave de configuración
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            config = ConfigSucursalDAO.obtener_config_por_clave(sucursal_id, clave)
            
            if not config:
                return {"success": False, "error": f"Configuración '{clave}' no encontrada para sucursal {sucursal_id}"}
            
            return {"success": True, "data": config}
            
        except Exception as e:
            logger.error(f"Error en ConfigSucursalService.obtener_config: {str(e)}")
            return {"success": False, "error": f"Error al obtener configuración: {str(e)}"}
    
    
    @staticmethod
    def listar_configs(sucursal_id: int) -> dict:
        """
        Listar todas las configuraciones de una sucursal.
        
        Args:
            sucursal_id: ID de la sucursal
            
        Returns:
            {success: bool, data?: list, error?: str}
        """
        try:
            configs = ConfigSucursalDAO.listar_configs_por_sucursal(sucursal_id)
            return {"success": True, "data": configs}
            
        except Exception as e:
            logger.error(f"Error en ConfigSucursalService.listar_configs: {str(e)}")
            return {"success": False, "error": f"Error al listar configuraciones: {str(e)}"}
    
    
    @staticmethod
    def eliminar_config(usuario_id: int, sucursal_id: int, clave: str) -> dict:
        """
        Eliminar configuración.
        Solo ADMIN puede eliminar configuraciones.
        
        Args:
            usuario_id: ID del usuario autenticado
            sucursal_id: ID de la sucursal
            clave: Clave de configuración
            
        Returns:
            {success: bool, message?: str, error?: str}
        """
        try:
            # VALIDACIÓN: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó eliminar config sin permisos")
                return {"success": False, "error": "Solo administradores pueden eliminar configuraciones"}
            
            eliminado = ConfigSucursalDAO.eliminar_config(sucursal_id, clave)
            
            if not eliminado:
                return {"success": False, "error": f"Configuración '{clave}' no encontrada"}
            
            logger.info(f"Config eliminada: sucursal={sucursal_id}, clave={clave} por usuario {usuario_id}")
            return {"success": True, "message": f"Configuración '{clave}' eliminada correctamente"}
            
        except Exception as e:
            logger.error(f"Error en ConfigSucursalService.eliminar_config: {str(e)}")
            return {"success": False, "error": f"Error al eliminar configuración: {str(e)}"}
