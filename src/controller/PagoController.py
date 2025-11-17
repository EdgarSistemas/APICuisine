"""
PagoController - Gestión de Pagos
Endpoints: POST (crear), POST (marcar pagado), GET (listar), GET/{id}
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
import logging

from src.services.operaciones.pago_service import PagoService
from src.schemas.pago_schema import (
    PagoCreateSchema,
    PagoMarcarPagadoSchema
)
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
# POST /api/pagos - Crear Pago
# ============================================================================
@bp.route('', methods=['POST'])
@jwt_required()
def crear_pago():
    """
    Crear registro de pago para un pedido.
    ---
    tags:
      - Pagos
    summary: Crear pago
    description: Registra un nuevo pago para un pedido.
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - pedido_id
              - sucursal_id
              - monto
            properties:
              pedido_id:
                type: integer
              sucursal_id:
                type: integer
              monto:
                type: number
              propina:
                type: number
                default: 0
              moneda:
                type: string
                default: MXN
    responses:
      201:
        description: Pago creado exitosamente
      400:
        description: Validación fallida
      403:
        description: Sin acceso a sucursal
      404:
        description: Pedido no existe
    """
    try:
        # Validar schema
        schema = PagoCreateSchema()
        data = schema.load(request.json)
        
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario')
        
        # Verificar acceso a sucursal
        if not validar_acceso_sucursal(usuario_id, data['sucursal_id']):
            return jsonify({"error": "No tienes acceso a esta sucursal"}), 403
        
        # Usar servicio para crear pago
        result = PagoService.crear_pago(
            pedido_id=data['pedido_id'],
            sucursal_id=data['sucursal_id'],
            monto=data['monto'],
            propina=data.get('propina', 0),
            moneda=data.get('moneda', 'MXN'),
            usuario_id=usuario_id
        )
        
        if not result['success']:
            if 'no existe' in result.get('error', ''):
                return jsonify({"error": result['error']}), 404
            elif 'mismatch' in result.get('error', ''):
                return jsonify({"error": result['error']}), 400
            else:
                return jsonify({"error": result['error']}), 400
        
        return jsonify({
            "message": "Pago creado exitosamente",
            "pago": result['data']
        }), 201
        
    except ValidationError as e:
        logger.error(f"Error de validación en crear_pago: {e.messages}")
        return jsonify({"error": "Datos inválidos", "detalles": e.messages}), 400
    except Exception as e:
        logger.error(f"Error en crear_pago: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


# ============================================================================
# GET /api/pagos - Listar Pagos
# ============================================================================
@bp.route('', methods=['GET'])
@jwt_required()
def obtener_pagos():
    """
    Listar pagos registrados.
    ---
    tags:
      - Pagos
    summary: Obtener lista de pagos
    description: Retorna lista de pagos con filtros opcionales.
    parameters:
      - in: query
        name: sucursal_id
        type: integer
        description: Filtrar por sucursal (opcional)
      - in: query
        name: pedido_id
        type: integer
        description: Filtrar por pedido (opcional)
    responses:
      200:
        description: Lista de pagos
    """
    try:
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario')
        
        from src.core.db.session_manager import get_db_session
        with get_db_session() as session:
            query = session.query(Pago)
            
            # Aplicar filtro multi-tenant
            query = agregar_filtro_sucursal(query, Pago, usuario_id)
            
            # Filtros opcionales
            sucursal_id = request.args.get('sucursal_id', type=int)
            if sucursal_id:
                query = query.filter(Pago.sucursal_id == sucursal_id)
            
            pedido_id = request.args.get('pedido_id', type=int)
            if pedido_id:
                query = query.filter(Pago.pedido_id == pedido_id)
            
            pagos = query.order_by(Pago.created_at.desc()).all()
            
            return jsonify({
                "pagos": [p.to_dict() for p in pagos],
                "total": len(pagos)
            }), 200
            
    except Exception as e:
        logger.error(f"Error listando pagos: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


# ============================================================================
# GET /api/pagos/{pago_id} - Obtener Pago por ID
# ============================================================================
@bp.route('/<int:pago_id>', methods=['GET'])
@jwt_required()
def obtener_pago(pago_id):
    """
    Obtener detalles de un pago específico.
    ---
    tags:
      - Pagos
    summary: Obtener pago por ID
    description: Retorna los detalles completos de un pago.
    parameters:
      - in: path
        name: pago_id
        type: integer
        required: true
    responses:
      200:
        description: Datos del pago
      403:
        description: Sin acceso a sucursal
      404:
        description: Pago no existe
    """
    try:
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario')
        
        result = PagoService.obtener_pago(pago_id)
        
        if not result['success']:
            return jsonify({"error": result['error']}), 404
        
        # Validar acceso a sucursal
        sucursal_id = result['data'].get('sucursal_id')
        if not validar_acceso_sucursal(usuario_id, sucursal_id):
            return jsonify({"error": "No tienes acceso a esta sucursal"}), 403
        
        return jsonify(result['data']), 200
            
    except Exception as e:
        logger.error(f"Error obteniendo pago {pago_id}: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


# ============================================================================
# POST /api/pagos/{pago_id}/marcar-pagado - Marcar Pago Completado
# ============================================================================
@bp.route('/<int:pago_id>/marcar-pagado', methods=['POST'])
@jwt_required()
def marcar_pagado(pago_id):
    """
    Marcar pago como completado - TRANSICIONA PEDIDO A PAGADO.
    ---
    tags:
      - Pagos
    summary: Marcar pago como completado (CRITICAL)
    description: |
      Marca pago como completado (estatus 1→2).
      Automáticamente transiciona el pedido asociado a estatus PAGADO (5).
      
    parameters:
      - in: path
        name: pago_id
        type: integer
        required: true
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - metodo_pago
            properties:
              metodo_pago:
                type: string
                description: Método de pago (Efectivo, Tarjeta, QR, etc)
              referencia:
                type: string
                description: Número de transacción (opcional)
    responses:
      200:
        description: Pago marcado como completado
      400:
        description: Validación fallida
      404:
        description: Pago no existe
    """
    try:
        schema = PagoMarcarPagadoSchema()
        data = schema.load(request.json)
        
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario')
        
        result = PagoService.marcar_pagado(
            pago_id=pago_id,
            metodo_pago=data['metodo_pago'],
            referencia=data.get('referencia'),
            usuario_id=usuario_id
        )
        
        if not result['success']:
            if 'no existe' in result.get('error', ''):
                return jsonify({"error": result['error']}), 404
            else:
                return jsonify({"error": result['error']}), 400
        
        return jsonify({
            "message": "Pago marcado como completado",
            "pago": result['data']
        }), 200
        
    except ValidationError as e:
        logger.error(f"Error de validación en marcar_pagado: {e.messages}")
        return jsonify({"error": "Datos inválidos", "detalles": e.messages}), 400
    except Exception as e:
        logger.error(f"Error en marcar_pagado: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


# ============================================================================
# PUT /api/pagos/{pago_id} - Actualizar Pago (propina, etc)
# ============================================================================
@bp.route('/<int:pago_id>', methods=['PUT'])
@jwt_required()
def actualizar_pago(pago_id):
    """
    Actualizar datos del pago (propina, etc).
    ---
    tags:
      - Pagos
    summary: Actualizar pago
    description: Actualiza campos del pago como propina.
    parameters:
      - in: path
        name: pago_id
        type: integer
        required: true
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              propina:
                type: number
    responses:
      200:
        description: Pago actualizado
      404:
        description: Pago no existe
      403:
        description: Sin acceso
    """
    try:
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario')
        data = request.get_json()
        
        result = PagoService.actualizar_pago(
            pago_id=pago_id,
            propina=data.get('propina'),
            usuario_id=usuario_id
        )
        
        if not result['success']:
            if 'no existe' in result.get('error', ''):
                return jsonify({"error": result['error']}), 404
            else:
                return jsonify({"error": result['error']}), 400
        
        return jsonify({
            "message": "Pago actualizado",
            "pago": result['data']
        }), 200
            
    except Exception as e:
        logger.error(f"Error actualizando pago {pago_id}: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


# ============================================================================
# DELETE /api/pagos/{pago_id} - Cancelar Pago (Soft Delete, SOLO ADMIN)
# ============================================================================
@bp.route('/<int:pago_id>', methods=['DELETE'])
@jwt_required()
def eliminar_pago(pago_id):
    """
    Cancelar pago - SOLO ADMIN.
    ---
    tags:
      - Pagos
    summary: Cancelar pago
    description: Soft delete - cambia estatus a voided/cancelado. Solo admins.
    parameters:
      - in: path
        name: pago_id
        type: integer
        required: true
    responses:
      200:
        description: Pago cancelado exitosamente
      403:
        description: Sin permisos
      404:
        description: Pago no existe
    """
    try:
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario')
        
        # Validar que es admin
        if not es_admin(usuario_id):
            return jsonify({"error": "Solo administradores pueden cancelar pagos"}), 403
        
        result = PagoService.cancelar_pago(pago_id, usuario_id)
        
        if not result['success']:
            if 'no existe' in result.get('error', ''):
                return jsonify({"error": result['error']}), 404
            else:
                return jsonify({"error": result['error']}), 400
        
        return jsonify({
            "message": "Pago cancelado exitosamente"
        }), 200
            
    except Exception as e:
        logger.error(f"Error cancelando pago {pago_id}: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500
