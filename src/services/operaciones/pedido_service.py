"""
PedidoService - Business Logic para Pedido
Gestión de pedidos vinculados a reservas
"""

from datetime import datetime
from decimal import Decimal
from src.dao.operaciones.pedido_dao import PedidoDAO
from src.dao.operaciones.pedido_item_dao import PedidoItemDAO
from src.dao.operaciones.reserva_dao import ReservaDAO
from src.dao.catalogos.mesa_dao import MesaDAO
import logging

logger = logging.getLogger(__name__)


class PedidoService:
    """Service para Pedido"""
    
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
        
        VALIDACIONES:
        1. Reserva existe
        2. Mesa existe y está activa
        3. No hay pedido activo en esa reserva (max 1 por reserva)
        
        Args:
            sucursal_id: ID de sucursal
            reserva_id: ID de reserva (OBLIGATORIO)
            inicia_usuario_id: ID usuario que inicia (cliente, mesero, etc)
            mesa_id: ID de mesa
            folio: Folio único del pedido
            cliente_id: ID del cliente
            tipo_pedido: 1=Dine-in, 2=Pickup, 3=Delivery
            canal: 1=Mesero, 2=Sistema, 3=App
            notas: Notas
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            # VALIDACIÓN 1: Reserva existe
            reserva = ReservaDAO.obtener_reserva_por_id(reserva_id)
            if not reserva:
                return {"success": False, "error": f"Reserva {reserva_id} no existe"}
            
            # VALIDACIÓN 2: Mesa existe y activa
            mesa = MesaDAO.obtener_mesa_por_id(mesa_id)
            if not mesa:
                return {"success": False, "error": f"Mesa {mesa_id} no existe"}
            if mesa.get('es_activa') != 1:
                return {"success": False, "error": f"Mesa {mesa_id} no está activa"}
            
            # VALIDACIÓN 3: No hay pedido activo en esta reserva
            pedido_existente = PedidoDAO.obtener_pedido_por_reserva(reserva_id)
            if pedido_existente:
                return {
                    "success": False,
                    "error": f"Ya existe un pedido activo para esta reserva: {pedido_existente['id_pedido']}"
                }
            
            # Crear pedido
            pedido = PedidoDAO.crear_pedido(
                sucursal_id=sucursal_id,
                reserva_id=reserva_id,
                inicia_usuario_id=inicia_usuario_id,
                mesa_id=mesa_id,
                folio=folio,
                cliente_id=cliente_id,
                tipo_pedido=tipo_pedido,
                canal=canal,
                notas=notas
            )
            
            # Cambiar reserva a EnCurso si aún está Programada
            if reserva.get('estatus') == 1:
                ReservaDAO.iniciar_reserva(reserva_id)
            
            logger.info(f"Pedido creado: ID {pedido['id_pedido']}, reserva {reserva_id}, folio {folio}")
            return {"success": True, "data": pedido}
            
        except Exception as e:
            logger.error(f"Error en PedidoService.crear_pedido: {str(e)}")
            return {"success": False, "error": f"Error al crear pedido: {str(e)}"}
    
    
    @staticmethod
    def obtener_pedido(pedido_id: int) -> dict:
        """
        Obtener detalles completos de un pedido con sus items.
        
        Args:
            pedido_id: ID del pedido
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            pedido = PedidoDAO.obtener_pedido_por_id(pedido_id)
            if not pedido:
                return {"success": False, "error": f"Pedido {pedido_id} no existe"}
            
            logger.info(f"Pedido {pedido_id} obtenido")
            return {"success": True, "data": pedido}
            
        except Exception as e:
            logger.error(f"Error en PedidoService.obtener_pedido: {str(e)}")
            return {"success": False, "error": f"Error al obtener pedido: {str(e)}"}
    
    
    @staticmethod
    def agregar_item(
        pedido_id: int,
        cantidad: int,
        producto_id: int = None,
        combo_id: int = None,
        precio: Decimal = None,
        notas: str = None
    ) -> dict:
        """
        Agregar item a pedido.
        
        VALIDACIONES:
        1. Pedido existe
        2. Producto o combo existe (XOR)
        3. Cantidad válida
        
        Args:
            pedido_id: ID del pedido
            cantidad: Cantidad
            producto_id: ID del producto (opcional)
            combo_id: ID del combo (opcional)
            precio: Precio unitario (opcional)
            notas: Notas
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            # VALIDACIÓN 1: Pedido existe
            if not PedidoDAO.pedido_existe(pedido_id):
                return {"success": False, "error": f"Pedido {pedido_id} no existe"}
            
            # VALIDACIÓN 2: Cantidad válida
            if cantidad < 1:
                return {"success": False, "error": "cantidad debe ser >= 1"}
            
            # VALIDACIÓN 3: producto_id XOR combo_id
            if not producto_id and not combo_id:
                return {"success": False, "error": "Debe especificar producto_id O combo_id"}
            if producto_id and combo_id:
                return {"success": False, "error": "No puede especificar ambos producto_id y combo_id"}
            
            # Agregar item
            item = PedidoItemDAO.agregar_item(
                pedido_id=pedido_id,
                cantidad=cantidad,
                precio_unit=precio,
                producto_id=producto_id,
                combo_id=combo_id,
                notas=notas
            )
            
            logger.info(f"Item agregado a pedido {pedido_id}: cantidad={cantidad}, producto_id={producto_id}, combo_id={combo_id}")
            return {"success": True, "data": item}
            
        except ValueError as ve:
            logger.error(f"Error en validación: {str(ve)}")
            return {"success": False, "error": str(ve)}
        except Exception as e:
            logger.error(f"Error en PedidoService.agregar_item: {str(e)}")
            return {"success": False, "error": f"Error al agregar item: {str(e)}"}
    
    
    @staticmethod
    def confirmar_items_a_cocina(pedido_id: int, item_ids: list, usuario_id: int = None) -> dict:
        """
        Confirmar items para ir a cocina.
        
        *** CRITICAL: TRIGGERS INVENTORY CONSUMPTION ***
        *** ATOMIC & IRREVERSIBLE ONCE COMMITTED ***
        
        Args:
            pedido_id: ID del pedido
            item_ids: Lista de IDs de items a confirmar
            usuario_id: ID del usuario que confirma
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            # VALIDACIÓN: Pedido existe
            pedido = PedidoDAO.obtener_pedido_por_id(pedido_id)
            if not pedido:
                return {"success": False, "error": f"Pedido {pedido_id} no existe"}
            
            # Validar que todos los items existan
            items_a_confirmar = []
            for item_id in item_ids:
                item = PedidoItemDAO.obtener_item_por_id(item_id)
                if not item:
                    return {"success": False, "error": f"Item {item_id} no existe"}
                if item.get('pedido_id') != pedido_id:
                    return {"success": False, "error": f"Item {item_id} no pertenece a este pedido"}
                items_a_confirmar.append(item)
            
            # Cambiar estatus de items a EN COCINA (3)
            PedidoItemDAO.cambiar_estatus_items_multiplos(item_ids, 3)
            
            # CONSUMIR INVENTARIO
            from src.services.operaciones.inventario_service import InventarioService
            resultado_inventario = InventarioService.consumir_por_pedido(
                pedido_id=pedido_id,
                sucursal_id=pedido['sucursal_id'],
                items=items_a_confirmar
            )
            
            if not resultado_inventario['success']:
                # Rollback: revertir cambios de estatus
                PedidoItemDAO.cambiar_estatus_items_multiplos(item_ids, 2)
                return {
                    "success": False,
                    "error": f"No se pudo consumir inventario: {resultado_inventario.get('error')}"
                }
            
            # Registrar cambio en historial
            PedidoDAO.registrar_cambio_estatus(
                pedido_id=pedido_id,
                estatus=2,  # Enviado (a cocina)
                comentario=f"{len(item_ids)} items confirmados a cocina"
            )
            
            logger.info(
                f"INVENTORY CONSUMED: {len(item_ids)} items confirmados a cocina para pedido {pedido_id} "
                f"por usuario {usuario_id}. Movimientos: {len(resultado_inventario.get('data', []))}"
            )
            
            return {
                "success": True,
                "data": {
                    "items_confirmados": len(item_ids),
                    "movimientos": resultado_inventario.get('data', [])
                }
            }
            
        except Exception as e:
            logger.error(f"Error en PedidoService.confirmar_items_a_cocina: {str(e)}", exc_info=True)
            return {"success": False, "error": f"Error al confirmar items: {str(e)}"}
    
    
    @staticmethod
    def obtener_total(pedido_id: int) -> dict:
        """
        Obtener total del pedido.
        
        Returns:
            {success: bool, total?: Decimal, error?: str}
        """
        try:
            if not PedidoDAO.pedido_existe(pedido_id):
                return {"success": False, "error": f"Pedido {pedido_id} no existe"}
            
            total = PedidoItemDAO.obtener_total_items_pedido(pedido_id, solo_confirmados=True)
            return {"success": True, "total": float(total)}
            
        except Exception as e:
            logger.error(f"Error en PedidoService.obtener_total: {str(e)}")
            return {"success": False, "error": str(e)}
    
    
    @staticmethod
    def marcar_listo(pedido_id: int, item_id: int = None) -> dict:
        """
        Marcar item(s) como listo(s) (cocina terminó).
        
        Si item_id es None, marca TODOS los items en cocina como listos.
        Si item_id es especificado, marca solo ese item.
        
        Args:
            pedido_id: ID del pedido
            item_id: ID del item (opcional, si None marca todos)
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            if not PedidoDAO.pedido_existe(pedido_id):
                return {"success": False, "error": f"Pedido {pedido_id} no existe"}
            
            if item_id:
                # Marcar item específico
                if not PedidoItemDAO.item_existe(item_id):
                    return {"success": False, "error": f"Item {item_id} no existe"}
                
                PedidoItemDAO.cambiar_estatus_item(item_id, 4)  # Listo
                logger.info(f"Item {item_id} marcado como listo")
                
                return {"success": True, "data": {"items_listos": 1}}
            else:
                # Marcar todos los items en cocina como listos
                items_cocina = PedidoItemDAO.listar_items_en_cocina(pedido_id)
                
                if not items_cocina:
                    return {"success": True, "data": {"items_listos": 0}}
                
                item_ids = [item['id_pedido_item'] for item in items_cocina]
                PedidoItemDAO.cambiar_estatus_items_multiplos(item_ids, 4)
                logger.info(f"{len(item_ids)} items marcados como listos para pedido {pedido_id}")
                
                return {"success": True, "data": {"items_listos": len(item_ids)}}
            
        except Exception as e:
            logger.error(f"Error en PedidoService.marcar_listo: {str(e)}")
            return {"success": False, "error": str(e)}
