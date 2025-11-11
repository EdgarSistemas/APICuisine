"""
UnidadMedidaService - Business Logic para Unidades de Medida
"""

from src.dao.inventario.unidad_medida_dao import UnidadMedidaDAO
from src.core.utils.multitenant import es_admin
import logging

logger = logging.getLogger(__name__)


class UnidadMedidaService:
    """Business logic para UnidadMedida"""
    
    @staticmethod
    def crear_unidad_medida(usuario_id: int, clave: str, nombre: str, simbolo: str = None) -> dict:
        """
        Crear nueva unidad de medida.
        Solo ADMIN puede crear.
        
        Args:
            usuario_id: ID del usuario autenticado
            clave: Clave única (kg, g, l, ml, pz, etc)
            nombre: Nombre descriptivo
            simbolo: Símbolo (opcional)
            
        Returns:
            {success: bool, data?: dict, error?: str, message?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó crear unidad de medida sin permisos")
                return {"success": False, "error": "Solo administradores pueden crear unidades de medida"}
            
            # VALIDACIÓN 2: Clave no debe existir
            if UnidadMedidaDAO.clave_existe(clave):
                logger.warning(f"Intento de crear unidad con clave duplicada: {clave}")
                return {"success": False, "error": f"La clave '{clave}' ya existe"}
            
            # CREAR
            unidad = UnidadMedidaDAO.crear_unidad_medida(clave, nombre, simbolo)
            
            logger.info(f"Admin {usuario_id} creó unidad de medida: {clave}")
            return {
                "success": True,
                "data": unidad,
                "message": f"Unidad de medida '{nombre}' creada exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error en UnidadMedidaService.crear_unidad_medida: {str(e)}")
            return {"success": False, "error": f"Error al crear unidad de medida: {str(e)}"}
    
    
    @staticmethod
    def obtener_unidad(unidad_id: int) -> dict:
        """
        Obtener unidad de medida por ID.
        
        Args:
            unidad_id: ID de la unidad
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            unidad = UnidadMedidaDAO.obtener_unidad_por_id(unidad_id)
            
            if not unidad:
                return {"success": False, "error": f"Unidad de medida {unidad_id} no encontrada"}
            
            return {"success": True, "data": unidad}
            
        except Exception as e:
            logger.error(f"Error en UnidadMedidaService.obtener_unidad: {str(e)}")
            return {"success": False, "error": f"Error al obtener unidad: {str(e)}"}
    
    
    @staticmethod
    def listar_unidades() -> dict:
        """
        Listar todas las unidades de medida.
        
        Returns:
            {success: bool, data?: list, error?: str}
        """
        try:
            unidades = UnidadMedidaDAO.obtener_todas_las_unidades()
            return {"success": True, "data": unidades}
            
        except Exception as e:
            logger.error(f"Error en UnidadMedidaService.listar_unidades: {str(e)}")
            return {"success": False, "error": f"Error al listar unidades: {str(e)}"}
    
    
    @staticmethod
    def actualizar_unidad(usuario_id: int, unidad_id: int, clave: str = None, 
                         nombre: str = None, simbolo: str = None) -> dict:
        """
        Actualizar unidad de medida.
        Solo ADMIN puede actualizar.
        
        Args:
            usuario_id: ID del usuario autenticado
            unidad_id: ID de la unidad
            clave: Nueva clave (opcional)
            nombre: Nuevo nombre (opcional)
            simbolo: Nuevo símbolo (opcional)
            
        Returns:
            {success: bool, data?: dict, error?: str, message?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó actualizar unidad de medida sin permisos")
                return {"success": False, "error": "Solo administradores pueden actualizar unidades de medida"}
            
            # VALIDACIÓN 2: Unidad debe existir
            if not UnidadMedidaDAO.unidad_existe(unidad_id):
                return {"success": False, "error": f"Unidad de medida {unidad_id} no existe"}
            
            # ACTUALIZAR
            unidad = UnidadMedidaDAO.actualizar_unidad(unidad_id, clave, nombre, simbolo)
            
            logger.info(f"Admin {usuario_id} actualizó unidad de medida: {unidad_id}")
            return {
                "success": True,
                "data": unidad,
                "message": "Unidad de medida actualizada exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error en UnidadMedidaService.actualizar_unidad: {str(e)}")
            return {"success": False, "error": f"Error al actualizar unidad: {str(e)}"}
