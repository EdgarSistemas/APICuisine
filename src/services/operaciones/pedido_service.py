"""
PedidoService - Servicio de negocio para Pedidos
Orquesta creación de pedidos, consumo de inventario y cambios de estado.

Sistema de estados de Pedido (estado_pedido):
- 0: Iniciado (pedido recién creado)
- 3: Completo (usuario cierra el pedido)
- 4: Cancelado
- 5: Pagado

Sistema de estados de PedidoItem (estatus_detalle):
- 1: EnCocina (item creado, inventario consumido)
- 2: Listo (preparado por cocina)
- 3: Completo (entregado)
- 4: Cancelado
- 5: Pagado

Flujo Pedido: 0 (crear) → 3 (cerrar) → 5 (pagar)
Flujo Items:  1 (crear+inventario) → 2 (cocina listo) → 3 (cerrar) → 5 (pagar)

IMPORTANTE: 
- Items se crean directamente en estatus 1 (EnCocina), consumiendo inventario
- Takeaway: Cuando todos items = 2 (Listo), auto-pagar a 5 (pedido e items)
"""

from datetime import datetime
from decimal import Decimal
from src.core.db.session_manager import get_db_session
from src.dao.operaciones.pedido_dao import (
    PedidoDAO, 
    ESTADO_INICIADO, ESTADO_COMPLETO, ESTADO_CANCELADO, ESTADO_PAGADO,
    ESTATUS_ITEM_EN_COCINA, ESTATUS_ITEM_LISTO, 
    ESTATUS_ITEM_COMPLETO, ESTATUS_ITEM_CANCELADO, ESTATUS_ITEM_PAGADO
)
from src.dao.operaciones.pedido_item_dao import PedidoItemDAO
from src.dao.operaciones.reserva_dao import ReservaDAO
from src.dao.inventario.inventario_dao import InventarioDAO
from src.models.operaciones.pedido_model import Pedido, PedidoItem
from src.models.operaciones.reserva_model import Reserva
from src.models.operaciones.hold_mesa_model import HoldMesa
from src.services.notification import NotificationService
import logging

logger = logging.getLogger(__name__)


class PedidoService:
    """Servicio de negocio para Pedidos"""
    
    @staticmethod
    def crear_pedido_dine_in(sucursal_id: int, cliente_id: int, canal: int, 
                            reserva_id: int, inicia_usuario_id: int, items: list = None, notas: str = None) -> dict:
        """
        Crea pedido tipo Dine-in (con mesa y reserva).
        
        Flujo:
        1. Validar que reserva existe y está activa (estatus 1 o 2)
        2. Obtener mesa_id de la reserva
        3. Crear Pedido (estado=0 Iniciado)
        4. Agregar items al pedido en estado EnCocina (1) + consumir inventario
        5. Retornar pedido creado
        
        NOTA: Los items se agregan con estatus_detalle=1 (EnCocina) y
        el consumo de inventario ocurre inmediatamente.
        
        Args:
            sucursal_id: ID de sucursal
            cliente_id: ID del cliente (OBLIGATORIO)
            canal: 1=PWA, 2=Móvil, 3=Presencial
            reserva_id: ID de reserva (OBLIGATORIO)
            inicia_usuario_id: ID del usuario que inicia
            items: [{"producto_id": X, "cantidad": Y, "notas": "..."}, ...] (opcional)
            notas: Notas del pedido
        
        Returns:
            dict: Pedido completo con items
        """
        # Los DAOs manejan sus propias sesiones, no necesitamos abrir una aquí
        try:
            # 1. Validar reserva y obtener mesa_id
            with get_db_session() as session:
                reserva = session.query(Reserva).filter_by(id_reserva=reserva_id).first()
                if not reserva:
                    raise ValueError(f"Reserva {reserva_id} no existe")
                
                if reserva.estatus not in [1, 2]:
                    raise ValueError(f"Reserva debe estar Programada (1) o EnCurso (2), estado actual: {reserva.estatus}")
                
                # 2. Obtener mesa_id desde HoldMesa (Reserva.hold_id → HoldMesa.mesa_id)
                if not reserva.hold_id:
                    raise ValueError(f"Reserva {reserva_id} no tiene hold asociado")
                
                hold = session.query(HoldMesa).filter_by(id_hold_mesa=reserva.hold_id).first()
                if not hold:
                    raise ValueError(f"HoldMesa {reserva.hold_id} no existe")
                
                mesa_id = hold.mesa_id
                if not mesa_id:
                    raise ValueError(f"HoldMesa {reserva.hold_id} no tiene mesa asignada")
            
            # 3. Crear pedido (estado=1 Abierto) - DAO maneja su propia sesión
            pedido_data = PedidoDAO.crear_pedido(
                sucursal_id=sucursal_id,
                cliente_id=cliente_id,
                tipo_pedido=1,  # Dine-in
                canal=canal,
                reserva_id=reserva_id,
                inicia_usuario_id=inicia_usuario_id,
                mesa_id=mesa_id,
                notas=notas
            )
            
            pedido_id = pedido_data['id_pedido']
            
            # 4. Agregar items - van directo a EnCocina y consumen inventario
            items_creados = []
            errores_consumo = []
            if items:
                for item in items:
                    item_data = PedidoItemDAO.agregar_item(
                        pedido_id=pedido_id,
                        sucursal_id=sucursal_id,
                        usuario_id=inicia_usuario_id,
                        producto_id=item.get('producto_id'),
                        combo_id=item.get('combo_id'),
                        cantidad=item.get('cantidad', 1),
                        precio_unit=Decimal(str(item.get('precio_unit'))) if item.get('precio_unit') else None,
                        notas=item.get('notas')
                    )
                    items_creados.append(item_data)
                    
                    # Verificar si hubo error de consumo
                    if not item_data.get('consumo_exitoso', False):
                        errores_consumo.append({
                            'item_id': item_data.get('id_pedido_item'),
                            'error': item_data.get('error_consumo', 'Consumo de inventario falló')
                        })
            
            # 5. Retornar pedido completo
            pedido_completo = PedidoDAO.obtener_pedido_completo(pedido_id)
            
            # Agregar info de consumo al resultado
            if errores_consumo:
                pedido_completo['advertencias_consumo'] = errores_consumo
                logger.warning(f"Pedido {pedido_id} creado con {len(errores_consumo)} errores de consumo de inventario")
            
            logger.info(f"Pedido Dine-in creado: {pedido_id}, reserva={reserva_id}, mesa={mesa_id}, items={len(items_creados)}")
            
            # Notificar a cocina
            try:
                mesa_num = str(mesa_id)  # TODO: obtener numero_mesa real
                NotificationService.notificar_pedido_creado(
                    pedido_id=pedido_id,
                    mesa_num=mesa_num,
                    cant_items=len(items_creados),
                    sucursal_id=sucursal_id
                )
            except Exception as notif_error:
                logger.warning(f"Error enviando notificación de pedido creado: {notif_error}")
            
            return pedido_completo
        
        except Exception as e:
            logger.error(f"Error al crear pedido Dine-in: {str(e)}")
            raise
    
    
    @staticmethod
    def crear_pedido_takeaway(sucursal_id: int, cliente_id: int, canal: int, 
                             inicia_usuario_id: int, items: list = None, notas: str = None) -> dict:
        """
        Crea pedido tipo Takeaway (sin mesa, crea reserva interna).
        
        Flujo:
        1. Validar cliente_id (OBLIGATORIO para takeaway)
        2. Crear Reserva interna: estatus=5, recepcionista_id=NULL
        3. Crear Pedido (tipo_pedido=2, mesa_id=NULL)
        4. Agregar items al pedido (si se proporcionan) en estado Iniciado
        5. Retornar pedido creado
        
        Args:
            sucursal_id: ID de sucursal
            cliente_id: ID del cliente (OBLIGATORIO)
            canal: 1=PWA, 2=Móvil, 3=Presencial
            inicia_usuario_id: ID del usuario que inicia
            items: [{"producto_id": X, "cantidad": Y, "notas": "..."}, ...] (opcional)
            notas: Notas del pedido
        
        Returns:
            dict: Pedido completo con items
        """
        with get_db_session() as session:
            try:
                # 1. Validar cliente_id (OBLIGATORIO)
                if not cliente_id:
                    raise ValueError("cliente_id es OBLIGATORIO para pedidos Takeaway")
                
                # 2. Crear Reserva interna
                reserva_interna = ReservaDAO.crear_reserva(
                    sucursal_id=sucursal_id,
                    cliente_id=cliente_id,
                    recepcionista_id=None,  # NULL para reserva interna
                    mesa_id=None,  # Sin mesa
                    num_personas=1,
                    hora_reserva=datetime.utcnow(),
                    estatus=5  # Interna
                )
                
                reserva_interna_id = reserva_interna['id_reserva']
                logger.info(f"Reserva interna creada para takeaway: {reserva_interna_id}")
                
                # 3. Crear pedido (tipo_pedido=2 Takeaway, mesa_id=NULL)
                pedido_data = PedidoDAO.crear_pedido(
                    sucursal_id=sucursal_id,
                    cliente_id=cliente_id,
                    tipo_pedido=2,  # Takeaway
                    canal=canal,
                    reserva_id=reserva_interna_id,
                    inicia_usuario_id=inicia_usuario_id,
                    mesa_id=None,  # NULL para takeaway
                    notas=notas
                )
                
                pedido_id = pedido_data['id_pedido']
                
                # 4. Agregar items - van directo a EnCocina y consumen inventario
                items_creados = []
                errores_consumo = []
                if items:
                    for item in items:
                        item_data = PedidoItemDAO.agregar_item(
                            pedido_id=pedido_id,
                            sucursal_id=sucursal_id,
                            usuario_id=inicia_usuario_id,
                            producto_id=item.get('producto_id'),
                            combo_id=item.get('combo_id'),
                            cantidad=item.get('cantidad', 1),
                            precio_unit=Decimal(str(item.get('precio_unit'))) if item.get('precio_unit') else None,
                            notas=item.get('notas')
                        )
                        items_creados.append(item_data)
                        
                        # Verificar si hubo error de consumo
                        if not item_data.get('consumo_exitoso', False):
                            errores_consumo.append({
                                'item_id': item_data.get('id_pedido_item'),
                                'error': item_data.get('error_consumo', 'Consumo de inventario falló')
                            })
                
                # 5. Retornar pedido completo
                pedido_completo = PedidoDAO.obtener_pedido_completo(pedido_id)
                pedido_completo['reserva_interna_id'] = reserva_interna_id
                
                # Agregar info de consumo al resultado
                if errores_consumo:
                    pedido_completo['advertencias_consumo'] = errores_consumo
                    logger.warning(f"Pedido Takeaway {pedido_id} creado con {len(errores_consumo)} errores de consumo")
                
                logger.info(f"Pedido Takeaway creado: {pedido_id}, cliente={cliente_id}, items={len(items_creados)}")
                
                return pedido_completo
            
            except Exception as e:
                session.rollback()
                logger.error(f"Error al crear pedido Takeaway: {str(e)}")
                raise
    
    
    @staticmethod
    def marcar_item_listo(item_id: int, usuario_id: int = None) -> dict:
        """
        Marca un item como listo (preparado en cocina).
        Cambia estatus_detalle: 1 (EnCocina) → 2 (Listo).
        
        TAKEAWAY AUTO-PAY:
        Si el pedido es Takeaway (tipo_pedido=2) y TODOS los items están
        ahora en estado Listo (2), se auto-paga:
        - Pedido: estado_pedido → 5 (Pagado)
        - Items: estatus_detalle → 5 (Pagado)
        
        Args:
            item_id: ID del item
            usuario_id: ID del usuario (cocinero)
        
        Returns:
            dict: Item actualizado (con info de auto-pay si aplica)
        """
        try:
            item = PedidoItemDAO.obtener_item_por_id(item_id)
            if not item:
                raise ValueError(f"Item {item_id} no existe")
            
            if item['estatus_detalle'] != ESTATUS_ITEM_EN_COCINA:
                raise ValueError(f"Solo se pueden marcar como listo items en cocina (estatus 1)")
            
            # Marcar item como Listo (2)
            item_actualizado = PedidoItemDAO.cambiar_estatus_item(
                item_id=item_id,
                nuevo_estatus=ESTATUS_ITEM_LISTO
            )
            
            logger.info(f"Item {item_id} marcado como listo (1→2)")
            
            # Notificar al mesero que el item está listo
            try:
                pedido_info = PedidoDAO.obtener_pedido_completo(item['pedido_id'])
                if pedido_info:
                    mesero_id = pedido_info.get('inicia_usuario_id')
                    mesa_id = pedido_info.get('mesa_id')
                    producto_nombre = item.get('producto_nombre', 'Producto')
                    if mesero_id:
                        NotificationService.notificar_item_listo(
                            pedido_id=item['pedido_id'],
                            producto=producto_nombre,
                            mesa_num=str(mesa_id) if mesa_id else 'N/A',
                            mesero_id=mesero_id
                        )
            except Exception as notif_error:
                logger.warning(f"Error enviando notificación item listo: {notif_error}")
            
            # Verificar si es Takeaway y todos los items están listos para auto-pay
            pedido_id = item['pedido_id']
            pedido_data = PedidoDAO.obtener_pedido_completo(pedido_id)
            
            auto_pagado = False
            if pedido_data and pedido_data['tipo_pedido'] == 2:  # Takeaway
                # Verificar si todos los items activos están en Listo (2)
                if PedidoItemDAO.verificar_todos_listos(pedido_id):
                    try:
                        # Auto-pagar: items a 5 y pedido a 5
                        PedidoService._auto_pagar_takeaway(pedido_id, usuario_id)
                        auto_pagado = True
                        logger.info(f"Pedido Takeaway {pedido_id} auto-pagado (todos items listos)")
                    except Exception as e:
                        logger.warning(f"Error en auto-pago takeaway: {str(e)}")
            
            # Actualizar respuesta con info de auto-pay
            if auto_pagado:
                item_actualizado = PedidoItemDAO.obtener_item_por_id(item_id)
                item_actualizado['auto_pagado'] = True
                item_actualizado['pedido_auto_pagado'] = True
            
            return item_actualizado
        
        except Exception as e:
            logger.error(f"Error al marcar item listo: {str(e)}")
            raise
    
    
    @staticmethod
    def _auto_pagar_takeaway(pedido_id: int, usuario_id: int = None) -> None:
        """
        Auto-paga un pedido Takeaway cuando todos los items están listos.
        
        Cambia:
        - Todos los items activos: estatus_detalle → 5 (Pagado)
        - Pedido: estado_pedido → 5 (Pagado)
        
        Args:
            pedido_id: ID del pedido
            usuario_id: ID del usuario
        """
        with get_db_session() as session:
            pedido_data = PedidoDAO.obtener_pedido_completo(pedido_id)
            
            if not pedido_data:
                raise ValueError(f"Pedido {pedido_id} no existe")
            
            if pedido_data['tipo_pedido'] != 2:  # No es Takeaway
                raise ValueError(f"Auto-pago solo aplica a pedidos Takeaway")
            
            # Marcar todos los items activos como Pagados (5)
            for item in pedido_data['items']:
                if item['estatus_detalle'] not in [ESTATUS_ITEM_CANCELADO, ESTATUS_ITEM_PAGADO]:
                    PedidoItemDAO.cambiar_estatus_item(
                        item_id=item['id_pedido_item'],
                        nuevo_estatus=ESTATUS_ITEM_PAGADO
                    )
            
            # Cambiar pedido directamente a Pagado (0 → 5)
            # Bypass de validación porque es auto-pay
            from src.models.operaciones.pedido_model import Pedido as PedidoModel
            pedido = session.query(PedidoModel).filter_by(id_pedido=pedido_id).first()
            if pedido:
                pedido.estado_pedido = ESTADO_PAGADO
                pedido.updated_at = datetime.utcnow()
                session.commit()
            
            logger.info(f"Pedido Takeaway {pedido_id} auto-pagado")
    
    
    @staticmethod
    def marcar_item_completo(item_id: int, usuario_id: int = None) -> dict:
        """
        Marca un item como completo (entregado al cliente).
        Cambia estatus_detalle: 2 (Listo) → 3 (Completo).
        
        Args:
            item_id: ID del item
            usuario_id: ID del usuario (mesero)
        
        Returns:
            dict: Item actualizado
        """
        try:
            item = PedidoItemDAO.obtener_item_por_id(item_id)
            if not item:
                raise ValueError(f"Item {item_id} no existe")
            
            if item['estatus_detalle'] != ESTATUS_ITEM_LISTO:
                raise ValueError(f"Solo se pueden marcar como completo items listos (estatus 2)")
            
            item_actualizado = PedidoItemDAO.cambiar_estatus_item(
                item_id=item_id,
                nuevo_estatus=ESTATUS_ITEM_COMPLETO
            )
            
            logger.info(f"Item {item_id} marcado como completo (2→3)")
            return item_actualizado
        
        except Exception as e:
            logger.error(f"Error al marcar item completo: {str(e)}")
            raise
    
    
    @staticmethod
    def cancelar_item(item_id: int, usuario_id: int = None, comentario: str = None) -> dict:
        """
        Cancela un item específico.
        Solo se pueden cancelar items en estado EnCocina (1) - antes de que cocina los marque como Listo.
        
        Args:
            item_id: ID del item
            usuario_id: ID del usuario
            comentario: Motivo de cancelación
        
        Returns:
            dict: Item actualizado
        """
        try:
            item = PedidoItemDAO.obtener_item_por_id(item_id)
            if not item:
                raise ValueError(f"Item {item_id} no existe")
            
            if item['estatus_detalle'] != ESTATUS_ITEM_EN_COCINA:
                raise ValueError(f"Solo se pueden cancelar items en cocina (estatus 1). Estado actual: {item['estatus_detalle']}")
            
            item_actualizado = PedidoItemDAO.cambiar_estatus_item(
                item_id=item_id,
                nuevo_estatus=ESTATUS_ITEM_CANCELADO
            )
            
            logger.info(f"Item {item_id} cancelado (1→4)")
            
            # Notificar a cocina sobre item cancelado
            try:
                pedido_info = PedidoDAO.obtener_pedido_completo(item['pedido_id'])
                if pedido_info:
                    producto_nombre = item.get('producto_nombre', 'Producto')
                    mesa_id = pedido_info.get('mesa_id')
                    NotificationService.notificar_item_cancelado(
                        pedido_id=item['pedido_id'],
                        producto=producto_nombre,
                        mesa_num=str(mesa_id) if mesa_id else 'N/A',
                        sucursal_id=pedido_info.get('sucursal_id')
                    )
            except Exception as notif_error:
                logger.warning(f"Error enviando notificación item cancelado: {notif_error}")
            
            return item_actualizado
        
        except Exception as e:
            logger.error(f"Error al cancelar item: {str(e)}")
            raise
    
    @staticmethod
    def obtener_pedido(pedido_id: int) -> dict:
        """
        Obtiene los detalles completos de un pedido.
        
        Args:
            pedido_id: ID del pedido
        
        Returns:
            dict: Pedido completo con items e histórico
        """
        try:
            pedido = PedidoDAO.obtener_pedido_completo(pedido_id)
            if not pedido:
                raise ValueError(f"Pedido {pedido_id} no existe")
            
            logger.info(f"Pedido {pedido_id} obtenido")
            return pedido
        
        except Exception as e:
            logger.error(f"Error al obtener pedido: {str(e)}")
            raise
    
    
    @staticmethod
    def agregar_item(pedido_id: int, producto_id: int = None, combo_id: int = None, 
                    cantidad: int = 1, notas: str = None) -> dict:
        """
        Agrega un item (producto o combo) a un pedido.
        El item se crea en estado EnCocina (1) y consume inventario inmediatamente.
        
        Validaciones:
        - Pedido debe estar en estado Iniciado (0) o Completo (3) antes de pagar
        - Debe proporcionar producto_id XOR combo_id
        - Cantidad debe ser válida (1-100)
        
        Args:
            pedido_id: ID del pedido
            producto_id: ID del producto (optional si combo_id)
            combo_id: ID del combo (optional si producto_id)
            cantidad: Cantidad del item (1-100)
            notas: Notas adicionales
        
        Returns:
            dict: Item creado
        """
        try:
            # Validar que pedido existe y está en estado válido
            pedido = PedidoDAO.obtener_pedido_completo(pedido_id)
            if not pedido:
                raise ValueError(f"Pedido {pedido_id} no existe")
            
            if pedido['estado_pedido'] not in [ESTADO_INICIADO, ESTADO_COMPLETO]:
                raise ValueError(f"Solo se pueden agregar items a pedidos en estado Iniciado (0) o Completo (3)")
            
            # Validar producto_id XOR combo_id
            if not producto_id and not combo_id:
                raise ValueError("Debe proporcionar producto_id o combo_id")
            
            if producto_id and combo_id:
                raise ValueError("No puede proporcionar ambos: producto_id y combo_id")
            
            # Validar cantidad
            if not isinstance(cantidad, int) or cantidad < 1 or cantidad > 100:
                raise ValueError("Cantidad debe ser un número entre 1 y 100")
            
            # Crear item - va directo a EnCocina y consume inventario
            item = PedidoItemDAO.agregar_item(
                pedido_id=pedido_id,
                sucursal_id=pedido['sucursal_id'],
                usuario_id=pedido.get('inicia_usuario_id'),
                producto_id=producto_id,
                combo_id=combo_id,
                cantidad=cantidad,
                precio_unit=None,  # Se obtiene del catálogo
                notas=notas
            )
            
            logger.info(f"Item agregado a pedido {pedido_id}: producto={producto_id}, combo={combo_id}, cantidad={cantidad}, inventario consumido")
            return item
        
        except Exception as e:
            logger.error(f"Error al agregar item: {str(e)}")
            raise
    
    
    @staticmethod
    def completar_pedido(pedido_id: int, usuario_id: int = None) -> dict:
        """
        Marca pedido como completo (usuario cierra el pedido).
        Cambia estado: 0 (Iniciado) → 3 (Completo).
        También marca todos los items activos como Completo (3).
        
        Validación: Todos los items activos deben estar en estado Listo (2) o superior.
        
        Args:
            pedido_id: ID del pedido
            usuario_id: ID del usuario
        
        Returns:
            dict: Pedido actualizado
        """
        with get_db_session() as session:
            try:
                pedido_data = PedidoDAO.obtener_pedido_completo(pedido_id)
                if not pedido_data:
                    raise ValueError(f"Pedido {pedido_id} no existe")
                
                if pedido_data['estado_pedido'] != ESTADO_INICIADO:
                    raise ValueError(f"Solo se pueden completar pedidos en estado Iniciado (0)")
                
                # Verificar que todos los items estén listos (estatus >= 2)
                if not PedidoItemDAO.verificar_todos_listos(pedido_id):
                    raise ValueError("No todos los items están listos. Todos los items activos deben estar en estado Listo (2) o superior.")
                
                # Marcar items activos como Completo (3)
                for item in pedido_data['items']:
                    if item['estatus_detalle'] == ESTATUS_ITEM_LISTO:  # Solo los que están en Listo
                        PedidoItemDAO.cambiar_estatus_item(
                            item_id=item['id_pedido_item'],
                            nuevo_estatus=ESTATUS_ITEM_COMPLETO
                        )
                
                PedidoDAO.cambiar_estado_pedido(
                    pedido_id=pedido_id,
                    nuevo_estado=ESTADO_COMPLETO,
                    usuario_id=usuario_id,
                    comentario="Pedido completado - cerrado por usuario"
                )
                
                session.commit()
                
                resultado = PedidoDAO.obtener_pedido_completo(pedido_id)
                logger.info(f"Pedido {pedido_id} completado (estado 0→3)")
                
                # Notificar a caja que el pedido está listo para cobrar
                try:
                    mesa_id = resultado.get('mesa_id')
                    total = resultado.get('total', 0)
                    NotificationService.notificar_pedido_completo(
                        pedido_id=pedido_id,
                        mesa_num=str(mesa_id) if mesa_id else 'N/A',
                        total=float(total),
                        sucursal_id=resultado.get('sucursal_id')
                    )
                except Exception as notif_error:
                    logger.warning(f"Error enviando notificación pedido completo: {notif_error}")
                
                return resultado
            
            except Exception as e:
                session.rollback()
                logger.error(f"Error al completar pedido: {str(e)}")
                raise
    
    
    @staticmethod
    def cancelar_pedido(pedido_id: int, usuario_id: int = None, comentario: str = None) -> dict:
        """
        Cancela un pedido completo.
        
        Solo se pueden cancelar pedidos en estado Iniciado (0).
        Si hay items en EnCocina o posteriores, estos ya consumieron inventario.
        
        Args:
            pedido_id: ID del pedido
            usuario_id: ID del usuario que cancela
            comentario: Motivo de cancelación
        
        Returns:
            dict: Pedido actualizado
        """
        with get_db_session() as session:
            try:
                pedido_data = PedidoDAO.obtener_pedido_completo(pedido_id)
                if not pedido_data:
                    raise ValueError(f"Pedido {pedido_id} no existe")
                
                estado_actual = pedido_data['estado_pedido']
                
                # Solo permitir cancelación en estado Iniciado (0)
                if estado_actual != ESTADO_INICIADO:
                    raise ValueError(
                        f"No se pueden cancelar pedidos en estado {estado_actual}. "
                        f"Solo se pueden cancelar pedidos en Iniciado (0)"
                    )
                
                # Cancelar todos los items (incluso los que están en cocina - ya consumieron inventario)
                for item in pedido_data['items']:
                    if item['estatus_detalle'] not in [ESTATUS_ITEM_CANCELADO, ESTATUS_ITEM_PAGADO]:
                        PedidoItemDAO.cambiar_estatus_item(
                            item_id=item['id_pedido_item'],
                            nuevo_estatus=ESTATUS_ITEM_CANCELADO
                        )
                
                PedidoDAO.cambiar_estado_pedido(
                    pedido_id=pedido_id,
                    nuevo_estado=ESTADO_CANCELADO,
                    usuario_id=usuario_id,
                    comentario=comentario or "Pedido cancelado"
                )
                
                session.commit()
                
                resultado = PedidoDAO.obtener_pedido_completo(pedido_id)
                logger.info(f"Pedido {pedido_id} cancelado (estado {estado_actual}→4)")
                
                # Notificar a cocina y mesero sobre pedido cancelado
                try:
                    mesa_id = resultado.get('mesa_id')
                    NotificationService.notificar_pedido_cancelado(
                        pedido_id=pedido_id,
                        mesa_num=str(mesa_id) if mesa_id else 'N/A',
                        sucursal_id=resultado.get('sucursal_id')
                    )
                except Exception as notif_error:
                    logger.warning(f"Error enviando notificación pedido cancelado: {notif_error}")
                
                return resultado
            
            except Exception as e:
                session.rollback()
                logger.error(f"Error al cancelar pedido: {str(e)}")
                raise
    
    
    # =========================================================================
    # DEPRECATED - Usar PagoService.marcar_pagado() en su lugar
    # Este método se mantiene por compatibilidad pero no debe usarse directamente
    # El flujo correcto es:
    #   1. POST /api/pagos (crear pago)
    #   2. POST /api/pagos/{id}/marcar-pagado (confirmar y transicionar pedido)
    # =========================================================================
    @staticmethod
    def pagar_pedido(pedido_id: int, usuario_id: int = None) -> dict:
        """
        DEPRECATED: Usar PagoService.marcar_pagado() en su lugar.
        
        Este método solo debe usarse internamente para auto-pago de takeaway.
        Para el flujo normal de pago, usar PagoController.
        
        Args:
            pedido_id: ID del pedido
            usuario_id: ID del usuario
        
        Returns:
            dict: Pedido actualizado
        """
        logger.warning(
            f"DEPRECATED: pagar_pedido llamado directamente. "
            f"Usar PagoService.marcar_pagado() para el flujo normal."
        )
        with get_db_session() as session:
            try:
                pedido_data = PedidoDAO.obtener_pedido_completo(pedido_id)
                if not pedido_data:
                    raise ValueError(f"Pedido {pedido_id} no existe")
                
                if pedido_data['estado_pedido'] != ESTADO_COMPLETO:
                    raise ValueError(f"Solo se pueden pagar pedidos en estado Completo (3)")
                
                # Marcar items activos como pagados
                for item in pedido_data['items']:
                    if item['estatus_detalle'] not in [ESTATUS_ITEM_CANCELADO, ESTATUS_ITEM_PAGADO]:
                        PedidoItemDAO.cambiar_estatus_item(
                            item_id=item['id_pedido_item'],
                            nuevo_estatus=ESTATUS_ITEM_PAGADO
                        )
                
                PedidoDAO.cambiar_estado_pedido(
                    pedido_id=pedido_id,
                    nuevo_estado=ESTADO_PAGADO,
                    usuario_id=usuario_id,
                    comentario="Pedido pagado"
                )
                
                session.commit()
                
                resultado = PedidoDAO.obtener_pedido_completo(pedido_id)
                logger.info(f"Pedido {pedido_id} pagado (estado 3→5)")
                
                return resultado
            
            except Exception as e:
                session.rollback()
                logger.error(f"Error al pagar pedido: {str(e)}")
                raise
    
    
    @staticmethod
    def listar_pedidos_sucursal(sucursal_id: int, estado: int = None, 
                                fecha_desde=None, fecha_hasta=None,
                                offset: int = 0, limit: int = 50) -> dict:
        """
        Lista pedidos de una sucursal con filtros opcionales.
        
        Args:
            sucursal_id: ID de la sucursal
            estado: Filtrar por estado (opcional)
            fecha_desde: Fecha inicio (opcional)
            fecha_hasta: Fecha fin (opcional)
            offset: Offset para paginación
            limit: Límite de resultados
        
        Returns:
            dict: {pedidos: [...], total: int}
        """
        try:
            pedidos, total = PedidoDAO.listar_pedidos_por_sucursal(
                sucursal_id=sucursal_id,
                estado=estado,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                offset=offset,
                limit=limit
            )
            
            return {
                'pedidos': pedidos,
                'total': total,
                'offset': offset,
                'limit': limit
            }
        
        except Exception as e:
            logger.error(f"Error al listar pedidos: {str(e)}")
            raise
    
    
    @staticmethod
    def obtener_pedidos_activos(sucursal_id: int) -> dict:
        """
        Obtiene pedidos activos (no cancelados ni pagados) de una sucursal.
        Útil para dashboard de cocina/servicio.
        
        Args:
            sucursal_id: ID de la sucursal
        
        Returns:
            dict: {iniciados: [...], completos: [...], total_activos: int}
        """
        try:
            iniciados = PedidoDAO.obtener_pedidos_por_estado(sucursal_id, ESTADO_INICIADO)
            completos = PedidoDAO.obtener_pedidos_por_estado(sucursal_id, ESTADO_COMPLETO)
            
            return {
                'iniciados': iniciados,
                'completos': completos,
                'total_activos': len(iniciados) + len(completos)
            }
        
        except Exception as e:
            logger.error(f"Error al obtener pedidos activos: {str(e)}")
            raise

