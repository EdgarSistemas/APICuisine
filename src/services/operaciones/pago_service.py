"""
PagoService - Lógica de negocio para Pagos
Responsabilidades:
- Crear pago ligado a pedido
- Marcar pago como completado
- Transicionar pedido a estatus PAGADO (5)
- Validaciones de monto y pedido
"""

import logging
from datetime import datetime

from src.core.db.session_manager import get_db_session
from src.models import Pago, Pedido

logger = logging.getLogger(__name__)


class PagoService:
    """
    Servicio para gestionar pagos de pedidos.
    Asegurar que el pedido esté completo antes de marcar como pagado.
    """
    
    @staticmethod
    def crear_pago(pedido_id, sucursal_id, monto, propina=0, moneda='MXN', usuario_id=None):
        """
        Crear registro de pago para un pedido.
        
        Args:
            pedido_id (int): ID del pedido a pagar
            sucursal_id (int): ID de la sucursal
            monto (float): Monto pagado
            propina (float): Propina (opcional)
            moneda (str): Moneda (MXN, USD, etc.)
            usuario_id (int): ID del cajero que registra el pago
        
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
                
                # Validar monto > 0
                if monto <= 0:
                    logger.warning(f"Monto inválido: {monto}")
                    return {
                        'success': False,
                        'error': 'El monto debe ser mayor a 0'
                    }
                
                # Crear pago
                pago = Pago(
                    pedido_id=pedido_id,
                    sucursal_id=sucursal_id,
                    monto=monto,
                    propina=propina,
                    moneda=moneda,
                    estatus=1,  # 1 = Pendiente
                    usuario_id=usuario_id,
                    created_at=datetime.utcnow()
                )
                
                session.add(pago)
                session.commit()
                
                logger.info(f"Pago creado: ID={pago.id_pago}, Pedido={pedido_id}, Monto={monto}")
                
                return {
                    'success': True,
                    'data': pago.to_dict()
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
    def marcar_pagado(pago_id, metodo_pago, referencia=None, usuario_id=None):
        """
        Marcar pago como completado.
        Transiciona pedido a estatus PAGADO (5).
        
        Args:
            pago_id (int): ID del pago
            metodo_pago (str): Método de pago (Efectivo, Tarjeta, QR, etc.)
            referencia (str): Número de transacción (opcional)
            usuario_id (int): ID del usuario que confirma
        
        Returns:
            dict: {success: bool, data: {pago_dict}, error: str}
        """
        try:
            with get_db_session() as session:
                # Obtener pago
                pago = session.query(Pago).filter(Pago.id_pago == pago_id).first()
                
                if not pago:
                    logger.warning(f"Pago {pago_id} no existe")
                    return {
                        'success': False,
                        'error': f'Pago {pago_id} no existe'
                    }
                
                # Obtener pedido asociado
                pedido = session.query(Pedido).filter(
                    Pedido.id_pedido == pago.pedido_id
                ).first()
                
                if not pedido:
                    logger.error(f"Pedido {pago.pedido_id} del pago {pago_id} no existe")
                    return {
                        'success': False,
                        'error': 'Pedido asociado no existe'
                    }
                
                # Actualizar pago
                pago.estatus = 2  # 2 = Pagado
                pago.metodo_pago = metodo_pago
                pago.referencia = referencia
                pago.fecha_pago = datetime.utcnow()
                
                # Transicionar pedido a PAGADO (estatus 5)
                pedido.estado_pedido = 5  # 5 = Pagado
                
                session.commit()
                
                logger.info(
                    f"Pago {pago_id} marcado como pagado. "
                    f"Pedido {pedido.id_pedido} transicionó a PAGADO. "
                    f"Método: {metodo_pago}"
                )
                
                return {
                    'success': True,
                    'data': pago.to_dict()
                }
        
        except Exception as e:
            logger.error(f"Error en marcar_pagado: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Error al marcar pago: {str(e)}'
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
