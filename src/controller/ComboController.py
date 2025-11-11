"""
ComboController - Endpoints REST para gestión de Combos
Arquitectura n-capas: Controller → Service → DAO → Database
Con documentación Swagger completa para todos los endpoints
"""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from src.services.catalogos.combo_service import ComboService
from src.schemas.combo_schema import ComboCreateSchema, ComboUpdateSchema, ComboProductoCreateSchema

logger = logging.getLogger(__name__)

# Blueprint para combos
bp = Blueprint('combos', __name__, url_prefix='/api/combos')


# ============================================================================
# GET /api/combos - Listar Combos
# ============================================================================
@bp.route('', methods=['GET'])
def listar_combos():
    """
    Listar todos los combos activos
    ---
    tags:
      - Combos
    responses:
      200:
        description: Lista de combos activos
    """
    try:
        resultado = ComboService.listar_combos(solo_activos=True)
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en listar_combos: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# GET /api/combos/<id> - Obtener Combo por ID
# ============================================================================
@bp.route('/<int:combo_id>', methods=['GET'])
def obtener_combo(combo_id):
    """
    Obtener combo por ID
    ---
    tags:
      - Combos
    parameters:
      - in: path
        name: combo_id
        type: integer
        required: true
    responses:
      200:
        description: Combo encontrado
      404:
        description: Combo no existe
    """
    try:
        resultado = ComboService.obtener_combo(combo_id)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 404
            
    except Exception as e:
        logger.error(f"Error en obtener_combo: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# POST /api/combos - Crear Combo
# ============================================================================
@bp.route('', methods=['POST'])
@jwt_required()
def crear_combo():
    """
    Crear nuevo combo
    Solo ADMIN
    ---
    tags:
      - Combos
    security:
      - Bearer: []
    parameters:
      - in: body
        name: combo
        required: true
        schema:
          type: object
          properties:
            nombre:
              type: string
              example: "Combo Desayuno"
            precio:
              type: number
              example: 12.50
            categoria_id:
              type: integer
              example: 1
            descripcion:
              type: string
            imagen_url:
              type: string
            productos:
              type: array
              items:
                type: object
                properties:
                  producto_id:
                    type: integer
                    example: 1
                  cantidad:
                    type: integer
                    example: 1
    responses:
      201:
        description: Combo creado
      400:
        description: Datos inválidos
      403:
        description: Solo ADMIN
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar schema
        schema = ComboCreateSchema()
        try:
            datos_validados = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': e.messages
            }), 400
        
        resultado = ComboService.crear_combo(
            usuario_id=usuario_id,
            nombre=datos_validados['nombre'],
            precio=datos_validados['precio'],
            categoria_id=datos_validados['categoria_id'],
            descripcion=datos_validados.get('descripcion'),
            imagen_url=datos_validados.get('imagen_url'),
            productos=datos_validados.get('productos')
        )
        
        if resultado['success']:
            logger.info(f"Combo '{datos_validados['nombre']}' creado por usuario {usuario_id}")
            return jsonify(resultado), 201
        else:
            status = 403 if 'admin' in resultado.get('error', '').lower() else 400
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error en crear_combo: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# PUT /api/combos/<id> - Actualizar Combo
# ============================================================================
@bp.route('/<int:combo_id>', methods=['PUT'])
@jwt_required()
def actualizar_combo(combo_id):
    """
    Actualizar combo
    Solo ADMIN
    ---
    tags:
      - Combos
    security:
      - Bearer: []
    parameters:
      - in: path
        name: combo_id
        type: integer
        required: true
      - in: body
        name: combo
        schema:
          type: object
          properties:
            nombre:
              type: string
            descripcion:
              type: string
            imagen_url:
              type: string
            precio:
              type: number
    responses:
      200:
        description: Combo actualizado
      403:
        description: Solo ADMIN
      404:
        description: Combo no existe
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar schema
        schema = ComboUpdateSchema()
        try:
            datos_validados = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': e.messages
            }), 400
        
        resultado = ComboService.actualizar_combo(
            usuario_id=usuario_id,
            combo_id=combo_id,
            nombre=datos_validados.get('nombre'),
            precio=datos_validados.get('precio'),
            descripcion=datos_validados.get('descripcion'),
            imagen_url=datos_validados.get('imagen_url'),
            es_activo=datos_validados.get('es_activo')
        )
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            status = 403 if 'admin' in resultado.get('error', '').lower() else 404
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error en actualizar_combo: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# DELETE /api/combos/<id> - Eliminar Combo
# ============================================================================
@bp.route('/<int:combo_id>', methods=['DELETE'])
@jwt_required()
def eliminar_combo(combo_id):
    """
    Eliminar combo (soft delete)
    Solo ADMIN
    ---
    tags:
      - Combos
    security:
      - Bearer: []
    parameters:
      - in: path
        name: combo_id
        type: integer
        required: true
    responses:
      200:
        description: Combo eliminado
      403:
        description: Solo ADMIN
      404:
        description: Combo no existe
    """
    try:
        usuario_id = get_jwt_identity()
        
        resultado = ComboService.eliminar_combo(usuario_id, combo_id)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            status = 403 if 'admin' in resultado.get('error', '').lower() else 404
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error en eliminar_combo: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500
