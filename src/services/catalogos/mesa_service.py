"""
MesaService - Business Logic para Mesas
Validaciones, multi-tenant awareness, role-based access
"""

from src.dao.catalogos.mesa_dao import MesaDAO
from src.dao.catalogos.area_dao import AreaDAO
from src.core.utils.multitenant import (
    es_admin, validar_acceso_sucursal, agregar_filtro_sucursal,
    validar_pertenencia_sucursal
)
import logging

logger = logging.getLogger(__name__)


class MesaService:
    """Business logic para Mesa"""
    
    @staticmethod
    def crear_mesa(usuario_id: int, area_id: int, capacidad: int) -> dict:
        """
        Crear nueva mesa.
        El código se genera automáticamente con formato MES-YYYYMMDDHHMMSS.
        
        SOLO ADMIN puede crear mesas.
        El área DEBE existir.
        
        Args:
            usuario_id: ID del usuario que crea
            area_id: ID del área donde crear la mesa
            capacidad: Capacidad de personas
            
        Returns:
            {success: bool, data?: Mesa dict, error?: str, message?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó crear mesa sin permisos")
                return {"success": False, "error": "Solo administradores pueden crear mesas"}
            
            # VALIDACIÓN 2: Area debe existir
            if not MesaDAO.area_existe(area_id):
                logger.warning(f"Intento de crear mesa en área inexistente: {area_id}")
                return {"success": False, "error": f"Área {area_id} no existe"}
            
            # VALIDACIÓN 3: capacidad válida
            if not capacidad or capacidad <= 0:
                return {"success": False, "error": "La capacidad debe ser mayor a 0"}
            
            # CREAR (el DAO genera código automático)
            mesa = MesaDAO.crear_mesa(area_id, capacidad)
            
            logger.info(f"Usuario {usuario_id} (ADMIN) creó mesa con código {mesa['codigo_mesa']}")
            return {
                "success": True,
                "data": mesa,
                "message": f"Mesa '{mesa['codigo_mesa']}' creada exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error en MesaService.crear_mesa: {str(e)}")
            return {"success": False, "error": f"Error al crear mesa: {str(e)}"}
    
    
    @staticmethod
    def obtener_mesas(usuario_id: int, area_id: int = None, sucursal_id: int = None) -> dict:
        """
        Obtener mesas con multi-tenant awareness.
        
        - ADMIN: puede ver todas las mesas (si sucursal_id=None) o de una sucursal
        - EMPLOYEE: ve solo las mesas de sus sucursales
        
        AHORA INCLUYE: estatus_actual y estatus_display para cada mesa
        
        Args:
            usuario_id: ID del usuario que consulta
            area_id: Filtro por área (opcional)
            sucursal_id: Filtro por sucursal (opcional)
            
        Returns:
            {success: bool, data: [Mesa dicts con estatus], total: int}
        """
        try:
            mesas = []
            
            # Si se filtra por area_id, obtener de esa área
            if area_id:
                mesas = MesaDAO.obtener_mesas_por_area_con_estatus(area_id, solo_activas=True)
            
            # Si se filtra por sucursal_id, obtener de esa sucursal
            elif sucursal_id:
                mesas = MesaDAO.obtener_mesas_por_sucursal_con_estatus(sucursal_id, solo_activas=True)
            
            # Si es ADMIN y no hay filtros, obtener todas
            elif es_admin(usuario_id):
                mesas = MesaDAO.obtener_todas_las_mesas_con_estatus(solo_activas=True)
            
            # Si es EMPLOYEE, obtener de sus sucursales
            else:
                # Obtener sucursales del employee
                sucursales_usuario = validar_acceso_sucursal(usuario_id)
                if not sucursales_usuario:
                    return {"success": True, "data": [], "total": 0}
                
                # Para cada sucursal, obtener mesas
                for suc_id in sucursales_usuario:
                    mesas_suc = MesaDAO.obtener_mesas_por_sucursal_con_estatus(suc_id, solo_activas=True)
                    mesas.extend(mesas_suc)
            
            logger.info(f"Usuario {usuario_id} consultó mesas: {len(mesas)} resultados")
            return {
                "success": True,
                "data": mesas,
                "total": len(mesas)
            }
            
        except Exception as e:
            logger.error(f"Error en MesaService.obtener_mesas: {str(e)}")
            return {"success": False, "data": [], "error": f"Error al obtener mesas: {str(e)}"}
    
    
    @staticmethod
    def obtener_mesa(usuario_id: int, mesa_id: int) -> dict:
        """
        Obtener una mesa específica con validación de acceso.
        
        AHORA INCLUYE: estatus_actual y estatus_display
        
        Args:
            usuario_id: ID del usuario que consulta
            mesa_id: ID de la mesa
            
        Returns:
            {success: bool, data?: Mesa dict con estatus, error?: str}
        """
        try:
            mesa = MesaDAO.obtener_mesa_con_estatus(mesa_id)
            
            if not mesa:
                logger.warning(f"Mesa {mesa_id} no encontrada")
                return {"success": False, "error": f"Mesa {mesa_id} no existe"}
            
            # VALIDACIÓN DE ACCESO: Si no es ADMIN, verificar que tenga acceso a la sucursal
            if not es_admin(usuario_id):
                sucursal_id = MesaDAO.obtener_sucursal_de_mesa(mesa_id)
                
                # Verificar acceso a la sucursal (via multitenant utility)
                if not validar_pertenencia_sucursal(usuario_id, sucursal_id):
                    logger.warning(f"Usuario {usuario_id} intentó acceder a mesa {mesa_id} sin permisos")
                    return {"success": False, "error": "No tiene acceso a esta mesa"}
            
            logger.info(f"Usuario {usuario_id} consultó mesa {mesa_id}")
            return {"success": True, "data": mesa}
            
        except Exception as e:
            logger.error(f"Error en MesaService.obtener_mesa: {str(e)}")
            return {"success": False, "error": f"Error al obtener mesa: {str(e)}"}
    
    
    @staticmethod
    def actualizar_mesa(usuario_id: int, mesa_id: int, capacidad: int = None) -> dict:
        """
        Actualizar mesa.
        El código de mesa NO se puede modificar.
        
        SOLO ADMIN puede actualizar.
        
        Args:
            usuario_id: ID del usuario que actualiza
            mesa_id: ID de la mesa
            capacidad: Nueva capacidad (opcional)
            
        Returns:
            {success: bool, data?: Mesa dict, error?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó actualizar mesa sin permisos")
                return {"success": False, "error": "Solo administradores pueden actualizar mesas"}
            
            # VALIDACIÓN 2: Mesa debe existir
            mesa = MesaDAO.obtener_mesa_por_id(mesa_id)
            if not mesa:
                return {"success": False, "error": f"Mesa {mesa_id} no existe"}
            
            # VALIDACIÓN 3: Si se actualiza capacidad, debe ser válida
            if capacidad is not None and capacidad <= 0:
                return {"success": False, "error": "La capacidad debe ser mayor a 0"}
            
            # ACTUALIZAR
            mesa_actualizada = MesaDAO.actualizar_mesa(mesa_id, capacidad=capacidad)
            
            logger.info(f"Usuario {usuario_id} (ADMIN) actualizó mesa {mesa_id}")
            return {
                "success": True,
                "data": mesa_actualizada,
                "message": "Mesa actualizada exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error en MesaService.actualizar_mesa: {str(e)}")
            return {"success": False, "error": f"Error al actualizar mesa: {str(e)}"}
    
    
    @staticmethod
    def eliminar_mesa(usuario_id: int, mesa_id: int) -> dict:
        """
        Eliminar mesa (soft delete).
        
        SOLO ADMIN puede eliminar.
        
        Args:
            usuario_id: ID del usuario que elimina
            mesa_id: ID de la mesa
            
        Returns:
            {success: bool, error?: str, message?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó eliminar mesa sin permisos")
                return {"success": False, "error": "Solo administradores pueden eliminar mesas"}
            
            # VALIDACIÓN 2: Mesa debe existir
            existe = MesaDAO.obtener_mesa_por_id(mesa_id)
            if not existe:
                return {"success": False, "error": f"Mesa {mesa_id} no existe"}
            
            # ELIMINAR (soft delete)
            eliminada = MesaDAO.eliminar_mesa_soft(mesa_id)
            
            if not eliminada:
                return {"success": False, "error": "No se pudo eliminar la mesa"}
            
            logger.info(f"Usuario {usuario_id} (ADMIN) eliminó mesa {mesa_id}")
            return {
                "success": True,
                "message": "Mesa eliminada exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error en MesaService.eliminar_mesa: {str(e)}")
            return {"success": False, "error": f"Error al eliminar mesa: {str(e)}"}
