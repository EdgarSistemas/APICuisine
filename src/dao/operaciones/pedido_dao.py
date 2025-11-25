"""
PedidoDAO - Data Access Object para operaciones.Pedido
Gestión de pedidos con creación, items, y cambio de estado

Sistema de estados de Pedido (estado_pedido):
- 0: Iniciado (pedido recién creado)
- 3: Completo (usuario cierra el pedido)
- 4: Cancelado
- 5: Pagado

Sistema de estados de PedidoItem (estatus_detalle):
- 1: EnCocina (enviado a preparar, AQUÍ SE CONSUME INVENTARIO)
- 2: Listo (preparado)
- 3: Completo (servido/entregado)
- 4: Cancelado
- 5: Pagado

Flujo Pedido: 0 (crear) → 3 (cerrar) → 5 (pagar)
Flujo Items:  1 (crear+inventario) → 2 (cocina listo) → 3 (cerrar) → 5 (pagar)
Takeaway: Cuando todos items = 2 (Listo), auto-pago a 5
"""

from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import and_, or_, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from src.models.operaciones.pedido_model import Pedido, PedidoItem, PedidoEstadoHist
from src.models.catalogos.producto_model import Producto
from src.models.catalogos.combo_model import Combo
from src.models.operaciones.reserva_model import Reserva
from src.core.db.session_manager import get_db_session
import uuid
import logging

logger = logging.getLogger(__name__)

# Constantes de estado de Pedido
ESTADO_INICIADO = 0      # Pedido recién creado
ESTADO_COMPLETO = 3      # Pedido cerrado por usuario
ESTADO_CANCELADO = 4     # Cancelado
ESTADO_PAGADO = 5        # Pagado

# Constantes de estatus_detalle de PedidoItem
ESTATUS_ITEM_EN_COCINA = 1   # Item creado, inventario consumido
ESTATUS_ITEM_LISTO = 2       # Preparado por cocina
ESTATUS_ITEM_COMPLETO = 3    # Entregado al cliente
ESTATUS_ITEM_CANCELADO = 4   # Cancelado
ESTATUS_ITEM_PAGADO = 5      # Pagado


class PedidoDAO:
    """Data Access Object para Pedido"""
    
    @staticmethod
    def crear_pedido(
        sucursal_id: int,
        cliente_id: int,
        tipo_pedido: int,
        canal: int,
        reserva_id: int,
        inicia_usuario_id: int,
        mesa_id: int = None,
        notas: str = None
    ) -> dict:
        """
        Crear nuevo pedido en estado 0=Iniciado (sin items aún)
        
        Args:
            sucursal_id: ID de sucursal
            cliente_id: ID del cliente (OBLIGATORIO)
            tipo_pedido: 1=Dine-in, 2=Takeaway
            canal: 1=PWA, 2=Móvil, 3=Presencial
            reserva_id: ID de reserva (OBLIGATORIO)
            inicia_usuario_id: ID usuario que inicia
            mesa_id: ID de mesa (REQUERIDO si tipo_pedido=1, NULL si tipo_pedido=2)
            notas: Notas
            
        Returns:
            Dict: {id_pedido, folio, estado_pedido, created_at}
        """
        with get_db_session() as session:
            try:
                # Generar folio único (18 caracteres)
                # Formato: PED-YYYYMMDDHHmmss
                folio = f"PED-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                
                # Validar reserva existe
                reserva = session.query(Reserva).filter_by(id_reserva=reserva_id).first()
                if not reserva:
                    raise ValueError(f"Reserva {reserva_id} no existe")
                
                pedido = Pedido(
                    sucursal_id=sucursal_id,
                    folio=folio,
                    cliente_id=cliente_id,
                    tipo_pedido=tipo_pedido,
                    canal=canal,
                    reserva_id=reserva_id,
                    mesa_id=mesa_id,
                    inicia_usuario_id=inicia_usuario_id,
                    estado_pedido=ESTADO_INICIADO,  # 0 = Iniciado
                    notas=notas
                )
                
                session.add(pedido)
                session.flush()
                
                logger.info(f"Pedido {pedido.id_pedido} creado: folio {folio}, reserva {reserva_id}")
                
                return {
                    'id_pedido': pedido.id_pedido,
                    'folio': pedido.folio,
                    'estado_pedido': pedido.estado_pedido,
                    'created_at': pedido.created_at.isoformat()
                }
            
            except IntegrityError as e:
                session.rollback()
                logger.error(f"Error de integridad al crear pedido: {str(e)}")
                raise ValueError(f"Error al crear pedido: {str(e)}")
            except Exception as e:
                session.rollback()
                logger.error(f"Error inesperado al crear pedido: {str(e)}")
                raise
    
    
    @staticmethod
    def crear_pedido_item(
        pedido_id: int,
        producto_id: int = None,
        combo_id: int = None,
        cantidad: int = 1,
        precio_unit: Decimal = None,
        notas: str = None
    ) -> dict:
        """
        Agrega un item al pedido
        
        Args:
            pedido_id: ID del pedido
            producto_id: ID del producto (si aplica)
            combo_id: ID del combo (si aplica)
            cantidad: Cantidad solicitada
            precio_unit: Precio unitario (se obtiene automáticamente si es None)
            notas: Notas del item
        
        Returns:
            Dict: {id_pedido_item, producto_id, combo_id, cantidad, precio_unit}
        """
        with get_db_session() as session:
            try:
                pedido = session.query(Pedido).filter_by(id_pedido=pedido_id).first()
                if not pedido:
                    raise ValueError(f"Pedido {pedido_id} no existe")
                
                # Solo se puede agregar items a pedidos en estado Iniciado (0) o Completo (3) antes de pagar
                if pedido.estado_pedido not in [ESTADO_INICIADO, ESTADO_COMPLETO]:
                    raise ValueError(f"Solo se pueden agregar items a pedidos en estado Iniciado (0) o Completo (3)")
                
                # Obtener precio si no viene
                if precio_unit is None:
                    if producto_id:
                        prod = session.query(Producto).filter_by(id_producto=producto_id).first()
                        if not prod:
                            raise ValueError(f"Producto {producto_id} no existe")
                        precio_unit = Decimal(str(prod.precio))
                    elif combo_id:
                        combo = session.query(Combo).filter_by(id_combo=combo_id).first()
                        if not combo:
                            raise ValueError(f"Combo {combo_id} no existe")
                        precio_unit = Decimal(str(combo.precio))
                    else:
                        raise ValueError("Debe especificar producto_id o combo_id")
                
                item = PedidoItem(
                    pedido_id=pedido_id,
                    producto_id=producto_id,
                    combo_id=combo_id,
                    cantidad=cantidad,
                    precio_unit=precio_unit,
                    estatus_detalle=ESTATUS_ITEM_EN_COCINA,  # 1 = EnCocina (items van directo)
                    notas=notas
                )
                
                session.add(item)
                session.flush()
                
                logger.info(f"Item agregado a pedido {pedido_id}: producto={producto_id}, combo={combo_id}, cant={cantidad}")
                
                return {
                    'id_pedido_item': item.id_pedido_item,
                    'producto_id': item.producto_id,
                    'combo_id': item.combo_id,
                    'cantidad': item.cantidad,
                    'precio_unit': str(item.precio_unit)
                }
            
            except Exception as e:
                session.rollback()
                logger.error(f"Error al crear item de pedido: {str(e)}")
                raise
    
    
    @staticmethod
    def cambiar_estado_pedido(pedido_id: int, nuevo_estado: int, usuario_id: int = None, comentario: str = None) -> dict:
        """
        Cambia el estado del pedido y registra en historial.
        
        Sistema de estados:
            0 = Iniciado (pedido recién creado)
            3 = Completo (usuario cierra pedido)
            4 = Cancelado
            5 = Pagado
        
        Transiciones válidas:
            0 → 3, 4 (Iniciado → Completo, Cancelado)
            3 → 4, 5 (Completo → Cancelado, Pagado)
            4 → (nada, estado final)
            5 → (nada, estado final)
        
        NOTA: El consumo de inventario NO ocurre aquí.
        Ocurre cuando PedidoItem se crea (estatus_detalle=1 EnCocina).
        
        Args:
            pedido_id: ID del pedido
            nuevo_estado: Nuevo estado
            usuario_id: ID del usuario que realiza cambio
            comentario: Comentario
        
        Returns:
            Dict: {id_pedido, estado_pedido, updated_at}
        """
        with get_db_session() as session:
            try:
                pedido = session.query(Pedido).filter_by(id_pedido=pedido_id).first()
                if not pedido:
                    raise ValueError(f"Pedido {pedido_id} no existe")
                
                # Validar transición
                estado_actual = pedido.estado_pedido
                transiciones_validas = {
                    ESTADO_INICIADO: [ESTADO_COMPLETO, ESTADO_CANCELADO],   # 0 → 3, 4
                    ESTADO_COMPLETO: [ESTADO_CANCELADO, ESTADO_PAGADO],     # 3 → 4, 5
                    ESTADO_CANCELADO: [],                                    # 4 → nada
                    ESTADO_PAGADO: []                                        # 5 → nada
                }
                
                if nuevo_estado not in transiciones_validas.get(estado_actual, []):
                    raise ValueError(
                        f"Transición no válida: {estado_actual} → {nuevo_estado}"
                    )
                
                # Registrar histórico
                hist = PedidoEstadoHist(
                    pedido_id=pedido_id,
                    estado_pedido=nuevo_estado,
                    usuario_id=usuario_id,
                    comentario=comentario
                )
                
                # Actualizar estado
                pedido.estado_pedido = nuevo_estado
                pedido.updated_at = datetime.utcnow()
                
                session.add(hist)
                session.flush()
                
                logger.info(f"Pedido {pedido_id} cambió de estado {estado_actual} → {nuevo_estado}")
                
                return {
                    'id_pedido': pedido_id,
                    'estado_pedido': nuevo_estado,
                    'estado_anterior': estado_actual,
                    'updated_at': pedido.updated_at.isoformat()
                }
            
            except Exception as e:
                session.rollback()
                logger.error(f"Error al cambiar estado: {str(e)}")
                raise
    
    
    @staticmethod
    def obtener_pedido_completo(pedido_id: int) -> dict:
        """
        Obtiene pedido con items e histórico de cambios.
        
        Returns:
            Dict con pedido completo o None
        """
        # Mapas de estados para display
        estado_pedido_map = {
            0: 'Iniciado',
            1: 'EnCocina',
            2: 'Listo',
            3: 'Completo',
            4: 'Cancelado',
            5: 'Pagado'
        }
        
        estatus_item_map = {
            0: 'Iniciado',
            1: 'EnCocina',
            2: 'Listo',
            3: 'Completo',
            4: 'Cancelado',
            5: 'Pagado'
        }
        
        with get_db_session() as session:
            try:
                pedido = session.query(Pedido).filter_by(id_pedido=pedido_id).first()
                if not pedido:
                    return None
                
                items = session.query(PedidoItem).filter_by(pedido_id=pedido_id).all()
                historico = session.query(PedidoEstadoHist).filter_by(pedido_id=pedido_id).all()
                
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
                    'estado_pedido_nombre': estado_pedido_map.get(pedido.estado_pedido, 'Desconocido'),
                    'notas': pedido.notas,
                    'created_at': pedido.created_at.isoformat() if pedido.created_at else None,
                    'updated_at': pedido.updated_at.isoformat() if pedido.updated_at else None,
                    'items': [
                        {
                            'id_pedido_item': item.id_pedido_item,
                            'producto_id': item.producto_id,
                            'combo_id': item.combo_id,
                            'cantidad': item.cantidad,
                            'precio_unit': str(item.precio_unit),
                            'estatus_detalle': item.estatus_detalle,
                            'estatus_detalle_nombre': estatus_item_map.get(item.estatus_detalle, 'Desconocido'),
                            'notas': item.notas,
                            'created_at': item.created_at.isoformat() if item.created_at else None
                        }
                        for item in items
                    ],
                    'historico': [
                        {
                            'id_pedido_estado_hist': h.id_pedido_estado_hist,
                            'estado_pedido': h.estado_pedido,
                            'estado_pedido_nombre': estado_pedido_map.get(h.estado_pedido, 'Desconocido'),
                            'usuario_id': h.usuario_id,
                            'created_at': h.created_at.isoformat() if h.created_at else None,
                            'comentario': h.comentario
                        }
                        for h in historico
                    ]
                }
            
            except Exception as e:
                logger.error(f"Error al obtener pedido: {str(e)}")
                raise
    
    
    @staticmethod
    def listar_pedidos_por_sucursal(sucursal_id: int, fecha_desde=None, fecha_hasta=None, 
                                     estado=None, tipo_pedido=None, offset=0, limit=50):
        """
        Lista pedidos de una sucursal con filtros opcionales
        
        Args:
            sucursal_id: ID de la sucursal
            fecha_desde: Fecha mínima (opcional)
            fecha_hasta: Fecha máxima (opcional)
            estado: Estado del pedido (opcional): 0=Iniciado, 3=Completo, 4=Cancelado, 5=Pagado
            tipo_pedido: Tipo de pedido (opcional): 1=Dine-in, 2=Takeaway
            offset: Paginación offset
            limit: Paginación limit
        
        Returns:
            tuple: (lista de pedidos, total)
        """
        with get_db_session() as session:
            try:
                query = session.query(Pedido).filter_by(sucursal_id=sucursal_id)
                
                if fecha_desde:
                    query = query.filter(Pedido.created_at >= fecha_desde)
                if fecha_hasta:
                    query = query.filter(Pedido.created_at <= fecha_hasta)
                if estado is not None:
                    query = query.filter(Pedido.estado_pedido == estado)
                if tipo_pedido is not None:
                    query = query.filter(Pedido.tipo_pedido == tipo_pedido)
                
                total = query.count()
                
                pedidos = query.order_by(Pedido.created_at.desc()).offset(offset).limit(limit).all()
                
                return (
                    [
                        {
                            'id_pedido': p.id_pedido,
                            'folio': p.folio,
                            'cliente_id': p.cliente_id,
                            'tipo_pedido': p.tipo_pedido,
                            'canal': p.canal,
                            'mesa_id': p.mesa_id,
                            'estado_pedido': p.estado_pedido,
                            'created_at': p.created_at.isoformat() if p.created_at else None
                        }
                        for p in pedidos
                    ],
                    total
                )
            
            except Exception as e:
                logger.error(f"Error al listar pedidos: {str(e)}")
                raise
    
    
    @staticmethod
    def obtener_pedidos_por_estado(sucursal_id: int, estado: int):
        """Obtiene todos los pedidos de una sucursal en un estado específico"""
        with get_db_session() as session:
            try:
                pedidos = session.query(Pedido).filter(
                    and_(
                        Pedido.sucursal_id == sucursal_id,
                        Pedido.estado_pedido == estado
                    )
                ).order_by(Pedido.created_at.desc()).all()
                
                return [
                    {
                        'id_pedido': p.id_pedido,
                        'folio': p.folio,
                        'cliente_id': p.cliente_id,
                        'mesa_id': p.mesa_id,
                        'estado_pedido': p.estado_pedido,
                        'created_at': p.created_at.isoformat() if p.created_at else None
                    }
                    for p in pedidos
                ]
            except Exception as e:
                logger.error(f"Error al obtener pedidos por estado: {str(e)}")
                raise
    
    
    @staticmethod
    def calcular_total_pedido(pedido_id: int) -> Decimal:
        """
        Calcula el total de un pedido (suma de items * cantidad * precio)
        
        Returns:
            Decimal: Total del pedido
        """
        with get_db_session() as session:
            try:
                items = session.query(PedidoItem).filter_by(pedido_id=pedido_id).all()
                
                total = Decimal('0.00')
                for item in items:
                    total += Decimal(str(item.precio_unit)) * Decimal(str(item.cantidad))
                
                return total
            
            except Exception as e:
                logger.error(f"Error al calcular total: {str(e)}")
                raise
    
    
    @staticmethod
    def pedido_existe(pedido_id: int) -> bool:
        """Verifica si un pedido existe"""
        with get_db_session() as session:
            try:
                existe = session.query(Pedido).filter_by(id_pedido=pedido_id).first() is not None
                return existe
            except Exception as e:
                logger.error(f"Error al verificar existencia de pedido: {str(e)}")
                return False
