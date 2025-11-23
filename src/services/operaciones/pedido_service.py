"""
PedidoService - Servicio de negocio para Pedidos
Orquesta creación de pedidos, consumo de inventario y cambios de estado
Maneja transacciones atómicas para garantizar consistencia
Estados: 1=Creado, 2=Confirmado, 3=EnPreparacion, 4=Listo, 5=Entregado, 6=Cancelado
Inventory descent: SOLO cuando estado_pedido → 3 (EnPreparacion)
"""

from datetime import datetime
from src.core.db.session_manager import get_db_session
from src.dao.operaciones.pedido_dao import PedidoDAO
from src.dao.operaciones.reserva_dao import ReservaDAO
from src.dao.inventario.inventario_dao import InventarioDAO
from src.models.operaciones.reserva_model import Reserva
import logging

logger = logging.getLogger(__name__)


class PedidoService:
    """Servicio de negocio para Pedidos"""
    
    @staticmethod
    def crear_pedido_dine_in(sucursal_id: int, cliente_id: int, canal: int, 
                            reserva_id: int, inicia_usuario_id: int, items: list, notas: str = None) -> dict:
        """
        Crea pedido tipo Dine-in (con mesa y reserva)
        
        Flujo:
        1. Validar que reserva existe y está activa (estatus 1 o 2)
        2. Obtener mesa_id de la reserva
        3. Crear Pedido (estado=1 Creado)
        4. Agregar items al pedido
        5. Retornar pedido creado
        
        Args:
            sucursal_id: ID de sucursal
            cliente_id: ID del cliente (OBLIGATORIO)
            canal: 1=PWA, 2=Móvil, 3=Presencial
            reserva_id: ID de reserva (OBLIGATORIO)
            inicia_usuario_id: ID del usuario que inicia
            items: [{"producto_id": X, "cantidad": Y, "notas": "..."}, ...]
            notas: Notas del pedido
        
        Returns:
            dict: Pedido completo con items
        
        Raises:
            ValueError: Si validaciones fallan
        """
        db = get_db_session()
        try:
            # 1. Validar reserva
            reserva = db.session.query(Reserva).filter_by(id_reserva=reserva_id).first()
            if not reserva:
                raise ValueError(f"Reserva {reserva_id} no existe")
            
            if reserva.estatus not in [1, 2]:
                raise ValueError(f"Reserva debe estar Activa (1) o Confirmada (2), estado actual: {reserva.estatus}")
            
            # 2. Obtener mesa_id de la reserva
            mesa_id = reserva.mesa_id
            if not mesa_id:
                raise ValueError(f"Reserva {reserva_id} no tiene mesa asignada")
            
            # 3. Crear pedido (estado=1 Creado, sin inventario aún)
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
            
            # 4. Agregar items
            items_creados = []
            for item in items:
                item_data = PedidoDAO.crear_pedido_item(
                    pedido_id=pedido_id,
                    producto_id=item.get('producto_id'),
                    combo_id=item.get('combo_id'),
                    cantidad=item.get('cantidad', 1),
                    notas=item.get('notas')
                )
                items_creados.append(item_data)
            
            # 5. Retornar pedido completo
            pedido_completo = PedidoDAO.obtener_pedido_completo(pedido_id)
            
            logger.info(f"Pedido Dine-in creado: {pedido_id}, reserva={reserva_id}, mesa={mesa_id}, items={len(items_creados)}")
            
            return pedido_completo
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al crear pedido Dine-in: {str(e)}")
            raise
    
    
    @staticmethod
    def crear_pedido_takeaway(sucursal_id: int, cliente_id: int, canal: int, 
                             inicia_usuario_id: int, items: list, notas: str = None) -> dict:
        """
        Crea pedido tipo Takeaway (sin mesa, crea reserva interna)
        
        Flujo:
        1. Validar cliente_id (OBLIGATORIO para takeaway)
        2. Crear Reserva interna: estatus=5, recepcionista_id=NULL, cliente_id=inicia_usuario_id
        3. Crear Pedido (tipo_pedido=2, mesa_id=NULL, reserva_id=reserva_interna)
        4. Agregar items al pedido
        5. Retornar pedido creado
        
        Args:
            sucursal_id: ID de sucursal
            cliente_id: ID del cliente (OBLIGATORIO)
            canal: 1=PWA, 2=Móvil, 3=Presencial
            inicia_usuario_id: ID del usuario que inicia
            items: [{"producto_id": X, "cantidad": Y, "notas": "..."}, ...]
            notas: Notas del pedido
        
        Returns:
            dict: Pedido completo con items
        
        Raises:
            ValueError: Si validaciones fallan
        """
        db = get_db_session()
        try:
            # 1. Validar cliente_id (OBLIGATORIO)
            if not cliente_id:
                raise ValueError("cliente_id es OBLIGATORIO para pedidos Takeaway")
            
            # 2. Crear Reserva interna
            #    estatus=5 (sin procesar/interna), no tiene recepcionista, cliente=inicia_usuario_id
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
            
            # 4. Agregar items
            items_creados = []
            for item in items:
                item_data = PedidoDAO.crear_pedido_item(
                    pedido_id=pedido_id,
                    producto_id=item.get('producto_id'),
                    combo_id=item.get('combo_id'),
                    cantidad=item.get('cantidad', 1),
                    notas=item.get('notas')
                )
                items_creados.append(item_data)
            
            # 5. Retornar pedido completo
            pedido_completo = PedidoDAO.obtener_pedido_completo(pedido_id)
            pedido_completo['reserva_interna_id'] = reserva_interna_id
            
            logger.info(f"Pedido Takeaway creado: {pedido_id}, cliente={cliente_id}, items={len(items_creados)}")
            
            return pedido_completo
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al crear pedido Takeaway: {str(e)}")
            raise
    
    
    @staticmethod
    def confirmar_pedido(pedido_id: int, usuario_id: int = None) -> dict:
        """
        Confirma un pedido (cambio de estado: 1 → 2)
        
        Validaciones:
        - Pedido debe estar en estado 1 (Creado)
        - Pedido debe tener al menos 1 item
        
        NO consume inventario aún (ocurre en cambiar_a_preparacion)
        
        Args:
            pedido_id: ID del pedido
            usuario_id: ID del usuario que confirma
        
        Returns:
            dict: Pedido actualizado
        
        Raises:
            ValueError: Si validaciones fallan
        """
        db = get_db_session()
        try:
            pedido_data = PedidoDAO.obtener_pedido_completo(pedido_id)
            if not pedido_data:
                raise ValueError(f"Pedido {pedido_id} no existe")
            
            if pedido_data['estado_pedido'] != 1:
                raise ValueError(f"Solo se pueden confirmar pedidos en estado Creado (1)")
            
            if not pedido_data['items']:
                raise ValueError(f"Pedido debe tener al menos 1 item")
            
            # Cambiar a estado 2 (Confirmado)
            PedidoDAO.cambiar_estado_pedido(
                pedido_id=pedido_id,
                nuevo_estado=2,
                usuario_id=usuario_id,
                comentario="Pedido confirmado"
            )
            
            db.session.commit()
            
            resultado = PedidoDAO.obtener_pedido_completo(pedido_id)
            logger.info(f"Pedido {pedido_id} confirmado (estado 1→2)")
            
            return resultado
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al confirmar pedido: {str(e)}")
            raise
    
    
    @staticmethod
    def cambiar_a_preparacion(pedido_id: int, usuario_id: int = None) -> dict:
        """
        Cambia pedido a preparación y CONSUME INVENTARIO
        (estado: 2 → 3 EnPreparacion)
        
        Flujo CRÍTICO:
        1. Validar pedido está en estado 2 (Confirmado)
        2. Para cada item del pedido:
           a. Si es PRODUCTO: obtener receta, validar stock de insumos
           b. Si es COMBO: resolver a productos → insumos (cascada)
           c. Consumir insumos por lotes (FIFO, cascada)
           d. Registrar Movimientos
        3. Si TODO OK, cambiar estado a 3 (EnPreparacion)
        4. Si error, ROLLBACK todo
        
        Args:
            pedido_id: ID del pedido
            usuario_id: ID del usuario que envía a cocina
        
        Returns:
            dict: Pedido actualizado con consumos registrados
        
        Raises:
            ValueError: Si falla cualquier consumo
        """
        db = get_db_session()
        try:
            pedido_data = PedidoDAO.obtener_pedido_completo(pedido_id)
            if not pedido_data:
                raise ValueError(f"Pedido {pedido_id} no existe")
            
            if pedido_data['estado_pedido'] != 2:
                raise ValueError(f"Solo se pueden enviar a preparación pedidos confirmados (estado 2)")
            
            sucursal_id = pedido_data['sucursal_id']
            
            # Procesar cada item
            for item in pedido_data['items']:
                producto_id = item.get('producto_id')
                combo_id = item.get('combo_id')
                cantidad_item = item.get('cantidad')
                
                # Dict para acumular insumos: {insumo_id: cantidad_total}
                insumos_a_consumir = {}
                
                if producto_id:
                    # CASO 1: Es un Producto directo
                    insumos_requeridos = InventarioDAO.obtener_insumos_de_producto(producto_id)
                    
                    if insumos_requeridos:
                        for insumo in insumos_requeridos:
                            insumo_id = insumo['insumo_id']
                            cant_por_unidad = insumo['cantidad_requerida']
                            cant_total = cant_por_unidad * cantidad_item
                            insumos_a_consumir[insumo_id] = insumos_a_consumir.get(insumo_id, 0) + cant_total
                    else:
                        logger.warning(f"Producto {producto_id} no tiene receta definida")
                
                elif combo_id:
                    # CASO 2: Es un Combo (cascada: Combo → Productos → Insumos)
                    insumos_combo = InventarioDAO.calcular_insumos_necesarios_combo(
                        combo_id=combo_id,
                        cantidad_pedido=cantidad_item
                    )
                    
                    if insumos_combo:
                        # Acumular insumos del combo
                        for insumo_id, cant_necesaria in insumos_combo.items():
                            insumos_a_consumir[insumo_id] = insumos_a_consumir.get(insumo_id, 0) + cant_necesaria
                    else:
                        logger.warning(f"Combo {combo_id} no tiene insumos resolubles")
                
                # Validar stock de todos los insumos del item actual
                for insumo_id, cantidad_necesaria in insumos_a_consumir.items():
                    hay_stock, disponible, error = InventarioDAO.verificar_stock_suficiente(
                        producto_id=insumo_id,
                        cantidad_necesaria=int(cantidad_necesaria),
                        sucursal_id=sucursal_id
                    )
                    
                    if not hay_stock:
                        raise ValueError(
                            f"Stock insuficiente para insumo {insumo_id}: {error}"
                        )
                
                # Consumir todos los insumos del item
                for insumo_id, cantidad_necesaria in insumos_a_consumir.items():
                    exito, lotes_consumidos, error = InventarioDAO.consumir_insumo_por_lotes(
                        producto_id=insumo_id,
                        cantidad_a_consumir=int(cantidad_necesaria),
                        sucursal_id=sucursal_id,
                        referencia=f"PEDIDO_{pedido_id}"
                    )
                    
                    if not exito:
                        raise ValueError(f"Error al consumir insumo {insumo_id}: {error}")
                    
                    tipo_item = "PRODUCTO" if producto_id else f"COMBO({combo_id})"
                    logger.info(f"{tipo_item} item: Insumo {insumo_id} consumido - {len(lotes_consumidos)} lotes, total={cantidad_necesaria}")
            
            # Si TODO OK, cambiar estado a 3 (EnPreparacion)
            PedidoDAO.cambiar_estado_pedido(
                pedido_id=pedido_id,
                nuevo_estado=3,
                usuario_id=usuario_id,
                comentario="Pedido en preparación, inventario consumido"
            )
            
            db.session.commit()
            
            resultado = PedidoDAO.obtener_pedido_completo(pedido_id)
            logger.info(f"Pedido {pedido_id} en preparación (estado 2→3), inventario consumido")
            
            return resultado
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al cambiar a preparación: {str(e)}")
            raise
    
    @staticmethod
    def obtener_pedido(pedido_id: int) -> dict:
        """
        Obtiene los detalles completos de un pedido
        
        Args:
            pedido_id: ID del pedido
        
        Returns:
            dict: Pedido completo con items e histórico
        
        Raises:
            ValueError: Si el pedido no existe
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
        Agrega un item (producto o combo) a un pedido
        
        Validaciones:
        - Pedido debe estar en estado 1 (Creado)
        - Debe proporcionar producto_id XOR combo_id (no ambos, no ninguno)
        - Cantidad debe ser válida (1-100)
        
        Args:
            pedido_id: ID del pedido
            producto_id: ID del producto (optional si combo_id)
            combo_id: ID del combo (optional si producto_id)
            cantidad: Cantidad del item (1-100)
            notas: Notas adicionales
        
        Returns:
            dict: Item creado
        
        Raises:
            ValueError: Si validaciones fallan
        """
        try:
            # Validar que pedido existe y está en estado Creado
            pedido = PedidoDAO.obtener_pedido_completo(pedido_id)
            if not pedido:
                raise ValueError(f"Pedido {pedido_id} no existe")
            
            if pedido['estado_pedido'] != 1:
                raise ValueError(f"Solo se pueden agregar items a pedidos en estado Creado (1). Estado actual: {pedido['estado_pedido']}")
            
            # Validar producto_id XOR combo_id
            if not producto_id and not combo_id:
                raise ValueError("Debe proporcionar producto_id o combo_id")
            
            if producto_id and combo_id:
                raise ValueError("No puede proporcionar ambos: producto_id y combo_id")
            
            # Validar cantidad
            if not isinstance(cantidad, int) or cantidad < 1 or cantidad > 100:
                raise ValueError("Cantidad debe ser un número entre 1 y 100")
            
            # Crear item
            item = PedidoDAO.crear_pedido_item(
                pedido_id=pedido_id,
                producto_id=producto_id,
                combo_id=combo_id,
                cantidad=cantidad,
                notas=notas
            )
            
            logger.info(f"Item agregado a pedido {pedido_id}: producto={producto_id}, combo={combo_id}, cantidad={cantidad}")
            return item
        
        except Exception as e:
            logger.error(f"Error al agregar item: {str(e)}")
            raise
    
    
    @staticmethod
    def cambiar_a_listo(pedido_id: int, usuario_id: int = None) -> dict:
        """
        Cambia pedido a listo (estado: 3 → 4)
        
        Args:
            pedido_id: ID del pedido
            usuario_id: ID del usuario que marca como listo
        
        Returns:
            dict: Pedido actualizado
        """
        db = get_db_session()
        try:
            pedido_data = PedidoDAO.obtener_pedido_completo(pedido_id)
            if not pedido_data:
                raise ValueError(f"Pedido {pedido_id} no existe")
            
            if pedido_data['estado_pedido'] != 3:
                raise ValueError(f"Solo se pueden marcar como listo pedidos en preparación (estado 3)")
            
            PedidoDAO.cambiar_estado_pedido(
                pedido_id=pedido_id,
                nuevo_estado=4,
                usuario_id=usuario_id,
                comentario="Pedido listo para servir"
            )
            
            db.session.commit()
            
            resultado = PedidoDAO.obtener_pedido_completo(pedido_id)
            logger.info(f"Pedido {pedido_id} listo (estado 3→4)")
            
            return resultado
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al cambiar a listo: {str(e)}")
            raise
    
    
    @staticmethod
    def cancelar_pedido(pedido_id: int, usuario_id: int = None, comentario: str = None) -> dict:
        """
        Cancela un pedido (estado: * → 6)
        
        NOTA: Solo se pueden cancelar pedidos en estado Creado (1) o Confirmado (2)
        No se pueden cancelar si ya están en cocina (3) o posteriores.
        
        Args:
            pedido_id: ID del pedido
            usuario_id: ID del usuario que cancela
            comentario: Comentario de cancelación
        
        Returns:
            dict: Pedido actualizado
        
        Raises:
            ValueError: Si no se puede cancelar
        """
        db = get_db_session()
        try:
            pedido_data = PedidoDAO.obtener_pedido_completo(pedido_id)
            if not pedido_data:
                raise ValueError(f"Pedido {pedido_id} no existe")
            
            estado_actual = pedido_data['estado_pedido']
            
            # Solo permitir cancelación en estados 1 (Creado) o 2 (Confirmado)
            if estado_actual not in [1, 2]:
                raise ValueError(
                    f"No se pueden cancelar pedidos en estado {estado_actual}. "
                    f"Solo se pueden cancelar pedidos en Creado (1) o Confirmado (2)"
                )
            
            PedidoDAO.cambiar_estado_pedido(
                pedido_id=pedido_id,
                nuevo_estado=6,
                usuario_id=usuario_id,
                comentario=comentario or "Pedido cancelado"
            )
            
            db.session.commit()
            
            resultado = PedidoDAO.obtener_pedido_completo(pedido_id)
            logger.info(f"Pedido {pedido_id} cancelado (estado {estado_actual}→6)")
            
            return resultado
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al cancelar pedido: {str(e)}")
            raise
    
    
    @staticmethod
    def entregar_pedido(pedido_id: int, usuario_id: int = None) -> dict:
        """
        Marca pedido como entregado (estado: 4 → 5)
        
        Args:
            pedido_id: ID del pedido
            usuario_id: ID del usuario que entrega
        
        Returns:
            dict: Pedido actualizado
        """
        db = get_db_session()
        try:
            pedido_data = PedidoDAO.obtener_pedido_completo(pedido_id)
            if not pedido_data:
                raise ValueError(f"Pedido {pedido_id} no existe")
            
            if pedido_data['estado_pedido'] != 4:
                raise ValueError(f"Solo se pueden entregar pedidos listos (estado 4)")
            
            PedidoDAO.cambiar_estado_pedido(
                pedido_id=pedido_id,
                nuevo_estado=5,
                usuario_id=usuario_id,
                comentario="Pedido entregado"
            )
            
            db.session.commit()
            
            resultado = PedidoDAO.obtener_pedido_completo(pedido_id)
            logger.info(f"Pedido {pedido_id} entregado (estado 4→5)")
            
            return resultado
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al entregar pedido: {str(e)}")
            raise

