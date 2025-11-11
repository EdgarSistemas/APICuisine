"""
ComboService - Business Logic para Combos y Combo-Productos
"""

from src.dao.catalogos.combo_dao import ComboDAO, ComboProductoDAO
from src.dao.catalogos.producto_dao import ProductoDAO
from src.core.utils.multitenant import es_admin
import logging

logger = logging.getLogger(__name__)


class ComboService:
    """Business logic para Combo"""
    
    @staticmethod
    def crear_combo(usuario_id: int, nombre: str, precio: float, categoria_id: int,
                   descripcion: str = None, imagen_url: str = None, productos: list = None) -> dict:
        """
        Crear nuevo combo con productos.
        Solo ADMIN puede crear.
        
        Args:
            usuario_id: ID del usuario autenticado
            nombre: Nombre del combo
            precio: Precio del combo
            categoria_id: ID de la categoría (para clasificación del combo)
            descripcion: Descripción (opcional)
            imagen_url: URL de imagen (opcional)
            productos: Lista de {producto_id, cantidad} (opcional)
            
        Returns:
            {success: bool, data?: dict, error?: str, message?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó crear combo sin permisos")
                return {"success": False, "error": "Solo administradores pueden crear combos"}
            
            # VALIDACIÓN 2: Categoría debe existir (validación de referencia)
            from src.dao.catalogos.producto_dao import ProductoDAO as ProductoDAOImport
            if not ProductoDAOImport.categoria_existe(categoria_id):
                return {"success": False, "error": f"Categoría {categoria_id} no existe"}
            
            # VALIDACIÓN 3: Si hay productos, validar que existan
            if productos:
                for item in productos:
                    producto_id = item.get('producto_id')
                    if not ProductoDAO.producto_existe(producto_id):
                        return {"success": False, "error": f"Producto {producto_id} no existe"}
            
            # CREAR COMBO
            combo = ComboDAO.crear_combo(nombre, precio, descripcion, imagen_url)
            
            # AGREGAR PRODUCTOS si los hay
            if productos:
                for item in productos:
                    ComboProductoDAO.agregar_producto_a_combo(
                        combo['id_combo'],
                        item['producto_id'],
                        item.get('cantidad', 1)
                    )
            
            logger.info(f"Admin {usuario_id} creó combo: {nombre}")
            return {
                "success": True,
                "data": combo,
                "message": f"Combo '{nombre}' creado exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error en ComboService.crear_combo: {str(e)}")
            return {"success": False, "error": f"Error al crear combo: {str(e)}"}
    
    
    @staticmethod
    def obtener_combo(combo_id: int) -> dict:
        """
        Obtener combo por ID con datos completos.
        Incluye lista de productos (sin datos de receta).
        
        Args:
            combo_id: ID del combo
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            combo = ComboDAO.obtener_combo_detallado(combo_id)
            
            if not combo:
                return {"success": False, "error": f"Combo {combo_id} no encontrado"}
            
            return {"success": True, "data": combo}
            
        except Exception as e:
            logger.error(f"Error en ComboService.obtener_combo: {str(e)}")
            return {"success": False, "error": f"Error al obtener combo: {str(e)}"}
    
    
    @staticmethod
    def listar_combos(solo_activos: bool = True) -> dict:
        """
        Listar todos los combos.
        
        Args:
            solo_activos: Si True, solo combos activos
            
        Returns:
            {success: bool, data?: list, error?: str}
        """
        try:
            combos = ComboDAO.obtener_todos_los_combos(solo_activos)
            return {"success": True, "data": combos}
            
        except Exception as e:
            logger.error(f"Error en ComboService.listar_combos: {str(e)}")
            return {"success": False, "error": f"Error al listar combos: {str(e)}"}
    
    
    @staticmethod
    def actualizar_combo(usuario_id: int, combo_id: int, nombre: str = None,
                        precio: float = None, descripcion: str = None,
                        imagen_url: str = None, es_activo: bool = None) -> dict:
        """
        Actualizar combo.
        Solo ADMIN puede actualizar.
        
        Args:
            usuario_id: ID del usuario autenticado
            combo_id: ID del combo
            nombre: Nuevo nombre (opcional)
            precio: Nuevo precio (opcional)
            descripcion: Nueva descripción (opcional)
            imagen_url: Nueva URL de imagen (opcional)
            es_activo: Nuevo estado (opcional)
            
        Returns:
            {success: bool, data?: dict, error?: str, message?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó actualizar combo sin permisos")
                return {"success": False, "error": "Solo administradores pueden actualizar combos"}
            
            # VALIDACIÓN 2: Combo debe existir
            if not ComboDAO.combo_existe(combo_id):
                return {"success": False, "error": f"Combo {combo_id} no existe"}
            
            # ACTUALIZAR
            combo = ComboDAO.actualizar_combo(combo_id, nombre, precio, descripcion, imagen_url, es_activo)
            
            logger.info(f"Admin {usuario_id} actualizó combo: {combo_id}")
            return {
                "success": True,
                "data": combo,
                "message": "Combo actualizado exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error en ComboService.actualizar_combo: {str(e)}")
            return {"success": False, "error": f"Error al actualizar combo: {str(e)}"}
    
    
    @staticmethod
    def eliminar_combo(usuario_id: int, combo_id: int) -> dict:
        """
        Eliminar combo (soft delete).
        Solo ADMIN puede eliminar.
        
        Args:
            usuario_id: ID del usuario autenticado
            combo_id: ID del combo
            
        Returns:
            {success: bool, error?: str, message?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó eliminar combo sin permisos")
                return {"success": False, "error": "Solo administradores pueden eliminar combos"}
            
            # VALIDACIÓN 2: Combo debe existir
            if not ComboDAO.combo_existe(combo_id):
                return {"success": False, "error": f"Combo {combo_id} no existe"}
            
            # ELIMINAR
            ComboDAO.eliminar_combo_soft(combo_id)
            
            logger.info(f"Admin {usuario_id} eliminó combo: {combo_id}")
            return {
                "success": True,
                "message": "Combo eliminado exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error en ComboService.eliminar_combo: {str(e)}")
            return {"success": False, "error": f"Error al eliminar combo: {str(e)}"}
    
    
    # =========== ComboProducto Operations ===========
    
    @staticmethod
    def agregar_producto_a_combo(usuario_id: int, combo_id: int, producto_id: int,
                                cantidad: int = 1) -> dict:
        """
        Agregar un producto a un combo.
        Solo ADMIN puede agregar.
        
        Args:
            usuario_id: ID del usuario autenticado
            combo_id: ID del combo
            producto_id: ID del producto
            cantidad: Cantidad (default: 1)
            
        Returns:
            {success: bool, data?: dict, error?: str, message?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó agregar producto a combo sin permisos")
                return {"success": False, "error": "Solo administradores pueden agregar productos a combos"}
            
            # VALIDACIÓN 2: Combo debe existir
            if not ComboDAO.combo_existe(combo_id):
                return {"success": False, "error": f"Combo {combo_id} no existe"}
            
            # VALIDACIÓN 3: Producto debe existir
            if not ComboProductoDAO.producto_existe(producto_id):
                return {"success": False, "error": f"Producto {producto_id} no existe"}
            
            # AGREGAR
            item = ComboProductoDAO.agregar_producto_a_combo(combo_id, producto_id, cantidad)
            
            logger.info(f"Admin {usuario_id} agregó producto {producto_id} a combo {combo_id}")
            return {
                "success": True,
                "data": item,
                "message": "Producto agregado al combo exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error en ComboService.agregar_producto_a_combo: {str(e)}")
            return {"success": False, "error": f"Error al agregar producto: {str(e)}"}
    
    
    @staticmethod
    def obtener_productos_combo(combo_id: int) -> dict:
        """
        Obtener todos los productos de un combo.
        
        Args:
            combo_id: ID del combo
            
        Returns:
            {success: bool, data?: list, error?: str}
        """
        try:
            # VALIDACIÓN: Combo debe existir
            if not ComboDAO.combo_existe(combo_id):
                return {"success": False, "error": f"Combo {combo_id} no existe"}
            
            items = ComboProductoDAO.obtener_productos_de_combo(combo_id)
            return {"success": True, "data": items}
            
        except Exception as e:
            logger.error(f"Error en ComboService.obtener_productos_combo: {str(e)}")
            return {"success": False, "error": f"Error al obtener productos del combo: {str(e)}"}
    
    
    @staticmethod
    def remover_producto_de_combo(usuario_id: int, combo_producto_id: int) -> dict:
        """
        Remover un producto de un combo.
        Solo ADMIN puede remover.
        
        Args:
            usuario_id: ID del usuario autenticado
            combo_producto_id: ID del combo-producto
            
        Returns:
            {success: bool, error?: str, message?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó remover producto de combo sin permisos")
                return {"success": False, "error": "Solo administradores pueden remover productos de combos"}
            
            # VALIDACIÓN 2: Combo-producto debe existir
            if not ComboProductoDAO.combo_producto_existe(combo_producto_id):
                return {"success": False, "error": f"Producto en combo no encontrado"}
            
            # REMOVER
            ComboProductoDAO.remover_producto_de_combo(combo_producto_id)
            
            logger.info(f"Admin {usuario_id} removió producto de combo: {combo_producto_id}")
            return {
                "success": True,
                "message": "Producto removido del combo exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error en ComboService.remover_producto_de_combo: {str(e)}")
            return {"success": False, "error": f"Error al remover producto: {str(e)}"}
