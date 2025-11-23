"""
InventarioDAO - Data Access Object para gestión de inventario
Maneja consumo de insumos por lotes con lógica FIFO y cascada
Inventory descent happens when estado_pedido changes to 3 (EnPreparacion)
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import and_, or_, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from src.core.db.session_manager import get_db_session
import logging

logger = logging.getLogger(__name__)


class InventarioDAO:
    """DAO para gestión de inventario con consumo por lotes"""
    
    @staticmethod
    def verificar_stock_suficiente(producto_id: int, cantidad_necesaria: int, sucursal_id: int) -> tuple:
        """
        Verifica si hay stock suficiente de un producto
        
        Args:
            producto_id: ID del producto/insumo
            cantidad_necesaria: Cantidad a consumir
            sucursal_id: ID de sucursal (para existencia filtrada)
        
        Returns:
            tuple: (hay_stock: bool, cantidad_disponible: int, error_msg: str)
        """
        db = get_db_session()
        try:
            # Query en SQL directo para obtener existencia disponible
            query = text("""
                SELECT ISNULL(SUM(cantidad_disponible), 0) as total
                FROM inventario.Existencia
                WHERE producto_id = :prod_id 
                  AND sucursal_id = :suc_id
            """)
            
            result = db.session.execute(query, {'prod_id': producto_id, 'suc_id': sucursal_id}).first()
            cantidad_disponible = result[0] if result else 0
            
            if cantidad_disponible >= cantidad_necesaria:
                return True, cantidad_disponible, None
            else:
                return False, cantidad_disponible, f"Stock insuficiente: disponible {cantidad_disponible}, requerido {cantidad_necesaria}"
        
        except Exception as e:
            logger.error(f"Error al verificar stock: {str(e)}")
            return False, 0, f"Error al verificar stock: {str(e)}"
    
    
    @staticmethod
    def consumir_insumo_por_lotes(producto_id: int, cantidad_a_consumir: int, 
                                   sucursal_id: int, referencia: str = None) -> tuple:
        """
        Consume insumo siguiendo FIFO por fecha_caducidad
        Cascada automática: si lote actual no tiene suficiente, usa el siguiente
        
        Args:
            producto_id: ID del producto/insumo a consumir
            cantidad_a_consumir: Cantidad total a consumir
            sucursal_id: ID de sucursal
            referencia: Referencia para Movimiento (ej: pedido_id)
        
        Returns:
            tuple: (éxito: bool, lotes_consumidos: list, error_msg: str)
        
        Lógica FIFO:
            1. Ordenar lotes por fecha_caducidad (NULL al final)
            2. Para cada lote en orden:
               - Consumir min(cantidad_restante, lote.cantidad_disponible)
               - Crear Movimiento registrando consumo
               - Actualizar Existencia.cantidad_disponible y rowversion
               - Si cantidad_restante > 0, continuar con siguiente lote
            3. Si cantidad_restante > 0 al final, retornar error
        """
        db = get_db_session()
        try:
            # Obtener lotes ordenados FIFO por fecha_caducidad
            query = text("""
                SELECT l.id_lote, l.cantidad_disponible, l.fecha_caducidad, e.rowversion
                FROM inventario.Lote l
                JOIN inventario.Existencia e ON l.id_lote = e.id_lote
                WHERE e.producto_id = :prod_id 
                  AND e.sucursal_id = :suc_id
                  AND l.cantidad_disponible > 0
                ORDER BY l.fecha_caducidad ASC, l.id_lote ASC
            """)
            
            lotes = db.session.execute(query, {
                'prod_id': producto_id,
                'suc_id': sucursal_id
            }).fetchall()
            
            if not lotes:
                return False, [], f"No hay lotes disponibles para producto {producto_id}"
            
            cantidad_restante = cantidad_a_consumir
            lotes_consumidos = []
            
            # Procesar cada lote en orden FIFO
            for id_lote, cant_disponible, fecha_caducidad, rowversion in lotes:
                if cantidad_restante <= 0:
                    break
                
                # Cantidad a consumir de este lote
                cantidad_consumir_lote = min(cantidad_restante, cant_disponible)
                
                # Actualizar Existencia con rowversion para evitar condiciones de carrera
                update_query = text("""
                    UPDATE inventario.Existencia
                    SET cantidad_disponible = cantidad_disponible - :cantidad,
                        rowversion = rowversion + 1,
                        updated_at = GETUTCDATE()
                    WHERE id_lote = :id_lote
                      AND rowversion = :rowversion
                """)
                
                result = db.session.execute(update_query, {
                    'cantidad': cantidad_consumir_lote,
                    'id_lote': id_lote,
                    'rowversion': rowversion
                })
                
                if result.rowcount == 0:
                    # Conflicto de versión, reintento con valores actuales
                    existencia_query = text("""
                        SELECT rowversion, cantidad_disponible 
                        FROM inventario.Existencia 
                        WHERE id_lote = :id_lote
                    """)
                    existing = db.session.execute(existencia_query, {'id_lote': id_lote}).first()
                    if existing:
                        rowversion = existing[0]
                        # Reintentar con nueva versión
                        result = db.session.execute(update_query, {
                            'cantidad': cantidad_consumir_lote,
                            'id_lote': id_lote,
                            'rowversion': rowversion
                        })
                
                # Crear Movimiento de registro
                movimiento_query = text("""
                    INSERT INTO inventario.Movimiento 
                    (id_lote, tipo_movimiento, cantidad, referencia, created_at)
                    VALUES (:id_lote, 'CONSUMO', :cantidad, :referencia, GETUTCDATE())
                """)
                
                db.session.execute(movimiento_query, {
                    'id_lote': id_lote,
                    'cantidad': cantidad_consumir_lote,
                    'referencia': referencia or ''
                })
                
                lotes_consumidos.append({
                    'id_lote': id_lote,
                    'cantidad_consumida': cantidad_consumir_lote,
                    'fecha_caducidad': fecha_caducidad.isoformat() if fecha_caducidad else None
                })
                
                cantidad_restante -= cantidad_consumir_lote
                logger.info(f"Consumo de lote {id_lote}: {cantidad_consumir_lote} unidades")
            
            if cantidad_restante > 0:
                db.session.rollback()
                return False, [], f"Stock insuficiente: faltaron {cantidad_restante} unidades"
            
            db.session.flush()
            return True, lotes_consumidos, None
        
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"Error de integridad en consumo de insumo: {str(e)}")
            return False, [], f"Error de integridad: {str(e)}"
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al consumir insumo: {str(e)}")
            return False, [], f"Error al consumir insumo: {str(e)}"
    
    
    @staticmethod
    def obtener_insumos_de_producto(producto_id: int) -> list:
        """
        Obtiene lista de insumos requeridos para un producto
        Lee de ProductoReceta
        
        Returns:
            list: [{insumo_id, cantidad_requerida}, ...]
        """
        db = get_db_session()
        try:
            query = text("""
                SELECT insumo_id, cantidad
                FROM catalogos.ProductoRecetaItem pri
                JOIN catalogos.ProductoReceta pr ON pri.receta_id = pr.id_receta
                WHERE pr.producto_id = :prod_id AND pr.es_activa = 1
            """)
            
            resultado = db.session.execute(query, {'prod_id': producto_id}).fetchall()
            
            return [
                {
                    'insumo_id': row[0],
                    'cantidad_requerida': row[1]
                }
                for row in resultado
            ]
        
        except Exception as e:
            logger.error(f"Error al obtener insumos: {str(e)}")
            return []
    
    
    @staticmethod
    def obtener_productos_de_combo(combo_id: int) -> list:
        """
        Resuelve un Combo a sus Productos constituyentes
        Cascada: Combo → ComboProducto → Producto (para cada uno obtener receta)
        
        Args:
            combo_id: ID del Combo
        
        Returns:
            list: [{producto_id, cantidad_en_combo}, ...]
        """
        db = get_db_session()
        try:
            query = text("""
                SELECT cp.producto_id, cp.cantidad
                FROM catalogos.ComboProducto cp
                WHERE cp.combo_id = :combo_id
            """)
            
            resultado = db.session.execute(query, {'combo_id': combo_id}).fetchall()
            
            return [
                {
                    'producto_id': row[0],
                    'cantidad_en_combo': row[1]
                }
                for row in resultado
            ]
        
        except Exception as e:
            logger.error(f"Error al obtener productos del combo: {str(e)}")
            return []
    
    
    @staticmethod
    def calcular_insumos_necesarios_combo(combo_id: int, cantidad_pedido: int = 1) -> dict:
        """
        Calcula TODOS los insumos necesarios para un Combo
        
        Flujo:
            1. Obtener productos del combo (ComboProducto)
            2. Para cada producto, obtener sus insumos (ProductoRecetaItem)
            3. Multiplicar cantidades: insumo_cantidad * producto_cantidad_en_combo * cantidad_pedido
            4. Retornar diccionario: {insumo_id: cantidad_total_necesaria}
        
        Args:
            combo_id: ID del Combo
            cantidad_pedido: Cantidad de combos pedidos (en PedidoItem.cantidad)
        
        Returns:
            dict: {insumo_id: cantidad_total, ...} O {} si error/combo no existe
        """
        db = get_db_session()
        try:
            # Query integral: Combo → Productos → Insumos
            query = text("""
                SELECT pri.insumo_id, 
                       SUM(pri.cantidad * cp.cantidad * :cant_pedido) as cantidad_necesaria
                FROM catalogos.ComboProducto cp
                JOIN catalogos.Producto p ON cp.producto_id = p.id_producto
                JOIN catalogos.ProductoReceta pr ON p.id_producto = pr.producto_id AND pr.es_activa = 1
                JOIN catalogos.ProductoRecetaItem pri ON pr.id_receta = pri.receta_id
                WHERE cp.combo_id = :combo_id
                GROUP BY pri.insumo_id
            """)
            
            resultado = db.session.execute(query, {
                'combo_id': combo_id,
                'cant_pedido': cantidad_pedido
            }).fetchall()
            
            insumos_dict = {
                row[0]: row[1]  # insumo_id: cantidad_total
                for row in resultado
            }
            
            logger.info(f"Combo {combo_id} resuelve a {len(insumos_dict)} insumos diferentes")
            return insumos_dict
        
        except Exception as e:
            logger.error(f"Error al calcular insumos del combo: {str(e)}")
            return {}
    
    
    @staticmethod
    def registrar_movimiento(id_lote: int, tipo_movimiento: str, cantidad: int, 
                            referencia: str = None) -> dict:
        """
        Registra un movimiento de inventario para auditoría
        
        Args:
            id_lote: ID del lote
            tipo_movimiento: RECEPCION, CONSUMO, AJUSTE, RECHAZO
            cantidad: Cantidad del movimiento
            referencia: Referencia externa (pedido_id, etc)
        
        Returns:
            dict: {id_movimiento, created_at}
        """
        db = get_db_session()
        try:
            query = text("""
                INSERT INTO inventario.Movimiento 
                (id_lote, tipo_movimiento, cantidad, referencia, created_at)
                VALUES (:id_lote, :tipo, :cantidad, :referencia, GETUTCDATE())
            """)
            
            result = db.session.execute(query, {
                'id_lote': id_lote,
                'tipo': tipo_movimiento,
                'cantidad': cantidad,
                'referencia': referencia or ''
            })
            
            db.session.flush()
            
            # Obtener el ID generado
            select_query = text("""
                SELECT TOP 1 id_movimiento, created_at 
                FROM inventario.Movimiento 
                ORDER BY id_movimiento DESC
            """)
            
            row = db.session.execute(select_query).first()
            
            logger.info(f"Movimiento registrado: lote={id_lote}, tipo={tipo_movimiento}, cant={cantidad}")
            
            return {
                'id_movimiento': row[0] if row else None,
                'created_at': row[1].isoformat() if row and row[1] else None
            }
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al registrar movimiento: {str(e)}")
            raise
    
    
    @staticmethod
    def obtener_disponibilidad_por_lote(producto_id: int, sucursal_id: int) -> list:
        """
        Obtiene desglose de disponibilidad por lote FIFO
        Útil para reporting y debugging
        
        Returns:
            list: [{id_lote, cantidad_disponible, fecha_caducidad}, ...]
        """
        db = get_db_session()
        try:
            query = text("""
                SELECT l.id_lote, e.cantidad_disponible, l.fecha_caducidad
                FROM inventario.Lote l
                JOIN inventario.Existencia e ON l.id_lote = e.id_lote
                WHERE e.producto_id = :prod_id 
                  AND e.sucursal_id = :suc_id
                  AND l.cantidad_disponible > 0
                ORDER BY l.fecha_caducidad ASC, l.id_lote ASC
            """)
            
            resultado = db.session.execute(query, {
                'prod_id': producto_id,
                'suc_id': sucursal_id
            }).fetchall()
            
            return [
                {
                    'id_lote': row[0],
                    'cantidad_disponible': row[1],
                    'fecha_caducidad': row[2].isoformat() if row[2] else None
                }
                for row in resultado
            ]
        
        except Exception as e:
            logger.error(f"Error al obtener disponibilidad: {str(e)}")
            return []
    
    
    @staticmethod
    def obtener_existencia_total(producto_id: int, sucursal_id: int) -> int:
        """
        Obtiene cantidad total disponible de un producto en una sucursal
        
        Returns:
            int: Total disponible
        """
        db = get_db_session()
        try:
            query = text("""
                SELECT ISNULL(SUM(cantidad_disponible), 0)
                FROM inventario.Existencia
                WHERE producto_id = :prod_id 
                  AND sucursal_id = :suc_id
            """)
            
            result = db.session.execute(query, {
                'prod_id': producto_id,
                'suc_id': sucursal_id
            }).first()
            
            return int(result[0]) if result else 0
        
        except Exception as e:
            logger.error(f"Error al obtener existencia total: {str(e)}")
            return 0

