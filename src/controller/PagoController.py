"""
PagoController - Gestión de Pagos

Endpoints:
  POST /api/pagos              - Crear pago (marca pedido e items como PAGADO)
  POST /api/pagos/listar       - Listar pagos (filtros en body)
  GET  /api/pagos/{id}         - Obtener pago por ID
  PUT  /api/pagos/{id}         - Actualizar pago (propina)
  DELETE /api/pagos/{id}       - Cancelar pago (admin)
  POST /api/pagos/pendientes   - Listar pedidos pendientes de pago

Flujo simplificado:
  Al crear pago con POST /api/pagos:
  - Pago se crea en estatus 2 (Pagado)
  - Pedido transiciona a 5 (Pagado)
  - Items transicionan a 5 (Pagado)
  - Reserva (si existe) a 3 (Completada)
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
import logging

from src.core.db.session_manager import get_db_session
from src.services.operaciones.pago_service import PagoService
from src.schemas.pago_schema import PagoCreateSchema
from src.core.utils.multitenant import (
    es_admin,
    validar_acceso_sucursal,
    obtener_sucursales_usuario
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
    Crear registro de pago - AUTOMÁTICAMENTE MARCA PEDIDO COMO PAGADO.
    ---
    tags:
      - Pagos
    summary: Crear Pago
    description: |
      Registra un pago para un pedido completado (estado 3).
      Automáticamente transiciona:
      - Pago: estatus 2 (Pagado)
      - Pedido: 3 (Completo) → 5 (Pagado)
      - Items: → 5 (Pagado)
      - Reserva: 2 (EnCurso) → 3 (Completada) si existe
    parameters:
      - in: body
        name: body
        required: true
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
              default: "MXN"
    responses:
      201:
        description: Pago creado y pedido marcado como pagado
      400:
        description: Validación fallida o pedido no está en estado Completo
      403:
        description: Sin acceso a la sucursal
      404:
        description: Pedido no existe
    """
    try:
        schema = PagoCreateSchema()
        data = schema.load(request.json)
        
        current_user = get_jwt_identity()
        
        # Verificar acceso a sucursal
        if not validar_acceso_sucursal(current_user, data['sucursal_id']):
            return jsonify({"error": "No tienes acceso a esta sucursal"}), 403
        
        result = PagoService.crear_pago(
            pedido_id=data['pedido_id'],
            sucursal_id=data['sucursal_id'],
            monto=data['monto'],
            propina=data.get('propina', 0),
            moneda=data.get('moneda', 'MXN'),
            usuario_id=current_user
        )
        
        if not result['success']:
            if 'no existe' in result.get('error', ''):
                return jsonify({"error": result['error']}), 404
            else:
                return jsonify({"error": result['error']}), 400
        
        return jsonify({
            "message": "Pago creado exitosamente - Pedido marcado como PAGADO",
            "pago": result['data'],
            "transiciones": result.get('transiciones', {})
        }), 201
        
    except ValidationError as e:
        logger.error(f"Error de validación en crear_pago: {e.messages}")
        return jsonify({"error": "Datos inválidos", "detalles": e.messages}), 400
    except Exception as e:
        logger.error(f"Error en crear_pago: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


# ============================================================================
# POST /api/pagos/listar - Listar Pagos
# ============================================================================
@bp.route('/listar', methods=['POST'])
@jwt_required()
def listar_pagos():
    """
    Listar pagos con filtros opcionales en body.
    ---
    tags:
      - Pagos
    summary: Listar Pagos
    description: Lista pagos con filtros opcionales. Todos los parámetros van en body.
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            sucursal_id:
              type: integer
              description: "Filtrar por sucursal (opcional)"
            pedido_id:
              type: integer
              description: "Filtrar por pedido (opcional)"
            estatus:
              type: integer
              description: "1=Pendiente, 2=Pagado, 3=Anulado (opcional)"
    responses:
      200:
        description: Lista de pagos
    """
    try:
        current_user = get_jwt_identity()
        payload = request.get_json() or {}
        
        sucursal_id = payload.get('sucursal_id')
        pedido_id = payload.get('pedido_id')
        estatus = payload.get('estatus')
        
        # Validar acceso a sucursal si se especifica
        if sucursal_id:
            if not validar_acceso_sucursal(current_user, sucursal_id):
                return jsonify({"error": "Sin acceso a esta sucursal"}), 403
        else:
            # Usar sucursales del usuario
            sucursales = obtener_sucursales_usuario(current_user)
            if not sucursales:
                return jsonify({"error": "Usuario sin sucursal asignada"}), 403
        
        with get_db_session() as session:
            query = session.query(Pago)
            
            # Filtrar por sucursal
            if sucursal_id:
                query = query.filter(Pago.sucursal_id == sucursal_id)
            else:
                sucursales = obtener_sucursales_usuario(current_user)
                if sucursales:
                    query = query.filter(Pago.sucursal_id.in_(sucursales))
            
            # Filtros opcionales
            if pedido_id:
                query = query.filter(Pago.pedido_id == pedido_id)
            
            if estatus:
                query = query.filter(Pago.estatus == estatus)
            
            pagos = query.order_by(Pago.created_at.desc()).all()
            
            return jsonify({
                "pagos": [p.to_dict() for p in pagos],
                "total": len(pagos),
                "filtros_aplicados": {
                    "sucursal_id": sucursal_id,
                    "pedido_id": pedido_id,
                    "estatus": estatus
                }
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
    summary: Obtener Pago
    parameters:
      - in: path
        name: pago_id
        type: integer
        required: true
    responses:
      200:
        description: Pago encontrado
      403:
        description: Sin acceso a la sucursal
      404:
        description: Pago no existe
    """
    try:
        current_user = get_jwt_identity()
        
        result = PagoService.obtener_pago(pago_id)
        
        if not result['success']:
            return jsonify({"error": result['error']}), 404
        
        # Validar acceso a sucursal
        sucursal_id = result['data'].get('sucursal_id')
        if not validar_acceso_sucursal(current_user, sucursal_id):
            return jsonify({"error": "No tienes acceso a esta sucursal"}), 403
        
        return jsonify(result['data']), 200
            
    except Exception as e:
        logger.error(f"Error obteniendo pago {pago_id}: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


# ============================================================================
# PUT /api/pagos/{pago_id} - Actualizar Pago (propina)
# ============================================================================
@bp.route('/<int:pago_id>', methods=['PUT'])
@jwt_required()
def actualizar_pago(pago_id):
    """
    Actualizar datos del pago (propina).
    ---
    tags:
      - Pagos
    summary: Actualizar Pago
    parameters:
      - in: path
        name: pago_id
        type: integer
        required: true
      - in: body
        name: body
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
    """
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        result = PagoService.actualizar_pago(
            pago_id=pago_id,
            propina=data.get('propina'),
            usuario_id=current_user
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
# DELETE /api/pagos/{pago_id} - Cancelar Pago (SOLO ADMIN)
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
    description: Soft delete - cambia estatus a cancelado (3). Solo admins.
    parameters:
      - in: path
        name: pago_id
        type: integer
        required: true
    responses:
      200:
        description: Pago cancelado
      403:
        description: Sin permisos
      404:
        description: Pago no existe
    """
    try:
        current_user = get_jwt_identity()
        
        if not es_admin(current_user):
            return jsonify({"error": "Solo administradores pueden cancelar pagos"}), 403
        
        result = PagoService.cancelar_pago(pago_id, current_user)
        
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


# ============================================================================
# POST /api/pagos/pendientes - Listar Pedidos Pendientes de Pago
# ============================================================================
@bp.route('/pendientes', methods=['POST'])
@jwt_required()
def listar_pedidos_pendientes():
    """
    Listar pedidos en estado Completo (3) pendientes de pago.
    ---
    tags:
      - Pagos
    summary: Listar Pedidos Pendientes de Pago
    description: |
      Lista pedidos en estado Completo (3) listos para pagar.
      Útil para vista de caja/cajero.
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            sucursal_id:
              type: integer
              description: "ID de la sucursal (opcional)"
    responses:
      200:
        description: Lista de pedidos pendientes de pago
      403:
        description: Sin acceso a la sucursal
    """
    try:
        current_user = get_jwt_identity()
        payload = request.get_json() or {}
        
        sucursal_id = payload.get('sucursal_id')
        
        # Si no viene sucursal, usar la primera del usuario
        if not sucursal_id:
            sucursales = obtener_sucursales_usuario(current_user)
            if not sucursales:
                return jsonify({"error": "Usuario sin sucursal asignada"}), 403
            sucursal_id = sucursales[0]
        
        # Validar acceso a sucursal
        if not validar_acceso_sucursal(current_user, sucursal_id):
            return jsonify({"error": "No tienes acceso a esta sucursal"}), 403
        
        result = PagoService.listar_pedidos_pendientes_pago(sucursal_id)
        
        if not result['success']:
            return jsonify({"error": result['error']}), 500
        
        return jsonify({
            "success": True,
            "pedidos": result['data'],
            "total": len(result['data']),
            "sucursal_id": sucursal_id
        }), 200
        
    except Exception as e:
        logger.error(f"Error listando pedidos pendientes: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500
