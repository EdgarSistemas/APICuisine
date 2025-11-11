"""
CalificacionService - Business Logic para Calificaciones
"""

from src.dao.servicio.calificacion_dao import CalificacionDAO
from src.core.utils.multitenant import es_admin
import logging

logger = logging.getLogger(__name__)


class CalificacionService:
    """Service para Calificaciones de servicio"""
    
    @staticmethod
    def crear_calificacion(cliente_id: int, pedido_id: int, empleado_id: int, calificacion: int, notas: str = None) -> dict:
        """
        Crear nueva calificación de servicio.
        
        Args:
            cliente_id: ID del cliente que califica
            pedido_id: ID del pedido
            empleado_id: ID del empleado calificado
            calificacion: Calificación (1-10)
            notas: Comentarios adicionales (opcional)
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            # VALIDACIÓN 1: Calificación en rango válido
            if calificacion < 1 or calificacion > 10:
                return {"success": False, "error": "La calificación debe estar entre 1 y 10"}
            
            # VALIDACIÓN 2: No permitir calificación duplicada
            if CalificacionDAO.existe_calificacion_pedido(pedido_id, cliente_id):
                return {"success": False, "error": "Ya has calificado este pedido"}
            
            calif = CalificacionDAO.crear_calificacion(cliente_id, pedido_id, empleado_id, calificacion, notas)
            return {"success": True, "data": calif}
            
        except Exception as e:
            logger.error(f"Error en CalificacionService.crear_calificacion: {str(e)}")
            return {"success": False, "error": f"Error al crear calificación: {str(e)}"}
    
    
    @staticmethod
    def obtener_calificacion(calificacion_id: int) -> dict:
        """
        Obtener calificación por ID.
        
        Args:
            calificacion_id: ID de la calificación
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            calif = CalificacionDAO.obtener_calificacion_por_id(calificacion_id)
            
            if not calif:
                return {"success": False, "error": f"Calificación {calificacion_id} no existe"}
            
            return {"success": True, "data": calif}
            
        except Exception as e:
            logger.error(f"Error en CalificacionService.obtener_calificacion: {str(e)}")
            return {"success": False, "error": f"Error al obtener calificación: {str(e)}"}
    
    
    @staticmethod
    def listar_calificaciones(usuario_id: int, pedido_id: int = None, empleado_id: int = None) -> dict:
        """
        Listar calificaciones.
        - ADMIN ve todas
        - Cliente ve solo sus calificaciones
        
        Args:
            usuario_id: ID del usuario autenticado
            pedido_id: Filtrar por pedido (opcional)
            empleado_id: Filtrar por empleado (opcional)
            
        Returns:
            {success: bool, data?: list, error?: str}
        """
        try:
            # Si no es admin, solo ve sus propias calificaciones
            cliente_id = None if es_admin(usuario_id) else usuario_id
            
            calificaciones = CalificacionDAO.listar_calificaciones(pedido_id, empleado_id, cliente_id)
            return {"success": True, "data": calificaciones}
            
        except Exception as e:
            logger.error(f"Error en CalificacionService.listar_calificaciones: {str(e)}")
            return {"success": False, "error": f"Error al listar calificaciones: {str(e)}"}
    
    
    @staticmethod
    def obtener_promedio_empleado(empleado_id: int) -> dict:
        """
        Obtener promedio de calificaciones de un empleado.
        
        Args:
            empleado_id: ID del empleado
            
        Returns:
            {success: bool, data?: float, error?: str}
        """
        try:
            promedio = CalificacionDAO.obtener_promedio_empleado(empleado_id)
            return {
                "success": True,
                "data": {
                    "empleado_id": empleado_id,
                    "promedio": round(promedio, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error en CalificacionService.obtener_promedio_empleado: {str(e)}")
            return {"success": False, "error": f"Error al obtener promedio: {str(e)}"}
