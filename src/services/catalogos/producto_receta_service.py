"""
ProductoRecetaService - Business Logic para Recetas y Items
"""

from src.dao.catalogos.producto_receta_dao import ProductoRecetaDAO, ProductoRecetaItemDAO
from src.core.utils.multitenant import es_admin
import logging

logger = logging.getLogger(__name__)


class ProductoRecetaService:
    """Business logic para ProductoReceta"""
    
    @staticmethod
    def crear_receta(usuario_id: int, producto_id: int, nombre: str) -> dict:
        """
        Crear nueva receta para un producto.
        Solo ADMIN puede crear.
        
        Args:
            usuario_id: ID del usuario autenticado
            producto_id: ID del producto
            nombre: Nombre descriptivo de la receta
            
        Returns:
            {success: bool, data?: dict, error?: str, message?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó crear receta sin permisos")
                return {"success": False, "error": "Solo administradores pueden crear recetas"}
            
            # VALIDACIÓN 2: Producto debe existir
            if not ProductoRecetaDAO.producto_existe(producto_id):
                return {"success": False, "error": f"Producto {producto_id} no existe"}
            
            # CREAR
            receta = ProductoRecetaDAO.crear_receta(producto_id, nombre)
            
            logger.info(f"Admin {usuario_id} creó receta: {nombre} para producto {producto_id}")
            return {
                "success": True,
                "data": receta,
                "message": f"Receta '{nombre}' creada exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error en ProductoRecetaService.crear_receta: {str(e)}")
            return {"success": False, "error": f"Error al crear receta: {str(e)}"}
    
    
    @staticmethod
    def obtener_receta(receta_id: int) -> dict:
        """
        Obtener receta con todos sus insumos.
        
        Args:
            receta_id: ID de la receta
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            receta = ProductoRecetaDAO.obtener_receta_por_id(receta_id)
            
            if not receta:
                return {"success": False, "error": f"Receta {receta_id} no encontrada"}
            
            return {"success": True, "data": receta}
            
        except Exception as e:
            logger.error(f"Error en ProductoRecetaService.obtener_receta: {str(e)}")
            return {"success": False, "error": f"Error al obtener receta: {str(e)}"}
    
    
    @staticmethod
    def obtener_receta_activa_producto(producto_id: int) -> dict:
        """
        Obtener la receta activa de un producto.
        
        Args:
            producto_id: ID del producto
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            receta = ProductoRecetaDAO.obtener_receta_activa_producto(producto_id)
            
            if not receta:
                return {"success": False, "error": f"No hay receta activa para producto {producto_id}"}
            
            return {"success": True, "data": receta}
            
        except Exception as e:
            logger.error(f"Error en ProductoRecetaService.obtener_receta_activa_producto: {str(e)}")
            return {"success": False, "error": f"Error: {str(e)}"}
    
    
    @staticmethod
    def listar_recetas_producto(producto_id: int, solo_activas: bool = True) -> dict:
        """
        Listar todas las recetas de un producto.
        
        Args:
            producto_id: ID del producto
            solo_activas: Si True, solo recetas activas
            
        Returns:
            {success: bool, data?: list, error?: str}
        """
        try:
            recetas = ProductoRecetaDAO.obtener_recetas_por_producto(producto_id, solo_activas)
            return {"success": True, "data": recetas}
            
        except Exception as e:
            logger.error(f"Error en ProductoRecetaService.listar_recetas_producto: {str(e)}")
            return {"success": False, "error": f"Error al listar recetas: {str(e)}"}
    
    
    @staticmethod
    def actualizar_receta(usuario_id: int, receta_id: int, nombre: str = None,
                         es_activa: bool = None) -> dict:
        """
        Actualizar receta.
        Solo ADMIN puede actualizar.
        
        Args:
            usuario_id: ID del usuario autenticado
            receta_id: ID de la receta
            nombre: Nuevo nombre (opcional)
            es_activa: Nuevo estado (opcional)
            
        Returns:
            {success: bool, data?: dict, error?: str, message?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó actualizar receta sin permisos")
                return {"success": False, "error": "Solo administradores pueden actualizar recetas"}
            
            # VALIDACIÓN 2: Receta debe existir
            if not ProductoRecetaDAO.receta_existe(receta_id):
                return {"success": False, "error": f"Receta {receta_id} no existe"}
            
            # ACTUALIZAR
            receta = ProductoRecetaDAO.actualizar_receta(receta_id, nombre, es_activa)
            
            logger.info(f"Admin {usuario_id} actualizó receta: {receta_id}")
            return {
                "success": True,
                "data": receta,
                "message": "Receta actualizada exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error en ProductoRecetaService.actualizar_receta: {str(e)}")
            return {"success": False, "error": f"Error al actualizar receta: {str(e)}"}
    
    
    @staticmethod
    def eliminar_receta(usuario_id: int, receta_id: int) -> dict:
        """
        Eliminar receta (soft delete).
        Solo ADMIN puede eliminar.
        
        Args:
            usuario_id: ID del usuario autenticado
            receta_id: ID de la receta
            
        Returns:
            {success: bool, error?: str, message?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó eliminar receta sin permisos")
                return {"success": False, "error": "Solo administradores pueden eliminar recetas"}
            
            # VALIDACIÓN 2: Receta debe existir
            if not ProductoRecetaDAO.receta_existe(receta_id):
                return {"success": False, "error": f"Receta {receta_id} no existe"}
            
            # ELIMINAR
            ProductoRecetaDAO.eliminar_receta_soft(receta_id)
            
            logger.info(f"Admin {usuario_id} eliminó receta: {receta_id}")
            return {
                "success": True,
                "message": "Receta eliminada exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error en ProductoRecetaService.eliminar_receta: {str(e)}")
            return {"success": False, "error": f"Error al eliminar receta: {str(e)}"}


class ProductoRecetaItemService:
    """Business logic para ProductoRecetaItem"""
    
    @staticmethod
    def agregar_insumo_a_receta(usuario_id: int, receta_id: int, insumo_id: int,
                               cantidad: float) -> dict:
        """
        Agregar insumo a una receta.
        Solo ADMIN puede agregar.
        
        Args:
            usuario_id: ID del usuario autenticado
            receta_id: ID de la receta
            insumo_id: ID del insumo
            cantidad: Cantidad en unidad base
            
        Returns:
            {success: bool, data?: dict, error?: str, message?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó agregar insumo a receta sin permisos")
                return {"success": False, "error": "Solo administradores pueden agregar insumos"}
            
            # VALIDACIÓN 2: Receta debe existir
            if not ProductoRecetaDAO.receta_existe(receta_id):
                return {"success": False, "error": f"Receta {receta_id} no existe"}
            
            # VALIDACIÓN 3: Insumo debe existir
            if not ProductoRecetaItemDAO.insumo_existe(insumo_id):
                return {"success": False, "error": f"Insumo {insumo_id} no existe"}
            
            # VALIDACIÓN 4: Insumo no debe estar ya en la receta
            if ProductoRecetaItemDAO.insumo_ya_en_receta(receta_id, insumo_id):
                return {"success": False, "error": "Este insumo ya está en la receta"}
            
            # AGREGAR
            item = ProductoRecetaItemDAO.agregar_insumo_a_receta(receta_id, insumo_id, cantidad)
            
            logger.info(f"Admin {usuario_id} agregó insumo {insumo_id} a receta {receta_id}")
            return {
                "success": True,
                "data": item,
                "message": "Insumo agregado a receta exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error en ProductoRecetaItemService.agregar_insumo_a_receta: {str(e)}")
            return {"success": False, "error": f"Error al agregar insumo: {str(e)}"}
    
    
    @staticmethod
    def obtener_insumos_receta(receta_id: int) -> dict:
        """
        Obtener todos los insumos de una receta.
        
        Args:
            receta_id: ID de la receta
            
        Returns:
            {success: bool, data?: list, error?: str}
        """
        try:
            # VALIDACIÓN: Receta debe existir
            if not ProductoRecetaDAO.receta_existe(receta_id):
                return {"success": False, "error": f"Receta {receta_id} no existe"}
            
            items = ProductoRecetaItemDAO.obtener_insumos_receta(receta_id)
            return {"success": True, "data": items}
            
        except Exception as e:
            logger.error(f"Error en ProductoRecetaItemService.obtener_insumos_receta: {str(e)}")
            return {"success": False, "error": f"Error al obtener insumos: {str(e)}"}
    
    
    @staticmethod
    def actualizar_cantidad_insumo(usuario_id: int, receta_item_id: int,
                                  cantidad: float) -> dict:
        """
        Actualizar cantidad de insumo en receta.
        Solo ADMIN puede actualizar.
        
        Args:
            usuario_id: ID del usuario autenticado
            receta_item_id: ID del item de receta
            cantidad: Nueva cantidad
            
        Returns:
            {success: bool, data?: dict, error?: str, message?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó actualizar cantidad sin permisos")
                return {"success": False, "error": "Solo administradores pueden actualizar"}
            
            # VALIDACIÓN 2: Item debe existir
            if not ProductoRecetaItemDAO.receta_item_existe(receta_item_id):
                return {"success": False, "error": f"Item de receta {receta_item_id} no existe"}
            
            # ACTUALIZAR
            item = ProductoRecetaItemDAO.actualizar_cantidad(receta_item_id, cantidad)
            
            logger.info(f"Admin {usuario_id} actualizó cantidad en item {receta_item_id}")
            return {
                "success": True,
                "data": item,
                "message": "Cantidad actualizada exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error en ProductoRecetaItemService.actualizar_cantidad_insumo: {str(e)}")
            return {"success": False, "error": f"Error al actualizar cantidad: {str(e)}"}
    
    
    @staticmethod
    def remover_insumo_de_receta(usuario_id: int, receta_item_id: int) -> dict:
        """
        Remover insumo de receta.
        Solo ADMIN puede remover.
        
        Args:
            usuario_id: ID del usuario autenticado
            receta_item_id: ID del item de receta
            
        Returns:
            {success: bool, error?: str, message?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó remover insumo sin permisos")
                return {"success": False, "error": "Solo administradores pueden remover insumos"}
            
            # VALIDACIÓN 2: Item debe existir
            if not ProductoRecetaItemDAO.receta_item_existe(receta_item_id):
                return {"success": False, "error": f"Item de receta {receta_item_id} no existe"}
            
            # REMOVER
            ProductoRecetaItemDAO.remover_insumo_de_receta(receta_item_id)
            
            logger.info(f"Admin {usuario_id} removió insumo de receta: {receta_item_id}")
            return {
                "success": True,
                "message": "Insumo removido de receta exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error en ProductoRecetaItemService.remover_insumo_de_receta: {str(e)}")
            return {"success": False, "error": f"Error al remover insumo: {str(e)}"}
