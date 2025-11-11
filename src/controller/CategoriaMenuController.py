"""
CategoriaMenuController - Endpoints REST para gestión de Categorías de Menú
Arquitectura n-capas: Controller → Service → DAO → Database
Con documentación Swagger completa para todos los endpoints
"""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from src.services.catalogos.categoria_menu_service import CategoriaMenuService
from src.schemas.categoria_menu_schema import CategoriaMenuCreateSchema, CategoriaMenuUpdateSchema

logger = logging.getLogger(__name__)

# Blueprint para categorias
bp = Blueprint('categorias', __name__, url_prefix='/api/categorias')


# ============================================================================
# GET /api/categorias - Listar Categorías
# ============================================================================
@bp.route('', methods=['GET'])
def listar_categorias():
    """
    Listar todas las categorías de menú activas
    ---
    tags:
      - Categorías de Menú
    responses:
      200:
        description: Lista de categorías activas
    """
    try:
        resultado = CategoriaMenuService.listar_categorias(solo_activas=True)
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en listar_categorias: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# GET /api/categorias/<id> - Obtener Categoría por ID
# ============================================================================
@bp.route('/<int:categoria_id>', methods=['GET'])
def obtener_categoria(categoria_id):
    """
    Obtener categoría por ID
    ---
    tags:
      - Categorías de Menú
    parameters:
      - in: path
        name: categoria_id
        type: integer
        required: true
    responses:
      200:
        description: Categoría encontrada
      404:
        description: Categoría no existe
    """
    try:
        resultado = CategoriaMenuService.obtener_categoria(categoria_id)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 404
            
    except Exception as e:
        logger.error(f"Error en obtener_categoria: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# POST /api/categorias - Crear Categoría
# ============================================================================
@bp.route('', methods=['POST'])
@jwt_required()
def crear_categoria():
    """
    Crear nueva categoría de menú
    Solo ADMIN
    ---
    tags:
      - Categorías de Menú
    security:
      - Bearer: []
    parameters:
      - in: body
        name: categoria
        required: true
        schema:
          type: object
          properties:
            nombre:
              type: string
              example: "Desayunos"
            descripcion:
              type: string
              example: "Platillos de desayuno"
    responses:
      201:
        description: Categoría creada
      400:
        description: Datos inválidos
      403:
        description: Solo ADMIN
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar schema
        schema = CategoriaMenuCreateSchema()
        try:
            datos_validados = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': e.messages
            }), 400
        
        resultado = CategoriaMenuService.crear_categoria(
            usuario_id=usuario_id,
            nombre=datos_validados['nombre'],
            descripcion=datos_validados.get('descripcion')
        )
        
        if resultado['success']:
            logger.info(f"Categoría '{datos_validados['nombre']}' creada por usuario {usuario_id}")
            return jsonify(resultado), 201
        else:
            status = 403 if 'admin' in resultado.get('error', '').lower() else 400
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error en crear_categoria: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# PUT /api/categorias/<id> - Actualizar Categoría
# ============================================================================
@bp.route('/<int:categoria_id>', methods=['PUT'])
@jwt_required()
def actualizar_categoria(categoria_id):
    """
    Actualizar categoría
    Solo ADMIN
    ---
    tags:
      - Categorías de Menú
    security:
      - Bearer: []
    parameters:
      - in: path
        name: categoria_id
        type: integer
        required: true
      - in: body
        name: categoria
        schema:
          type: object
          properties:
            nombre:
              type: string
            descripcion:
              type: string
    responses:
      200:
        description: Categoría actualizada
      403:
        description: Solo ADMIN
      404:
        description: Categoría no existe
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar schema
        schema = CategoriaMenuUpdateSchema()
        try:
            datos_validados = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': e.messages
            }), 400
        
        resultado = CategoriaMenuService.actualizar_categoria(
            usuario_id=usuario_id,
            categoria_id=categoria_id,
            nombre=datos_validados.get('nombre'),
            descripcion=datos_validados.get('descripcion')
        )
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            status = 403 if 'admin' in resultado.get('error', '').lower() else 404
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error en actualizar_categoria: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# DELETE /api/categorias/<id> - Eliminar Categoría
# ============================================================================
@bp.route('/<int:categoria_id>', methods=['DELETE'])
@jwt_required()
def eliminar_categoria(categoria_id):
    """
    Eliminar categoría (soft delete)
    Solo ADMIN
    ---
    tags:
      - Categorías de Menú
    security:
      - Bearer: []
    parameters:
      - in: path
        name: categoria_id
        type: integer
        required: true
    responses:
      200:
        description: Categoría eliminada
      403:
        description: Solo ADMIN
      404:
        description: Categoría no existe
    """
    try:
        usuario_id = get_jwt_identity()
        
        resultado = CategoriaMenuService.eliminar_categoria(usuario_id, categoria_id)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            status = 403 if 'admin' in resultado.get('error', '').lower() else 404
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error en eliminar_categoria: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500
