"""
PedidoItemDAO - Data Access Object para operaciones.PedidoItem
Gestión de items (productos/combos) dentro de pedidos

Sistema de estados (estatus_detalle):
- 1: EnCocina (en preparación, inventario ya consumido)
- 2: Listo (preparado)
- 3: Completo (servido/entregado)
- 4: Cancelado
- 5: Pagado

IMPORTANTE: Los items se crean directamente en estatus 1 (EnCocina) y el
inventario se consume inmediatamente al agregar el item.
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import and_
from src.models.operaciones.pedido_item_model import PedidoItem
from src.models.catalogos.producto_model import Producto
from src.models.catalogos.combo_model import Combo
from src.dao.inventario.inventario_dao import InventarioDAO
from src.core.db.session_manager import get_db_session
import logging

logger = logging.getLogger(__name__)

# Constantes de estatus
ESTATUS_EN_COCINA = 1   # Estado inicial de items, inventario consumido
ESTATUS_LISTO = 2       # Preparado por cocina
ESTATUS_COMPLETO = 3    # Entregado
ESTATUS_CANCELADO = 4   # Cancelado
ESTATUS_PAGADO = 5      # Pagado


class PedidoItemDAO:
    """Data Access Object para PedidoItem"""
    
    @staticmethod
    def agregar_item(
        pedido_id: int,
        cantidad: int,
        sucursal_id: int,
        usuario_id: int = None,
        precio_unit: Decimal = None,
        producto_id: int = None,
        combo_id: int = None,
        notas: str = None
    ) -> dict:
        """
        Agregar item (producto o combo) a un pedido.
        - Los items se crean directamente en estatus_detalle=1 (EnCocina)
        - El inventario se consume inmediatamente (FIFO por lotes)
        - Si no se proporciona precio_unit, se obtiene del catálogo
        
        Args:
            pedido_id: ID del pedido
            cantidad: Cantidad
            sucursal_id: ID de sucursal (para consumo de inventario)
            usuario_id: ID del usuario (para registro de movimiento)
            precio_unit: Precio unitario (opcional, se obtiene del catálogo si no se envía)
            producto_id: ID del producto (si es producto)
            combo_id: ID del combo (si es combo)
            notas: Notas del item
            
        Returns:
            Dict del item creado con detalle de consumo de inventario
        """
        with get_db_session() as session:
            # Validar que sea producto O combo, no ambos
            if not producto_id and not combo_id:
                raise ValueError("Debe especificar producto_id O combo_id")
            if producto_id and combo_id:
                raise ValueError("No puede especificar ambos producto_id y combo_id")
            
            # Si no se proporciona precio_unit, obtenerlo del catálogo
            if precio_unit is None:
                if producto_id:
                    producto = session.query(Producto).filter(
                        Producto.id_producto == producto_id
                    ).first()
                    if not producto:
                        raise ValueError(f"Producto {producto_id} no existe")
                    if not producto.es_activo:
                        raise ValueError(f"Producto {producto_id} no está activo")
                    precio_unit = Decimal(str(producto.precio))
                    logger.info(f"Precio obtenido de Producto {producto_id}: {precio_unit}")
                elif combo_id:
                    combo = session.query(Combo).filter(
                        Combo.id_combo == combo_id
                    ).first()
                    if not combo:
                        raise ValueError(f"Combo {combo_id} no existe")
                    if not combo.es_activo:
                        raise ValueError(f"Combo {combo_id} no está activo")
                    precio_unit = Decimal(str(combo.precio))
                    logger.info(f"Precio obtenido de Combo {combo_id}: {precio_unit}")
            
            # Crear item con estatus_detalle=1 (EnCocina)
            item = PedidoItem(
                pedido_id=pedido_id,
                producto_id=producto_id,
                combo_id=combo_id,
                cantidad=cantidad,
                precio_unit=precio_unit,
                estatus_detalle=ESTATUS_EN_COCINA,  # 1 = EnCocina (directo)
                notas=notas
            )
            session.add(item)
            session.flush()  # Para obtener el ID
            
            item_id = item.id_pedido_item
            logger.info(f"Item {item_id} creado en sesión, procediendo a consumir inventario")
            
        # Consumir inventario (fuera de la sesión del item para evitar conflictos de transacción)
        detalle_consumo = None
        consumo_exitoso = False
        error_consumo = None
        
        try:
            exito, detalle_consumo, error = InventarioDAO.consumir_item_pedido(
                item_id=item_id,
                pedido_id=pedido_id,
                producto_id=producto_id,
                combo_id=combo_id,
                cantidad=cantidad,
                sucursal_id=sucursal_id,
                usuario_id=usuario_id
            )
            
            if not exito:
                error_consumo = error
                logger.error(f"Error consumiendo inventario para item {item_id}: {error}")
            else:
                consumo_exitoso = True
                if detalle_consumo:
                    logger.info(f"Inventario consumido para item {item_id}: {len(detalle_consumo)} insumos")
                else:
                    logger.warning(f"Item {item_id} no tiene insumos configurados - no se consumió inventario")
        except Exception as e:
            error_consumo = str(e)
            logger.error(f"Excepción al consumir inventario para item {item_id}: {str(e)}")
        
        # Obtener item actualizado
        with get_db_session() as session:
            item = session.query(PedidoItem).filter(
                PedidoItem.id_pedido_item == item_id
            ).first()
            
            result = PedidoItemDAO._serializar_item(item)
            result['inventario_consumido'] = detalle_consumo
            result['consumo_exitoso'] = consumo_exitoso
            if error_consumo:
                result['error_consumo'] = error_consumo
            
            logger.info(f"Item {item_id} agregado a pedido {pedido_id} en EnCocina, precio={precio_unit}, consumo_exitoso={consumo_exitoso}")
            return result
    
    
    @staticmethod
    def obtener_item_por_id(item_id: int) -> dict:
        """
        Obtener item por ID.
        
        Args:
            item_id: ID del item
            
        Returns:
            Dict del item o None
        """
        with get_db_session() as session:
            item = session.query(PedidoItem).filter(
                PedidoItem.id_pedido_item == item_id
            ).first()
            
            return PedidoItemDAO._serializar_item(item) if item else None
    
    
    @staticmethod
    def listar_items_pedido(pedido_id: int, estatus_detalle: int = None) -> list:
        """
        Listar items de un pedido.
        
        Args:
            pedido_id: ID del pedido
            estatus_detalle: Filtrar por estatus (opcional)
            
        Returns:
            Lista de items
        """
        with get_db_session() as session:
            query = session.query(PedidoItem).filter(
                PedidoItem.pedido_id == pedido_id
            )
            
            if estatus_detalle is not None:
                query = query.filter(PedidoItem.estatus_detalle == estatus_detalle)
            
            items = query.order_by(PedidoItem.created_at.asc()).all()
            return [PedidoItemDAO._serializar_item(item) for item in items]
    
    
    @staticmethod
    def listar_items_en_cocina(pedido_id: int) -> list:
        """
        Listar items de un pedido que están en cocina.
        
        Args:
            pedido_id: ID del pedido
            
        Returns:
            Lista de items en cocina (estatus_detalle=1)
        """
        with get_db_session() as session:
            items = session.query(PedidoItem).filter(
                and_(
                    PedidoItem.pedido_id == pedido_id,
                    PedidoItem.estatus_detalle == ESTATUS_EN_COCINA  # 1 = EnCocina
                )
            ).order_by(PedidoItem.created_at.asc()).all()
            
            return [PedidoItemDAO._serializar_item(item) for item in items]
    
    
    @staticmethod
    def cambiar_estatus_item(item_id: int, nuevo_estatus: int) -> dict:
        """
        Cambiar estatus de un item.
        Estados: 0=Iniciado, 1=EnCocina, 2=Listo, 3=Completo, 4=Cancelado, 5=Pagado
        
        Args:
            item_id: ID del item
            nuevo_estatus: Nuevo estatus
            
        Returns:
            Dict actualizado o None
        """
        with get_db_session() as session:
            item = session.query(PedidoItem).filter(
                PedidoItem.id_pedido_item == item_id
            ).first()
            
            if not item:
                return None
            
            item.estatus_detalle = nuevo_estatus
            item.updated_at = datetime.now()
            session.commit()
            logger.info(f"Item {item_id} cambió a estatus_detalle {nuevo_estatus}")
            return PedidoItemDAO._serializar_item(item)
    
    
    @staticmethod
    def cambiar_estatus_items_multiplos(item_ids: list, nuevo_estatus: int) -> int:
        """
        Cambiar estatus a múltiples items de una vez.
        
        Args:
            item_ids: Lista de IDs de items
            nuevo_estatus: Nuevo estatus para todos
            
        Returns:
            Cantidad de items actualizados
        """
        with get_db_session() as session:
            result = session.query(PedidoItem).filter(
                PedidoItem.id_pedido_item.in_(item_ids)
            ).update(
                {
                    'estatus_detalle': nuevo_estatus,
                    'updated_at': datetime.now()
                },
                synchronize_session=False
            )
            session.commit()
            logger.info(f"{result} items actualizados a estatus_detalle {nuevo_estatus}")
            return result
    
    
    @staticmethod
    def obtener_total_items_pedido(pedido_id: int, solo_confirmados: bool = False) -> Decimal:
        """
        Obtener total de items de un pedido.
        
        Args:
            pedido_id: ID del pedido
            solo_confirmados: Si True, solo items en cocina o más (estatus_detalle >= 1)
            
        Returns:
            Total en Decimal
        """
        with get_db_session() as session:
            query = session.query(PedidoItem).filter(
                PedidoItem.pedido_id == pedido_id
            )
            
            if solo_confirmados:
                query = query.filter(PedidoItem.estatus_detalle >= ESTATUS_EN_COCINA)
            
            items = query.all()
            
            total = Decimal('0.00')
            for item in items:
                total += Decimal(str(item.precio_unit)) * Decimal(str(item.cantidad))
            
            return total
    
    
    @staticmethod
    def existe_item_agregado_no_confirmado(pedido_id: int) -> bool:
        """
        Verificar si hay items agregados pero no enviados a cocina.
        
        Args:
            pedido_id: ID del pedido
            
        Returns:
            True si hay items no confirmados (estatus_detalle = 0)
        """
        with get_db_session() as session:
            existe = session.query(PedidoItem).filter(
                and_(
                    PedidoItem.pedido_id == pedido_id,
                    PedidoItem.estatus_detalle == ESTATUS_INICIADO  # 0 = Iniciado
                )
            ).first()
            
            return existe is not None
    
    
    @staticmethod
    def item_existe(item_id: int) -> bool:
        """
        Verificar si un item existe.
        
        Args:
            item_id: ID del item
            
        Returns:
            True si existe
        """
        with get_db_session() as session:
            existe = session.query(PedidoItem).filter(
                PedidoItem.id_pedido_item == item_id
            ).first()
            return existe is not None
    
    
    @staticmethod
    def verificar_todos_listos(pedido_id: int) -> bool:
        """
        Verificar si todos los items de un pedido están en estado Listo o superior.
        Excluye items cancelados. Útil para auto-completar pedidos para llevar.
        
        Args:
            pedido_id: ID del pedido
            
        Returns:
            True si todos los items activos están listos (estatus_detalle >= 2)
        """
        with get_db_session() as session:
            # Contar items activos (no cancelados)
            total_activos = session.query(PedidoItem).filter(
                and_(
                    PedidoItem.pedido_id == pedido_id,
                    PedidoItem.estatus_detalle != ESTATUS_CANCELADO  # 4 = Cancelado
                )
            ).count()
            
            if total_activos == 0:
                return False  # No hay items activos
            
            # Contar items listos o en estado superior (2, 3, 5)
            items_listos = session.query(PedidoItem).filter(
                and_(
                    PedidoItem.pedido_id == pedido_id,
                    PedidoItem.estatus_detalle >= ESTATUS_LISTO,  # >= 2 (Listo, Completo, Pagado)
                    PedidoItem.estatus_detalle != ESTATUS_CANCELADO  # No cancelados
                )
            ).count()
            
            return items_listos == total_activos
    
    
    @staticmethod
    def listar_items_por_estatus(pedido_id: int, estatus_list: list) -> list:
        """
        Listar items de un pedido por múltiples estados.
        
        Args:
            pedido_id: ID del pedido
            estatus_list: Lista de estados a filtrar
            
        Returns:
            Lista de items
        """
        with get_db_session() as session:
            items = session.query(PedidoItem).filter(
                and_(
                    PedidoItem.pedido_id == pedido_id,
                    PedidoItem.estatus_detalle.in_(estatus_list)
                )
            ).order_by(PedidoItem.created_at.asc()).all()
            
            return [PedidoItemDAO._serializar_item(item) for item in items]
    
    
    @staticmethod
    def _serializar_item(item) -> dict:
        """Helper para serializar item"""
        if not item:
            return None
        
        # Mapa de estados para display
        estatus_map = {
            0: 'Iniciado',
            1: 'EnCocina',
            2: 'Listo',
            3: 'Completo',
            4: 'Cancelado',
            5: 'Pagado'
        }
        
        return {
            'id_pedido_item': item.id_pedido_item,
            'pedido_id': item.pedido_id,
            'producto_id': item.producto_id,
            'combo_id': item.combo_id,
            'cantidad': item.cantidad,
            'precio_unit': float(item.precio_unit),
            'estatus_detalle': item.estatus_detalle,
            'estatus_nombre': estatus_map.get(item.estatus_detalle, 'Desconocido'),
            'notas': item.notas,
            'created_at': item.created_at.isoformat() if item.created_at else None,
            'updated_at': item.updated_at.isoformat() if item.updated_at else None
        }
