"""
ProductoRecetaController - Endpoints REST para gestión de Recetas de Productos
Arquitectura n-capas: Controller → Service → DAO → Database
Con documentación Swagger completa para todos los endpoints
"""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from src.services.catalogos.producto_receta_service import ProductoRecetaService, ProductoRecetaItemService
from src.schemas.producto_receta_schema import ProductoRecetaCreateSchema, ProductoRecetaUpdateSchema, ProductoRecetaItemCreateSchema, ProductoRecetaItemUpdateSchema

logger = logging.getLogger(__name__)

# Blueprint para recetas
bp = Blueprint('recetas', __name__, url_prefix='/api/recetas')


# ============================================================================
# GET /api/recetas - Listar Recetas
# ============================================================================
@bp.route('', methods=['GET'])
def listar_recetas():
    """
    Listar todas las recetas de productos
    ---
    tags:
      - Recetas
    parameters:
      - in: query
        name: producto_id
        type: integer
      - in: query
        name: solo_activas
        type: boolean
        default: true
    responses:
      200:
        description: Lista de recetas
    """
    try:
        producto_id = request.args.get('producto_id', type=int)
        solo_activas = request.args.get('solo_activas', 'true').lower() == 'true'
        
        resultado = ProductoRecetaService.listar_recetas(producto_id, solo_activas)
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en listar_recetas: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# GET /api/recetas/<id> - Obtener Receta por ID
# ============================================================================
@bp.route('/<int:receta_id>', methods=['GET'])
def obtener_receta(receta_id):
    """
    Obtener receta por ID con sus items
    ---
    tags:
      - Recetas
    parameters:
      - in: path
        name: receta_id
        type: integer
        required: true
    responses:
      200:
        description: Receta encontrada
      404:
        description: Receta no existe
    """
    try:
        resultado = ProductoRecetaService.obtener_receta(receta_id)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 404
            
    except Exception as e:
        logger.error(f"Error en obtener_receta: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# POST /api/recetas - Crear Receta
# ============================================================================
@bp.route('', methods=['POST'])
@jwt_required()
def crear_receta():
    """
    Crear nueva receta para un producto
    Solo ADMIN
    ---
    tags:
      - Recetas
    security:
      - Bearer: []
    parameters:
      - in: body
        name: receta
        required: true
        schema:
          type: object
          properties:
            producto_id:
              type: integer
              example: 1
            nombre:
              type: string
              example: "Receta Estándar"
    responses:
      201:
        description: Receta creada
      400:
        description: Datos inválidos
      403:
        description: Solo ADMIN
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar schema
        schema = ProductoRecetaCreateSchema()
        try:
            datos_validados = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': e.messages
            }), 400
        
        resultado = ProductoRecetaService.crear_receta(
            usuario_id=usuario_id,
            producto_id=datos_validados['producto_id'],
            nombre=datos_validados.get('nombre')
        )
        
        if resultado['success']:
            logger.info(f"Receta para producto {datos_validados['producto_id']} creada por usuario {usuario_id}")
            return jsonify(resultado), 201
        else:
            status = 403 if 'admin' in resultado.get('error', '').lower() else 400
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error en crear_receta: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# PUT /api/recetas/<id> - Actualizar Receta
# ============================================================================
@bp.route('/<int:receta_id>', methods=['PUT'])
@jwt_required()
def actualizar_receta(receta_id):
    """
    Actualizar receta
    Solo ADMIN
    ---
    tags:
      - Recetas
    security:
      - Bearer: []
    parameters:
      - in: path
        name: receta_id
        type: integer
        required: true
      - in: body
        name: receta
        schema:
          type: object
          properties:
            nombre:
              type: string
            es_activa:
              type: boolean
    responses:
      200:
        description: Receta actualizada
      403:
        description: Solo ADMIN
      404:
        description: Receta no existe
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar schema
        schema = ProductoRecetaUpdateSchema()
        try:
            datos_validados = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': e.messages
            }), 400
        
        resultado = ProductoRecetaService.actualizar_receta(
            usuario_id=usuario_id,
            receta_id=receta_id,
            nombre=datos_validados.get('nombre'),
            es_activa=datos_validados.get('es_activa')
        )
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            status = 403 if 'admin' in resultado.get('error', '').lower() else 404
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error en actualizar_receta: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# DELETE /api/recetas/<id> - Eliminar Receta
# ============================================================================
@bp.route('/<int:receta_id>', methods=['DELETE'])
@jwt_required()
def eliminar_receta(receta_id):
    """
    Eliminar receta (soft delete)
    Solo ADMIN
    ---
    tags:
      - Recetas
    security:
      - Bearer: []
    parameters:
      - in: path
        name: receta_id
        type: integer
        required: true
    responses:
      200:
        description: Receta eliminada
      403:
        description: Solo ADMIN
      404:
        description: Receta no existe
    """
    try:
        usuario_id = get_jwt_identity()
        
        resultado = ProductoRecetaService.eliminar_receta(usuario_id, receta_id)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            status = 403 if 'admin' in resultado.get('error', '').lower() else 404
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error en eliminar_receta: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# GET /api/recetas/<id>/items - Obtener Items de Receta
# ============================================================================
@bp.route('/<int:receta_id>/items', methods=['GET'])
def obtener_items_receta(receta_id):
    """
    Obtener todos los insumos de una receta
    ---
    tags:
      - Recetas
    parameters:
      - in: path
        name: receta_id
        type: integer
        required: true
    responses:
      200:
        description: Lista de insumos en la receta
      404:
        description: Receta no existe
    """
    try:
        resultado = ProductoRecetaItemService.listar_items_receta(receta_id)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 404
            
    except Exception as e:
        logger.error(f"Error en obtener_items_receta: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# POST /api/recetas/<id>/items - Agregar Insumo a Receta
# ============================================================================
@bp.route('/<int:receta_id>/items', methods=['POST'])
@jwt_required()
def agregar_insumo_receta(receta_id):
    """
    Agregar un insumo a una receta
    Solo ADMIN
    ---
    tags:
      - Recetas
    security:
      - Bearer: []
    parameters:
      - in: path
        name: receta_id
        type: integer
        required: true
      - in: body
        name: item
        required: true
        schema:
          type: object
          properties:
            insumo_id:
              type: integer
              example: 1
            cantidad:
              type: number
              example: 500.5
    responses:
      201:
        description: Insumo agregado a receta
      400:
        description: Datos inválidos
      403:
        description: Solo ADMIN
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar schema
        schema = ProductoRecetaItemCreateSchema()
        try:
            datos_validados = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': e.messages
            }), 400
        
        resultado = ProductoRecetaItemService.agregar_insumo_receta(
            usuario_id=usuario_id,
            receta_id=receta_id,
            insumo_id=datos_validados['insumo_id'],
            cantidad=datos_validados['cantidad']
        )
        
        if resultado['success']:
            logger.info(f"Insumo {datos_validados['insumo_id']} agregado a receta {receta_id} por usuario {usuario_id}")
            return jsonify(resultado), 201
        else:
            status = 403 if 'admin' in resultado.get('error', '').lower() else 400
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error en agregar_insumo_receta: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# PUT /api/recetas/items/<id> - Actualizar Cantidad de Insumo
# ============================================================================
@bp.route('/items/<int:receta_item_id>', methods=['PUT'])
@jwt_required()
def actualizar_item_receta(receta_item_id):
    """
    Actualizar cantidad de insumo en receta
    Solo ADMIN
    ---
    tags:
      - Recetas
    security:
      - Bearer: []
    parameters:
      - in: path
        name: receta_item_id
        type: integer
        required: true
      - in: body
        name: item
        schema:
          type: object
          properties:
            cantidad:
              type: number
              example: 250.5
    responses:
      200:
        description: Item actualizado
      403:
        description: Solo ADMIN
      404:
        description: Item no existe
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar schema
        schema = ProductoRecetaItemUpdateSchema()
        try:
            datos_validados = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': e.messages
            }), 400
        
        resultado = ProductoRecetaItemService.actualizar_cantidad_item(
            usuario_id=usuario_id,
            receta_item_id=receta_item_id,
            cantidad=datos_validados['cantidad']
        )
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            status = 403 if 'admin' in resultado.get('error', '').lower() else 404
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error en actualizar_item_receta: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# DELETE /api/recetas/items/<id> - Remover Insumo de Receta
# ============================================================================
@bp.route('/items/<int:receta_item_id>', methods=['DELETE'])
@jwt_required()
def remover_insumo_receta(receta_item_id):
    """
    Remover un insumo de una receta
    Solo ADMIN
    ---
    tags:
      - Recetas
    security:
      - Bearer: []
    parameters:
      - in: path
        name: receta_item_id
        type: integer
        required: true
    responses:
      200:
        description: Insumo removido de receta
      403:
        description: Solo ADMIN
      404:
        description: Item no existe
    """
    try:
        usuario_id = get_jwt_identity()
        
        resultado = ProductoRecetaItemService.remover_insumo_receta(usuario_id, receta_item_id)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            status = 403 if 'admin' in resultado.get('error', '').lower() else 404
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error en remover_insumo_receta: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500
