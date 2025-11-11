"""
ProductoController - Endpoints REST para gestión de Productos
Arquitectura n-capas: Controller → Service → DAO → Database
Con documentación Swagger completa para todos los endpoints
"""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from src.services.catalogos.producto_service import ProductoService
from src.schemas.producto_schema import ProductoCreateSchema, ProductoUpdateSchema

logger = logging.getLogger(__name__)

# Blueprint para productos
bp = Blueprint('productos', __name__, url_prefix='/api/productos')


# ============================================================================
# GET /api/productos - Listar Productos
# ============================================================================
@bp.route('', methods=['GET'])
def listar_productos():
    """
    Listar todos los productos activos
    ---
    tags:
      - Productos
    responses:
      200:
        description: Lista de productos activos
    """
    try:
        resultado = ProductoService.listar_productos()
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en listar_productos: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# GET /api/productos/<id> - Obtener Producto por ID
# ============================================================================
@bp.route('/<int:producto_id>', methods=['GET'])
def obtener_producto(producto_id):
    """
    Obtener producto por ID
    ---
    tags:
      - Productos
    parameters:
      - in: path
        name: producto_id
        type: integer
        required: true
    responses:
      200:
        description: Producto encontrado
      404:
        description: Producto no existe
    """
    try:
        resultado = ProductoService.obtener_producto(producto_id)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 404
            
    except Exception as e:
        logger.error(f"Error en obtener_producto: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# POST /api/productos - Crear Producto
# ============================================================================
@bp.route('', methods=['POST'])
@jwt_required()
def crear_producto():
    """
    Crear nuevo producto
    Solo ADMIN
    ---
    tags:
      - Productos
    security:
      - Bearer: []
    parameters:
      - in: body
        name: producto
        required: true
        schema:
          type: object
          properties:
            categoria_id:
              type: integer
              example: 1
            codigo:
              type: string
              example: "PAN001"
            nombre:
              type: string
              example: "Pan Integral"
            descripcion:
              type: string
            imagen_url:
              type: string
            precio:
              type: number
              example: 5.50
            receta_items:
              type: array
              items:
                type: object
                properties:
                  insumo_id:
                    type: integer
                    example: 1
                  cantidad:
                    type: number
                    example: 500
    responses:
      201:
        description: Producto creado
      400:
        description: Datos inválidos
      403:
        description: Solo ADMIN
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar schema
        schema = ProductoCreateSchema()
        try:
            datos_validados = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': e.messages
            }), 400
        
        resultado = ProductoService.crear_producto(
            usuario_id=usuario_id,
            categoria_id=datos_validados['categoria_id'],
            nombre=datos_validados['nombre'],
            precio=datos_validados['precio'],
            codigo=datos_validados.get('codigo'),
            descripcion=datos_validados.get('descripcion'),
            imagen_url=datos_validados.get('imagen_url'),
            receta_items=datos_validados.get('receta_items')
        )
        
        if resultado['success']:
            logger.info(f"Producto '{datos_validados['nombre']}' creado por usuario {usuario_id}")
            return jsonify(resultado), 201
        else:
            status = 403 if 'admin' in resultado.get('error', '').lower() else 400
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error en crear_producto: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# PUT /api/productos/<id> - Actualizar Producto
# ============================================================================
@bp.route('/<int:producto_id>', methods=['PUT'])
@jwt_required()
def actualizar_producto(producto_id):
    """
    Actualizar producto
    Solo ADMIN
    ---
    tags:
      - Productos
    security:
      - Bearer: []
    parameters:
      - in: path
        name: producto_id
        type: integer
        required: true
      - in: body
        name: producto
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
            receta_items:
              type: array
              items:
                type: object
                properties:
                  id_receta_item:
                    type: integer
                  cantidad:
                    type: number
    responses:
      200:
        description: Producto actualizado
      403:
        description: Solo ADMIN
      404:
        description: Producto no existe
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar schema
        schema = ProductoUpdateSchema()
        try:
            datos_validados = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': e.messages
            }), 400
        
        resultado = ProductoService.actualizar_producto(
            usuario_id=usuario_id,
            producto_id=producto_id,
            nombre=datos_validados.get('nombre'),
            descripcion=datos_validados.get('descripcion'),
            imagen_url=datos_validados.get('imagen_url'),
            precio=datos_validados.get('precio'),
            receta_items=datos_validados.get('receta_items')
        )
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            status = 403 if 'admin' in resultado.get('error', '').lower() else 404
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error en actualizar_producto: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# DELETE /api/productos/<id> - Eliminar Producto
# ============================================================================
@bp.route('/<int:producto_id>', methods=['DELETE'])
@jwt_required()
def eliminar_producto(producto_id):
    """
    Eliminar producto (soft delete)
    Solo ADMIN
    ---
    tags:
      - Productos
    security:
      - Bearer: []
    parameters:
      - in: path
        name: producto_id
        type: integer
        required: true
    responses:
      200:
        description: Producto eliminado
      403:
        description: Solo ADMIN
      404:
        description: Producto no existe
    """
    try:
        usuario_id = get_jwt_identity()
        
        resultado = ProductoService.eliminar_producto(usuario_id, producto_id)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            status = 403 if 'admin' in resultado.get('error', '').lower() else 404
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error en eliminar_producto: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500
