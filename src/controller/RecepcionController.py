"""
RecepcionController - Endpoints REST para recepciones
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
import logging

from src.services.inventario.recepcion_service import RecepcionService
from src.schemas.recepcion_schema import RecepcionCreateSchema, RecepcionUpdateSchema

logger = logging.getLogger(__name__)
bp = Blueprint('recepciones', __name__, url_prefix='/api/recepciones')


# ============================================================================
# POST /api/recepciones - Crear Recepción con Detalles
# ============================================================================
@bp.route('', methods=['POST'])
@jwt_required()
def crear_recepcion():
    """
    Crear nueva recepción con detalles y generar lotes automáticamente
    Solo ADMIN
    ---
    tags:
      - Recepciones
    security:
      - Bearer: []
    parameters:
      - in: body
        name: recepcion
        required: true
        schema:
          type: object
          properties:
            sucursal_id:
              type: integer
              example: 1
            compra_id:
              type: integer
              example: 1
            recibido_por:
              type: integer
              example: 1
            notas:
              type: string
            detalles:
              type: array
              items:
                type: object
                properties:
                  insumo_id:
                    type: integer
                    example: 5
                  cant_presentacion:
                    type: number
                    example: 5
                  unidades_por_present:
                    type: number
                    example: 50
                  costo_unitario:
                    type: number
                    example: 25.50
                  lote_numero:
                    type: string
                  lote_proveedor:
                    type: string
                  fecha_caducidad:
                    type: string
                    format: date
    responses:
      201:
        description: Recepción creada
      400:
        description: Datos inválidos
      403:
        description: Solo ADMIN
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar schema
        schema = RecepcionCreateSchema()
        try:
            datos_validados = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': e.messages
            }), 400
        
        resultado = RecepcionService.crear_recepcion(
            usuario_id=usuario_id,
            sucursal_id=datos_validados.get('sucursal_id', data.get('sucursal_id')),
            compra_id=datos_validados['compra_id'],
            recibido_por=datos_validados['recibido_por'],
            detalles=datos_validados['detalles'],
            notas=datos_validados.get('notas')
        )
        
        if resultado['success']:
            logger.info(f"Recepción creada por usuario {usuario_id}")
            return jsonify(resultado), 201
        else:
            status = 403 if 'admin' in resultado.get('error', '').lower() else 400
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error en crear_recepcion: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# GET /api/recepciones - Listar Recepciones
# ============================================================================
@bp.route('', methods=['GET'])
@jwt_required()
def listar_recepciones():
    """
    Listar recepciones de la sucursal
    ---
    tags:
      - Recepciones
    security:
      - Bearer: []
    parameters:
      - in: query
        name: sucursal_id
        type: integer
        required: true
    responses:
      200:
        description: Lista de recepciones
    """
    try:
        usuario_id = get_jwt_identity()
        sucursal_id = request.args.get('sucursal_id', type=int)
        
        if not sucursal_id:
            return jsonify({
                'success': False,
                'error': 'sucursal_id es requerido'
            }), 400
        
        resultado = RecepcionService.listar_recepciones(usuario_id, sucursal_id)
        return jsonify(resultado), 200 if resultado['success'] else 500
        
    except Exception as e:
        logger.error(f"Error en listar_recepciones: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# GET /api/recepciones/<id> - Obtener Recepción por ID
# ============================================================================
@bp.route('/<int:recepcion_id>', methods=['GET'])
@jwt_required()
def obtener_recepcion(recepcion_id):
    """
    Obtener recepción con detalles completos
    ---
    tags:
      - Recepciones
    security:
      - Bearer: []
    parameters:
      - in: path
        name: recepcion_id
        type: integer
        required: true
    responses:
      200:
        description: Recepción encontrada
      404:
        description: Recepción no existe
    """
    try:
        resultado = RecepcionService.obtener_recepcion(recepcion_id)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 404
            
    except Exception as e:
        logger.error(f"Error en obtener_recepcion: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# PATCH /api/recepciones/<id>/cancelar - Cancelar Recepción
# ============================================================================
@bp.route('/<int:recepcion_id>/cancelar', methods=['PATCH'])
@jwt_required()
def cancelar_recepcion(recepcion_id):
    """
    Cancelar una recepción
    - Solo ADMIN o COMPRAS
    - Marca Lotes como cancelados
    - Crea Movimientos de salida para revertir
    - Resta cantidades de Existencias
    - Opcionalmente revierte Compra a estatus=1
    ---
    tags:
      - Recepciones
    security:
      - Bearer: []
    parameters:
      - in: path
        name: recepcion_id
        type: integer
        required: true
      - in: body
        name: opciones
        schema:
          type: object
          properties:
            revertir_compra:
              type: boolean
              default: true
              description: Si true, regresa Compra a estatus 1 (Pendiente)
    responses:
      200:
        description: Recepción cancelada exitosamente
      400:
        description: Error de validación
      403:
        description: Solo ADMIN o COMPRAS
      404:
        description: Recepción no existe
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json() or {}
        revertir_compra = data.get('revertir_compra', True)
        
        resultado = RecepcionService.cancelar_recepcion(
            usuario_id=usuario_id,
            recepcion_id=recepcion_id,
            revertir_compra=revertir_compra
        )
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            # Determinar código de estado según el error
            error_msg = resultado.get('error', '').lower()
            if 'admin' in error_msg or 'compras' in error_msg or 'permisos' in error_msg:
                status = 403
            elif 'no existe' in error_msg:
                status = 404
            else:
                status = 400
            
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error en cancelar_recepcion: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500

