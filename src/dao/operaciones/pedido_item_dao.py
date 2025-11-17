"""
PedidoItemDAO - Data Access Object para operaciones.PedidoItem
Gestión de items (productos/combos) dentro de pedidos
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import and_
from src.models.operaciones.pedido_item_model import PedidoItem
from src.core.db.session_manager import get_db_session
import logging

logger = logging.getLogger(__name__)


class PedidoItemDAO:
    """Data Access Object para PedidoItem"""
    
    @staticmethod
    def agregar_item(
        pedido_id: int,
        cantidad: int,
        precio_unit: Decimal,
        producto_id: int = None,
        combo_id: int = None,
        notas: str = None
    ) -> dict:
        """
        Agregar item (producto o combo) a un pedido.
        
        Args:
            pedido_id: ID del pedido
            cantidad: Cantidad
            precio_unit: Precio unitario
            producto_id: ID del producto (si es producto)
            combo_id: ID del combo (si es combo)
            notas: Notas del item
            
        Returns:
            Dict del item creado
        """
        with get_db_session() as session:
            # Validar que sea producto O combo, no ambos
            if not producto_id and not combo_id:
                raise ValueError("Debe especificar producto_id O combo_id")
            if producto_id and combo_id:
                raise ValueError("No puede especificar ambos producto_id y combo_id")
            
            item = PedidoItem(
                pedido_id=pedido_id,
                producto_id=producto_id,
                combo_id=combo_id,
                cantidad=cantidad,
                precio_unit=precio_unit,
                estatus=1,  # Agregado
                notas=notas
            )
            session.add(item)
            session.flush()
            session.commit()
            logger.info(f"Item agregado: ID {item.id_pedido_item} a pedido {pedido_id}")
            return PedidoItemDAO._serializar_item(item)
    
    
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
    def listar_items_pedido(pedido_id: int, estatus: int = None) -> list:
        """
        Listar items de un pedido.
        
        Args:
            pedido_id: ID del pedido
            estatus: Filtrar por estatus (opcional)
            
        Returns:
            Lista de items
        """
        with get_db_session() as session:
            query = session.query(PedidoItem).filter(
                PedidoItem.pedido_id == pedido_id
            )
            
            if estatus:
                query = query.filter(PedidoItem.estatus == estatus)
            
            items = query.order_by(PedidoItem.created_at.asc()).all()
            return [PedidoItemDAO._serializar_item(item) for item in items]
    
    
    @staticmethod
    def listar_items_en_cocina(pedido_id: int) -> list:
        """
        Listar items de un pedido que están en cocina.
        
        Args:
            pedido_id: ID del pedido
            
        Returns:
            Lista de items en cocina (estatus=3)
        """
        with get_db_session() as session:
            items = session.query(PedidoItem).filter(
                and_(
                    PedidoItem.pedido_id == pedido_id,
                    PedidoItem.estatus == 3  # En cocina
                )
            ).order_by(PedidoItem.created_at.asc()).all()
            
            return [PedidoItemDAO._serializar_item(item) for item in items]
    
    
    @staticmethod
    def cambiar_estatus_item(item_id: int, nuevo_estatus: int) -> dict:
        """
        Cambiar estatus de un item.
        Estados: 1=Agregado, 2=Confirmado, 3=EnCocina, 4=Listo, 5=Servido
        
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
            
            item.estatus = nuevo_estatus
            item.updated_at = datetime.now()
            session.commit()
            logger.info(f"Item {item_id} cambió a estatus {nuevo_estatus}")
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
                    'estatus': nuevo_estatus,
                    'updated_at': datetime.now()
                },
                synchronize_session=False
            )
            session.commit()
            logger.info(f"{result} items actualizados a estatus {nuevo_estatus}")
            return result
    
    
    @staticmethod
    def obtener_total_items_pedido(pedido_id: int, solo_confirmados: bool = False) -> Decimal:
        """
        Obtener total de items de un pedido.
        
        Args:
            pedido_id: ID del pedido
            solo_confirmados: Si True, solo items en cocina o más (estatus >= 3)
            
        Returns:
            Total en Decimal
        """
        with get_db_session() as session:
            query = session.query(PedidoItem).filter(
                PedidoItem.pedido_id == pedido_id
            )
            
            if solo_confirmados:
                query = query.filter(PedidoItem.estatus >= 3)  # Confirmados en adelante
            
            items = query.all()
            
            total = Decimal('0.00')
            for item in items:
                total += Decimal(str(item.precio_unit)) * Decimal(str(item.cantidad))
            
            return total
    
    
    @staticmethod
    def existe_item_agregado_no_confirmado(pedido_id: int) -> bool:
        """
        Verificar si hay items agregados pero no confirmados.
        
        Args:
            pedido_id: ID del pedido
            
        Returns:
            True si hay items no confirmados
        """
        with get_db_session() as session:
            existe = session.query(PedidoItem).filter(
                and_(
                    PedidoItem.pedido_id == pedido_id,
                    PedidoItem.estatus < 3  # No confirmado (<3)
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
    def _serializar_item(item) -> dict:
        """Helper para serializar item"""
        if not item:
            return None
        
        return {
            'id_pedido_item': item.id_pedido_item,
            'pedido_id': item.pedido_id,
            'producto_id': item.producto_id,
            'combo_id': item.combo_id,
            'cantidad': item.cantidad,
            'precio_unit': float(item.precio_unit),
            'estatus': item.estatus,
            'notas': item.notas,
            'created_at': item.created_at.isoformat() if item.created_at else None,
            'updated_at': item.updated_at.isoformat() if item.updated_at else None
        }
