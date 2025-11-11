"""
ProductoService - Business Logic para Productos
"""

from datetime import datetime
from src.dao.catalogos.producto_dao import ProductoDAO
from src.dao.catalogos.combo_dao import ComboProductoDAO
from src.dao.catalogos.producto_receta_dao import ProductoRecetaDAO, ProductoRecetaItemDAO
from src.dao.inventario.insumo_dao import InsumoDAO
from src.core.utils.multitenant import es_admin
import logging

logger = logging.getLogger(__name__)


class ProductoService:
    """Business logic para Producto"""
    
    @staticmethod
    def _generar_codigo_producto() -> str:
        """
        Generar código de producto automáticamente.
        Formato: PRO-YYYYMMDDHHMM (ej: PRO-202511082236)
        """
        return f"PRO-{datetime.now().strftime('%Y%m%d%H%M')}"
    
    @staticmethod
    def crear_producto(usuario_id: int, categoria_id: int, nombre: str, precio: float,
                      codigo: str = None, descripcion: str = None, 
                      imagen_url: str = None, receta_items: list = None) -> dict:
        """
        Crear nuevo producto con receta opcional.
        Solo ADMIN puede crear.
        
        Args:
            usuario_id: ID del usuario autenticado
            categoria_id: ID de la categoría
            nombre: Nombre del producto
            precio: Precio unitario
            codigo: Código del producto (opcional, se genera automáticamente)
            descripcion: Descripción (opcional)
            imagen_url: URL de imagen (opcional)
            receta_items: Lista de {insumo_id, cantidad} (opcional)
            
        Returns:
            {success: bool, data?: dict, error?: str, message?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó crear producto sin permisos")
                return {"success": False, "error": "Solo administradores pueden crear productos"}
            
            # VALIDACIÓN 2: Categoría debe existir
            if not ProductoDAO.categoria_existe(categoria_id):
                logger.warning(f"Intento de crear producto con categoría inexistente: {categoria_id}")
                return {"success": False, "error": f"Categoría {categoria_id} no existe"}
            
            # VALIDACIÓN 3: Si hay receta_items, validar que los insumos existan
            if receta_items:
                for item in receta_items:
                    insumo_id = item.get('insumo_id')
                    if not InsumoDAO.insumo_existe(insumo_id):
                        return {"success": False, "error": f"Insumo {insumo_id} no existe"}
            
            # GENERAR CÓDIGO si no se proporciona
            if not codigo:
                codigo = ProductoService._generar_codigo_producto()
            
            # CREAR PRODUCTO
            producto = ProductoDAO.crear_producto(
                categoria_id, nombre, precio, codigo, descripcion, imagen_url
            )
            
            # CREAR RECETA si hay items
            if receta_items:
                receta = ProductoRecetaDAO.crear_receta(
                    producto['id_producto'],
                    f"Receta {nombre}"
                )
                
                # AGREGAR INSUMOS A LA RECETA
                for item in receta_items:
                    ProductoRecetaItemDAO.agregar_insumo_a_receta(
                        receta['id_receta'],
                        item['insumo_id'],
                        item['cantidad']
                    )
            
            logger.info(f"Admin {usuario_id} creó producto: {nombre} (código: {codigo})")
            return {
                "success": True,
                "data": producto,
                "message": f"Producto '{nombre}' creado exitosamente (código: {codigo})"
            }
            
        except Exception as e:
            logger.error(f"Error en ProductoService.crear_producto: {str(e)}")
            return {"success": False, "error": f"Error al crear producto: {str(e)}"}
    
    
    @staticmethod
    def obtener_producto(producto_id: int) -> dict:
        """
        Obtener producto por ID con datos completos.
        Incluye categoría, receta e insumos con unidad de medida.
        
        Args:
            producto_id: ID del producto
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            producto = ProductoDAO.obtener_producto_detallado(producto_id)
            
            if not producto:
                return {"success": False, "error": f"Producto {producto_id} no encontrado"}
            
            return {"success": True, "data": producto}
            
        except Exception as e:
            logger.error(f"Error en ProductoService.obtener_producto: {str(e)}")
            return {"success": False, "error": f"Error al obtener producto: {str(e)}"}
    
    
    @staticmethod
    def listar_productos() -> dict:
        """
        Listar todos los productos activos.
        
        Returns:
            {success: bool, data?: list, error?: str}
        """
        try:
            productos = ProductoDAO.obtener_todos_los_productos(solo_activos=True)
            return {"success": True, "data": productos}
            
        except Exception as e:
            logger.error(f"Error en ProductoService.listar_productos: {str(e)}")
            return {"success": False, "error": f"Error al listar productos: {str(e)}"}
    
    
    @staticmethod
    def actualizar_producto(usuario_id: int, producto_id: int, nombre: str = None,
                           precio: float = None, descripcion: str = None,
                           imagen_url: str = None, receta_items: list = None) -> dict:
        """
        Actualizar producto (datos básicos y cantidades de receta).
        Solo ADMIN puede actualizar.
        
        Args:
            usuario_id: ID del usuario autenticado
            producto_id: ID del producto
            nombre: Nuevo nombre (opcional)
            precio: Nuevo precio (opcional)
            descripcion: Nueva descripción (opcional)
            imagen_url: Nueva URL de imagen (opcional)
            receta_items: Lista de {id_receta_item, cantidad} para actualizar cantidades (opcional)
            
        Returns:
            {success: bool, data?: dict, error?: str, message?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó actualizar producto sin permisos")
                return {"success": False, "error": "Solo administradores pueden actualizar productos"}
            
            # VALIDACIÓN 2: Producto debe existir
            if not ProductoDAO.producto_existe(producto_id):
                return {"success": False, "error": f"Producto {producto_id} no existe"}
            
            # ACTUALIZAR DATOS BÁSICOS
            producto = ProductoDAO.actualizar_producto(
                producto_id, nombre, precio, descripcion, imagen_url
            )
            
            # ACTUALIZAR CANTIDADES DE RECETA si se proporcionan
            if receta_items:
                for item in receta_items:
                    receta_item_id = item.get('id_receta_item')
                    cantidad = item.get('cantidad')
                    if receta_item_id and cantidad:
                        ProductoRecetaItemDAO.actualizar_cantidad(receta_item_id, cantidad)
            
            logger.info(f"Admin {usuario_id} actualizó producto: {producto_id}")
            return {
                "success": True,
                "data": producto,
                "message": "Producto actualizado exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error en ProductoService.actualizar_producto: {str(e)}")
            return {"success": False, "error": f"Error al actualizar producto: {str(e)}"}
    
    
    @staticmethod
    def eliminar_producto(usuario_id: int, producto_id: int) -> dict:
        """
        Eliminar producto (soft delete).
        Solo ADMIN puede eliminar.
        
        Args:
            usuario_id: ID del usuario autenticado
            producto_id: ID del producto
            
        Returns:
            {success: bool, error?: str, message?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó eliminar producto sin permisos")
                return {"success": False, "error": "Solo administradores pueden eliminar productos"}
            
            # VALIDACIÓN 2: Producto debe existir
            if not ProductoDAO.producto_existe(producto_id):
                return {"success": False, "error": f"Producto {producto_id} no existe"}
            
            # ELIMINAR
            ProductoDAO.eliminar_producto_soft(producto_id)
            
            logger.info(f"Admin {usuario_id} eliminó producto: {producto_id}")
            return {
                "success": True,
                "message": "Producto eliminado exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error en ProductoService.eliminar_producto: {str(e)}")
            return {"success": False, "error": f"Error al eliminar producto: {str(e)}"}
