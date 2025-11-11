"""
CategoriaMenuService - Business Logic para Categorías de Menú
"""

from src.dao.catalogos.categoria_menu_dao import CategoriaMenuDAO
from src.core.utils.multitenant import es_admin
import logging

logger = logging.getLogger(__name__)


class CategoriaMenuService:
    """Business logic para CategoriaMenu"""
    
    @staticmethod
    def crear_categoria(usuario_id: int, nombre: str, descripcion: str = None) -> dict:
        """
        Crear nueva categoría de menú.
        Solo ADMIN puede crear.
        
        Args:
            usuario_id: ID del usuario autenticado
            nombre: Nombre de la categoría
            descripcion: Descripción (opcional)
            
        Returns:
            {success: bool, data?: dict, error?: str, message?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó crear categoría sin permisos")
                return {"success": False, "error": "Solo administradores pueden crear categorías"}
            
            # CREAR
            categoria = CategoriaMenuDAO.crear_categoria(nombre, descripcion)
            
            logger.info(f"Admin {usuario_id} creó categoría: {nombre}")
            return {
                "success": True,
                "data": categoria,
                "message": f"Categoría '{nombre}' creada exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error en CategoriaMenuService.crear_categoria: {str(e)}")
            return {"success": False, "error": f"Error al crear categoría: {str(e)}"}
    
    
    @staticmethod
    def obtener_categoria(categoria_id: int) -> dict:
        """
        Obtener categoría por ID.
        
        Args:
            categoria_id: ID de la categoría
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            categoria = CategoriaMenuDAO.obtener_categoria_por_id(categoria_id)
            
            if not categoria:
                return {"success": False, "error": f"Categoría {categoria_id} no encontrada"}
            
            return {"success": True, "data": categoria}
            
        except Exception as e:
            logger.error(f"Error en CategoriaMenuService.obtener_categoria: {str(e)}")
            return {"success": False, "error": f"Error al obtener categoría: {str(e)}"}
    
    
    @staticmethod
    def listar_categorias(solo_activas: bool = True) -> dict:
        """
        Listar todas las categorías.
        
        Args:
            solo_activas: Si True, solo categorías activas
            
        Returns:
            {success: bool, data?: list, error?: str}
        """
        try:
            categorias = CategoriaMenuDAO.obtener_todas_las_categorias(solo_activas)
            return {"success": True, "data": categorias}
            
        except Exception as e:
            logger.error(f"Error en CategoriaMenuService.listar_categorias: {str(e)}")
            return {"success": False, "error": f"Error al listar categorías: {str(e)}"}
    
    
    @staticmethod
    def actualizar_categoria(usuario_id: int, categoria_id: int, nombre: str = None,
                            descripcion: str = None) -> dict:
        """
        Actualizar categoría.
        Solo ADMIN puede actualizar.
        
        Args:
            usuario_id: ID del usuario autenticado
            categoria_id: ID de la categoría
            nombre: Nuevo nombre (opcional)
            descripcion: Nueva descripción (opcional)
            es_activa: Nuevo estado (opcional)
            
        Returns:
            {success: bool, data?: dict, error?: str, message?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó actualizar categoría sin permisos")
                return {"success": False, "error": "Solo administradores pueden actualizar categorías"}
            
            # VALIDACIÓN 2: Categoría debe existir
            if not CategoriaMenuDAO.categoria_existe(categoria_id):
                return {"success": False, "error": f"Categoría {categoria_id} no existe"}
            
            # ACTUALIZAR
            # ACTUALIZAR
            categoria = CategoriaMenuDAO.actualizar_categoria(categoria_id, nombre, descripcion)
            
            logger.info(f"Admin {usuario_id} actualizó categoría: {categoria_id}")
            return {
                "success": True,
                "data": categoria,
                "message": "Categoría actualizada exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error en CategoriaMenuService.actualizar_categoria: {str(e)}")
            return {"success": False, "error": f"Error al actualizar categoría: {str(e)}"}
    
    
    @staticmethod
    def eliminar_categoria(usuario_id: int, categoria_id: int) -> dict:
        """
        Eliminar categoría (soft delete).
        Solo ADMIN puede eliminar.
        
        Args:
            usuario_id: ID del usuario autenticado
            categoria_id: ID de la categoría
            
        Returns:
            {success: bool, error?: str, message?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó eliminar categoría sin permisos")
                return {"success": False, "error": "Solo administradores pueden eliminar categorías"}
            
            # VALIDACIÓN 2: Categoría debe existir
            if not CategoriaMenuDAO.categoria_existe(categoria_id):
                return {"success": False, "error": f"Categoría {categoria_id} no existe"}
            
            # ELIMINAR
            CategoriaMenuDAO.eliminar_categoria_soft(categoria_id)
            
            logger.info(f"Admin {usuario_id} eliminó categoría: {categoria_id}")
            return {
                "success": True,
                "message": "Categoría eliminada exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error en CategoriaMenuService.eliminar_categoria: {str(e)}")
            return {"success": False, "error": f"Error al eliminar categoría: {str(e)}"}
