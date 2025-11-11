"""
MejoraController - Endpoints REST para Mejoras/Sugerencias
"""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from src.services.servicio.mejora_service import MejoraService
from src.schemas.servicio_schema import MejoraCreateSchema

logger = logging.getLogger(__name__)

# Blueprint para mejoras
bp = Blueprint('mejoras', __name__, url_prefix='/api/mejoras')


# ============================================================================
# POST /api/mejoras - Crear Mejora/Sugerencia
# ============================================================================
@bp.route('', methods=['POST'])
@jwt_required()
def crear_mejora():
    """
    Crear nueva sugerencia de mejora
    ---
    tags:
      - Mejoras
    security:
      - Bearer: []
    parameters:
      - in: body
        name: mejora
        required: true
        schema:
          type: object
          properties:
            notas:
              type: string
              example: "Sería bueno tener más opciones vegetarianas"
    responses:
      201:
        description: Mejora creada
      400:
        description: Datos inválidos
    """
    try:
        cliente_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar schema
        schema = MejoraCreateSchema()
        try:
            datos_validados = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': e.messages
            }), 400
        
        resultado = MejoraService.crear_mejora(
            cliente_id=cliente_id,
            notas=datos_validados['notas']
        )
        
        if resultado['success']:
            logger.info(f"Mejora creada por cliente {cliente_id}")
            return jsonify(resultado), 201
        else:
            return jsonify(resultado), 400
            
    except Exception as e:
        logger.error(f"Error en crear_mejora: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# GET /api/mejoras - Listar Mejoras
# ============================================================================
@bp.route('', methods=['GET'])
@jwt_required()
def listar_mejoras():
    """
    Listar mejoras/sugerencias
    - Clientes ven solo sus sugerencias
    - ADMIN ve todas
    ---
    tags:
      - Mejoras
    security:
      - Bearer: []
    parameters:
      - in: query
        name: estatus
        type: integer
        description: Filtrar por estatus (1=Registrada, 2=En proceso, etc)
    responses:
      200:
        description: Lista de mejoras
    """
    try:
        usuario_id = get_jwt_identity()
        estatus = request.args.get('estatus', type=int)
        
        resultado = MejoraService.listar_mejoras(usuario_id, estatus)
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en listar_mejoras: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# GET /api/mejoras/<id> - Obtener Mejora
# ============================================================================
@bp.route('/<int:mejora_id>', methods=['GET'])
@jwt_required()
def obtener_mejora(mejora_id):
    """
    Obtener mejora por ID
    ---
    tags:
      - Mejoras
    security:
      - Bearer: []
    parameters:
      - in: path
        name: mejora_id
        type: integer
        required: true
    responses:
      200:
        description: Mejora encontrada
      404:
        description: Mejora no existe
    """
    try:
        resultado = MejoraService.obtener_mejora(mejora_id)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 404
            
    except Exception as e:
        logger.error(f"Error en obtener_mejora: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500
