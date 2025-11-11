"""
ProveedorController - Endpoints REST para gestión de Proveedores
Arquitectura n-capas: Controller → Service → DAO → Database
Con documentación Swagger completa para todos los endpoints
"""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from src.services.inventario.proveedor_service import ProveedorService
from src.schemas.proveedor_schema import ProveedorCreateSchema, ProveedorUpdateSchema

logger = logging.getLogger(__name__)

# Blueprint para proveedores
bp = Blueprint('proveedores', __name__, url_prefix='/api/proveedores')


# ============================================================================
# GET /api/proveedores - Listar Proveedores
# ============================================================================
@bp.route('', methods=['GET'])
def listar_proveedores():
    """
    Listar todos los proveedores activos
    ---
    tags:
      - Proveedores
    responses:
      200:
        description: Lista de proveedores activos
    """
    try:
        resultado = ProveedorService.listar_proveedores()
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en listar_proveedores: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# GET /api/proveedores/<id> - Obtener Proveedor por ID
# ============================================================================
@bp.route('/<int:proveedor_id>', methods=['GET'])
def obtener_proveedor(proveedor_id):
    """
    Obtener proveedor por ID
    ---
    tags:
      - Proveedores
    parameters:
      - in: path
        name: proveedor_id
        type: integer
        required: true
    responses:
      200:
        description: Proveedor encontrado
      404:
        description: Proveedor no existe
    """
    try:
        resultado = ProveedorService.obtener_proveedor(proveedor_id)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 404
            
    except Exception as e:
        logger.error(f"Error en obtener_proveedor: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# POST /api/proveedores - Crear Proveedor
# ============================================================================
@bp.route('', methods=['POST'])
@jwt_required()
def crear_proveedor():
    """
    Crear nuevo proveedor
    Solo ADMIN
    ---
    tags:
      - Proveedores
    security:
      - Bearer: []
    parameters:
      - in: body
        name: proveedor
        required: true
        schema:
          type: object
          properties:
            nombre:
              type: string
              example: "Proveedor XYZ"
            telefono:
              type: string
              example: "+5551234567"
            email:
              type: string
              example: "contacto@proveedor.com"
    responses:
      201:
        description: Proveedor creado
      400:
        description: Datos inválidos
      403:
        description: Solo ADMIN
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar schema
        schema = ProveedorCreateSchema()
        try:
            datos_validados = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': e.messages
            }), 400
        
        resultado = ProveedorService.crear_proveedor(
            usuario_id=usuario_id,
            nombre=datos_validados['nombre'],
            telefono=datos_validados.get('telefono'),
            email=datos_validados.get('email')
        )
        
        if resultado['success']:
            logger.info(f"Proveedor '{datos_validados['nombre']}' creado por usuario {usuario_id}")
            return jsonify(resultado), 201
        else:
            status = 403 if 'admin' in resultado.get('error', '').lower() else 400
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error en crear_proveedor: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# PUT /api/proveedores/<id> - Actualizar Proveedor
# ============================================================================
@bp.route('/<int:proveedor_id>', methods=['PUT'])
@jwt_required()
def actualizar_proveedor(proveedor_id):
    """
    Actualizar proveedor
    Solo ADMIN
    ---
    tags:
      - Proveedores
    security:
      - Bearer: []
    parameters:
      - in: path
        name: proveedor_id
        type: integer
        required: true
      - in: body
        name: proveedor
        schema:
          type: object
          properties:
            nombre:
              type: string
            telefono:
              type: string
            email:
              type: string
    responses:
      200:
        description: Proveedor actualizado
      403:
        description: Solo ADMIN
      404:
        description: Proveedor no existe
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar schema
        schema = ProveedorUpdateSchema()
        try:
            datos_validados = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': e.messages
            }), 400
        
        resultado = ProveedorService.actualizar_proveedor(
            usuario_id=usuario_id,
            proveedor_id=proveedor_id,
            nombre=datos_validados.get('nombre'),
            telefono=datos_validados.get('telefono'),
            email=datos_validados.get('email')
        )
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            status = 403 if 'admin' in resultado.get('error', '').lower() else 404
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error en actualizar_proveedor: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# DELETE /api/proveedores/<id> - Eliminar Proveedor
# ============================================================================
@bp.route('/<int:proveedor_id>', methods=['DELETE'])
@jwt_required()
def eliminar_proveedor(proveedor_id):
    """
    Eliminar proveedor (soft delete)
    Solo ADMIN
    ---
    tags:
      - Proveedores
    security:
      - Bearer: []
    parameters:
      - in: path
        name: proveedor_id
        type: integer
        required: true
    responses:
      200:
        description: Proveedor eliminado
      403:
        description: Solo ADMIN
      404:
        description: Proveedor no existe
    """
    try:
        usuario_id = get_jwt_identity()
        
        resultado = ProveedorService.eliminar_proveedor(usuario_id, proveedor_id)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            status = 403 if 'admin' in resultado.get('error', '').lower() else 404
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error en eliminar_proveedor: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500
