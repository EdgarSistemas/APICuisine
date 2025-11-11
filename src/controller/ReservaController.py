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
    POST /api/reservas
    
    Crear reserva confirmada.
    Puede venir desde un hold (recomendado) o directo.
    
    Body:
    {
        "cliente_id": 10,
        "recepcionista_id": 5,  // Opcional
        "inicio": "2025-11-15T19:00:00",
        "fin_estimado": "2025-11-15T21:00:00",
        "tolerancia_min": 15,  // Opcional
        "notas": "Celebración cumpleaños",  // Opcional
        "hold_id": 123  // Opcional - ID del hold origen
    }
    
    Returns:
        201: Reserva creada
        400: Validación fallida
        404: Hold no existe (si se especifica)
        409: Hold expirado o no activo
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
    GET /api/reservas/{reserva_id}
    
    Obtener detalles de una reserva.
    
    Returns:
        200: Datos de la reserva
        404: Reserva no existe
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
    GET /api/reservas?cliente_id=10&estatus=1&fecha_desde=2025-11-10
    
    Listar reservas con filtros opcionales.
    
    Query params:
        - cliente_id (opcional): Filtrar por cliente
        - estatus (opcional): Filtrar por estatus (1=Programada, 2=EnCurso, etc.)
        - fecha_desde (opcional): Desde fecha (ISO format)
        - fecha_hasta (opcional): Hasta fecha (ISO format)
    
    Returns:
        200: Lista de reservas
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
    POST /api/reservas/{reserva_id}/iniciar
    
    Iniciar reserva (cliente llegó).
    Cambia estatus a 2 (EnCurso).
    
    Returns:
        200: Reserva iniciada
        400: No está en horario permitido o estatus incorrecto
        404: Reserva no existe
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
    POST /api/reservas/{reserva_id}/completar
    
    Completar reserva (cliente terminó).
    Cambia estatus a 3 (Completada).
    
    Returns:
        200: Reserva completada
        400: Estatus incorrecto
        404: Reserva no existe
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
    POST /api/reservas/{reserva_id}/cancelar
    
    Cancelar reserva.
    Cambia estatus a 5 (Cancelada).
    
    Body (opcional):
    {
        "motivo": "Cambio de planes"
    }
    
    Returns:
        200: Reserva cancelada
        400: Estatus incorrecto
        404: Reserva no existe
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
    POST /api/reservas/{reserva_id}/no-show
    
    Marcar manualmente como NoShow.
    Solo recepcionistas/admins.
    
    Returns:
        200: Reserva marcada como NoShow
        403: Sin permisos
        404: Reserva no existe
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
