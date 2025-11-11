"""
AsignacionMesaController - Endpoints REST para gestión de Asignaciones de Mesas
Arquitectura n-capas: Controller → Service → DAO → Database
Con documentación Swagger completa para todos los endpoints
"""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.services.asignacion_mesa.asignacion_mesa_service import AsignacionMesaService

logger = logging.getLogger(__name__)

# Blueprint para asignaciones de mesa
bp = Blueprint('asignaciones_mesa', __name__, url_prefix='/api/asignaciones')


# ============================================================================
# POST /api/asignaciones/mesas/{mesa_id} - Asignar Mesero a Mesa
# ============================================================================
@bp.route('/mesas/<int:mesa_id>', methods=['POST'])
@jwt_required()
def asignar_mesero(mesa_id):
    """
    Asignar un mesero a una mesa
    ---
    tags:
      - Asignaciones de Mesas
    security:
      - Bearer: []
    parameters:
      - in: path
        name: mesa_id
        required: true
        type: integer
        description: "ID de la mesa"
      - in: body
        name: asignacion
        required: true
        schema:
          type: object
          required:
            - usuario_id
          properties:
            usuario_id:
              type: integer
              example: 5
              description: "ID del mesero/usuario a asignar"
    responses:
      201:
        description: Mesero asignado exitosamente a la mesa
      400:
        description: Datos inválidos
      403:
        description: Solo administradores pueden asignar meseros
      404:
        description: Mesa o usuario no encontrado
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json()
        
        mesero_id = data.get('usuario_id')
        
        if not mesero_id:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': 'usuario_id es requerido'
            }), 400
        
        resultado = AsignacionMesaService.asignar_mesero(usuario_id, mesa_id, mesero_id)
        
        if resultado['success']:
            logger.info(f"Mesero {mesero_id} asignado a mesa {mesa_id} por usuario {usuario_id}")
            return jsonify(resultado), 201
        else:
            error_msg = resultado.get('error', '').lower()
            if 'admin' in error_msg:
                status = 403
            elif 'no existe' in error_msg or 'no encontrad' in error_msg:
                status = 404
            else:
                status = 400
            return jsonify(resultado), status
        
    except Exception as e:
        logger.error(f"Error asignando mesero a mesa {mesa_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500



# ============================================================================
# DELETE /api/asignaciones/{id} - Desasignar Mesero de Mesa
# ============================================================================
@bp.route('/<int:asignacion_id>', methods=['DELETE'])
@jwt_required()
def desasignar_mesero_endpoint(asignacion_id):
    """
    Desasignar un mesero de una mesa
    ---
    tags:
      - Asignaciones de Mesas
    security:
      - Bearer: []
    parameters:
      - in: path
        name: asignacion_id
        required: true
        type: integer
        description: "ID de la asignación a eliminar"
    responses:
      200:
        description: Mesero desasignado exitosamente
      404:
        description: Asignación no encontrada
      403:
        description: Solo administradores pueden desasignar meseros
    """
    try:
        usuario_id = get_jwt_identity()
        resultado = AsignacionMesaService.desasignar_mesero(usuario_id, asignacion_id)
        
        if resultado['success']:
            logger.info(f"Asignación {asignacion_id} eliminada por usuario {usuario_id}")
            return jsonify(resultado), 200
        else:
            error_msg = resultado.get('error', '').lower()
            if 'admin' in error_msg:
                status = 403
            elif 'no existe' in error_msg:
                status = 404
            else:
                status = 400
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error desasignando mesero {asignacion_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500



# ============================================================================
# GET /api/asignaciones/mesas/{mesa_id} - Obtener Asignaciones de Mesa
# ============================================================================
@bp.route('/mesas/<int:mesa_id>', methods=['GET'])
@jwt_required()
def obtener_asignaciones_mesa_endpoint(mesa_id):
    """
    Obtener todas las asignaciones activas de una mesa
    ---
    tags:
      - Asignaciones de Mesas
    security:
      - Bearer: []
    parameters:
      - in: path
        name: mesa_id
        required: true
        type: integer
        description: "ID de la mesa"
    responses:
      200:
        description: Lista de asignaciones activas de la mesa
      404:
        description: Mesa no encontrada
      403:
        description: Sin acceso a esta mesa
    """
    try:
        usuario_id = get_jwt_identity()
        resultado = AsignacionMesaService.obtener_asignaciones_mesa(usuario_id, mesa_id)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            error_msg = resultado.get('error', '').lower()
            if 'no existe' in error_msg:
                status = 404
            else:
                status = 403
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error obteniendo asignaciones de mesa {mesa_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500



# ============================================================================
# GET /api/asignaciones/meseros/{usuario_id} - Obtener Mesas de Mesero
# ============================================================================
@bp.route('/meseros/<int:usuario_id>', methods=['GET'])
@jwt_required()
def obtener_mesas_mesero_endpoint(usuario_id):
    """
    Obtener todas las mesas asignadas a un mesero
    ---
    tags:
      - Asignaciones de Mesas
    security:
      - Bearer: []
    parameters:
      - in: path
        name: usuario_id
        required: true
        type: integer
        description: "ID del mesero/usuario"
    responses:
      200:
        description: Lista de mesas asignadas al mesero
      404:
        description: Usuario no encontrado
      403:
        description: Sin permiso para ver estas mesas
    """
    try:
        usuario_autenticado = get_jwt_identity()
        resultado = AsignacionMesaService.obtener_mesas_mesero(usuario_autenticado, usuario_id)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            error_msg = resultado.get('error', '').lower()
            if 'no existe' in error_msg:
                status = 404
            else:
                status = 403
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error obteniendo mesas del mesero {usuario_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500



# ============================================================================
# GET /api/asignaciones/mesas/{mesa_id}/activa - Obtener Asignación Activa
# ============================================================================
@bp.route('/mesas/<int:mesa_id>/activa', methods=['GET'])
@jwt_required()
def obtener_asignacion_activa_mesa_endpoint(mesa_id):
    """
    Obtener la asignación activa de una mesa
    ---
    tags:
      - Asignaciones de Mesas
    security:
      - Bearer: []
    parameters:
      - in: path
        name: mesa_id
        required: true
        type: integer
        description: "ID de la mesa"
    responses:
      200:
        description: Asignación activa de la mesa (puede ser null si no hay)
      404:
        description: Mesa no encontrada
      403:
        description: Sin acceso a esta mesa
    """
    try:
        usuario_id = get_jwt_identity()
        resultado = AsignacionMesaService.obtener_asignacion_activa_mesa(usuario_id, mesa_id)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            error_msg = resultado.get('error', '').lower()
            if 'no existe' in error_msg:
                status = 404
            else:
                status = 403
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error obteniendo asignación activa de mesa {mesa_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500
