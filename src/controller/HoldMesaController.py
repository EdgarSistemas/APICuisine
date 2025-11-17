"""
HoldMesaController - Endpoints REST para HoldMesa
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from src.services.operaciones.hold_mesa_service import HoldMesaService
from src.schemas.reserva_schema import HoldMesaCreateSchema, HoldMesaCancelarSchema
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Blueprint
hold_mesa_bp = Blueprint('hold_mesa', __name__, url_prefix='/api/holds')


@hold_mesa_bp.route('/', methods=['POST'])
@jwt_required()
def crear_hold():
    """
    Crear hold temporal de mesa (3 minutos).
    ---
    tags:
      - Holds
    summary: Crear hold de mesa
    description: Crea un hold temporal de 3 minutos para reservar una mesa.
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - mesa_id
            properties:
              mesa_id:
                type: integer
              actor_tipo:
                type: integer
                description: 1=Cliente, 2=Recepcionista
              inicio:
                type: string
                format: date-time
              fin_estimado:
                type: string
                format: date-time
              ttl_minutes:
                type: integer
                default: 3
    responses:
      201:
        description: Hold creado
      400:
        description: Validación fallida
      409:
        description: Mesa no disponible
    """
    try:
        # Validar schema
        schema = HoldMesaCreateSchema()
        data = schema.load(request.json)
        
        # Usuario autenticado
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario')
        
        # Crear hold
        result = HoldMesaService.crear_hold(
            usuario_id=usuario_id,
            mesa_id=data['mesa_id'],
            actor_tipo=data['actor_tipo'],
            inicio=data['inicio'],
            fin_estimado=data['fin_estimado'],
            ttl_minutes=data.get('ttl_minutes', 5),
            notas=data.get('notas')
        )
        
        if not result['success']:
            # Mesa no disponible u otro error
            return jsonify({"error": result['error']}), 409 if 'disponible' in result['error'] else 400
        
        return jsonify({
            "message": "Hold creado exitosamente",
            "hold": result['data']
        }), 201
        
    except ValidationError as e:
        logger.error(f"Error de validación en crear_hold: {e.messages}")
        return jsonify({"error": "Datos inválidos", "detalles": e.messages}), 400
    except Exception as e:
        logger.error(f"Error en crear_hold: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@hold_mesa_bp.route('/<int:hold_id>', methods=['GET'])
@jwt_required()
def obtener_hold(hold_id):
    """
    Obtener detalles de un hold
    ---
    tags:
      - Holds
    summary: Obtener hold por ID
    description: Retrieves detailed information about a specific hold including mesa details and remaining TTL.
    parameters:
      - in: path
        name: hold_id
        type: integer
        required: true
        description: ID del hold
    responses:
      200:
        description: Hold encontrado
        schema:
          type: object
          properties:
            id_hold_mesa:
              type: integer
            mesa_id:
              type: integer
            estatus:
              type: integer
              description: "1=Activo, 2=Cancelado, 3=Expirado"
            actor_usuario_id:
              type: integer
            inicio:
              type: string
              format: date-time
            fin_estimado:
              type: string
              format: date-time
            fechahora_expiracion:
              type: string
              format: date-time
      404:
        description: Hold no existe
      500:
        description: Error interno
    """
    try:
        result = HoldMesaService.obtener_hold(hold_id)
        
        if not result['success']:
            return jsonify({"error": result['error']}), 404
        
        return jsonify(result['data']), 200
        
    except Exception as e:
        logger.error(f"Error en obtener_hold: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@hold_mesa_bp.route('/', methods=['GET'])
@jwt_required()
def listar_holds_activos():
    """
    Listar holds activos (no expirados)
    ---
    tags:
      - Holds
    summary: Listar holds activos
    description: Lista todos los holds activos. Opcionalmente filtrar por mesa_id. Excluye holds expirados y cancelados.
    parameters:
      - in: query
        name: mesa_id
        type: integer
        required: false
        description: Filtrar por mesa (opcional)
    responses:
      200:
        description: Lista de holds activos
        schema:
          type: object
          properties:
            holds:
              type: array
              items:
                type: object
                properties:
                  id_hold_mesa:
                    type: integer
                  mesa_id:
                    type: integer
                  estatus:
                    type: integer
                  actor_usuario_id:
                    type: integer
                  inicio:
                    type: string
                    format: date-time
                  fin_estimado:
                    type: string
                    format: date-time
                  fechahora_expiracion:
                    type: string
                    format: date-time
            total:
              type: integer
      400:
        description: Error al listar holds
      500:
        description: Error interno
    """
    try:
        mesa_id = request.args.get('mesa_id', type=int)
        
        result = HoldMesaService.listar_holds_activos(mesa_id)
        
        if not result['success']:
            return jsonify({"error": result['error']}), 400
        
        return jsonify({
            "holds": result['data'],
            "total": len(result['data'])
        }), 200
        
    except Exception as e:
        logger.error(f"Error en listar_holds_activos: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@hold_mesa_bp.route('/<int:hold_id>/cancelar', methods=['POST'])
@jwt_required()
def cancelar_hold(hold_id):
    """
    Cancelar hold activo
    ---
    tags:
      - Holds
    summary: Cancelar hold
    description: Cancela un hold activo. Solo el usuario que creó el hold puede cancelarlo (o admin/recepcionista).
    parameters:
      - in: path
        name: hold_id
        type: integer
        required: true
        description: ID del hold a cancelar
    requestBody:
      required: false
      content:
        application/json:
          schema:
            type: object
            properties:
              motivo:
                type: string
                description: Razón de la cancelación (opcional)
    responses:
      200:
        description: Hold cancelado exitosamente
        schema:
          type: object
          properties:
            message:
              type: string
            hold:
              type: object
              properties:
                id_hold_mesa:
                  type: integer
                estatus:
                  type: integer
                  description: "Será 2 (Cancelado)"
      403:
        description: Sin permisos para cancelar este hold
      404:
        description: Hold no existe
      400:
        description: Hold no está activo o datos inválidos
      500:
        description: Error interno
    """
    try:
        # Validar schema (motivo opcional)
        schema = HoldMesaCancelarSchema()
        data = schema.load(request.json or {})
        
        # Usuario autenticado
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario')
        
        # Cancelar
        result = HoldMesaService.cancelar_hold(usuario_id, hold_id)
        
        if not result['success']:
            # Determinar código según error
            if 'no existe' in result['error']:
                return jsonify({"error": result['error']}), 404
            elif 'no está activo' in result['error']:
                return jsonify({"error": result['error']}), 400
            else:
                return jsonify({"error": result['error']}), 403
        
        return jsonify({
            "message": "Hold cancelado exitosamente",
            "hold": result['data']
        }), 200
        
    except ValidationError as e:
        logger.error(f"Error de validación en cancelar_hold: {e.messages}")
        return jsonify({"error": "Datos inválidos", "detalles": e.messages}), 400
    except Exception as e:
        logger.error(f"Error en cancelar_hold: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@hold_mesa_bp.route('/disponibilidad', methods=['POST'])
@jwt_required()
def verificar_disponibilidad():
    """
    Verificar disponibilidad de mesa en rango de fechas
    ---
    tags:
      - Holds
    summary: Verificar disponibilidad de mesa
    description: Verifica si una mesa está disponible para reservar en un rango de fechas específico. Útil para mostrar disponibilidad antes de crear hold. Excluye holds y reservas activas en ese período.
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - mesa_id
              - inicio
              - fin_estimado
            properties:
              mesa_id:
                type: integer
                description: ID de la mesa
              inicio:
                type: string
                format: date-time
                example: "2025-11-15T19:00:00"
              fin_estimado:
                type: string
                format: date-time
                example: "2025-11-15T21:00:00"
    responses:
      200:
        description: Verificación completada
        schema:
          type: object
          properties:
            disponible:
              type: boolean
              description: "true si la mesa está disponible en ese período"
            mensaje:
              type: string
              description: "Descripción del resultado (disponible o razón por la que no)"
      400:
        description: Datos inválidos o mesa no existe
        schema:
          type: object
          properties:
            error:
              type: string
              description: Mensaje de error (ej, "Mesa 5 no existe", "Formato de fecha inválido")
      500:
        description: Error interno
    """
    try:
        data = request.json
        
        # Validar campos requeridos
        if not all(k in data for k in ['mesa_id', 'inicio', 'fin_estimado']):
            return jsonify({"error": "Faltan campos requeridos: mesa_id, inicio, fin_estimado"}), 400
        
        # Parsear fechas
        inicio = datetime.fromisoformat(data['inicio'].replace('Z', '+00:00'))
        fin_estimado = datetime.fromisoformat(data['fin_estimado'].replace('Z', '+00:00'))
        
        # Verificar
        result = HoldMesaService.verificar_disponibilidad_mesa(
            data['mesa_id'],
            inicio,
            fin_estimado
        )
        
        if not result['success']:
            return jsonify({"error": result['error']}), 400
        
        return jsonify({
            "disponible": result['disponible'],
            "mensaje": result['mensaje']
        }), 200
        
    except ValueError as e:
        return jsonify({"error": f"Formato de fecha inválido: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Error en verificar_disponibilidad: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500
