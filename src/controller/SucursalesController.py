"""Controlador REST para Sucursales"""

import logging
from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.services.catalogos.sucursal_service import SucursalService
from src.schemas.sucursal_schema import SucursalCreateSchema, SucursalUpdateSchema
from src.core.utils.multitenant import es_admin as es_admin_fn

logger = logging.getLogger(__name__)

# Blueprint para sucursales
sucursales_bp = Blueprint('sucursales', __name__, url_prefix='/api/sucursales')

# Instanciar esquemas y servicio
sucursal_create_schema = SucursalCreateSchema()
sucursal_update_schema = SucursalUpdateSchema()
sucursal_service = SucursalService()

@sucursales_bp.route('', methods=['POST'])
@jwt_required()
def crear_sucursal():
    """
    Crear nueva sucursal
    ---
    tags:
      - Sucursales
    security:
      - Bearer: []
    parameters:
      - in: body
        name: sucursal
        required: true
        schema:
          type: object
          properties:
            codigo_sucursal:
              type: string
              example: "SUC-001"
            nombre:
              type: string
              example: "Sucursal Centro"
            telefono:
              type: string
              example: "555-123-4567"
            direccion:
              type: string
              example: "Av. Principal #123"
    responses:
      201:
        description: Sucursal creada exitosamente
      400:
        description: Datos inválidos
    """
    try:
        datos_sucursal = sucursal_create_schema.load(request.get_json())
        
        # Restaurar dependencia de usuario_id
        usuario_id = get_jwt_identity()
        sucursal = sucursal_service.crear_sucursal(datos_sucursal, usuario_id)
        
        logger.info(f"Sucursal creada")
        return jsonify({
            'success': True,
            'message': 'Sucursal creada exitosamente',
            'data': sucursal
        }), 201
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'VALIDATION_ERROR',
            'message': 'Datos inválidos',
            'details': e.messages
        }), 400
    except Exception as e:
        logger.error(f"Error creando sucursal: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500


@sucursales_bp.route('/<int:id_sucursal>', methods=['GET'])
@jwt_required()
def obtener_sucursal(id_sucursal):
    """
    Obtener sucursal por ID
    ---
    tags:
      - Sucursales
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id_sucursal
        required: true
        type: integer
    responses:
      200:
        description: Sucursal encontrada
      404:
        description: Sucursal no encontrada
    """
    try:
        sucursal = sucursal_service.obtener_sucursal(id_sucursal)
        return jsonify({
            'success': True,
            'data': sucursal
        }), 200
        
    except Exception as e:
        if "no encontrada" in str(e).lower():
            return jsonify({
                'success': False,
                'error': 'NOT_FOUND',
                'message': f'Sucursal con ID {id_sucursal} no encontrada'
            }), 404
        
        logger.error(f"Error obteniendo sucursal {id_sucursal}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500


@sucursales_bp.route('', methods=['GET'])
def listar_sucursales():
  """
  Listar sucursales
  ---
  tags:
    - Sucursales
  responses:
    200:
      description: Lista de sucursales
  """
  try:
    usuario_id = None
    es_admin = False
    # Si el usuario está autenticado, obtener su id y rol
    try:
      usuario_id = get_jwt_identity()
      es_admin = es_admin_fn(usuario_id)
    except Exception:
      pass
    sucursales = sucursal_service.listar_sucursales(usuario_id=usuario_id, es_admin=es_admin)
    return jsonify({
      'success': True,
      'data': sucursales
    }), 200
  except Exception as e:
    logger.error(f"Error listando sucursales: {str(e)}")
    return jsonify({
      'success': False,
      'error': 'INTERNAL_ERROR',
      'message': 'Error interno del servidor'
    }), 500


@sucursales_bp.route('/activas', methods=['GET'])
def listar_sucursales_activas():
    """
    Listar sucursales activas
    ---
    tags:
      - Sucursales
    responses:
      200:
        description: Lista de sucursales activas
    """
    try:
        sucursales = sucursal_service.obtener_sucursales_activas()
        return jsonify({
            'success': True,
            'data': sucursales
        }), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo sucursales activas: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500


@sucursales_bp.route('/<int:id_sucursal>', methods=['PUT'])
@jwt_required()
def actualizar_sucursal(id_sucursal):
    """
    Actualizar sucursal
    ---
    tags:
      - Sucursales
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id_sucursal
        required: true
        type: integer
      - in: body
        name: sucursal
        required: true
        schema:
          type: object
          properties:
            nombre:
              type: string
              example: "Sucursal Centro Actualizada"
            telefono:
              type: string
              example: "555-987-6543"
            direccion:
              type: string
              example: "Nueva Dirección #456"
    responses:
      200:
        description: Sucursal actualizada exitosamente
      404:
        description: Sucursal no encontrada
      400:
        description: Datos inválidos
    """
    try:
        datos_actualizacion = sucursal_update_schema.load(request.get_json())
        sucursal = sucursal_service.actualizar_sucursal(id_sucursal, datos_actualizacion)
        
        logger.info(f"Sucursal {id_sucursal} actualizada")
        return jsonify({
            'success': True,
            'message': 'Sucursal actualizada exitosamente',
            'data': sucursal
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'VALIDATION_ERROR',
            'message': 'Datos inválidos',
            'details': e.messages
        }), 400
    except Exception as e:
        if "no encontrada" in str(e).lower():
            return jsonify({
                'success': False,
                'error': 'NOT_FOUND',
                'message': f'Sucursal con ID {id_sucursal} no encontrada'
            }), 404
        
        logger.error(f"Error actualizando sucursal {id_sucursal}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500


@sucursales_bp.route('/<int:id_sucursal>', methods=['DELETE'])
@jwt_required()
def eliminar_sucursal(id_sucursal):
    """
    Eliminar sucursal (eliminación lógica)
    ---
    tags:
      - Sucursales
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id_sucursal
        required: true
        type: integer
    responses:
      200:
        description: Sucursal eliminada exitosamente
      404:
        description: Sucursal no encontrada
    """
    try:
        resultado = sucursal_service.eliminar_sucursal(id_sucursal)
        
        logger.info(f"Sucursal {id_sucursal} eliminada")
        return jsonify({
            'success': True,
            'message': 'Sucursal eliminada exitosamente'
        }), 200
        
    except Exception as e:
        if "no encontrada" in str(e).lower():
            return jsonify({
                'success': False,
                'error': 'NOT_FOUND',
                'message': f'Sucursal con ID {id_sucursal} no encontrada'
            }), 404
        
        logger.error(f"Error eliminando sucursal {id_sucursal}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500