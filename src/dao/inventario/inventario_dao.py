"""
InventarioDAO - Data Access Object para gestión de inventario
Maneja consumo de insumos por lotes con lógica FIFO y cascada

Esquema de tablas:
- inventario.Existencia: sucursal_id, insumo_id, cantidad (agregado por sucursal)
- inventario.Lote: det_recepcion_id, cantidad_inicial, cantidad_disponible, fecha_caducidad
- inventario.Movimiento: sucursal_id, insumo_id, lote_id, tipo_mov (1=Entrada, 2=Salida), 
                         motivo (1=Recepción, 2=Pedido, 3=Merma), pedido_id

Inventory descent happens when PedidoItem.estatus_detalle → 1 (EnCocina)
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import and_, or_, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from src.models.inventario.existencia_model import Existencia
from src.models.inventario.lote_model import Lote
from src.models.inventario.movimiento_model import Movimiento
from src.models.catalogos.producto_receta_model import ProductoReceta
from src.models.catalogos.producto_receta_item_model import ProductoRecetaItem
from src.core.db.session_manager import get_db_session
import logging

logger = logging.getLogger(__name__)

# Constantes de tipo_mov
TIPO_MOV_ENTRADA = 1
TIPO_MOV_SALIDA = 2

# Constantes de motivo
MOTIVO_RECEPCION = 1
MOTIVO_PEDIDO = 2
MOTIVO_MERMA = 3


class InventarioDAO:
    """DAO para gestión de inventario con consumo por lotes"""
    
    @staticmethod
    def verificar_stock_suficiente(insumo_id: int, cantidad_necesaria: Decimal, sucursal_id: int) -> tuple:
        """
        Verifica si hay stock suficiente de un insumo en una sucursal.
        
        Args:
            insumo_id: ID del insumo
            cantidad_necesaria: Cantidad a consumir (unidad base)
            sucursal_id: ID de sucursal
        
        Returns:
            tuple: (hay_stock: bool, cantidad_disponible: Decimal, error_msg: str|None)
        """
        with get_db_session() as session:
            try:
                # Obtener existencia de Existencia (agregado por sucursal+insumo)
                existencia = session.query(Existencia).filter(
                    and_(
                        Existencia.insumo_id == insumo_id,
                        Existencia.sucursal_id == sucursal_id
                    )
                ).first()
                
                cantidad_disponible = Decimal(str(existencia.cantidad)) if existencia else Decimal('0')
                
                if cantidad_disponible >= cantidad_necesaria:
                    return True, cantidad_disponible, None
                else:
                    return False, cantidad_disponible, f"Stock insuficiente de insumo {insumo_id}: disponible {cantidad_disponible}, requerido {cantidad_necesaria}"
            
            except Exception as e:
                logger.error(f"Error al verificar stock: {str(e)}")
                return False, Decimal('0'), f"Error al verificar stock: {str(e)}"
    
    
    @staticmethod
    def consumir_insumo_por_lotes(
        insumo_id: int, 
        cantidad_a_consumir: Decimal, 
        sucursal_id: int, 
        pedido_id: int = None,
        usuario_id: int = None
    ) -> tuple:
        """
        Consume insumo siguiendo FIFO por fecha_caducidad.
        Cascada automática: si lote actual no tiene suficiente, usa el siguiente.
        
        Args:
            insumo_id: ID del insumo a consumir
            cantidad_a_consumir: Cantidad total a consumir (unidad base)
            sucursal_id: ID de sucursal
            pedido_id: ID del pedido que origina el consumo
            usuario_id: ID del usuario que realiza la operación
        
        Returns:
            tuple: (éxito: bool, lotes_consumidos: list, error_msg: str|None)
        
        Lógica FIFO:
            1. Obtener lotes del insumo ordenados por fecha_caducidad (NULL al final)
            2. Para cada lote en orden:
               - Consumir min(cantidad_restante, lote.cantidad_disponible)
               - UPDATE Lote.cantidad_disponible
               - UPDATE Existencia.cantidad
               - INSERT Movimiento (tipo_mov=2, motivo=2)
            3. Si cantidad_restante > 0 al final, retornar error
        """
        with get_db_session() as session:
            try:
                cantidad_restante = Decimal(str(cantidad_a_consumir))
                
                # Obtener lotes del insumo para la sucursal
                # Los lotes se conectan via: Lote → RecepcionDetalle → Recepcion → Compra (tiene sucursal_id)
                query = text("""
                    SELECT l.id_lote, l.cantidad_disponible, l.fecha_caducidad, rd.insumo_id
                    FROM inventario.Lote l
                    JOIN inventario.RecepcionDetalle rd ON l.det_recepcion_id = rd.id_recepcion_det
                    JOIN inventario.Recepcion r ON rd.recepcion_id = r.id_recepcion
                    JOIN inventario.Compra c ON r.compra_id = c.id_compra
                    WHERE rd.insumo_id = :insumo_id 
                      AND c.sucursal_id = :sucursal_id
                      AND l.cantidad_disponible > 0
                      AND l.estado = 1
                    ORDER BY l.fecha_caducidad ASC, l.id_lote ASC
                """)
                
                lotes = session.execute(query, {
                    'insumo_id': insumo_id,
                    'sucursal_id': sucursal_id
                }).fetchall()
                
                if not lotes:
                    return False, [], f"No hay lotes disponibles para insumo {insumo_id} en sucursal {sucursal_id}"
                
                lotes_consumidos = []
                
                # Procesar cada lote en orden FIFO
                for id_lote, cant_disponible, fecha_caducidad, _ in lotes:
                    if cantidad_restante <= 0:
                        break
                    
                    cant_disponible = Decimal(str(cant_disponible))
                    
                    # Cantidad a consumir de este lote
                    cantidad_consumir_lote = min(cantidad_restante, cant_disponible)
                    
                    # Actualizar Lote.cantidad_disponible
                    lote = session.query(Lote).filter(Lote.id_lote == id_lote).first()
                    if lote:
                        lote.cantidad_disponible = lote.cantidad_disponible - cantidad_consumir_lote
                        
                        # Si se agotó el lote, cambiar estado
                        if lote.cantidad_disponible <= 0:
                            lote.estado = 2  # Agotado
                    
                    # Crear Movimiento de salida
                    movimiento = Movimiento(
                        sucursal_id=sucursal_id,
                        insumo_id=insumo_id,
                        lote_id=id_lote,
                        tipo_mov=TIPO_MOV_SALIDA,  # 2 = Salida
                        motivo=MOTIVO_PEDIDO,  # 2 = Pedido
                        cantidad=cantidad_consumir_lote,
                        pedido_id=pedido_id,
                        det_recepcion_id=None,
                        compra_id=None,
                        merma_id=None,
                        usuario_id=usuario_id
                    )
                    session.add(movimiento)
                    
                    lotes_consumidos.append({
                        'id_lote': id_lote,
                        'cantidad_consumida': float(cantidad_consumir_lote),
                        'fecha_caducidad': fecha_caducidad.isoformat() if fecha_caducidad else None
                    })
                    
                    cantidad_restante -= cantidad_consumir_lote
                    logger.info(f"Consumo de lote {id_lote}: {cantidad_consumir_lote} unidades de insumo {insumo_id}")
                
                if cantidad_restante > 0:
                    session.rollback()
                    return False, [], f"Stock insuficiente de insumo {insumo_id}: faltaron {cantidad_restante} unidades"
                
                # Actualizar Existencia agregada
                existencia = session.query(Existencia).filter(
                    and_(
                        Existencia.insumo_id == insumo_id,
                        Existencia.sucursal_id == sucursal_id
                    )
                ).first()
                
                if existencia:
                    existencia.cantidad = existencia.cantidad - cantidad_a_consumir
                    existencia.updated_at = datetime.utcnow()
                
                session.commit()
                return True, lotes_consumidos, None
            
            except IntegrityError as e:
                session.rollback()
                logger.error(f"Error de integridad en consumo de insumo: {str(e)}")
                return False, [], f"Error de integridad: {str(e)}"
            except Exception as e:
                session.rollback()
                logger.error(f"Error al consumir insumo: {str(e)}")
                return False, [], f"Error al consumir insumo: {str(e)}"
    
    
    @staticmethod
    def obtener_insumos_de_producto(producto_id: int) -> list:
        """
        Obtiene lista de insumos requeridos para un producto.
        Lee de ProductoReceta → ProductoRecetaItem.
        
        Args:
            producto_id: ID del producto
        
        Returns:
            list: [{'insumo_id': int, 'cantidad_requerida': Decimal}, ...]
        """
        with get_db_session() as session:
            try:
                # Buscar receta activa del producto
                receta = session.query(ProductoReceta).filter(
                    and_(
                        ProductoReceta.producto_id == producto_id,
                        ProductoReceta.es_activa == True
                    )
                ).first()
                
                if not receta:
                    logger.warning(f"Producto {producto_id} no tiene receta activa")
                    return []
                
                # Obtener items de la receta
                items = session.query(ProductoRecetaItem).filter(
                    ProductoRecetaItem.receta_id == receta.id_receta
                ).all()
                
                return [
                    {
                        'insumo_id': item.insumo_id,
                        'cantidad_requerida': Decimal(str(item.cantidad))
                    }
                    for item in items
                ]
            
            except Exception as e:
                logger.error(f"Error al obtener insumos de producto {producto_id}: {str(e)}")
                return []
    
    
    @staticmethod
    def obtener_productos_de_combo(combo_id: int) -> list:
        """
        Resuelve un Combo a sus Productos constituyentes.
        
        Args:
            combo_id: ID del Combo
        
        Returns:
            list: [{'producto_id': int, 'cantidad_en_combo': int}, ...]
        """
        with get_db_session() as session:
            try:
                query = text("""
                    SELECT cp.producto_id, cp.cantidad
                    FROM catalogos.ComboProducto cp
                    WHERE cp.combo_id = :combo_id
                """)
                
                resultado = session.execute(query, {'combo_id': combo_id}).fetchall()
                
                return [
                    {
                        'producto_id': row[0],
                        'cantidad_en_combo': row[1]
                    }
                    for row in resultado
                ]
            
            except Exception as e:
                logger.error(f"Error al obtener productos del combo {combo_id}: {str(e)}")
                return []
    
    
    @staticmethod
    def calcular_insumos_necesarios_combo(combo_id: int, cantidad_pedido: int = 1) -> dict:
        """
        Calcula TODOS los insumos necesarios para un Combo.
        
        Flujo:
            1. Obtener productos del combo (ComboProducto)
            2. Para cada producto, obtener sus insumos (ProductoRecetaItem)
            3. Multiplicar cantidades: insumo_cantidad * producto_cantidad_en_combo * cantidad_pedido
            4. Agregar insumos repetidos
        
        Args:
            combo_id: ID del Combo
            cantidad_pedido: Cantidad de combos pedidos
        
        Returns:
            dict: {insumo_id: cantidad_total, ...} O {} si error/combo no existe
        """
        with get_db_session() as session:
            try:
                # Query integral: Combo → Productos → Insumos
                query = text("""
                    SELECT pri.insumo_id, 
                           SUM(CAST(pri.cantidad AS DECIMAL(10,2)) * cp.cantidad * :cant_pedido) as cantidad_necesaria
                    FROM catalogos.ComboProducto cp
                    JOIN catalogos.Producto p ON cp.producto_id = p.id_producto
                    JOIN catalogos.ProductoReceta pr ON p.id_producto = pr.producto_id AND pr.es_activa = 1
                    JOIN catalogos.ProductoRecetaItem pri ON pr.id_receta = pri.receta_id
                    WHERE cp.combo_id = :combo_id
                    GROUP BY pri.insumo_id
                """)
                
                resultado = session.execute(query, {
                    'combo_id': combo_id,
                    'cant_pedido': cantidad_pedido
                }).fetchall()
                
                insumos_dict = {
                    row[0]: Decimal(str(row[1]))  # insumo_id: cantidad_total
                    for row in resultado
                }
                
                logger.info(f"Combo {combo_id} x {cantidad_pedido} resuelve a {len(insumos_dict)} insumos diferentes")
                return insumos_dict
            
            except Exception as e:
                logger.error(f"Error al calcular insumos del combo {combo_id}: {str(e)}")
                return {}
    
    
    @staticmethod
    def registrar_movimiento(
        sucursal_id: int,
        insumo_id: int,
        lote_id: int,
        tipo_mov: int,
        motivo: int,
        cantidad: Decimal,
        pedido_id: int = None,
        det_recepcion_id: int = None,
        compra_id: int = None,
        merma_id: int = None,
        usuario_id: int = None
    ) -> dict:
        """
        Registra un movimiento de inventario para auditoría.
        
        Args:
            sucursal_id: ID de sucursal
            insumo_id: ID del insumo
            lote_id: ID del lote
            tipo_mov: 1=Entrada, 2=Salida
            motivo: 1=Recepción, 2=Pedido, 3=Merma
            cantidad: Cantidad del movimiento (unidad base)
            pedido_id: ID del pedido (si aplica)
            det_recepcion_id: ID del detalle de recepción (si aplica)
            compra_id: ID de compra (si aplica)
            merma_id: ID de merma (si aplica)
            usuario_id: ID del usuario
        
        Returns:
            dict: {id_movimiento, created_at}
        """
        with get_db_session() as session:
            try:
                movimiento = Movimiento(
                    sucursal_id=sucursal_id,
                    insumo_id=insumo_id,
                    lote_id=lote_id,
                    tipo_mov=tipo_mov,
                    motivo=motivo,
                    cantidad=cantidad,
                    pedido_id=pedido_id,
                    det_recepcion_id=det_recepcion_id,
                    compra_id=compra_id,
                    merma_id=merma_id,
                    usuario_id=usuario_id
                )
                session.add(movimiento)
                session.commit()
                
                logger.info(f"Movimiento registrado: sucursal={sucursal_id}, insumo={insumo_id}, tipo={tipo_mov}, motivo={motivo}, cant={cantidad}")
                
                return {
                    'id_movimiento': movimiento.id_movimiento,
                    'created_at': movimiento.created_at.isoformat() if movimiento.created_at else None
                }
            
            except Exception as e:
                session.rollback()
                logger.error(f"Error al registrar movimiento: {str(e)}")
                raise
    
    
    @staticmethod
    def obtener_disponibilidad_por_lote(insumo_id: int, sucursal_id: int) -> list:
        """
        Obtiene desglose de disponibilidad por lote FIFO.
        Útil para reporting y debugging.
        
        Args:
            insumo_id: ID del insumo
            sucursal_id: ID de la sucursal
        
        Returns:
            list: [{'id_lote': int, 'cantidad_disponible': Decimal, 'fecha_caducidad': str}, ...]
        """
        with get_db_session() as session:
            try:
                query = text("""
                    SELECT l.id_lote, l.cantidad_disponible, l.fecha_caducidad
                    FROM inventario.Lote l
                    JOIN inventario.RecepcionDetalle rd ON l.det_recepcion_id = rd.id_recepcion_det
                    JOIN inventario.Recepcion r ON rd.recepcion_id = r.id_recepcion
                    JOIN inventario.Compra c ON r.compra_id = c.id_compra
                    WHERE rd.insumo_id = :insumo_id 
                      AND c.sucursal_id = :sucursal_id
                      AND l.cantidad_disponible > 0
                      AND l.estado = 1
                    ORDER BY l.fecha_caducidad ASC, l.id_lote ASC
                """)
                
                resultado = session.execute(query, {
                    'insumo_id': insumo_id,
                    'sucursal_id': sucursal_id
                }).fetchall()
                
                return [
                    {
                        'id_lote': row[0],
                        'cantidad_disponible': float(row[1]) if row[1] else 0,
                        'fecha_caducidad': row[2].isoformat() if row[2] else None
                    }
                    for row in resultado
                ]
            
            except Exception as e:
                logger.error(f"Error al obtener disponibilidad de insumo {insumo_id}: {str(e)}")
                return []
    
    
    @staticmethod
    def obtener_existencia_total(insumo_id: int, sucursal_id: int) -> Decimal:
        """
        Obtiene cantidad total disponible de un insumo en una sucursal.
        
        Args:
            insumo_id: ID del insumo
            sucursal_id: ID de la sucursal
        
        Returns:
            Decimal: Total disponible
        """
        with get_db_session() as session:
            try:
                existencia = session.query(Existencia).filter(
                    and_(
                        Existencia.insumo_id == insumo_id,
                        Existencia.sucursal_id == sucursal_id
                    )
                ).first()
                
                return Decimal(str(existencia.cantidad)) if existencia else Decimal('0')
            
            except Exception as e:
                logger.error(f"Error al obtener existencia total de insumo {insumo_id}: {str(e)}")
                return Decimal('0')
    
    
    @staticmethod
    def consumir_item_pedido(
        item_id: int,
        pedido_id: int,
        producto_id: int,
        combo_id: int,
        cantidad: int,
        sucursal_id: int,
        usuario_id: int = None
    ) -> tuple:
        """
        Consume inventario para un PedidoItem completo.
        Resuelve producto/combo a sus insumos y consume de cada uno.
        
        Este es el método principal a llamar cuando un item pasa a EnCocina.
        
        Args:
            item_id: ID del PedidoItem
            pedido_id: ID del Pedido
            producto_id: ID del producto (si es producto)
            combo_id: ID del combo (si es combo)
            cantidad: Cantidad de unidades pedidas
            sucursal_id: ID de sucursal
            usuario_id: ID del usuario
        
        Returns:
            tuple: (éxito: bool, detalle_consumo: list, error_msg: str|None)
        """
        try:
            insumos_a_consumir = {}  # {insumo_id: cantidad_total}
            
            if combo_id:
                # Combo: resolver a insumos
                insumos_a_consumir = InventarioDAO.calcular_insumos_necesarios_combo(combo_id, cantidad)
            elif producto_id:
                # Producto: obtener insumos de receta
                insumos_receta = InventarioDAO.obtener_insumos_de_producto(producto_id)
                for item in insumos_receta:
                    insumo_id = item['insumo_id']
                    cantidad_req = item['cantidad_requerida'] * cantidad
                    insumos_a_consumir[insumo_id] = insumos_a_consumir.get(insumo_id, Decimal('0')) + cantidad_req
            
            if not insumos_a_consumir:
                logger.warning(f"Item {item_id} no tiene insumos a consumir")
                return True, [], None  # No hay consumo pero no es error
            
            # Verificar stock de todos los insumos primero
            for insumo_id, cantidad_req in insumos_a_consumir.items():
                hay_stock, disponible, error = InventarioDAO.verificar_stock_suficiente(
                    insumo_id, cantidad_req, sucursal_id
                )
                if not hay_stock:
                    return False, [], error
            
            # Consumir cada insumo
            detalle_consumo = []
            for insumo_id, cantidad_req in insumos_a_consumir.items():
                exito, lotes, error = InventarioDAO.consumir_insumo_por_lotes(
                    insumo_id=insumo_id,
                    cantidad_a_consumir=cantidad_req,
                    sucursal_id=sucursal_id,
                    pedido_id=pedido_id,
                    usuario_id=usuario_id
                )
                
                if not exito:
                    logger.error(f"Error consumiendo insumo {insumo_id} para item {item_id}: {error}")
                    return False, [], error
                
                detalle_consumo.append({
                    'insumo_id': insumo_id,
                    'cantidad_consumida': float(cantidad_req),
                    'lotes': lotes
                })
            
            logger.info(f"Item {item_id} consumió {len(detalle_consumo)} insumos diferentes")
            return True, detalle_consumo, None
        
        except Exception as e:
            logger.error(f"Error consumiendo item {item_id}: {str(e)}")
            return False, [], f"Error en consumo: {str(e)}"

