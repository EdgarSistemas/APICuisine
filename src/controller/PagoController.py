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
    Crear registro de pago para un pedido completado.
    ---
    tags:
      - Pagos
    summary: "Paso 1: Crear Pago"
    description: Registra un nuevo pago para un pedido completado. El pago inicialmente está en estado Pendiente (1). Posteriormente se marca como Pagado (2) cuando se confirma el método de pago.
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
              description: "ID del pedido para el cual se crea el pago. Ej: 25"
            sucursal_id:
              type: integer
              description: "ID de la sucursal. Ej: 1"
            monto:
              type: number
              description: "Monto total del pago (sin incluir propina). Ej: 450.50"
            propina:
              type: number
              description: "Monto de propina (opcional, default: 0). Ej: 50.00"
              default: 0
            moneda:
              type: string
              description: "Código de moneda (default: MXN). Ej: MXN, USD, EUR"
              default: "MXN"
        example:
          pedido_id: 25
          sucursal_id: 1
          monto: 450.50
          propina: 50.00
          moneda: "MXN"
    responses:
      201:
        description: "Pago creado exitosamente"
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Pago creado exitosamente"
            pago:
              type: object
              properties:
                id_pago:
                  type: integer
                  example: 15
                pedido_id:
                  type: integer
                  example: 25
                sucursal_id:
                  type: integer
                  example: 1
                monto:
                  type: number
                  example: 450.50
                propina:
                  type: number
                  example: 50.00
                total:
                  type: number
                  example: 500.50
                moneda:
                  type: string
                  example: "MXN"
                estatus:
                  type: integer
                  example: 1
                  description: "1=Pendiente, 2=Pagado"
                created_at:
                  type: string
                  format: date-time
      400:
        description: "Validación fallida"
      403:
        description: "Sin acceso a la sucursal"
      404:
        description: "Pedido no existe"
    x-code-samples:
      - lang: curl
        source: |
          curl -X POST http://localhost:5000/api/pagos/ \\
            -H "Content-Type: application/json" \\
            -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
            -d '{
              "pedido_id": 25,
              "sucursal_id": 1,
              "monto": 450.50,
              "propina": 50.00,
              "moneda": "MXN"
            }'
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
    Listar todos los pagos registrados con filtros opcionales.
    ---
    tags:
      - Pagos
    summary: "Paso 1B: Listar Pagos"
    description: Lista todos los pagos con posibilidad de filtrar por sucursal y pedido. Solo retorna pagos de la sucursal del usuario autenticado (multi-tenant). Útil para reportes y auditoría financiera.
    parameters:
      - in: query
        name: sucursal_id
        type: integer
        required: false
        description: "Filtrar por sucursal (opcional). Ej: ?sucursal_id=1"
      - in: query
        name: pedido_id
        type: integer
        required: false
        description: "Filtrar por pedido (opcional). Ej: ?pedido_id=25"
    responses:
      200:
        description: "Lista de pagos obtenida exitosamente"
        schema:
          type: object
          properties:
            pagos:
              type: array
              items:
                type: object
                properties:
                  id_pago:
                    type: integer
                  pedido_id:
                    type: integer
                  monto:
                    type: number
                  propina:
                    type: number
                  total:
                    type: number
                  estatus:
                    type: integer
                    description: "1=Pendiente, 2=Pagado"
                  metodo_pago:
                    type: string
                  created_at:
                    type: string
                    format: date-time
            total:
              type: integer
              description: "Cantidad total de pagos que coinciden con los filtros"
    x-code-samples:
      - lang: curl
        source: |
          # Listar todos los pagos
          curl -X GET http://localhost:5000/api/pagos/ \\
            -H "Authorization: Bearer YOUR_JWT_TOKEN"

          # Listar pagos de la sucursal 1
          curl -X GET "http://localhost:5000/api/pagos/?sucursal_id=1" \\
            -H "Authorization: Bearer YOUR_JWT_TOKEN"
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
    Obtener detalles de un pago específico por ID.
    ---
    tags:
      - Pagos
    summary: "Paso 1C: Obtener Pago"
    description: Obtiene la información completa de un pago específico incluyendo monto, propina, método de pago y auditoría.
    parameters:
      - in: path
        name: pago_id
        type: integer
        required: true
        description: "ID del pago a consultar. Ej: 15"
    responses:
      200:
        description: "Pago encontrado exitosamente"
        schema:
          type: object
          properties:
            id_pago:
              type: integer
              example: 15
            pedido_id:
              type: integer
              example: 25
            sucursal_id:
              type: integer
              example: 1
            monto:
              type: number
              example: 450.50
            propina:
              type: number
              example: 50.00
            total:
              type: number
              example: 500.50
            moneda:
              type: string
              example: "MXN"
            estatus:
              type: integer
              example: 1
              description: "1=Pendiente, 2=Pagado"
            metodo_pago:
              type: string
              example: null
            referencia:
              type: string
              example: null
            created_at:
              type: string
              format: date-time
            updated_at:
              type: string
              format: date-time
      403:
        description: "Sin acceso a la sucursal"
      404:
        description: "Pago no existe"
    x-code-samples:
      - lang: curl
        source: |
          curl -X GET http://localhost:5000/api/pagos/15 \\
            -H "Authorization: Bearer YOUR_JWT_TOKEN"
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
    summary: "Paso 2: Marcar Pago como Pagado (CRITICAL)"
    description: |
      **⚠️ OPERACIÓN CRÍTICA ⚠️**
      
      Marca el pago como completado (estatus 1→2).
      Automáticamente transiciona el pedido asociado a estatus PAGADO (5).
      
      IMPORTANTE:
      - Cierra la transacción del cliente
      - Actualiza inventario en reportes
      - Registra en auditoría financiera
      - Es el paso final del flujo completo
    parameters:
      - in: path
        name: pago_id
        type: integer
        required: true
        description: "ID del pago. Ej: 15"
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - metodo_pago
          properties:
            metodo_pago:
              type: string
              description: "Método de pago usado. Ej: Efectivo, Tarjeta, QR, Transferencia"
            referencia:
              type: string
              description: "Número de transacción o referencia (opcional). Ej: TXN123456789"
        example:
          metodo_pago: "Tarjeta"
          referencia: "TXN123456789"
    responses:
      200:
        description: "Pago marcado como completado y pedido transitado a pagado"
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Pago marcado como completado"
            pago:
              type: object
              properties:
                id_pago:
                  type: integer
                  example: 15
                pedido_id:
                  type: integer
                  example: 25
                monto:
                  type: number
                  example: 450.50
                propina:
                  type: number
                  example: 50.00
                total:
                  type: number
                  example: 500.50
                estatus:
                  type: integer
                  example: 2
                  description: "2=Pagado"
                metodo_pago:
                  type: string
                  example: "Tarjeta"
                referencia:
                  type: string
                  example: "TXN123456789"
                updated_at:
                  type: string
                  format: date-time
      400:
        description: "Validación fallida"
        schema:
          type: object
          properties:
            error:
              type: string
      404:
        description: "Pago no existe"
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Pago 15 no existe"
    x-validation-notes: |
      VALIDACIONES INTERNAS:
      1. Pago debe existir y estar Pendiente (estatus=1)
      2. Pedido debe existir y estar Completado (estado=3)
      3. Ambos en la misma sucursal
      
      TRANSICIONES AUTOMÁTICAS:
      - Pago: 1 (Pendiente) → 2 (Pagado)
      - Pedido: 3 (Completado) → 5 (Pagado)
      
      FLUJO COMPLETO FINALIZADO:
      Hold (confirmado) → Reserva (completada) → Pedido (pagado) → Pago (pagado) ✅
    x-code-samples:
      - lang: curl
        source: |
          curl -X POST http://localhost:5000/api/pagos/15/marcar-pagado \\
            -H "Content-Type: application/json" \\
            -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
            -d '{
              "metodo_pago": "Tarjeta",
              "referencia": "TXN123456789"
            }'
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
    summary: "Paso 2B: Actualizar Pago"
    description: Permite actualizar campos del pago como propina antes de marcarlo como pagado. Útil si el cliente agrega propina después de crear el pago.
    parameters:
      - in: path
        name: pago_id
        type: integer
        required: true
        description: "ID del pago. Ej: 15"
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            propina:
              type: number
              description: "Nueva cantidad de propina. Ej: 75.00"
        example:
          propina: 75.00
    responses:
      200:
        description: "Pago actualizado exitosamente"
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Pago actualizado"
            pago:
              type: object
      404:
        description: "Pago no existe"
      403:
        description: "Sin acceso"
    x-code-samples:
      - lang: curl
        source: |
          curl -X PUT http://localhost:5000/api/pagos/15 \\
            -H "Content-Type: application/json" \\
            -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
            -d '{
              "propina": 75.00
            }'
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
