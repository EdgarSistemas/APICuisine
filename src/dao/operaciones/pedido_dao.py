"""
PedidoDAO - Data Access Object para operaciones.Pedido
Gestión de pedidos vinculados a reservas
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import and_, or_
from src.models.operaciones.pedido_model import Pedido
from src.models.operaciones.pedido_item_model import PedidoItem
from src.models.operaciones.pedido_estado_hist_model import PedidoEstadoHist
from src.core.db.session_manager import get_db_session
import logging

logger = logging.getLogger(__name__)


class PedidoDAO:
    """Data Access Object para Pedido"""
    
    @staticmethod
    def crear_pedido(
        sucursal_id: int,
        reserva_id: int,
        inicia_usuario_id: int,
        mesa_id: int,
        folio: str,
        cliente_id: int = None,
        tipo_pedido: int = 1,
        canal: int = 2,
        notas: str = None
    ) -> dict:
        """
        Crear nuevo pedido vinculado a reserva.
        
        Args:
            sucursal_id: ID de sucursal
            reserva_id: ID de reserva (OBLIGATORIO)
            inicia_usuario_id: ID usuario que inicia (cliente, mesero, etc)
            mesa_id: ID de mesa
            folio: Folio único del pedido
            cliente_id: ID del cliente (opcional)
            tipo_pedido: 1=Dine-in, 2=Pickup, 3=Delivery
            canal: 1=Mesero, 2=Sistema, 3=App
            notas: Notas
            
        Returns:
            Dict serializado del pedido
        """
        with get_db_session() as session:
            pedido = Pedido(
                sucursal_id=sucursal_id,
                folio=folio,
                cliente_id=cliente_id,
                tipo_pedido=tipo_pedido,
                canal=canal,
                reserva_id=reserva_id,
                mesa_id=mesa_id,
                inicia_usuario_id=inicia_usuario_id,
                estado_pedido=1,  # Abierto
                notas=notas
            )
            session.add(pedido)
            session.flush()  # Para obtener el ID
            session.commit()
            logger.info(f"Pedido creado: ID {pedido.id_pedido}, folio {folio}, reserva {reserva_id}")
            return PedidoDAO._serializar_pedido(pedido)
    
    
    @staticmethod
    def obtener_pedido_por_id(pedido_id: int) -> dict:
        """
        Obtener pedido por ID.
        
        Args:
            pedido_id: ID del pedido
            
        Returns:
            Dict del pedido con items o None
        """
        with get_db_session() as session:
            pedido = session.query(Pedido).filter(
                Pedido.id_pedido == pedido_id
            ).first()
            
            if not pedido:
                return None
            
            return PedidoDAO._serializar_pedido(pedido)
    
    
    @staticmethod
    def obtener_pedido_por_reserva(reserva_id: int) -> dict:
        """
        Obtener pedido vinculado a una reserva.
        
        Args:
            reserva_id: ID de reserva
            
        Returns:
            Dict del pedido o None
        """
        with get_db_session() as session:
            pedido = session.query(Pedido).filter(
                Pedido.reserva_id == reserva_id
            ).first()
            
            if not pedido:
                return None
            
            return PedidoDAO._serializar_pedido(pedido)
    
    
    @staticmethod
    def obtener_pedidos_por_sucursal(sucursal_id: int, estatus: int = None) -> list:
        """
        Obtener pedidos de una sucursal.
        
        Args:
            sucursal_id: ID de sucursal
            estatus: Filtrar por estado_pedido (opcional)
            
        Returns:
            Lista de pedidos
        """
        with get_db_session() as session:
            query = session.query(Pedido).filter(
                Pedido.sucursal_id == sucursal_id
            )
            
            if estatus:
                query = query.filter(Pedido.estado_pedido == estatus)
            
            pedidos = query.order_by(Pedido.created_at.desc()).all()
            return [PedidoDAO._serializar_pedido(p) for p in pedidos]
    
    
    @staticmethod
    def obtener_pedidos_cocina(sucursal_id: int) -> list:
        """
        Obtener pedidos con items en cocina.
        
        Args:
            sucursal_id: ID de sucursal
            
        Returns:
            Lista de pedidos
        """
        with get_db_session() as session:
            # Items que están en cocina (estatus=3)
            items_cocina = session.query(PedidoItem).filter(
                PedidoItem.estatus == 3  # En cocina
            ).all()
            
            pedido_ids = list(set([item.pedido_id for item in items_cocina]))
            
            pedidos = session.query(Pedido).filter(
                and_(
                    Pedido.id_pedido.in_(pedido_ids),
                    Pedido.sucursal_id == sucursal_id
                )
            ).all()
            
            return [PedidoDAO._serializar_pedido(p) for p in pedidos]
    
    
    @staticmethod
    def cambiar_estatus_pedido(pedido_id: int, nuevo_estatus: int) -> dict:
        """
        Cambiar estatus de pedido.
        
        Args:
            pedido_id: ID del pedido
            nuevo_estatus: Nuevo estado (1=Abierto, 2=Enviado, 3=Entregado, 4=Cancelado, 5=Pagado)
            
        Returns:
            Dict actualizado o None
        """
        with get_db_session() as session:
            pedido = session.query(Pedido).filter(
                Pedido.id_pedido == pedido_id
            ).first()
            
            if not pedido:
                return None
            
            pedido.estado_pedido = nuevo_estatus
            pedido.updated_at = datetime.now()
            session.commit()
            logger.info(f"Pedido {pedido_id} cambió a estatus {nuevo_estatus}")
            return PedidoDAO._serializar_pedido(pedido)
    
    
    @staticmethod
    def obtener_total_pedido(pedido_id: int) -> Decimal:
        """
        Obtener total de un pedido (suma de items confirmados).
        
        Args:
            pedido_id: ID del pedido
            
        Returns:
            Total en Decimal
        """
        with get_db_session() as session:
            items = session.query(PedidoItem).filter(
                and_(
                    PedidoItem.pedido_id == pedido_id,
                    PedidoItem.estatus >= 3  # Items confirmados/en cocina/listos
                )
            ).all()
            
            total = Decimal('0.00')
            for item in items:
                total += Decimal(str(item.precio_unit)) * Decimal(str(item.cantidad))
            
            return total
    
    
    @staticmethod
    def registrar_cambio_estatus(pedido_id: int, estatus: int, usuario_id: int = None, comentario: str = None) -> dict:
        """
        Registrar cambio de estatus en historial.
        
        Args:
            pedido_id: ID del pedido
            estatus: Nuevo estatus
            usuario_id: ID del usuario que hace cambio
            comentario: Comentario opcional
            
        Returns:
            Dict del registro de historial
        """
        with get_db_session() as session:
            hist = PedidoEstadoHist(
                pedido_id=pedido_id,
                estado_pedido=estatus,
                usuario_id=usuario_id,
                comentario=comentario
            )
            session.add(hist)
            session.commit()
            logger.info(f"Cambio de estatus registrado: Pedido {pedido_id} → {estatus}")
            
            return {
                'id_pedido_estado_hist': hist.id_pedido_estado_hist,
                'pedido_id': hist.pedido_id,
                'estado_pedido': hist.estado_pedido,
                'usuario_id': hist.usuario_id,
                'created_at': hist.created_at.isoformat() if hist.created_at else None,
                'comentario': hist.comentario
            }
    
    
    @staticmethod
    def pedido_existe(pedido_id: int) -> bool:
        """
        Verificar si un pedido existe.
        
        Args:
            pedido_id: ID del pedido
            
        Returns:
            True si existe
        """
        with get_db_session() as session:
            existe = session.query(Pedido).filter(
                Pedido.id_pedido == pedido_id
            ).first()
            return existe is not None
    
    
    @staticmethod
    def _serializar_pedido(pedido) -> dict:
        """Helper para serializar pedido con items"""
        if not pedido:
            return None
        
        items = [
            {
                'id_pedido_item': item.id_pedido_item,
                'pedido_id': item.pedido_id,
                'producto_id': item.producto_id,
                'combo_id': item.combo_id,
                'cantidad': item.cantidad,
                'precio_unit': float(item.precio_unit),
                'estatus': item.estatus,
                'notas': item.notas,
                'created_at': item.created_at.isoformat() if item.created_at else None
            }
            for item in pedido.pedido_items
        ]
        
        return {
            'id_pedido': pedido.id_pedido,
            'sucursal_id': pedido.sucursal_id,
            'folio': pedido.folio,
            'cliente_id': pedido.cliente_id,
            'tipo_pedido': pedido.tipo_pedido,
            'canal': pedido.canal,
            'reserva_id': pedido.reserva_id,
            'mesa_id': pedido.mesa_id,
            'inicia_usuario_id': pedido.inicia_usuario_id,
            'estado_pedido': pedido.estado_pedido,
            'notas': pedido.notas,
            'items': items,
            'created_at': pedido.created_at.isoformat() if pedido.created_at else None,
            'updated_at': pedido.updated_at.isoformat() if pedido.updated_at else None
        }
