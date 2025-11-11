"""
AsignacionMesaService - Business Logic para Asignaciones de Mesas
Validaciones para asignar/desasignar meseros a mesas
"""

from src.dao.operaciones.asignacion_mesa_dao import AsignacionMesaDAO
from src.core.utils.multitenant import es_admin, obtener_rol_usuario, validar_pertenencia_sucursal
import logging

logger = logging.getLogger(__name__)


class AsignacionMesaService:
    """Business logic para AsignacionMesa"""
    
    @staticmethod
    def asignar_mesero(usuario_admin_id: int, mesa_id: int, mesero_id: int) -> dict:
        """
        Asignar un mesero a una mesa.
        
        SOLO ADMIN puede hacer esto.
        El mesero DEBE ser de rol Mesero (rol_id=5).
        La mesa DEBE existir.
        El mesero DEBE existir.
        
        Args:
            usuario_admin_id: ID del usuario ADMIN que realiza la asignación
            mesa_id: ID de la mesa
            mesero_id: ID del mesero (usuario)
            
        Returns:
            {success: bool, data?: AsignacionMesa dict, error?: str, message?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_admin_id):
                logger.warning(f"Usuario {usuario_admin_id} intentó asignar mesa sin permisos")
                return {"success": False, "error": "Solo administradores pueden asignar mesas"}
            
            # VALIDACIÓN 2: Mesa debe existir
            if not AsignacionMesaDAO.mesa_existe(mesa_id):
                logger.warning(f"Intento de asignar usuario a mesa inexistente: {mesa_id}")
                return {"success": False, "error": f"Mesa {mesa_id} no existe"}
            
            # VALIDACIÓN 3: Usuario/Mesero debe existir
            if not AsignacionMesaDAO.usuario_existe(mesero_id):
                logger.warning(f"Intento de asignar mesero inexistente: {mesero_id}")
                return {"success": False, "error": f"Mesero {mesero_id} no existe"}
            
            # VALIDACIÓN 4: El usuario debe ser Mesero (rol_id=5)
            rol_mesero = obtener_rol_usuario(mesero_id)
            if rol_mesero != 5:  # Mesero role
                logger.warning(f"Usuario {mesero_id} no es Mesero (rol={rol_mesero})")
                return {"success": False, "error": f"Usuario {mesero_id} no es Mesero"}
            
            # CREAR ASIGNACIÓN
            asignacion = AsignacionMesaDAO.asignar_mesero(mesa_id, mesero_id)
            
            logger.info(f"Admin {usuario_admin_id} asignó mesero {mesero_id} a mesa {mesa_id}")
            return {
                "success": True,
                "data": asignacion,
                "message": f"Mesero asignado a mesa {mesa_id} exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error en AsignacionMesaService.asignar_mesero: {str(e)}")
            return {"success": False, "error": f"Error al asignar mesero: {str(e)}"}
    
    
    @staticmethod
    def desasignar_mesero(usuario_admin_id: int, asignacion_id: int) -> dict:
        """
        Desasignar un mesero de una mesa.
        
        SOLO ADMIN puede hacer esto.
        La asignación DEBE existir.
        
        Args:
            usuario_admin_id: ID del usuario ADMIN que realiza la desasignación
            asignacion_id: ID de la asignación
            
        Returns:
            {success: bool, error?: str, message?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_admin_id):
                logger.warning(f"Usuario {usuario_admin_id} intentó desasignar mesa sin permisos")
                return {"success": False, "error": "Solo administradores pueden desasignar mesas"}
            
            # VALIDACIÓN 2: Asignación debe existir
            asignacion = AsignacionMesaDAO.obtener_asignacion_por_id(asignacion_id)
            if not asignacion:
                logger.warning(f"Asignación inexistente: {asignacion_id}")
                return {"success": False, "error": f"Asignación {asignacion_id} no existe"}
            
            # DESASIGNAR (soft delete)
            eliminada = AsignacionMesaDAO.desasignar_mesero(asignacion_id)
            
            if not eliminada:
                return {"success": False, "error": "No se pudo desasignar el mesero"}
            
            logger.info(f"Admin {usuario_admin_id} desasignó asignación {asignacion_id}")
            return {
                "success": True,
                "message": "Mesero desasignado exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error en AsignacionMesaService.desasignar_mesero: {str(e)}")
            return {"success": False, "error": f"Error al desasignar mesero: {str(e)}"}
    
    
    @staticmethod
    def obtener_asignaciones_mesa(usuario_id: int, mesa_id: int) -> dict:
        """
        Obtener todas las asignaciones de una mesa.
        
        Args:
            usuario_id: ID del usuario que consulta (para validar acceso)
            mesa_id: ID de la mesa
            
        Returns:
            {success: bool, data?: [AsignacionMesa dicts], error?: str}
        """
        try:
            # VALIDACIÓN: Si no es ADMIN, verificar acceso a sucursal
            if not es_admin(usuario_id):
                sucursal_id = AsignacionMesaDAO.obtener_sucursal_de_mesa(mesa_id)
                if not validar_pertenencia_sucursal(usuario_id, sucursal_id):
                    logger.warning(f"Usuario {usuario_id} intentó acceder a asignaciones de mesa {mesa_id} sin permisos")
                    return {"success": False, "error": "No tiene acceso a esta mesa"}
            
            # OBTENER
            asignaciones = AsignacionMesaDAO.obtener_asignaciones_por_mesa(mesa_id, solo_activas=True)
            
            logger.info(f"Usuario {usuario_id} consultó asignaciones de mesa {mesa_id}")
            return {
                "success": True,
                "data": asignaciones
            }
            
        except Exception as e:
            logger.error(f"Error en AsignacionMesaService.obtener_asignaciones_mesa: {str(e)}")
            return {"success": False, "error": f"Error al obtener asignaciones: {str(e)}"}
    
    
    @staticmethod
    def obtener_mesas_mesero(usuario_consulta_id: int, mesero_id: int) -> dict:
        """
        Obtener todas las mesas asignadas a un mesero.
        
        Args:
            usuario_consulta_id: ID del usuario que consulta
            mesero_id: ID del mesero
            
        Returns:
            {success: bool, data?: [Mesa dicts], error?: str}
        """
        try:
            # VALIDACIÓN: Solo ADMIN o el mismo Mesero
            if not es_admin(usuario_consulta_id) and usuario_consulta_id != mesero_id:
                logger.warning(f"Usuario {usuario_consulta_id} intentó ver mesas de mesero {mesero_id} sin permisos")
                return {"success": False, "error": "No tiene permiso para ver estas mesas"}
            
            # OBTENER
            mesas = AsignacionMesaDAO.obtener_mesas_por_mesero(mesero_id, solo_activas=True)
            
            logger.info(f"Usuario {usuario_consulta_id} consultó mesas del mesero {mesero_id}")
            return {
                "success": True,
                "data": mesas
            }
            
        except Exception as e:
            logger.error(f"Error en AsignacionMesaService.obtener_mesas_mesero: {str(e)}")
            return {"success": False, "error": f"Error al obtener mesas: {str(e)}"}
    
    
    @staticmethod
    def obtener_asignacion_activa_mesa(usuario_id: int, mesa_id: int) -> dict:
        """
        Obtener la asignación ACTIVA de una mesa (debe haber solo 1).
        
        Args:
            usuario_id: ID del usuario que consulta
            mesa_id: ID de la mesa
            
        Returns:
            {success: bool, data?: AsignacionMesa dict o None, error?: str}
        """
        try:
            # VALIDACIÓN: Si no es ADMIN, verificar acceso a sucursal
            if not es_admin(usuario_id):
                sucursal_id = AsignacionMesaDAO.obtener_sucursal_de_mesa(mesa_id)
                if not validar_pertenencia_sucursal(usuario_id, sucursal_id):
                    logger.warning(f"Usuario {usuario_id} intentó acceder a asignación de mesa {mesa_id} sin permisos")
                    return {"success": False, "error": "No tiene acceso a esta mesa"}
            
            # OBTENER
            asignacion = AsignacionMesaDAO.obtener_asignacion_activa_mesa(mesa_id)
            
            logger.info(f"Usuario {usuario_id} consultó asignación activa de mesa {mesa_id}")
            return {
                "success": True,
                "data": asignacion
            }
            
        except Exception as e:
            logger.error(f"Error en AsignacionMesaService.obtener_asignacion_activa_mesa: {str(e)}")
            return {"success": False, "error": f"Error al obtener asignación: {str(e)}"}
