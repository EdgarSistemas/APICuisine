"""
InventarioService - Business Logic para consumo de inventario
Gestión de movimientos, lotes y consumo por recetas
"""

from datetime import datetime
from decimal import Decimal
from src.dao.inventario.existencia_dao import ExistenciaDAO
from src.dao.inventario.lote_dao import LoteDAO
from src.dao.inventario.movimiento_dao import MovimientoDAO
from src.dao.catalogos.producto_dao import ProductoDAO
from src.dao.catalogos.combo_dao import ComboDAO
from src.models.catalogos.producto_receta_model import ProductoReceta
from src.core.db.session_manager import get_db_session
import logging

logger = logging.getLogger(__name__)


class InventarioService:
    """Service para gestión de inventario"""
    
    @staticmethod
    def consumir_por_pedido(pedido_id: int, sucursal_id: int, items: list) -> dict:
        """
        Consumir inventario para un pedido.
        
        Por cada item (producto/combo):
        1. Obtiene la receta del producto
        2. Para cada insumo de la receta:
           - Busca lotes ordenados por fecha_caducidad ASC (cercanos a vencer primero)
           - Descuenta cantidad_receta * cantidad_items
           - Crea movimiento de inventario
        
        Args:
            pedido_id: ID del pedido
            sucursal_id: ID de sucursal
            items: Lista de dicts con {'id_pedido_item', 'cantidad', 'producto_id', 'combo_id'}
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            movimientos_creados = []
            
            for item in items:
                item_id = item.get('id_pedido_item')
                cantidad = item.get('cantidad', 1)
                producto_id = item.get('producto_id')
                combo_id = item.get('combo_id')
                
                if producto_id:
                    # Es un producto: consumir por receta
                    resultado = InventarioService._consumir_producto(
                        producto_id=producto_id,
                        cantidad=cantidad,
                        sucursal_id=sucursal_id,
                        pedido_id=pedido_id
                    )
                    
                    if not resultado['success']:
                        return {
                            "success": False,
                            "error": f"Error consumiendo producto {producto_id}: {resultado.get('error')}"
                        }
                    
                    movimientos_creados.extend(resultado.get('data', []))
                
                elif combo_id:
                    # Es un combo: desglosa productos y consume c/u
                    resultado = InventarioService._consumir_combo(
                        combo_id=combo_id,
                        cantidad=cantidad,
                        sucursal_id=sucursal_id,
                        pedido_id=pedido_id
                    )
                    
                    if not resultado['success']:
                        return {
                            "success": False,
                            "error": f"Error consumiendo combo {combo_id}: {resultado.get('error')}"
                        }
                    
                    movimientos_creados.extend(resultado.get('data', []))
            
            logger.info(f"Consumo completado para pedido {pedido_id}: {len(movimientos_creados)} movimientos")
            return {
                "success": True,
                "data": {
                    "movimientos": len(movimientos_creados),
                    "detalles": movimientos_creados
                }
            }
            
        except Exception as e:
            logger.error(f"Error en InventarioService.consumir_por_pedido: {str(e)}")
            return {"success": False, "error": f"Error consumiendo inventario: {str(e)}"}
    
    
    @staticmethod
    def _consumir_producto(producto_id: int, cantidad: int, sucursal_id: int, pedido_id: int) -> dict:
        """
        Consumir inventario para un producto.
        
        Busca la receta del producto, y para cada insumo:
        - Busca lotes cercanos a vencer (fecha_caducidad ASC)
        - Descuenta cantidad_receta * cantidad del producto
        
        Args:
            producto_id: ID del producto
            cantidad: Cantidad del producto a cocinar
            sucursal_id: ID de sucursal
            pedido_id: ID del pedido
            
        Returns:
            {success: bool, data?: list, error?: str}
        """
        try:
            with get_db_session() as session:
                # Obtener receta del producto
                receta = session.query(ProductoReceta).filter(
                    ProductoReceta.producto_id == producto_id,
                    ProductoReceta.es_activa == True
                ).first()
                
                if not receta:
                    return {
                        "success": False,
                        "error": f"No hay receta activa para producto {producto_id}"
                    }
                
                movimientos = []
                
                # Por cada insumo en la receta
                for item_receta in receta.items:
                    insumo_id = item_receta.insumo_id
                    cantidad_por_unidad = item_receta.cantidad  # Cantidad de insumo por 1 unidad producto
                    cantidad_a_descontar = cantidad_por_unidad * cantidad  # Total a descontar
                    
                    # Consumir insumo de lotes
                    resultado_consumo = InventarioService._descontar_de_lotes(
                        insumo_id=insumo_id,
                        sucursal_id=sucursal_id,
                        cantidad_a_descontar=cantidad_a_descontar,
                        motivo_id=2,  # Receta/Consumo
                        pedido_id=pedido_id
                    )
                    
                    if not resultado_consumo['success']:
                        return resultado_consumo
                    
                    movimientos.extend(resultado_consumo.get('data', []))
                
                return {"success": True, "data": movimientos}
                
        except Exception as e:
            logger.error(f"Error en _consumir_producto: {str(e)}")
            return {"success": False, "error": str(e)}
    
    
    @staticmethod
    def _consumir_combo(combo_id: int, cantidad: int, sucursal_id: int, pedido_id: int) -> dict:
        """
        Consumir inventario para un combo.
        
        Desglosa los productos del combo y consume c/u.
        
        Args:
            combo_id: ID del combo
            cantidad: Cantidad del combo
            sucursal_id: ID de sucursal
            pedido_id: ID del pedido
            
        Returns:
            {success: bool, data?: list, error?: str}
        """
        try:
            # Obtener productos del combo
            combo = ComboDAO.obtener_combo_por_id(combo_id)
            if not combo:
                return {"success": False, "error": f"Combo {combo_id} no existe"}
            
            if not combo.get('productos'):
                return {"success": False, "error": f"Combo {combo_id} no tiene productos"}
            
            movimientos = []
            
            # Por cada producto en el combo
            for producto_en_combo in combo['productos']:
                producto_id = producto_en_combo.get('producto_id')
                
                resultado = InventarioService._consumir_producto(
                    producto_id=producto_id,
                    cantidad=cantidad,  # Mismo cantidad del combo
                    sucursal_id=sucursal_id,
                    pedido_id=pedido_id
                )
                
                if not resultado['success']:
                    return resultado
                
                movimientos.extend(resultado.get('data', []))
            
            return {"success": True, "data": movimientos}
            
        except Exception as e:
            logger.error(f"Error en _consumir_combo: {str(e)}")
            return {"success": False, "error": str(e)}
    
    
    @staticmethod
    def _descontar_de_lotes(
        insumo_id: int,
        sucursal_id: int,
        cantidad_a_descontar: Decimal,
        motivo_id: int,
        pedido_id: int
    ) -> dict:
        """
        Descontar cantidad de lotes disponibles.
        
        Busca lotes ordenados por fecha_caducidad ASC (cercanos a vencer primero)
        y descuenta hasta cubrir la cantidad requerida.
        
        Args:
            insumo_id: ID del insumo
            sucursal_id: ID de sucursal
            cantidad_a_descontar: Cantidad a descontar
            motivo_id: ID del motivo de movimiento (2=Consumo)
            pedido_id: ID del pedido
            
        Returns:
            {success: bool, data?: list, error?: str}
        """
        try:
            movimientos = []
            pendiente = Decimal(str(cantidad_a_descontar))
            
            # Obtener lotes activos ordenados por fecha_caducidad
            lotes = LoteDAO.obtener_lotes_disponibles(
                insumo_id=insumo_id,
                sucursal_id=sucursal_id,
                ordenar_por_caducidad=True  # Cercanos a vencer primero
            )
            
            if not lotes:
                return {
                    "success": False,
                    "error": f"No hay lotes disponibles del insumo {insumo_id} en sucursal {sucursal_id}"
                }
            
            # Descontar de cada lote hasta cubrir cantidad
            for lote in lotes:
                if pendiente <= 0:
                    break
                
                cantidad_disponible = Decimal(str(lote.get('cantidad_disponible', 0)))
                
                if cantidad_disponible <= 0:
                    continue
                
                # Cantidad a descontar de este lote
                cantidad_lote = min(pendiente, cantidad_disponible)
                
                # Crear movimiento
                resultado_mov = MovimientoDAO.crear_movimiento(
                    sucursal_id=sucursal_id,
                    insumo_id=insumo_id,
                    lote_id=lote.get('id_lote'),
                    tipo_mov=2,  # Salida
                    motivo=motivo_id,  # Receta/Consumo
                    cantidad=cantidad_lote,
                    pedido_id=pedido_id
                )
                
                if not resultado_mov:
                    return {
                        "success": False,
                        "error": f"Error creando movimiento para lote {lote.get('id_lote')}"
                    }
                
                # Actualizar lote
                LoteDAO.descontar_cantidad(lote.get('id_lote'), cantidad_lote)
                
                # Actualizar existencia
                ExistenciaDAO.descontar_cantidad(
                    sucursal_id=sucursal_id,
                    insumo_id=insumo_id,
                    cantidad=cantidad_lote
                )
                
                movimientos.append(resultado_mov)
                pendiente -= cantidad_lote
            
            # Verificar que se descont todo
            if pendiente > 0:
                return {
                    "success": False,
                    "error": f"Stock insuficiente del insumo {insumo_id}. Faltó descontar {pendiente}"
                }
            
            logger.info(f"Consumo descontado para insumo {insumo_id} en sucursal {sucursal_id}: -{cantidad_a_descontar}")
            return {"success": True, "data": movimientos}
            
        except Exception as e:
            logger.error(f"Error en _descontar_de_lotes: {str(e)}")
            return {"success": False, "error": str(e)}
