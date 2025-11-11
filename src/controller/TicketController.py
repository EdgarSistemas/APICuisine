"""
TicketController - Endpoints REST para Tickets de incidencias
"""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from src.services.ticket.ticket_service import TicketService
from src.schemas.ticket_schema import TicketCreateSchema, TicketUpdateEstatusSchema

logger = logging.getLogger(__name__)

# Blueprint para tickets
bp = Blueprint('tickets', __name__, url_prefix='/api/tickets')


# ============================================================================
# POST /api/tickets - Crear Ticket
# ============================================================================
@bp.route('', methods=['POST'])
@jwt_required()
def crear_ticket():
    """
    Crear nuevo ticket de incidencia
    Cualquier usuario autenticado puede crear
    ---
    tags:
      - Tickets
    security:
      - Bearer: []
    parameters:
      - in: body
        name: ticket
        required: true
        schema:
          type: object
          properties:
            notas:
              type: string
              example: "La caja registradora no enciende"
            imagen_url:
              type: string
              example: "https://storage.com/img.jpg"
    responses:
      201:
        description: Ticket creado
      400:
        description: Datos inválidos
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar schema
        schema = TicketCreateSchema()
        try:
            datos_validados = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': e.messages
            }), 400
        
        resultado = TicketService.crear_ticket(
            usuario_id=usuario_id,
            notas=datos_validados['notas'],
            imagen_url=datos_validados.get('imagen_url')
        )
        
        if resultado['success']:
            logger.info(f"Ticket creado por usuario {usuario_id}")
            return jsonify(resultado), 201
        else:
            return jsonify(resultado), 400
            
    except Exception as e:
        logger.error(f"Error en crear_ticket: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# GET /api/tickets - Listar Tickets
# ============================================================================
@bp.route('', methods=['GET'])
@jwt_required()
def listar_tickets():
    """
    Listar tickets
    - Usuarios ven solo sus tickets
    - ADMIN ve todos
    ---
    tags:
      - Tickets
    security:
      - Bearer: []
    parameters:
      - in: query
        name: usuario_id
        type: integer
        description: Filtrar por usuario (solo ADMIN)
      - in: query
        name: estatus
        type: integer
        description: Filtrar por estatus (1=Registrada, 2=EnProceso, 3=Completada, 4=Cancelada)
    responses:
      200:
        description: Lista de tickets
    """
    try:
        usuario_id = get_jwt_identity()
        filtro_usuario_id = request.args.get('usuario_id', type=int)
        estatus = request.args.get('estatus', type=int)
        
        resultado = TicketService.listar_tickets(usuario_id, filtro_usuario_id, estatus)
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en listar_tickets: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# GET /api/tickets/<id> - Obtener Ticket
# ============================================================================
@bp.route('/<int:ticket_id>', methods=['GET'])
@jwt_required()
def obtener_ticket(ticket_id):
    """
    Obtener ticket por ID
    ---
    tags:
      - Tickets
    security:
      - Bearer: []
    parameters:
      - in: path
        name: ticket_id
        type: integer
        required: true
    responses:
      200:
        description: Ticket encontrado
      404:
        description: Ticket no existe
    """
    try:
        resultado = TicketService.obtener_ticket(ticket_id)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 404
            
    except Exception as e:
        logger.error(f"Error en obtener_ticket: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# PATCH /api/tickets/<id>/estatus - Actualizar Estatus
# ============================================================================
@bp.route('/<int:ticket_id>/estatus', methods=['PATCH'])
@jwt_required()
def actualizar_estatus(ticket_id):
    """
    Actualizar estatus de ticket
    Solo ADMIN
    ---
    tags:
      - Tickets
    security:
      - Bearer: []
    parameters:
      - in: path
        name: ticket_id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            estatus:
              type: integer
              example: 2
              description: 1=Registrada, 2=EnProceso, 3=Completada, 4=Cancelada
    responses:
      200:
        description: Estatus actualizado
      403:
        description: Solo ADMIN
      404:
        description: Ticket no existe
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar schema
        schema = TicketUpdateEstatusSchema()
        try:
            datos_validados = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': e.messages
            }), 400
        
        resultado = TicketService.actualizar_estatus(
            usuario_id=usuario_id,
            ticket_id=ticket_id,
            estatus=datos_validados['estatus']
        )
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            status = 403 if 'admin' in resultado.get('error', '').lower() else 404
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error en actualizar_estatus: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500
