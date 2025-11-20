"""
InsumoService - Business Logic para Insumos
"""

from src.dao.inventario.insumo_dao import InsumoDAO
from src.dao.inventario.unidad_medida_dao import UnidadMedidaDAO
from src.dao.inventario.existencia_dao import ExistenciaDAO
from src.dao.inventario.lote_dao import LoteDAO
from src.core.utils.multitenant import es_admin
import logging

logger = logging.getLogger(__name__)


class InsumoService:
    """Business logic para Insumo"""
    
    @staticmethod
    def crear_insumo(usuario_id: int, nombre: str, minimo_stock: float, unidad_id: int) -> dict:
        """
        Crear nuevo insumo.
        Solo ADMIN puede crear.
        
        Args:
            usuario_id: ID del usuario autenticado
            nombre: Nombre del insumo
            minimo_stock: Mínimo stock del insumo
            unidad_id: ID de la unidad de medida
            
        Returns:
            {success: bool, data?: dict, error?: str, message?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó crear insumo sin permisos")
                return {"success": False, "error": "Solo administradores pueden crear insumos"}
            
            # VALIDACIÓN 2: Unidad de medida debe existir
            if not UnidadMedidaDAO.unidad_existe(unidad_id):
                logger.warning(f"Intento de crear insumo con unidad inexistente: {unidad_id}")
                return {"success": False, "error": f"Unidad de medida {unidad_id} no existe"}
            
            # CREAR
            insumo = InsumoDAO.crear_insumo(nombre, minimo_stock, unidad_id)
            
            logger.info(f"Admin {usuario_id} creó insumo: {nombre}")
            return {
                "success": True,
                "data": insumo,
                "message": f"Insumo '{nombre}' creado exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error en InsumoService.crear_insumo: {str(e)}")
            return {"success": False, "error": f"Error al crear insumo: {str(e)}"}
    
    
    @staticmethod
    def obtener_insumo(insumo_id: int) -> dict:
        """
        Obtener insumo por ID.
        
        Args:
            insumo_id: ID del insumo
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            insumo = InsumoDAO.obtener_insumo_por_id(insumo_id)
            
            if not insumo:
                return {"success": False, "error": f"Insumo {insumo_id} no encontrado"}
            
            return {"success": True, "data": insumo}
            
        except Exception as e:
            logger.error(f"Error en InsumoService.obtener_insumo: {str(e)}")
            return {"success": False, "error": f"Error al obtener insumo: {str(e)}"}
    
    
    @staticmethod
    def listar_insumos(solo_activos: bool = True) -> dict:
        """
        Listar todos los insumos (sin existencias).
        
        Args:
            solo_activos: Si True, solo insumos activos
            
        Returns:
            {success: bool, data?: list, error?: str}
        """
        try:
            insumos = InsumoDAO.obtener_todos_los_insumos(solo_activos)
            return {"success": True, "data": insumos}
            
        except Exception as e:
            logger.error(f"Error en InsumoService.listar_insumos: {str(e)}")
            return {"success": False, "error": f"Error al listar insumos: {str(e)}"}
    
    
    @staticmethod
    def listar_insumos_con_existencias(sucursal_id: int, solo_activos: bool = True) -> dict:
        """
        Lista todos los insumos con sus existencias para una sucursal específica.
        
        Args:
            sucursal_id: ID de la sucursal
            solo_activos: Si True, solo devuelve insumos activos
            
        Returns:
            {
                success: bool, 
                data?: [
                    {
                        id_insumo: int,
                        nombre: str,
                        unidad_id: int,
                        unidad_clave: str,
                        unidad_nombre: str,
                        es_activo: bool,
                        cantidad: Decimal,
                        costo_promedio: Decimal,
                        updated_at: datetime
                    }
                ],
                error?: str
            }
        """
        try:
            # Obtener insumos con existencias desde el DAO
            insumos_con_existencias = InsumoDAO.listar_insumos_con_existencias(
                sucursal_id=sucursal_id,
                solo_activos=solo_activos
            )
            
            logger.info(f"Se listaron {len(insumos_con_existencias)} insumos con existencias para sucursal {sucursal_id}")
            return {
                "success": True,
                "data": insumos_con_existencias
            }
            
        except Exception as e:
            logger.error(f"Error al listar insumos con existencias: {str(e)}")
            return {
                "success": False,
                "error": f"Error al listar insumos con existencias: {str(e)}"
            }
    
    
    @staticmethod
    def actualizar_insumo(usuario_id: int, insumo_id: int, nombre: str = None, minimo_stock: float = None) -> dict:
        """
        Actualizar insumo.
        Solo ADMIN puede actualizar.
        
        Args:
            usuario_id: ID del usuario autenticado
            insumo_id: ID del insumo
            nombre: Nuevo nombre (opcional)
            minimo_stock: Nuevo mínimo stock (opcional)            
        Returns:
            {success: bool, data?: dict, error?: str, message?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó actualizar insumo sin permisos")
                return {"success": False, "error": "Solo administradores pueden actualizar insumos"}
            
            # VALIDACIÓN 2: Insumo debe existir
            if not InsumoDAO.insumo_existe(insumo_id):
                return {"success": False, "error": f"Insumo {insumo_id} no existe"}
            
            # ACTUALIZAR
            insumo = InsumoDAO.actualizar_insumo(insumo_id, nombre, minimo_stock)
            
            logger.info(f"Admin {usuario_id} actualizó insumo: {insumo_id}")
            return {
                "success": True,
                "data": insumo,
                "message": "Insumo actualizado exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error en InsumoService.actualizar_insumo: {str(e)}")
            return {"success": False, "error": f"Error al actualizar insumo: {str(e)}"}

    
    @staticmethod
    def obtener_lotes_proximos_a_vencer(sucursal_id: int, dias_proximidad: int = 30) -> dict:
        """
        Obtener lotes próximos a vencer por sucursal.
        
        Filtra lotes que vencen dentro de N días (default 30).
        
        Args:
            sucursal_id: ID de la sucursal
            dias_proximidad: Cantidad de días para considerar como "próximo a vencer" (default: 30)
            
        Returns:
            {
                success: bool, 
                data?: [
                    {
                        id_lote: int,
                        lote: str,
                        lote_proveedor: str,
                        cantidad_disponible: float,
                        costo_total: float,
                        fecha_caducidad: str (YYYY-MM-DD HH:MM:SS),
                        dias_para_vencer: int,
                        urgencia: str (Crítica|Alta|Media),
                        insumo_nombre: str,
                        unidad_clave: str
                    }
                ],
                error?: str,
                message?: str
            }
        """
        try:
            lotes = LoteDAO.obtener_lotes_proximos_a_vencer(sucursal_id, dias_proximidad)
            
            logger.info(f"Se obtuvieron {len(lotes)} lotes próximos a vencer en sucursal {sucursal_id}")
            return {
                "success": True,
                "data": lotes,
                "message": f"Se encontraron {len(lotes)} lotes próximos a vencer"
            }
            
        except Exception as e:
            logger.error(f"Error en InsumoService.obtener_lotes_proximos_a_vencer: {str(e)}")
            return {"success": False, "error": f"Error al obtener lotes próximos a vencer: {str(e)}"}
    
    
    @staticmethod
    def obtener_lotes_vencidos(sucursal_id: int) -> dict:
        """
        Obtener lotes vencidos por sucursal.
        
        Args:
            sucursal_id: ID de la sucursal
            
        Returns:
            {
                success: bool,
                data?: [
                    {
                        id_lote: int,
                        lote: str,
                        lote_proveedor: str,
                        cantidad_disponible: float,
                        costo_total_perdida: float,
                        fecha_caducidad: str (YYYY-MM-DD HH:MM:SS),
                        dias_vencido: int,
                        insumo_nombre: str,
                        unidad_clave: str
                    }
                ],
                error?: str,
                message?: str
            }
        """
        try:
            lotes = LoteDAO.obtener_lotes_vencidos(sucursal_id)
            
            logger.info(f"Se obtuvieron {len(lotes)} lotes vencidos en sucursal {sucursal_id}")
            return {
                "success": True,
                "data": lotes,
                "message": f"Se encontraron {len(lotes)} lotes vencidos"
            }
            
        except Exception as e:
            logger.error(f"Error en InsumoService.obtener_lotes_vencidos: {str(e)}")
            return {"success": False, "error": f"Error al obtener lotes vencidos: {str(e)}"}
