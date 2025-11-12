"""
InsumoController - Endpoints REST para gestión de Insumos
Arquitectura n-capas: Controller → Service → DAO → Database
Con documentación Swagger completa para todos los endpoints
"""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from src.services.inventario.insumo_service import InsumoService
from src.schemas.insumo_schema import InsumoCreateSchema, InsumoUpdateSchema

logger = logging.getLogger(__name__)

# Blueprint para insumos
bp = Blueprint('insumos', __name__, url_prefix='/api/insumos')


# ============================================================================
# GET /api/insumos - Listar Insumos
# ============================================================================
@bp.route('', methods=['GET'])
@jwt_required()
def listar_insumos():
    """
    Listar todos los insumos activos (sin existencias)
    ---
    tags:
      - Insumos
    responses:
      200:
        description: Lista de insumos activos
    """
    try:
        resultado = InsumoService.listar_insumos(solo_activos=True)
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en listar_insumos: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# POST /api/insumos/existencias - Listar Insumos con Existencias por Sucursal
# ============================================================================
@bp.route('/existencias', methods=['POST'])
@jwt_required()
def listar_insumos_con_existencias():
    """
    Listar todos los insumos con sus existencias para una sucursal
    ---
    tags:
      - Insumos
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - sucursal_id
          properties:
            sucursal_id:
              type: integer
              example: 1
              description: ID de la sucursal
            solo_activos:
              type: boolean
              example: true
              default: true
              description: Si es true, solo devuelve insumos activos
    responses:
      200:
        description: Lista de insumos con existencias (cantidad y costo_promedio)
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                type: object
                properties:
                  id_insumo:
                    type: integer
                  nombre:
                    type: string
                  unidad_id:
                    type: integer
                  unidad_clave:
                    type: string
                  unidad_nombre:
                    type: string
                  es_activo:
                    type: boolean
                  cantidad:
                    type: number
                  costo_promedio:
                    type: number
                  updated_at:
                    type: string
                    format: date-time
      400:
        description: Falta sucursal_id
    """
    try:
        data = request.get_json()
        
        # Validar que venga sucursal_id
        sucursal_id = data.get('sucursal_id')
        if not sucursal_id:
            return jsonify({
                'success': False,
                'error': 'MISSING_SUCURSAL_ID',
                'message': 'Debe proporcionar sucursal_id en el body'
            }), 400
        
        solo_activos = data.get('solo_activos', True)
        
        resultado = InsumoService.listar_insumos_con_existencias(
            sucursal_id=sucursal_id,
            solo_activos=solo_activos
        )
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en listar_insumos_con_existencias: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# GET /api/insumos/<id> - Obtener Insumo por ID
# ============================================================================
@bp.route('/<int:insumo_id>', methods=['GET'])
@jwt_required()
def obtener_insumo(insumo_id):
    """
    Obtener insumo por ID
    ---
    tags:
      - Insumos
    parameters:
      - in: path
        name: insumo_id
        type: integer
        required: true
    responses:
      200:
        description: Insumo encontrado
      404:
        description: Insumo no existe
    """
    try:
        resultado = InsumoService.obtener_insumo(insumo_id)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 404
            
    except Exception as e:
        logger.error(f"Error en obtener_insumo: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# POST /api/insumos - Crear Insumo
# ============================================================================
@bp.route('', methods=['POST'])
@jwt_required()
def crear_insumo():
    """
    Crear nuevo insumo
    Solo ADMIN
    ---
    tags:
      - Insumos
    security:
      - Bearer: []
    parameters:
      - in: body
        name: insumo
        required: true
        schema:
          type: object
          properties:
            nombre:
              type: string
              example: "Harina Premium"
            unidad_id:
              type: integer
              example: 1
    responses:
      201:
        description: Insumo creado
      400:
        description: Datos inválidos
      403:
        description: Solo ADMIN
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar schema
        schema = InsumoCreateSchema()
        try:
            datos_validados = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': e.messages
            }), 400
        
        resultado = InsumoService.crear_insumo(
            usuario_id=usuario_id,
            nombre=datos_validados['nombre'],
            unidad_id=datos_validados['unidad_id']
        )
        
        if resultado['success']:
            logger.info(f"Insumo '{datos_validados['nombre']}' creado por usuario {usuario_id}")
            return jsonify(resultado), 201
        else:
            status = 403 if 'admin' in resultado.get('error', '').lower() else 400
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error en crear_insumo: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# PUT /api/insumos/<id> - Actualizar Insumo
# ============================================================================
@bp.route('/<int:insumo_id>', methods=['PUT'])
@jwt_required()
def actualizar_insumo(insumo_id):
    """
    Actualizar insumo
    Solo ADMIN
    ---
    tags:
      - Insumos
    security:
      - Bearer: []
    parameters:
      - in: path
        name: insumo_id
        type: integer
        required: true
      - in: body
        name: insumo
        schema:
          type: object
          properties:
            nombre:
              type: string
    responses:
      200:
        description: Insumo actualizado
      403:
        description: Solo ADMIN
      404:
        description: Insumo no existe
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar schema
        schema = InsumoUpdateSchema()
        try:
            datos_validados = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': e.messages
            }), 400
        
        resultado = InsumoService.actualizar_insumo(
            usuario_id=usuario_id,
            insumo_id=insumo_id,
            nombre=datos_validados.get('nombre')
        )
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            status = 403 if 'admin' in resultado.get('error', '').lower() else 404
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error en actualizar_insumo: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500
