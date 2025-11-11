"""
PagoController - Gestión de pagos
Endpoints: POST, GET, GET/{id}, PUT, DELETE (soft)
Note: Pago → Pedido relationship, validates pedido ownership
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from src.core.utils.multitenant import (
    es_admin,
    validar_acceso_sucursal,
    agregar_filtro_sucursal,
    validar_pertenencia_sucursal,
    validar_sucursal_existe
)
from src.models import Pago, Pedido

logger = logging.getLogger(__name__)
bp = Blueprint('pagos', __name__, url_prefix='/api/pagos')


# ============================================================================
# POST /api/pagos - Crear Pago (Admin + Cajero)
# ============================================================================
@bp.route('', methods=['POST'])
@jwt_required()
def crear_pago():
    """
    Crear pago (Admin o Cajero de su sucursal)
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json()
        
        # Validación 1: campos requeridos
        pedido_id = data.get('pedido_id')
        sucursal_id = data.get('sucursal_id')
        monto = data.get('monto')
        
        if not pedido_id or not sucursal_id or not monto:
            return {'success': False, 'error': 'pedido_id, sucursal_id, monto requeridos'}, 400
        
        # Validación 2: sucursal existe
        if not validar_sucursal_existe(sucursal_id):
            return {'success': False, 'error': 'Sucursal no existe'}, 400
        
        # Validación 3: usuario tiene acceso
        if not validar_acceso_sucursal(usuario_id, sucursal_id):
            return {'success': False, 'error': 'FORBIDDEN'}, 403
        
        from src.core.db.session_manager import get_db_session
        with get_db_session() as session:
            # Validación 4: pedido existe y pertenece a sucursal
            pedido = session.query(Pedido).get(pedido_id)
            if not pedido or pedido.sucursal_id != sucursal_id:
                return {'success': False, 'error': 'Pedido no existe o sucursal mismatch'}, 400
            
            # Crear pago
            pago = Pago(
                pedido_id=pedido_id,
                sucursal_id=sucursal_id,
                monto=monto,
                propina=data.get('propina', 0),
                moneda=data.get('moneda', 'MXN'),
                estatus=data.get('estatus', 1),  # 1 = Pagado
                usuario_id=usuario_id
            )
            
            session.add(pago)
            session.commit()
            logger.info(f"Pago {pago.id_pago} creado por usuario {usuario_id}")
            
            return {
                'success': True,
                'data': pago.to_dict(),
                'message': 'Pago creado'
            }, 201
        
    except Exception as e:
        logger.error(f"Error creando pago: {str(e)}")
        return {'success': False, 'error': 'Error interno'}, 500


# ============================================================================
# GET /api/pagos - Listar Pagos
# ============================================================================
@bp.route('', methods=['GET'])
@jwt_required()
def obtener_pagos():
    """
    Listar pagos (Admin ve todos, Cajero ve su sucursal)
    """
    try:
        usuario_id = get_jwt_identity()
        
        from src.core.db.session_manager import get_db_session
        with get_db_session() as session:
            query = session.query(Pago)
            
            # Aplicar filtro multi-tenant
            query = agregar_filtro_sucursal(query, Pago, usuario_id)
            
            pagos = query.order_by(Pago.created_at.desc()).all()
            
            return {
                'success': True,
                'data': [p.to_dict() for p in pagos],
                'total': len(pagos)
            }, 200
            
    except Exception as e:
        logger.error(f"Error listando pagos: {str(e)}")
        return {'success': False, 'error': 'Error interno'}, 500


# ============================================================================
# GET /api/pagos/{id} - Obtener Pago por ID
# ============================================================================
@bp.route('/<int:pago_id>', methods=['GET'])
@jwt_required()
def obtener_pago(pago_id):
    """
    Obtener pago específico
    """
    try:
        usuario_id = get_jwt_identity()
        
        from src.core.db.session_manager import get_db_session
        with get_db_session() as session:
            pago = session.query(Pago).get(pago_id)
            
            if not pago:
                return {'success': False, 'error': 'Pago no existe'}, 404
            
            # Validar acceso
            if not validar_pertenencia_sucursal(usuario_id, pago):
                return {'success': False, 'error': 'FORBIDDEN'}, 403
            
            return {
                'success': True,
                'data': pago.to_dict()
            }, 200
            
    except Exception as e:
        logger.error(f"Error obteniendo pago {pago_id}: {str(e)}")
        return {'success': False, 'error': 'Error interno'}, 500


# ============================================================================
# PUT /api/pagos/{id} - Actualizar Pago (propina, estatus)
# ============================================================================
@bp.route('/<int:pago_id>', methods=['PUT'])
@jwt_required()
def actualizar_pago(pago_id):
    """
    Actualizar pago (propina, estatus solo su sucursal)
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json()
        
        from src.core.db.session_manager import get_db_session
        with get_db_session() as session:
            pago = session.query(Pago).get(pago_id)
            
            if not pago:
                return {'success': False, 'error': 'Pago no existe'}, 404
            
            # Validar acceso
            if not validar_pertenencia_sucursal(usuario_id, pago):
                return {'success': False, 'error': 'FORBIDDEN'}, 403
            
            # Actualizar campos
            if 'propina' in data:
                pago.propina = data['propina']
            if 'estatus' in data:
                pago.estatus = data['estatus']
            
            session.commit()
            logger.info(f"Pago {pago_id} actualizado por usuario {usuario_id}")
            
            return {
                'success': True,
                'data': pago.to_dict(),
                'message': 'Pago actualizado'
            }, 200
            
    except Exception as e:
        logger.error(f"Error actualizando pago {pago_id}: {str(e)}")
        return {'success': False, 'error': 'Error interno'}, 500


# ============================================================================
# DELETE /api/pagos/{id} - Eliminar Pago (Soft, SOLO ADMIN)
# ============================================================================
@bp.route('/<int:pago_id>', methods=['DELETE'])
@jwt_required()
def eliminar_pago(pago_id):
    """
    Eliminar pago - SOLO ADMIN (soft delete)
    """
    try:
        usuario_id = get_jwt_identity()
        
        # Validar que es admin
        if not es_admin(usuario_id):
            return {'success': False, 'error': 'FORBIDDEN'}, 403
        
        from src.core.db.session_manager import get_db_session
        with get_db_session() as session:
            pago = session.query(Pago).get(pago_id)
            
            if not pago:
                return {'success': False, 'error': 'Pago no existe'}, 404
            
            # Soft delete: cambiar estatus
            pago.estatus = 3  # 3 = Voided/Cancelado
            session.commit()
            logger.info(f"Pago {pago_id} marcado voided por admin {usuario_id}")
            
            return {
                'success': True,
                'message': 'Pago cancelado'
            }, 200
            
    except Exception as e:
        logger.error(f"Error eliminando pago {pago_id}: {str(e)}")
        return {'success': False, 'error': 'Error interno'}, 500
