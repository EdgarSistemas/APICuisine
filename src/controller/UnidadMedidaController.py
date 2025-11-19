"""
UnidadMedidaController - Endpoints REST para gestión de Unidades de Medida
Arquitectura n-capas: Controller → Service → DAO → Database
Con documentación Swagger completa para todos los endpoints
"""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from src.services.inventario.unidad_medida_service import UnidadMedidaService
from src.schemas.unidad_medida_schema import UnidadMedidaCreateSchema, UnidadMedidaUpdateSchema

logger = logging.getLogger(__name__)

# Blueprint para unidades de medida
bp = Blueprint('unidades_medida', __name__, url_prefix='/api/unidades')


# ============================================================================
# GET /api/unidades - Listar Unidades de Medida
# ============================================================================
@bp.route('', methods=['GET'])
def listar_unidades():
    """
    Listar todas las unidades de medida
    ---
    tags:
      - Unidades de Medida
    responses:
      200:
        description: Lista de unidades de medida
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: array
              items:
                type: object
                properties:
                  id_unidad:
                    type: integer
                  clave:
                    type: string
                  nombre:
                    type: string
    """
    try:
        resultado = UnidadMedidaService.listar_unidades()
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en listar_unidades: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# GET /api/unidades/<id> - Obtener Unidad por ID
# ============================================================================
@bp.route('/<int:unidad_id>', methods=['GET'])
def obtener_unidad(unidad_id):
    """
    Obtener unidad de medida por ID
    ---
    tags:
      - Unidades de Medida
    parameters:
      - in: path
        name: unidad_id
        type: integer
        required: true
    responses:
      200:
        description: Unidad encontrada
      404:
        description: Unidad no existe
    """
    try:
        resultado = UnidadMedidaService.obtener_unidad(unidad_id)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 404
            
    except Exception as e:
        logger.error(f"Error en obtener_unidad: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# POST /api/unidades - Crear Unidad de Medida
# ============================================================================
@bp.route('', methods=['POST'])
@jwt_required()
def crear_unidad():
    """
    Crear nueva unidad de medida
    Solo ADMIN
    ---
    tags:
      - Unidades de Medida
    security:
      - Bearer: []
    parameters:
      - in: body
        name: unidad
        required: true
        schema:
          type: object
          properties:
            clave:
              type: string
              example: "kg"
            nombre:
              type: string
              example: "Kilogramo"
    responses:
      201:
        description: Unidad creada
      400:
        description: Datos inválidos
      403:
        description: Solo ADMIN
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar schema
        schema = UnidadMedidaCreateSchema()
        try:
            datos_validados = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': e.messages
            }), 400
        
        resultado = UnidadMedidaService.crear_unidad_medida(
            usuario_id=usuario_id,
            clave=datos_validados['clave'],
            nombre=datos_validados['nombre'],
        )
        
        if resultado['success']:
            logger.info(f"Unidad '{datos_validados['nombre']}' creada por usuario {usuario_id}")
            return jsonify(resultado), 201
        else:
            status = 403 if 'admin' in resultado.get('error', '').lower() else 400
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error en crear_unidad: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# PUT /api/unidades/<id> - Actualizar Unidad de Medida
# ============================================================================
@bp.route('/<int:unidad_id>', methods=['PUT'])
@jwt_required()
def actualizar_unidad(unidad_id):
    """
    Actualizar unidad de medida
    Solo ADMIN
    ---
    tags:
      - Unidades de Medida
    security:
      - Bearer: []
    parameters:
      - in: path
        name: unidad_id
        type: integer
        required: true
      - in: body
        name: unidad
        schema:
          type: object
          properties:
            clave:
              type: string
            nombre:
              type: string
    responses:
      200:
        description: Unidad actualizada
      403:
        description: Solo ADMIN
      404:
        description: Unidad no existe
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar schema
        schema = UnidadMedidaUpdateSchema()
        try:
            datos_validados = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': e.messages
            }), 400
        
        resultado = UnidadMedidaService.actualizar_unidad(
            usuario_id=usuario_id,
            unidad_id=unidad_id,
            clave=datos_validados.get('clave'),
            nombre=datos_validados.get('nombre')
        )
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            status = 403 if 'admin' in resultado.get('error', '').lower() else 404
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error en actualizar_unidad: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500
