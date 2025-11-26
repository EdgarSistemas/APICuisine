"""
PagoService - Lógica de negocio para Pagos

Responsabilidades:
- Crear pago: automáticamente marca pedido e items como PAGADO (5)
- Marcar reserva como completada (3) si existe
- Aplicar cupón de descuento si se proporciona campania_usuario_id

Flujo simplificado:
  POST /api/pagos -> Pago creado en estatus 2 (Pagado)
                  -> Pedido transiciona a 5 (Pagado)
                  -> Items transicionan a 5 (Pagado)
                  -> Reserva (si existe) a 3 (Completada)
                  -> Cupón (si existe) marcado como usado

Columnas disponibles en pagos.Pago:
  id_pago, pedido_id, sucursal_id, monto, propina, moneda, estatus, usuario_id,
  monto_descontado, campania_usuario_id, created_at, updated_at
"""

import logging
from datetime import datetime
from decimal import Decimal

from src.core.db.session_manager import get_db_session
from src.models import Pago, Pedido
from src.models.operaciones.pedido_item_model import PedidoItem
from src.models.operaciones.reserva_model import Reserva
from src.models.marketing.campania_usuario_model import CampaniaUsuario

logger = logging.getLogger(__name__)


class PagoService:
    """
    Servicio para gestionar pagos de pedidos.
    Asegurar que el pedido esté completo antes de marcar como pagado.
    """
    
    @staticmethod
    def crear_pago(
        pedido_id, 
        sucursal_id, 
        monto, 
        propina=0, 
        moneda='MXN', 
        usuario_id=None,
        campania_usuario_id=None,
        monto_descontado=None
    ):
        """
        Crear registro de pago para un pedido.
        Automáticamente transiciona pedido e items a estado PAGADO (5).
        Marca reserva como completada (3) si existe.
        Invalida el cupón si se proporciona campania_usuario_id.
        
        Args:
            pedido_id (int): ID del pedido a pagar
            sucursal_id (int): ID de la sucursal
            monto (float): Monto total del pedido (antes de descuento)
            propina (float): Propina (opcional)
            moneda (str): Moneda (MXN, USD, etc.)
            usuario_id (int): ID del cajero que registra el pago
            campania_usuario_id (int): ID del cupón del cliente (opcional)
            monto_descontado (float): Monto del descuento aplicado (opcional)
        
        Returns:
            dict: {success: bool, data: {pago_dict}, error: str}
        """
        try:
            with get_db_session() as session:
                # Validar que pedido existe y pertenece a sucursal
                pedido = session.query(Pedido).filter(
                    Pedido.id_pedido == pedido_id,
                    Pedido.sucursal_id == sucursal_id
                ).first()
                
                if not pedido:
                    logger.warning(f"Pedido {pedido_id} no existe o sucursal mismatch")
                    return {
                        'success': False,
                        'error': 'Pedido no existe o no pertenece a esta sucursal'
                    }
                
                # Validar que pedido esté en Completo (3)
                if pedido.estado_pedido != 3:
                    return {
                        'success': False,
                        'error': f'Pedido debe estar en estado Completo (3), actualmente está en {pedido.estado_pedido}'
                    }
                
                # Validar monto > 0
                if monto <= 0:
                    logger.warning(f"Monto inválido: {monto}")
                    return {
                        'success': False,
                        'error': 'El monto debe ser mayor a 0'
                    }
                
                # Validar cupón si viene
                cupon_usado = False
                if campania_usuario_id:
                    campania_usuario = session.query(CampaniaUsuario).filter(
                        CampaniaUsuario.id_campania_usuario == campania_usuario_id
                    ).first()
                    
                    if not campania_usuario:
                        return {
                            'success': False,
                            'error': f'Cupón {campania_usuario_id} no existe'
                        }
                    
                    if campania_usuario.estatus != 0:
                        return {
                            'success': False,
                            'error': 'El cupón ya fue utilizado'
                        }
                
                # 1. Crear pago en estado PAGADO (2)
                pago = Pago(
                    pedido_id=pedido_id,
                    sucursal_id=sucursal_id,
                    monto=Decimal(str(monto)),
                    propina=Decimal(str(propina)),
                    moneda=moneda,
                    estatus=2,  # 2 = Pagado (directo)
                    usuario_id=usuario_id,
                    campania_usuario_id=campania_usuario_id,
                    monto_descontado=Decimal(str(monto_descontado)) if monto_descontado else None
                )
                session.add(pago)
                session.flush()
                
                # 2. Marcar cupón como usado si viene
                if campania_usuario_id:
                    campania_usuario = session.query(CampaniaUsuario).filter(
                        CampaniaUsuario.id_campania_usuario == campania_usuario_id
                    ).first()
                    
                    if campania_usuario:
                        campania_usuario.estatus = 1  # 1 = Usado
                        cupon_usado = True
                        logger.info(f"Cupón {campania_usuario_id} marcado como usado")
                
                # 3. Transicionar pedido a PAGADO (5)
                pedido.estado_pedido = 5
                pedido.updated_at = datetime.utcnow()
                
                # 4. Transicionar todos los items del pedido a PAGADO (5)
                items_actualizados = session.query(PedidoItem).filter(
                    PedidoItem.pedido_id == pedido.id_pedido,
                    PedidoItem.estatus_detalle.in_([2, 3])  # Solo items Listo o Completo
                ).update(
                    {PedidoItem.estatus_detalle: 5},
                    synchronize_session='fetch'
                )
                
                # 5. Marcar reserva como completada si existe
                reserva_completada = False
                if pedido.reserva_id:
                    reserva = session.query(Reserva).filter(
                        Reserva.id_reserva == pedido.reserva_id
                    ).first()
                    
                    if reserva and reserva.estatus == 2:  # 2 = EnCurso
                        reserva.estatus = 3  # 3 = Completada
                        reserva.updated_at = datetime.utcnow()
                        reserva_completada = True
                        logger.info(f"Reserva {reserva.id_reserva} marcada como Completada")
                
                session.commit()
                
                logger.info(
                    f"Pago creado y completado: ID={pago.id_pago}, Pedido={pedido_id} -> 5, "
                    f"Items actualizados={items_actualizados}, Reserva completada={reserva_completada}, "
                    f"Cupón usado={cupon_usado}"
                )
                
                return {
                    'success': True,
                    'data': pago.to_dict(),
                    'transiciones': {
                        'pedido': 5,
                        'items_actualizados': items_actualizados,
                        'reserva_completada': reserva_completada,
                        'cupon_usado': cupon_usado
                    }
                }
        
        except Exception as e:
            logger.error(f"Error en crear_pago: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Error al crear pago: {str(e)}'
            }
    
    
    @staticmethod
    def obtener_pago(pago_id):
        """
        Obtener detalles de un pago.
        
        Args:
            pago_id (int): ID del pago
        
        Returns:
            dict: {success: bool, data: {pago_dict}, error: str}
        """
        try:
            with get_db_session() as session:
                pago = session.query(Pago).filter(Pago.id_pago == pago_id).first()
                
                if not pago:
                    logger.warning(f"Pago {pago_id} no existe")
                    return {
                        'success': False,
                        'error': f'Pago {pago_id} no existe'
                    }
                
                return {
                    'success': True,
                    'data': pago.to_dict()
                }
        
        except Exception as e:
            logger.error(f"Error en obtener_pago: {str(e)}")
            return {
                'success': False,
                'error': f'Error al obtener pago: {str(e)}'
            }
    
    
    @staticmethod
    def actualizar_pago(pago_id, propina=None, usuario_id=None):
        """
        Actualizar datos de un pago (propina, etc).
        
        Args:
            pago_id (int): ID del pago
            propina (float): Nueva propina (opcional)
            usuario_id (int): ID del usuario que actualiza
        
        Returns:
            dict: {success: bool, data: {pago_dict}, error: str}
        """
        try:
            with get_db_session() as session:
                pago = session.query(Pago).filter(Pago.id_pago == pago_id).first()
                
                if not pago:
                    logger.warning(f"Pago {pago_id} no existe")
                    return {
                        'success': False,
                        'error': f'Pago {pago_id} no existe'
                    }
                
                # Actualizar campos permitidos
                if propina is not None:
                    if propina < 0:
                        return {
                            'success': False,
                            'error': 'Propina no puede ser negativa'
                        }
                    pago.propina = propina
                
                session.commit()
                
                logger.info(f"Pago {pago_id} actualizado por usuario {usuario_id}")
                
                return {
                    'success': True,
                    'data': pago.to_dict()
                }
        
        except Exception as e:
            logger.error(f"Error en actualizar_pago: {str(e)}")
            return {
                'success': False,
                'error': f'Error al actualizar pago: {str(e)}'
            }
    
    
    @staticmethod
    def cancelar_pago(pago_id, usuario_id=None):
        """
        Cancelar pago (soft delete - cambiar estatus).
        Solo admins.
        
        Args:
            pago_id (int): ID del pago
            usuario_id (int): ID del admin que cancela
        
        Returns:
            dict: {success: bool, error: str}
        """
        try:
            with get_db_session() as session:
                pago = session.query(Pago).filter(Pago.id_pago == pago_id).first()
                
                if not pago:
                    logger.warning(f"Pago {pago_id} no existe")
                    return {
                        'success': False,
                        'error': f'Pago {pago_id} no existe'
                    }
                
                # Soft delete
                pago.estatus = 3  # 3 = Voided/Cancelado
                
                session.commit()
                
                logger.info(f"Pago {pago_id} cancelado por admin {usuario_id}")
                
                return {
                    'success': True
                }
        
        except Exception as e:
            logger.error(f"Error en cancelar_pago: {str(e)}")
            return {
                'success': False,
                'error': f'Error al cancelar pago: {str(e)}'
            }
    
    
    @staticmethod
    def listar_pedidos_pendientes_pago(sucursal_id):
        """
        Listar pedidos en estado Completo (3) que están pendientes de pago.
        Incluye items con subtotales y total del pedido.
        
        Args:
            sucursal_id (int): ID de la sucursal
        
        Returns:
            dict: {success: bool, data: [{pedido con items y total}], error: str}
        """
        try:
            from src.models.catalogos.producto_model import Producto
            from src.models.catalogos.combo_model import Combo
            
            with get_db_session() as session:
                # Pedidos en estado 3 (Completo) - listos para pagar
                pedidos = session.query(Pedido).filter(
                    Pedido.sucursal_id == sucursal_id,
                    Pedido.estado_pedido == 3  # 3 = Completo
                ).order_by(Pedido.created_at.desc()).all()
                
                resultado = []
                for pedido in pedidos:
                    # Verificar si ya tiene pago registrado
                    pago_existente = session.query(Pago).filter(
                        Pago.pedido_id == pedido.id_pedido,
                        Pago.estatus.in_([1, 2])  # Pendiente o Pagado
                    ).first()
                    
                    # Obtener items del pedido con info de producto/combo
                    items_pedido = session.query(PedidoItem).filter(
                        PedidoItem.pedido_id == pedido.id_pedido,
                        PedidoItem.estatus_detalle.notin_([4])  # Excluir cancelados
                    ).all()
                    
                    items_detalle = []
                    total_pedido = 0
                    
                    for item in items_pedido:
                        # Calcular subtotal del item
                        precio_unit = float(item.precio_unit) if item.precio_unit else 0
                        subtotal = precio_unit * item.cantidad
                        total_pedido += subtotal
                        
                        # Obtener nombre del producto o combo
                        nombre_item = None
                        tipo_item = None
                        
                        if item.producto_id:
                            producto = session.query(Producto).filter(
                                Producto.id_producto == item.producto_id
                            ).first()
                            nombre_item = producto.nombre if producto else f"Producto #{item.producto_id}"
                            tipo_item = "producto"
                        elif item.combo_id:
                            combo = session.query(Combo).filter(
                                Combo.id_combo == item.combo_id
                            ).first()
                            nombre_item = combo.nombre if combo else f"Combo #{item.combo_id}"
                            tipo_item = "combo"
                        
                        items_detalle.append({
                            'id_pedido_item': item.id_pedido_item,
                            'tipo': tipo_item,
                            'producto_id': item.producto_id,
                            'combo_id': item.combo_id,
                            'nombre': nombre_item,
                            'cantidad': item.cantidad,
                            'precio_unit': precio_unit,
                            'subtotal': subtotal,
                            'notas': item.notas,
                            'estatus': item.estatus_detalle
                        })
                    
                    # Construir diccionario del pedido
                    pedido_dict = {
                        'id_pedido': pedido.id_pedido,
                        'folio': pedido.folio,
                        'sucursal_id': pedido.sucursal_id,
                        'cliente_id': pedido.cliente_id,
                        'mesa_id': pedido.mesa_id,
                        'tipo_pedido': pedido.tipo_pedido,
                        'tipo_pedido_display': 'Dine-in' if pedido.tipo_pedido == 1 else 'Takeaway',
                        'estado_pedido': pedido.estado_pedido,
                        'notas': pedido.notas,
                        'created_at': pedido.created_at.isoformat() if pedido.created_at else None,
                        'items': items_detalle,
                        'total': round(total_pedido, 2),
                        'tiene_pago': pago_existente is not None,
                        'pago_id': pago_existente.id_pago if pago_existente else None,
                        'pago_estatus': pago_existente.estatus if pago_existente else None
                    }
                    
                    resultado.append(pedido_dict)
                
                logger.info(f"Listados {len(resultado)} pedidos pendientes de pago con detalle")
                
                return {
                    'success': True,
                    'data': resultado
                }
        
        except Exception as e:
            logger.error(f"Error en listar_pedidos_pendientes_pago: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Error al listar pedidos: {str(e)}'
            }
