"""
ProveedorService - Lógica de negocio para proveedores
"""

import logging
from src.dao.inventario.proveedor_dao import ProveedorDAO
from src.core.utils.multitenant import es_admin

logger = logging.getLogger(__name__)


class ProveedorService:
    """Service de Proveedor"""
    
    @staticmethod
    def crear_proveedor(usuario_id: int, nombre: str, telefono: str = None, 
                       email: str = None) -> dict:
        """
        Crear nuevo proveedor.
        Solo ADMIN puede crear.
        
        Args:
            usuario_id: ID del usuario autenticado
            nombre: Nombre del proveedor
            telefono: Teléfono (opcional)
            email: Email (opcional)
            
        Returns:
            {success: bool, data?: dict, error?: str, message?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó crear proveedor sin permisos")
                return {"success": False, "error": "Solo administradores pueden crear proveedores"}
            
            # CREAR PROVEEDOR
            proveedor = ProveedorDAO.crear_proveedor(nombre, telefono, email)
            
            logger.info(f"Admin {usuario_id} creó proveedor: {nombre}")
            return {
                "success": True,
                "data": proveedor,
                "message": f"Proveedor '{nombre}' creado exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error en ProveedorService.crear_proveedor: {str(e)}")
            return {"success": False, "error": f"Error al crear proveedor: {str(e)}"}
    
    
    @staticmethod
    def obtener_proveedor(proveedor_id: int) -> dict:
        """
        Obtener proveedor por ID.
        
        Args:
            proveedor_id: ID del proveedor
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            proveedor = ProveedorDAO.obtener_proveedor_por_id(proveedor_id)
            
            if not proveedor:
                return {"success": False, "error": f"Proveedor {proveedor_id} no encontrado"}
            
            return {"success": True, "data": proveedor}
            
        except Exception as e:
            logger.error(f"Error en ProveedorService.obtener_proveedor: {str(e)}")
            return {"success": False, "error": f"Error al obtener proveedor: {str(e)}"}
    
    
    @staticmethod
    def listar_proveedores(solo_activos: bool = True) -> dict:
        """
        Listar todos los proveedores.
        
        Args:
            solo_activos: Si True, solo proveedores activos
            
        Returns:
            {success: bool, data?: list, error?: str}
        """
        try:
            proveedores = ProveedorDAO.obtener_todos_proveedores(solo_activos)
            return {
                "success": True,
                "data": proveedores
            }
            
        except Exception as e:
            logger.error(f"Error en ProveedorService.listar_proveedores: {str(e)}")
            return {"success": False, "error": f"Error al listar proveedores: {str(e)}"}
    
    
    @staticmethod
    def actualizar_proveedor(usuario_id: int, proveedor_id: int, 
                            nombre: str = None, telefono: str = None, 
                            email: str = None) -> dict:
        """
        Actualizar proveedor.
        Solo ADMIN puede actualizar.
        
        Args:
            usuario_id: ID del usuario autenticado
            proveedor_id: ID del proveedor
            nombre: Nuevo nombre (opcional)
            telefono: Nuevo teléfono (opcional)
            email: Nuevo email (opcional)
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó actualizar proveedor sin permisos")
                return {"success": False, "error": "Solo administradores pueden actualizar proveedores"}
            
            # VALIDACIÓN 2: Proveedor existe
            if not ProveedorDAO.proveedor_existe(proveedor_id):
                return {"success": False, "error": f"Proveedor {proveedor_id} no existe"}
            
            # ACTUALIZAR
            proveedor = ProveedorDAO.actualizar_proveedor(proveedor_id, nombre, telefono, email)
            
            logger.info(f"Admin {usuario_id} actualizó proveedor: {proveedor_id}")
            return {
                "success": True,
                "data": proveedor,
                "message": "Proveedor actualizado exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error en ProveedorService.actualizar_proveedor: {str(e)}")
            return {"success": False, "error": f"Error al actualizar proveedor: {str(e)}"}
    
    
    @staticmethod
    def eliminar_proveedor(usuario_id: int, proveedor_id: int) -> dict:
        """
        Eliminar proveedor (soft delete).
        Solo ADMIN puede eliminar.
        
        Args:
            usuario_id: ID del usuario autenticado
            proveedor_id: ID del proveedor
            
        Returns:
            {success: bool, error?: str, message?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó eliminar proveedor sin permisos")
                return {"success": False, "error": "Solo administradores pueden eliminar proveedores"}
            
            # ELIMINAR
            resultado = ProveedorDAO.eliminar_proveedor(proveedor_id)
            
            if not resultado:
                return {"success": False, "error": f"Proveedor {proveedor_id} no existe"}
            
            logger.info(f"Admin {usuario_id} eliminó proveedor: {proveedor_id}")
            return {
                "success": True,
                "message": "Proveedor eliminado exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error en ProveedorService.eliminar_proveedor: {str(e)}")
            return {"success": False, "error": f"Error al eliminar proveedor: {str(e)}"}
