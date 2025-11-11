"""
CompraService - Lógica de negocio para compras
"""

import logging
from datetime import datetime
from src.dao.inventario.compra_dao import CompraDAO, CompraDetalleDAO
from src.dao.inventario.insumo_dao import InsumoDAO
from src.dao.inventario.proveedor_dao import ProveedorDAO
from src.core.utils.multitenant import es_admin, validar_sucursal_existe, tiene_rol

logger = logging.getLogger(__name__)


class CompraService:
    """Service de Compra"""
    
    @staticmethod
    def _generar_folio_compra() -> str:
        """
        Generar folio de compra: COM-YYYYMMDDHHMMSS
        Ejemplo: COM-20251109152555
        """
        return f"COM-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    @staticmethod
    def crear_compra(usuario_id: int, sucursal_id: int, proveedor_id: int, 
                    detalles: list) -> dict:
        """
        Crear nueva compra con detalles.
        Solo ADMIN (id_rol=1) o COMPRAS (id_rol=8).
        
        Args:
            usuario_id: ID del usuario autenticado (del JWT)
            sucursal_id: ID de la sucursal (del payload)
            proveedor_id: ID del proveedor
            detalles: Lista de {insumo_id, cant_presentacion, costo_unit_present}
            
        Returns:
            {success: bool, data?: dict, error?: str, message?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN (id_rol=1) o COMPRAS (id_rol=8)
            if not (es_admin(usuario_id) or tiene_rol(usuario_id, 8)):
                logger.warning(f"Usuario {usuario_id} intentó crear compra sin permisos")
                return {"success": False, "error": "Solo administradores o usuarios de compras pueden registrar compras"}
            
            # VALIDACIÓN 2: Sucursal existe
            if not validar_sucursal_existe(sucursal_id):
                return {"success": False, "error": f"Sucursal {sucursal_id} no existe"}
            
            # VALIDACIÓN 3: Proveedor existe
            if not ProveedorDAO.proveedor_existe(proveedor_id):
                return {"success": False, "error": f"Proveedor {proveedor_id} no existe"}
            
            # VALIDACIÓN 4: Detalles no vacíos
            if not detalles or len(detalles) == 0:
                return {"success": False, "error": "Debe incluir al menos un detalle"}
            
            # VALIDACIÓN 5: Todos los insumos existen
            for item in detalles:
                insumo_id = item.get('insumo_id')
                if not InsumoDAO.insumo_existe(insumo_id):
                    return {"success": False, "error": f"Insumo {insumo_id} no existe"}
            
            # GENERAR FOLIO
            folio = CompraService._generar_folio_compra()
            
            # CREAR COMPRA
            compra = CompraDAO.crear_compra(usuario_id, sucursal_id, proveedor_id, folio)
            
            # AGREGAR DETALLES
            for item in detalles:
                CompraDetalleDAO.agregar_detalle(
                    compra['id_compra'],
                    item['insumo_id'],
                    item['cant_presentacion'],
                    item['costo_unit_present'],
                    item['presentacion']
                )
            
            logger.info(f"Admin {usuario_id} creó compra: {folio} con {len(detalles)} detalles")
            return {
                "success": True,
                "data": CompraDAO.obtener_compra_detallada(compra['id_compra']),
                "message": f"Compra '{folio}' creada exitosamente con {len(detalles)} artículos"
            }
            
        except Exception as e:
            logger.error(f"Error en CompraService.crear_compra: {str(e)}")
            return {"success": False, "error": f"Error al crear compra: {str(e)}"}
    
    
    @staticmethod
    def obtener_compra(compra_id: int) -> dict:
        """
        Obtener compra por ID con datos completos:
        - Proveedor (nombre, telefono, email)
        - Sucursal (nombre, codigo)
        - Usuario (nombre, apellido, email)
        - Detalles con insumo y unidad de medida
        
        Args:
            compra_id: ID de la compra
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            compra = CompraDAO.obtener_compra_completa(compra_id)
            
            if not compra:
                return {"success": False, "error": f"Compra {compra_id} no encontrada"}
            
            return {"success": True, "data": compra}
            
        except Exception as e:
            logger.error(f"Error en CompraService.obtener_compra: {str(e)}")
            return {"success": False, "error": f"Error al obtener compra: {str(e)}"}
    
    
    @staticmethod
    def listar_compras_por_sucursal(sucursal_id: int) -> dict:
        """
        Listar compras de una sucursal.
        
        Args:
            sucursal_id: ID de la sucursal
            
        Returns:
            {success: bool, data?: list, error?: str, total?: int}
        """
        try:
            # VALIDACIÓN: Sucursal existe
            if not validar_sucursal_existe(sucursal_id):
                return {"success": False, "error": f"Sucursal {sucursal_id} no existe"}
            
            compras = CompraDAO.listar_compras_por_sucursal(sucursal_id)
            return {
                "success": True,
                "data": compras,
                "total": len(compras)
            }
            
        except Exception as e:
            logger.error(f"Error en CompraService.listar_compras_por_sucursal: {str(e)}")
            return {"success": False, "error": f"Error al listar compras: {str(e)}"}
    
    
    @staticmethod
    def cancelar_compra(usuario_id: int, compra_id: int) -> dict:
        """
        Cancelar una compra (estatus=3).
        Solo ADMIN o COMPRAS.
        No se puede cancelar si ya tiene recepción asociada.
        
        Args:
            usuario_id: ID del usuario autenticado
            compra_id: ID de la compra a cancelar
            
        Returns:
            {success: bool, message?: str, error?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN o COMPRAS
            if not (es_admin(usuario_id) or tiene_rol(usuario_id, 8)):
                logger.warning(f"Usuario {usuario_id} intentó cancelar compra sin permisos")
                return {"success": False, "error": "Solo administradores o usuarios de compras pueden cancelar compras"}
            
            # VALIDACIÓN 2: Compra existe
            compra = CompraDAO.obtener_compra_por_id(compra_id)
            if not compra:
                return {"success": False, "error": f"Compra {compra_id} no existe"}
            
            # VALIDACIÓN 3: No está ya cancelada
            estatus_actual = compra.get('estatus') if isinstance(compra, dict) else compra.estatus
            if estatus_actual == 3:
                return {"success": False, "error": "La compra ya está cancelada"}
            
            # VALIDACIÓN 4: No tiene recepción asociada (estatus != 2)
            if estatus_actual == 2:
                return {"success": False, "error": "No se puede cancelar una compra que ya tiene recepción registrada"}
            
            # Cancelar compra (cambiar estatus a 3)
            actualizado = CompraDAO.actualizar_estatus_compra(compra_id, 3)
            
            if not actualizado:
                return {"success": False, "error": "No se pudo actualizar el estatus de la compra"}
            
            logger.info(f"Compra {compra_id} cancelada por usuario {usuario_id}")
            return {
                "success": True,
                "message": f"Compra {compra_id} cancelada exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error en CompraService.cancelar_compra: {str(e)}")
            return {"success": False, "error": f"Error al cancelar compra: {str(e)}"}
