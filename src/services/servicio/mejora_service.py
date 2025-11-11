"""
MejoraService - Business Logic para Mejoras/Sugerencias
"""

from src.dao.servicio.mejora_dao import MejoraDAO
from src.core.utils.multitenant import es_admin
import logging

logger = logging.getLogger(__name__)


class MejoraService:
    """Service para Mejoras/Sugerencias"""
    
    @staticmethod
    def crear_mejora(cliente_id: int, notas: str) -> dict:
        """
        Crear nueva sugerencia de mejora.
        
        Args:
            cliente_id: ID del cliente que sugiere
            notas: Descripción de la sugerencia
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            # Validar que notas no esté vacío
            if not notas or len(notas.strip()) == 0:
                return {"success": False, "error": "Las notas son requeridas"}
            
            mejora = MejoraDAO.crear_mejora(cliente_id, notas)
            return {"success": True, "data": mejora}
            
        except Exception as e:
            logger.error(f"Error en MejoraService.crear_mejora: {str(e)}")
            return {"success": False, "error": f"Error al crear mejora: {str(e)}"}
    
    
    @staticmethod
    def obtener_mejora(mejora_id: int) -> dict:
        """
        Obtener mejora por ID.
        
        Args:
            mejora_id: ID de la mejora
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            mejora = MejoraDAO.obtener_mejora_por_id(mejora_id)
            
            if not mejora:
                return {"success": False, "error": f"Mejora {mejora_id} no existe"}
            
            return {"success": True, "data": mejora}
            
        except Exception as e:
            logger.error(f"Error en MejoraService.obtener_mejora: {str(e)}")
            return {"success": False, "error": f"Error al obtener mejora: {str(e)}"}
    
    
    @staticmethod
    def listar_mejoras(usuario_id: int, estatus: int = None) -> dict:
        """
        Listar mejoras.
        - ADMIN ve todas
        - Cliente ve solo sus sugerencias
        
        Args:
            usuario_id: ID del usuario autenticado
            estatus: Filtrar por estatus (opcional)
            
        Returns:
            {success: bool, data?: list, error?: str}
        """
        try:
            # Si no es admin, solo ve sus propias mejoras
            cliente_id = None if es_admin(usuario_id) else usuario_id
            
            mejoras = MejoraDAO.listar_mejoras(cliente_id, estatus)
            return {"success": True, "data": mejoras}
            
        except Exception as e:
            logger.error(f"Error en MejoraService.listar_mejoras: {str(e)}")
            return {"success": False, "error": f"Error al listar mejoras: {str(e)}"}
