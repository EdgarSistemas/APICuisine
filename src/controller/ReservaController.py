"""
ReservaController - Endpoints REST para Reserva
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from src.services.operaciones.reserva_service import ReservaService
from src.schemas.reserva_schema import (
    ReservaCreateSchema,
    ReservaActualizarEstatusSchema,
    ReservaCancelarSchema,
    ReservaListarQuerySchema
)
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Blueprint
reserva_bp = Blueprint('reserva', __name__, url_prefix='/api/reservas')


@reserva_bp.route('/', methods=['POST'])
@jwt_required()
def crear_reserva():
    """
    Crear reserva confirmada desde hold.
    ---
    tags:
      - Reservas
    summary: Crear reserva
    description: Crea una reserva confirmada. Recomendado desde un hold existente.
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              cliente_id:
                type: integer
              inicio:
                type: string
                format: date-time
              fin_estimado:
                type: string
                format: date-time
              hold_id:
                type: integer
    responses:
      201:
        description: Reserva creada
      400:
        description: Validación fallida
      404:
        description: Hold no existe
      409:
        description: Hold expirado
    """
    try:
        # Validar schema
        schema = ReservaCreateSchema()
        data = schema.load(request.json)
        
        # Usuario autenticado
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario')
        
        # Crear reserva
        result = ReservaService.crear_reserva(
            usuario_id=usuario_id,
            cliente_id=data.get('cliente_id'),
            recepcionista_id=data.get('recepcionista_id'),
            inicio=data['inicio'],
            fin_estimado=data['fin_estimado'],
            tolerancia_min=data.get('tolerancia_min'),
            notas=data.get('notas'),
            hold_id=data.get('hold_id')
        )
        
        if not result['success']:
            # Determinar código de error
            if 'no existe' in result['error']:
                return jsonify({"error": result['error']}), 404
            elif 'expiró' in result['error'] or 'no está activo' in result['error']:
                return jsonify({"error": result['error']}), 409
            else:
                return jsonify({"error": result['error']}), 400
        
        return jsonify({
            "message": "Reserva creada exitosamente",
            "reserva": result['data']
        }), 201
        
    except ValidationError as e:
        logger.error(f"Error de validación en crear_reserva: {e.messages}")
        return jsonify({"error": "Datos inválidos", "detalles": e.messages}), 400
    except Exception as e:
        logger.error(f"Error en crear_reserva: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@reserva_bp.route('/<int:reserva_id>', methods=['GET'])
@jwt_required()
def obtener_reserva(reserva_id):
    """
    Obtener detalles de una reserva
    ---
    tags:
      - Reservas
    summary: Obtener reserva por ID
    description: Retrieves detailed information about a specific reservation including customer, mesa, and status information.
    parameters:
      - in: path
        name: reserva_id
        type: integer
        required: true
        description: ID de la reserva
    responses:
      200:
        description: Reserva encontrada
        schema:
          type: object
          properties:
            id_reserva:
              type: integer
            mesa_id:
              type: integer
            cliente_id:
              type: integer
            estatus:
              type: integer
              description: "1=Programada, 2=EnCurso, 3=Completada, 4=NoShow, 5=Cancelada"
            inicio:
              type: string
              format: date-time
            fin_estimado:
              type: string
              format: date-time
            usuario_creacion_id:
              type: integer
            notas:
              type: string
      404:
        description: Reserva no existe
      500:
        description: Error interno
    """
    try:
        result = ReservaService.obtener_reserva(reserva_id)
        
        if not result['success']:
            return jsonify({"error": result['error']}), 404
        
        return jsonify(result['data']), 200
        
    except Exception as e:
        logger.error(f"Error en obtener_reserva: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@reserva_bp.route('/', methods=['GET'])
@jwt_required()
def listar_reservas():
    """
    Listar reservas con filtros
    ---
    tags:
      - Reservas
    summary: Listar reservas
    description: Lists all reservations with optional filters by customer, status, and date range. Only returns reservations from the authenticated user's sucursal (multi-tenant).
    parameters:
      - in: query
        name: cliente_id
        type: integer
        required: false
        description: Filtrar por cliente (opcional)
      - in: query
        name: estatus
        type: integer
        required: false
        description: "Filtrar por estatus: 1=Programada, 2=EnCurso, 3=Completada, 4=NoShow, 5=Cancelada (opcional)"
      - in: query
        name: fecha_desde
        type: string
        format: date
        required: false
        description: Desde fecha en formato ISO (opcional)
      - in: query
        name: fecha_hasta
        type: string
        format: date
        required: false
        description: Hasta fecha en formato ISO (opcional)
    responses:
      200:
        description: Lista de reservas
        schema:
          type: object
          properties:
            reservas:
              type: array
              items:
                type: object
                properties:
                  id_reserva:
                    type: integer
                  mesa_id:
                    type: integer
                  cliente_id:
                    type: integer
                  estatus:
                    type: integer
                  inicio:
                    type: string
                    format: date-time
                  fin_estimado:
                    type: string
                    format: date-time
            total:
              type: integer
      400:
        description: Parametros invalidos
      500:
        description: Error interno
    """
    try:
        # Parsear query params
        schema = ReservaListarQuerySchema()
        filters = schema.load(request.args)
        
        # Usuario autenticado
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario')
        
        # Listar
        result = ReservaService.listar_reservas(
            usuario_id=usuario_id,
            cliente_id=filters.get('cliente_id'),
            estatus=filters.get('estatus'),
            fecha_desde=filters.get('fecha_desde'),
            fecha_hasta=filters.get('fecha_hasta')
        )
        
        if not result['success']:
            return jsonify({"error": result['error']}), 400
        
        return jsonify({
            "reservas": result['data'],
            "total": len(result['data'])
        }), 200
        
    except ValidationError as e:
        logger.error(f"Error de validación en listar_reservas: {e.messages}")
        return jsonify({"error": "Parámetros inválidos", "detalles": e.messages}), 400
    except Exception as e:
        logger.error(f"Error en listar_reservas: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@reserva_bp.route('/<int:reserva_id>/iniciar', methods=['POST'])
@jwt_required()
def iniciar_reserva(reserva_id):
    """
    Iniciar reserva (cliente llego)
    ---
    tags:
      - Reservas
    summary: Iniciar reserva
    description: Marks a reservation as started (customer arrived). Changes status to 2 (EnCurso). Validates that the reservation is within allowed check-in window.
    parameters:
      - in: path
        name: reserva_id
        type: integer
        required: true
        description: ID de la reserva a iniciar
    responses:
      200:
        description: Reserva iniciada exitosamente
        schema:
          type: object
          properties:
            message:
              type: string
            reserva:
              type: object
              properties:
                id_reserva:
                  type: integer
                estatus:
                  type: integer
                  description: "Sera 2 (EnCurso)"
      400:
        description: No esta en horario permitido, estatus incorrecto, o cliente no llego a tiempo
      404:
        description: Reserva no existe
      500:
        description: Error interno
    """
    try:
        # Usuario autenticado
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario')
        
        # Iniciar
        result = ReservaService.iniciar_reserva(usuario_id, reserva_id)
        
        if not result['success']:
            if 'no existe' in result['error']:
                return jsonify({"error": result['error']}), 404
            else:
                return jsonify({"error": result['error']}), 400
        
        return jsonify({
            "message": "Reserva iniciada exitosamente",
            "reserva": result['data']
        }), 200
        
    except Exception as e:
        logger.error(f"Error en iniciar_reserva: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@reserva_bp.route('/<int:reserva_id>/completar', methods=['POST'])
@jwt_required()
def completar_reserva(reserva_id):
    """
    Completar reserva (cliente termino)
    ---
    tags:
      - Reservas
    summary: Completar reserva
    description: Marks a reservation as completed. Changes status to 3 (Completada). This is done when the customer finishes their meal and leaves.
    parameters:
      - in: path
        name: reserva_id
        type: integer
        required: true
        description: ID de la reserva a completar
    responses:
      200:
        description: Reserva completada exitosamente
        schema:
          type: object
          properties:
            message:
              type: string
            reserva:
              type: object
              properties:
                id_reserva:
                  type: integer
                estatus:
                  type: integer
                  description: "Sera 3 (Completada)"
      400:
        description: Estatus incorrecto o no puede completarse
      404:
        description: Reserva no existe
      500:
        description: Error interno
    """
    try:
        # Usuario autenticado
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario')
        
        # Completar
        result = ReservaService.completar_reserva(usuario_id, reserva_id)
        
        if not result['success']:
            if 'no existe' in result['error']:
                return jsonify({"error": result['error']}), 404
            else:
                return jsonify({"error": result['error']}), 400
        
        return jsonify({
            "message": "Reserva completada exitosamente",
            "reserva": result['data']
        }), 200
        
    except Exception as e:
        logger.error(f"Error en completar_reserva: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@reserva_bp.route('/<int:reserva_id>/cancelar', methods=['POST'])
@jwt_required()
def cancelar_reserva(reserva_id):
    """
    Cancelar reserva
    ---
    tags:
      - Reservas
    summary: Cancelar reserva
    description: Cancels an active reservation. Changes status to 5 (Cancelada). Can only cancel from Programada (1) or EnCurso (2) status.
    parameters:
      - in: path
        name: reserva_id
        type: integer
        required: true
        description: ID de la reserva a cancelar
    requestBody:
      required: false
      content:
        application/json:
          schema:
            type: object
            properties:
              motivo:
                type: string
                description: Razon de la cancelacion (opcional)
    responses:
      200:
        description: Reserva cancelada exitosamente
        schema:
          type: object
          properties:
            message:
              type: string
            reserva:
              type: object
              properties:
                id_reserva:
                  type: integer
                estatus:
                  type: integer
                  description: "Sera 5 (Cancelada)"
      400:
        description: Estatus incorrecto o no puede cancelarse, o datos invalidos
      404:
        description: Reserva no existe
      500:
        description: Error interno
    """
    try:
        # Validar schema
        schema = ReservaCancelarSchema()
        data = schema.load(request.json or {})
        
        # Usuario autenticado
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario')
        
        # Cancelar
        result = ReservaService.cancelar_reserva(
            usuario_id,
            reserva_id,
            data.get('motivo')
        )
        
        if not result['success']:
            if 'no existe' in result['error']:
                return jsonify({"error": result['error']}), 404
            else:
                return jsonify({"error": result['error']}), 400
        
        return jsonify({
            "message": "Reserva cancelada exitosamente",
            "reserva": result['data']
        }), 200
        
    except ValidationError as e:
        logger.error(f"Error de validación en cancelar_reserva: {e.messages}")
        return jsonify({"error": "Datos inválidos", "detalles": e.messages}), 400
    except Exception as e:
        logger.error(f"Error en cancelar_reserva: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@reserva_bp.route('/<int:reserva_id>/no-show', methods=['POST'])
@jwt_required()
def marcar_no_show(reserva_id):
    """
    Marcar reserva como NoShow
    ---
    tags:
      - Reservas
    summary: Marcar como NoShow
    description: Manually marks a reservation as NoShow (status 4). Only recepcionistas/admins can perform this action. Should be used when a customer with a reservation does not show up by the end of the tolerance window.
    parameters:
      - in: path
        name: reserva_id
        type: integer
        required: true
        description: ID de la reserva a marcar como NoShow
    responses:
      200:
        description: Reserva marcada como NoShow exitosamente
        schema:
          type: object
          properties:
            message:
              type: string
            reserva:
              type: object
              properties:
                id_reserva:
                  type: integer
                estatus:
                  type: integer
                  description: "Sera 4 (NoShow)"
      400:
        description: Estatus incorrecto o no puede marcarse como NoShow
      403:
        description: Sin permisos para marcar como NoShow (requiere recepcionista/admin)
      404:
        description: Reserva no existe
      500:
        description: Error interno
    """
    try:
        # Usuario autenticado
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario')
        
        # TODO: Validar rol de usuario (recepcionista/admin)
        
        # Marcar
        result = ReservaService.marcar_no_show(usuario_id, reserva_id)
        
        if not result['success']:
            if 'no existe' in result['error']:
                return jsonify({"error": result['error']}), 404
            else:
                return jsonify({"error": result['error']}), 400
        
        return jsonify({
            "message": "Reserva marcada como NoShow",
            "reserva": result['data']
        }), 200
        
    except Exception as e:
        logger.error(f"Error en marcar_no_show: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500
