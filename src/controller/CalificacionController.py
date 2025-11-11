"""
CalificacionController - Endpoints REST para Calificaciones de servicio
"""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from src.services.servicio.calificacion_service import CalificacionService
from src.schemas.servicio_schema import CalificacionCreateSchema

logger = logging.getLogger(__name__)

# Blueprint para calificaciones
bp = Blueprint('calificaciones', __name__, url_prefix='/api/calificaciones')


# ============================================================================
# POST /api/calificaciones - Crear Calificación
# ============================================================================
@bp.route('', methods=['POST'])
@jwt_required()
def crear_calificacion():
    """
    Crear nueva calificación de servicio
    ---
    tags:
      - Calificaciones
    security:
      - Bearer: []
    parameters:
      - in: body
        name: calificacion
        required: true
        schema:
          type: object
          properties:
            pedido_id:
              type: integer
              example: 1
            empleado_id:
              type: integer
              example: 5
            calificacion:
              type: integer
              example: 9
              description: Calificación de 1 a 10
            notas:
              type: string
              example: "Excelente servicio"
    responses:
      201:
        description: Calificación creada
      400:
        description: Datos inválidos o ya calificado
    """
    try:
        cliente_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar schema
        schema = CalificacionCreateSchema()
        try:
            datos_validados = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': e.messages
            }), 400
        
        resultado = CalificacionService.crear_calificacion(
            cliente_id=cliente_id,
            pedido_id=datos_validados['pedido_id'],
            empleado_id=datos_validados['empleado_id'],
            calificacion=datos_validados['calificacion'],
            notas=datos_validados.get('notas')
        )
        
        if resultado['success']:
            logger.info(f"Calificación creada por cliente {cliente_id} para pedido {datos_validados['pedido_id']}")
            return jsonify(resultado), 201
        else:
            return jsonify(resultado), 400
            
    except Exception as e:
        logger.error(f"Error en crear_calificacion: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# GET /api/calificaciones - Listar Calificaciones
# ============================================================================
@bp.route('', methods=['GET'])
@jwt_required()
def listar_calificaciones():
    """
    Listar calificaciones
    - Clientes ven solo sus calificaciones
    - ADMIN ve todas
    ---
    tags:
      - Calificaciones
    security:
      - Bearer: []
    parameters:
      - in: query
        name: pedido_id
        type: integer
        description: Filtrar por pedido
      - in: query
        name: empleado_id
        type: integer
        description: Filtrar por empleado
    responses:
      200:
        description: Lista de calificaciones
    """
    try:
        usuario_id = get_jwt_identity()
        pedido_id = request.args.get('pedido_id', type=int)
        empleado_id = request.args.get('empleado_id', type=int)
        
        resultado = CalificacionService.listar_calificaciones(usuario_id, pedido_id, empleado_id)
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en listar_calificaciones: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# GET /api/calificaciones/<id> - Obtener Calificación
# ============================================================================
@bp.route('/<int:calificacion_id>', methods=['GET'])
@jwt_required()
def obtener_calificacion(calificacion_id):
    """
    Obtener calificación por ID
    ---
    tags:
      - Calificaciones
    security:
      - Bearer: []
    parameters:
      - in: path
        name: calificacion_id
        type: integer
        required: true
    responses:
      200:
        description: Calificación encontrada
      404:
        description: Calificación no existe
    """
    try:
        resultado = CalificacionService.obtener_calificacion(calificacion_id)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 404
            
    except Exception as e:
        logger.error(f"Error en obtener_calificacion: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# GET /api/calificaciones/empleado/<id>/promedio - Promedio de Empleado
# ============================================================================
@bp.route('/empleado/<int:empleado_id>/promedio', methods=['GET'])
@jwt_required()
def obtener_promedio_empleado(empleado_id):
    """
    Obtener promedio de calificaciones de un empleado
    ---
    tags:
      - Calificaciones
    security:
      - Bearer: []
    parameters:
      - in: path
        name: empleado_id
        type: integer
        required: true
    responses:
      200:
        description: Promedio calculado
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: object
              properties:
                empleado_id:
                  type: integer
                promedio:
                  type: number
    """
    try:
        resultado = CalificacionService.obtener_promedio_empleado(empleado_id)
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en obtener_promedio_empleado: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500
