"""
PagoDAO - Data Access Layer for Payments
"""

import logging
from decimal import Decimal
from datetime import datetime, timedelta

from src.core.db.session_manager import get_db_session
from src.models import Pago, Pedido, Sucursal, Usuario

logger = logging.getLogger(__name__)


class PagoDAO:
    """Data access methods for Pago entity"""
    
    @staticmethod
    def crear_pago(pedido_id: int, sucursal_id: int, monto: Decimal, 
                   propina: Decimal = Decimal('0.00'), moneda: str = 'MXN', 
                   usuario_id: int = None) -> dict:
        """
        Create new payment record.
        
        Returns: {id_pago, pedido_id, sucursal_id, monto, propina, moneda, estatus, usuario_id, created_at, updated_at}
        Raises: ValueError if validation fails
        """
        try:
            with get_db_session() as session:
                pago = Pago(
                    pedido_id=pedido_id,
                    sucursal_id=sucursal_id,
                    monto=monto,
                    propina=propina,
                    moneda=moneda,
                    estatus=1,  # Registrado
                    usuario_id=usuario_id
                )
                session.add(pago)
                session.flush()
                pago_id = pago.id_pago
                session.commit()
                
                logger.info(f"Pago creado: id_pago={pago_id}, pedido_id={pedido_id}, monto={monto}")
                return pago.to_dict()
        except Exception as e:
            logger.error(f"Error en PagoDAO.crear_pago: {str(e)}")
            raise ValueError(f"Error al crear pago: {str(e)}")
    
    
    @staticmethod
    def obtener_pago(pago_id: int) -> dict:
        """Get payment by ID"""
        try:
            with get_db_session() as session:
                pago = session.query(Pago).filter(Pago.id_pago == pago_id).first()
                if not pago:
                    raise ValueError(f"Pago {pago_id} no existe")
                return pago.to_dict()
        except Exception as e:
            logger.error(f"Error en PagoDAO.obtener_pago: {str(e)}")
            raise ValueError(str(e))
    
    
    @staticmethod
    def listar_pagos(sucursal_id: int = None, pedido_id: int = None, 
                     estatus: int = None, fecha_inicio: datetime = None, 
                     fecha_fin: datetime = None, limit: int = 50, 
                     offset: int = 0) -> dict:
        """List payments with filters"""
        try:
            with get_db_session() as session:
                query = session.query(Pago)
                
                if sucursal_id:
                    query = query.filter(Pago.sucursal_id == sucursal_id)
                if pedido_id:
                    query = query.filter(Pago.pedido_id == pedido_id)
                if estatus:
                    query = query.filter(Pago.estatus == estatus)
                if fecha_inicio:
                    query = query.filter(Pago.created_at >= fecha_inicio)
                if fecha_fin:
                    query = query.filter(Pago.created_at <= fecha_fin)
                
                total = query.count()
                pagos = query.order_by(Pago.created_at.desc()).limit(limit).offset(offset).all()
                
                return {
                    'pagos': [p.to_dict() for p in pagos],
                    'total': total
                }
        except Exception as e:
            logger.error(f"Error en PagoDAO.listar_pagos: {str(e)}")
            raise ValueError(str(e))
    
    
    @staticmethod
    def listar_pagos_por_pedido(pedido_id: int) -> list:
        """Get all payments for specific order"""
        try:
            with get_db_session() as session:
                pagos = session.query(Pago).filter(
                    Pago.pedido_id == pedido_id
                ).order_by(Pago.created_at.desc()).all()
                return [p.to_dict() for p in pagos]
        except Exception as e:
            logger.error(f"Error en PagoDAO.listar_pagos_por_pedido: {str(e)}")
            raise ValueError(str(e))
    
    
    @staticmethod
    def obtener_pago_principal(pedido_id: int) -> dict:
        """Get primary confirmed payment for order (estatus=2)"""
        try:
            with get_db_session() as session:
                pago = session.query(Pago).filter(
                    Pago.pedido_id == pedido_id,
                    Pago.estatus == 2  # Confirmado
                ).order_by(Pago.created_at.desc()).first()
                return pago.to_dict() if pago else None
        except Exception as e:
            logger.error(f"Error en PagoDAO.obtener_pago_principal: {str(e)}")
            raise ValueError(str(e))
    
    
    @staticmethod
    def cambiar_estatus(pago_id: int, nuevo_estatus: int, usuario_id: int = None) -> dict:
        """Change payment status with validation"""
        try:
            with get_db_session() as session:
                pago = session.query(Pago).filter(Pago.id_pago == pago_id).first()
                if not pago:
                    raise ValueError(f"Pago {pago_id} no existe")
                
                # Validar transiciones permitidas
                estatus_actual = pago.estatus
                transiciones_validas = {
                    1: [2, 3],  # Registrado → Confirmado o Revertido
                    2: [3],     # Confirmado → Revertido (admin only)
                    3: []       # Revertido (terminal)
                }
                
                if nuevo_estatus not in transiciones_validas.get(estatus_actual, []):
                    raise ValueError(f"Transición inválida: {estatus_actual} → {nuevo_estatus}")
                
                pago.estatus = nuevo_estatus
                pago.usuario_id = usuario_id
                pago.updated_at = datetime.utcnow()
                session.commit()
                
                logger.info(f"Pago {pago_id} cambió estatus: {estatus_actual} → {nuevo_estatus}")
                return pago.to_dict()
        except Exception as e:
            logger.error(f"Error en PagoDAO.cambiar_estatus: {str(e)}")
            raise ValueError(str(e))
    
    
    @staticmethod
    def actualizar_pago(pago_id: int, propina: Decimal = None, 
                       monto: Decimal = None) -> dict:
        """Update payment (only before confirmation)"""
        try:
            with get_db_session() as session:
                pago = session.query(Pago).filter(Pago.id_pago == pago_id).first()
                if not pago:
                    raise ValueError(f"Pago {pago_id} no existe")
                
                if pago.estatus != 1:
                    raise ValueError("No se puede actualizar pago confirmado")
                
                if propina is not None:
                    if propina < Decimal('0.00'):
                        raise ValueError("Propina no puede ser negativa")
                    pago.propina = propina
                
                if monto is not None:
                    if monto <= Decimal('0.00'):
                        raise ValueError("Monto debe ser mayor a 0")
                    pago.monto = monto
                
                pago.updated_at = datetime.utcnow()
                session.commit()
                
                logger.info(f"Pago {pago_id} actualizado")
                return pago.to_dict()
        except Exception as e:
            logger.error(f"Error en PagoDAO.actualizar_pago: {str(e)}")
            raise ValueError(str(e))
    
    
    @staticmethod
    def calcular_total(pago_id: int) -> Decimal:
        """Calculate total (monto + propina)"""
        try:
            with get_db_session() as session:
                pago = session.query(Pago).filter(Pago.id_pago == pago_id).first()
                if not pago:
                    raise ValueError(f"Pago {pago_id} no existe")
                return Decimal(str(pago.monto)) + Decimal(str(pago.propina))
        except Exception as e:
            logger.error(f"Error en PagoDAO.calcular_total: {str(e)}")
            raise ValueError(str(e))
    
    
    @staticmethod
    def validar_pago(pago_id: int) -> dict:
        """Validate payment consistency"""
        try:
            with get_db_session() as session:
                pago = session.query(Pago).filter(Pago.id_pago == pago_id).first()
                if not pago:
                    return {'valid': False, 'errors': ['Pago no existe']}
                
                errors = []
                
                # Validar pedido existe
                pedido = session.query(Pedido).filter(Pedido.id_pedido == pago.pedido_id).first()
                if not pedido:
                    errors.append('Pedido asociado no existe')
                else:
                    # Validar sucursal match
                    if pedido.sucursal_id != pago.sucursal_id:
                        errors.append('Sucursal no coincide con pedido')
                
                # Validar estatus válido
                if pago.estatus not in [1, 2, 3]:
                    errors.append(f'Estatus inválido: {pago.estatus}')
                
                return {
                    'valid': len(errors) == 0,
                    'errors': errors
                }
        except Exception as e:
            logger.error(f"Error en PagoDAO.validar_pago: {str(e)}")
            raise ValueError(str(e))
