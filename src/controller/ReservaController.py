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
    Crear reserva confirmada (preferentemente desde hold).
    ---
    tags:
      - Reservas
    summary: "Paso 1: Crear Reserva"
    description: Crea una nueva reserva confirmada. Es recomendable que venga desde un Hold previo confirmado, pero también se puede crear directamente. Si viene de un Hold, se valida que esté activo y no haya expirado. El Hold se marca como confirmado automáticamente.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - inicio
            - fin_estimado
          properties:
            cliente_id:
              type: integer
              description: "ID del cliente que hace la reserva (opcional)"
            recepcionista_id:
              type: integer
              description: "ID del recepcionista si es una reserva creada por recepción (opcional)"
            inicio:
              type: string
              format: date-time
              description: "Fecha y hora de inicio de la reserva (ISO 8601). Ej: 2025-11-18T19:00:00"
            fin_estimado:
              type: string
              format: date-time
              description: "Fecha y hora estimada de fin (ISO 8601). Ej: 2025-11-18T20:30:00"
            tolerancia_min:
              type: integer
              description: "Minutos de tolerancia antes de marcar como NoShow (default: 15, rango: 0-120)"
            notas:
              type: string
              description: "Notas adicionales sobre la reserva. Ej: 'Mesa cerca de la ventana, cumpleaños' (opcional)"
            hold_id:
              type: integer
              description: "ID del Hold confirmado previamente (opcional pero recomendado). Si se envía, se valida que el Hold esté activo y no haya expirado"
        example:
          cliente_id: 1
          recepcionista_id: 2
          inicio: "2025-11-18T19:00:00"
          fin_estimado: "2025-11-18T20:30:00"
          tolerancia_min: 15
          notas: "Mesa cerca de la ventana"
          hold_id: 5
    responses:
      201:
        description: "Reserva creada exitosamente"
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Reserva creada exitosamente"
            reserva:
              type: object
              properties:
                id_reserva:
                  type: integer
                  example: 10
                cliente_id:
                  type: integer
                  example: 1
                recepcionista_id:
                  type: integer
                  example: 2
                inicio:
                  type: string
                  format: date-time
                  example: "2025-11-18T19:00:00"
                fin_estimado:
                  type: string
                  format: date-time
                  example: "2025-11-18T20:30:00"
                estatus:
                  type: integer
                  example: 1
                  description: "1=Programada, 2=EnCurso, 3=Completada, 4=NoShow, 5=Cancelada"
                tolerancia_min:
                  type: integer
                  example: 15
                notas:
                  type: string
                  example: "Mesa cerca de la ventana"
                hold_id:
                  type: integer
                  example: 5
                estatus_display:
                  type: string
                  example: "Programada"
                puede_iniciar:
                  type: boolean
                  example: false
                created_at:
                  type: string
                  format: date-time
      400:
        description: "Error de validación o datos inválidos"
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Datos inválidos"
            detalles:
              type: object
              example: {"fin_estimado": ["fin_estimado debe ser posterior a inicio"]}
      404:
        description: "Hold no existe"
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Hold 5 no existe"
      409:
        description: "Hold expirado o no está activo"
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Hold 5 ya expiró"
      500:
        description: "Error interno del servidor"
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Error al crear reserva: ..."
    x-code-samples:
      - lang: curl
        source: |
          curl -X POST http://localhost:5000/api/reservas/ \\
            -H "Content-Type: application/json" \\
            -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
            -d '{
              "cliente_id": 1,
              "recepcionista_id": 2,
              "inicio": "2025-11-18T19:00:00",
              "fin_estimado": "2025-11-18T20:30:00",
              "tolerancia_min": 15,
              "notas": "Mesa cerca de la ventana",
              "hold_id": 5
            }'
    """
    try:
        # Validar schema
        schema = ReservaCreateSchema()
        data = schema.load(request.json)
        
        # Usuario autenticado
        current_user = get_jwt_identity()
        
        # Crear reserva
        result = ReservaService.crear_reserva(
            usuario_id=current_user,
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
    Obtener detalles de una reserva por ID.
    ---
    tags:
      - Reservas
    summary: "Paso 2: Obtener Reserva"
    description: Obtiene la información completa de una reserva específica incluyendo cliente, mesa, estado actual y notas. Útil para verificar el estado antes de iniciar o completar una reserva.
    parameters:
      - in: path
        name: reserva_id
        type: integer
        required: true
        description: "ID de la reserva a consultar. Ej: 10"
    responses:
      200:
        description: "Reserva encontrada exitosamente"
        schema:
          type: object
          properties:
            id_reserva:
              type: integer
              example: 10
            cliente_id:
              type: integer
              example: 1
            recepcionista_id:
              type: integer
              example: 2
            inicio:
              type: string
              format: date-time
              example: "2025-11-18T19:00:00"
            fin_estimado:
              type: string
              format: date-time
              example: "2025-11-18T20:30:00"
            estatus:
              type: integer
              example: 1
              description: "1=Programada, 2=EnCurso, 3=Completada, 4=NoShow, 5=Cancelada"
            estatus_display:
              type: string
              example: "Programada"
            tolerancia_min:
              type: integer
              example: 15
            notas:
              type: string
              example: "Mesa cerca de la ventana"
            hold_id:
              type: integer
              example: 5
            puede_iniciar:
              type: boolean
              example: false
              description: "Indica si está dentro de la ventana de tiempo permitida para iniciar"
            created_at:
              type: string
              format: date-time
              example: "2025-11-18T14:30:00"
            updated_at:
              type: string
              format: date-time
              example: null
      404:
        description: "Reserva no existe"
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Reserva 10 no existe"
      500:
        description: "Error interno del servidor"
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Error al obtener reserva: ..."
    x-code-samples:
      - lang: curl
        source: |
          curl -X GET http://localhost:5000/api/reservas/10 \\
            -H "Authorization: Bearer YOUR_JWT_TOKEN"
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
    Listar todas las reservas con filtros opcionales.
    ---
    tags:
      - Reservas
    summary: "Paso 2B: Listar Reservas (con filtros)"
    description: Lista todas las reservas con posibilidad de filtrar por sucursal, cliente, estado y rango de fechas. Solo retorna reservas de la sucursal del usuario autenticado (multi-tenant). Útil para tableros y reportes.
    parameters:
      - in: query
        name: sucursal_id
        type: integer
        required: false
        description: "Filtrar por ID de sucursal (opcional). Ej: ?sucursal_id=1"
      - in: query
        name: cliente_id
        type: integer
        required: false
        description: "Filtrar por ID de cliente (opcional). Ej: ?cliente_id=1"
      - in: query
        name: estatus
        type: integer
        required: false
        description: "Filtrar por estatus (opcional). 1=Programada, 2=EnCurso, 3=Completada, 4=NoShow, 5=Cancelada. Ej: ?estatus=1"
      - in: query
        name: fecha_desde
        type: string
        format: 2025-11-19 14:00:00
        required: false
        description: "Reservas desde esta fecha (ISO 8601, opcional). Ej: ?fecha_desde=2025-11-18T00:00:00"
      - in: query
        name: fecha_hasta
        type: string
        format: 2025-11-19 14:00:00
        required: false
        description: "Reservas hasta esta fecha (ISO 8601, opcional). Ej: ?fecha_hasta=2025-11-18T23:59:59"
    responses:
      200:
        description: "Lista de reservas obtenida exitosamente"
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
                    example: 10
                  cliente_id:
                    type: integer
                    example: 1
                  recepcionista_id:
                    type: integer
                    example: 2
                  inicio:
                    type: string
                    format: date-time
                    example: "2025-11-18T19:00:00"
                  fin_estimado:
                    type: string
                    format: date-time
                    example: "2025-11-18T20:30:00"
                  estatus:
                    type: integer
                    example: 1
                  estatus_display:
                    type: string
                    example: "Programada"
                  tolerancia_min:
                    type: integer
                    example: 15
                  notas:
                    type: string
                    example: "Mesa cerca de la ventana"
                  hold_id:
                    type: integer
                    example: 5
                  puede_iniciar:
                    type: boolean
                    example: false
                  created_at:
                    type: string
                    format: date-time
                    example: "2025-11-18T14:30:00"
            total:
              type: integer
              example: 2
              description: "Cantidad total de reservas que coinciden con los filtros"
      400:
        description: "Parámetros inválidos"
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Parámetros inválidos"
            detalles:
              type: object
      500:
        description: "Error interno del servidor"
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Error al listar reservas: ..."
    x-code-samples:
      - lang: curl
        source: |
          # Listar todas las reservas
          curl -X GET http://localhost:5000/api/reservas/ \\
            -H "Authorization: Bearer YOUR_JWT_TOKEN"

          # Listar reservas de la sucursal 1
          curl -X GET "http://localhost:5000/api/reservas/?sucursal_id=1" \\
            -H "Authorization: Bearer YOUR_JWT_TOKEN"

          # Listar reservas programadas del cliente 1 en sucursal 1
          curl -X GET "http://localhost:5000/api/reservas/?sucursal_id=1&cliente_id=1&estatus=1" \\
            -H "Authorization: Bearer YOUR_JWT_TOKEN"

          # Listar reservas de una fecha específica en sucursal 1
          curl -X GET "http://localhost:5000/api/reservas/?sucursal_id=1&fecha_desde=2025-11-18T00:00:00&fecha_hasta=2025-11-18T23:59:59" \\
            -H "Authorization: Bearer YOUR_JWT_TOKEN"
    """
    try:
        # Parsear query params
        schema = ReservaListarQuerySchema()
        filters = schema.load(request.args)
        
        # Usuario autenticado
        current_user = get_jwt_identity()
        
        # Listar
        result = ReservaService.listar_reservas(
            usuario_id=current_user,
            sucursal_id=filters.get('sucursal_id'),
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


@reserva_bp.route('/mesero/<int:usuario_id>', methods=['GET'])
@jwt_required()
def listar_reservas_por_mesero(usuario_id):
    """
    Listar reservas asignadas a un mesero, ordenadas por estatus.
    ---
    tags:
      - Reservas
    summary: "Listar Reservas por Mesero"
    description: Retorna todas las reservas asignadas a un mesero específico (a través de AsignacionMesa de la mesa). Las reservas se ordenan por estatus (de menor a mayor). Útil para que el mesero vea sus reservas pendientes.
    parameters:
      - in: path
        name: usuario_id
        type: integer
        required: true
        description: "ID del mesero (usuario). Ej: 5"
    responses:
      200:
        description: "Lista de reservas del mesero obtenida exitosamente"
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
                    example: 10
                  cliente_id:
                    type: integer
                    example: 1
                  inicio:
                    type: string
                    format: date-time
                    example: "2025-11-19 19:00:00"
                  fin_estimado:
                    type: string
                    format: date-time
                    example: "2025-11-19 20:30:00"
                  estatus:
                    type: integer
                    example: 1
                    description: "1=Programada, 2=EnCurso, 3=Completada, 4=NoShow, 5=Cancelada"
                  estatus_display:
                    type: string
                    example: "Programada"
                  tolerancia_min:
                    type: integer
                    example: 15
                  notas:
                    type: string
                    example: "Mesa cerca de la ventana"
                  puede_iniciar:
                    type: boolean
                    example: true
                  created_at:
                    type: string
                    format: date-time
            total:
              type: integer
              example: 3
              description: "Cantidad total de reservas del mesero"
      404:
        description: "Mesero no existe o no tiene reservas asignadas"
        schema:
          type: object
          properties:
            reservas:
              type: array
              example: []
            total:
              type: integer
              example: 0
      500:
        description: "Error interno del servidor"
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Error al listar reservas del mesero: ..."
    x-code-samples:
      - lang: curl
        source: |
          curl -X GET http://localhost:5000/api/reservas/mesero/5 \\
            -H "Authorization: Bearer YOUR_JWT_TOKEN"
    """
    try:
        # Usuario autenticado
        current_user = get_jwt_identity()
        
        # Listar
        result = ReservaService.listar_reservas_por_mesero(usuario_id)
        
        if not result['success']:
            return jsonify({"error": result['error']}), 500
        
        return jsonify({
            "reservas": result['data'],
            "total": len(result['data'])
        }), 200
        
    except Exception as e:
        logger.error(f"Error en listar_reservas_por_mesero: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500



@reserva_bp.route('/<int:reserva_id>/iniciar', methods=['POST'])
@jwt_required()
def iniciar_reserva(reserva_id):
    """
    Iniciar reserva (cliente llegó a la mesa).
    ---
    tags:
      - Reservas
    summary: "Paso 3: Iniciar Reserva"
    description: Marca la reserva como iniciada cuando el cliente llega a su mesa. Cambia el estado a 2 (EnCurso). Valida que la reserva esté programada y que esté dentro de la ventana de tiempo permitida (inicio - tolerancia_min <= ahora).
    parameters:
      - in: path
        name: reserva_id
        type: integer
        required: true
        description: "ID de la reserva a iniciar. Ej: 10"
    responses:
      200:
        description: "Reserva iniciada exitosamente"
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Reserva iniciada exitosamente"
            reserva:
              type: object
              properties:
                id_reserva:
                  type: integer
                  example: 10
                cliente_id:
                  type: integer
                  example: 1
                recepcionista_id:
                  type: integer
                  example: 2
                inicio:
                  type: string
                  format: date-time
                  example: "2025-11-18T19:00:00"
                fin_estimado:
                  type: string
                  format: date-time
                  example: "2025-11-18T20:30:00"
                estatus:
                  type: integer
                  example: 2
                  description: "Será 2 (EnCurso)"
                estatus_display:
                  type: string
                  example: "En Curso"
                tolerancia_min:
                  type: integer
                  example: 15
                notas:
                  type: string
                  example: "Mesa cerca de la ventana"
                hold_id:
                  type: integer
                  example: 5
                puede_iniciar:
                  type: boolean
                  example: false
                updated_at:
                  type: string
                  format: date-time
                  example: "2025-11-18T18:47:00"
      400:
        description: "Reserva no puede iniciarse"
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Aún no es hora de iniciar. La reserva es a las 19:00, puedes llegar desde 18:45"
      404:
        description: "Reserva no existe"
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Reserva 10 no existe"
      500:
        description: "Error interno del servidor"
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Error al iniciar reserva: ..."
    x-validation-notes: |
      VALIDACIONES INTERNAS:
      1. Reserva debe existir (404 si no)
      2. Reserva debe estar en estado Programada (estatus=1)
      3. Hora actual debe ser >= (inicio - tolerancia_min)
      
      EJEMPLO:
      - Reserva a las 19:00 con tolerancia de 15 min
      - Puede iniciarse desde las 18:45 en adelante
    x-code-samples:
      - lang: curl
        source: |
          curl -X POST http://localhost:5000/api/reservas/10/iniciar \\
            -H "Content-Type: application/json" \\
            -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
            -d '{}'
    """
    try:
        # Usuario autenticado
        current_user = get_jwt_identity()
        
        # Iniciar
        result = ReservaService.iniciar_reserva(current_user, reserva_id)
        
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
    Completar reserva (cliente terminó su comida y se va).
    ---
    tags:
      - Reservas
    summary: "Paso 4: Completar Reserva"
    description: Marca la reserva como completada cuando el cliente termina su comida y se va. Cambia el estado a 3 (Completada). Este es el paso previo a crear el Pedido y Pago. Valida que la reserva esté en estado EnCurso (2).
    parameters:
      - in: path
        name: reserva_id
        type: integer
        required: true
        description: "ID de la reserva a completar. Ej: 10"
    responses:
      200:
        description: "Reserva completada exitosamente"
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Reserva completada exitosamente"
            reserva:
              type: object
              properties:
                id_reserva:
                  type: integer
                  example: 10
                cliente_id:
                  type: integer
                  example: 1
                recepcionista_id:
                  type: integer
                  example: 2
                inicio:
                  type: string
                  format: date-time
                  example: "2025-11-18T19:00:00"
                fin_estimado:
                  type: string
                  format: date-time
                  example: "2025-11-18T20:30:00"
                estatus:
                  type: integer
                  example: 3
                  description: "Será 3 (Completada)"
                estatus_display:
                  type: string
                  example: "Completada"
                tolerancia_min:
                  type: integer
                  example: 15
                notas:
                  type: string
                  example: "Mesa cerca de la ventana"
                hold_id:
                  type: integer
                  example: 5
                puede_iniciar:
                  type: boolean
                  example: false
                updated_at:
                  type: string
                  format: date-time
                  example: "2025-11-18T20:25:00"
      400:
        description: "Reserva no puede completarse"
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Reserva 10 no está en curso (estatus=1)"
      404:
        description: "Reserva no existe"
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Reserva 10 no existe"
      500:
        description: "Error interno del servidor"
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Error al completar reserva: ..."
    x-validation-notes: |
      VALIDACIONES INTERNAS:
      1. Reserva debe existir (404 si no)
      2. Reserva debe estar en estado EnCurso (estatus=2)
      3. Solo se puede completar cuando el cliente termina su comida
      
      SIGUIENTE PASO:
      Después de completar la reserva, puedes proceder a:
      - Crear Pedido: POST /api/pedidos/
      - Crear Pago: POST /api/pagos/
    x-code-samples:
      - lang: curl
        source: |
          curl -X POST http://localhost:5000/api/reservas/10/completar \\
            -H "Content-Type: application/json" \\
            -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
            -d '{}'
    """
    try:
        # Usuario autenticado
        current_user = get_jwt_identity()
        
        # Completar
        result = ReservaService.completar_reserva(current_user, reserva_id)
        
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
    Cancelar una reserva activa.
    ---
    tags:
      - Reservas
    summary: "Paso 4B: Cancelar Reserva"
    description: Cancela una reserva que aún está activa. Cambia el estado a 5 (Cancelada). Solo se puede cancelar si está en estado Programada (1) o EnCurso (2). No se pueden cancelar reservas ya completadas, NoShow o canceladas. Se puede proporcionar un motivo de la cancelación.
    parameters:
      - in: path
        name: reserva_id
        type: integer
        required: true
        description: "ID de la reserva a cancelar. Ej: 10"
      - in: body
        name: body
        required: false
        schema:
          type: object
          properties:
            motivo:
              type: string
              description: "Razón de la cancelación (opcional). Ej: 'Cliente pidió cancelación por cambio de planes'"
        example:
          motivo: "Cliente pidió cancelación por cambio de planes"
    responses:
      200:
        description: "Reserva cancelada exitosamente"
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Reserva cancelada exitosamente"
            reserva:
              type: object
              properties:
                id_reserva:
                  type: integer
                  example: 10
                cliente_id:
                  type: integer
                  example: 1
                recepcionista_id:
                  type: integer
                  example: 2
                inicio:
                  type: string
                  format: date-time
                  example: "2025-11-18T19:00:00"
                fin_estimado:
                  type: string
                  format: date-time
                  example: "2025-11-18T20:30:00"
                estatus:
                  type: integer
                  example: 5
                  description: "Será 5 (Cancelada)"
                estatus_display:
                  type: string
                  example: "Cancelada"
                tolerancia_min:
                  type: integer
                  example: 15
                notas:
                  type: string
                  example: "Mesa cerca de la ventana"
                hold_id:
                  type: integer
                  example: 5
                puede_iniciar:
                  type: boolean
                  example: false
                updated_at:
                  type: string
                  format: date-time
                  example: "2025-11-18T18:50:00"
      400:
        description: "Reserva no puede cancelarse o datos inválidos"
        schema:
          type: object
          properties:
            error:
              type: string
              example: "No se puede cancelar. Reserva en estatus 3"
      404:
        description: "Reserva no existe"
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Reserva 10 no existe"
      500:
        description: "Error interno del servidor"
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Error al cancelar reserva: ..."
    x-validation-notes: |
      VALIDACIONES INTERNAS:
      1. Reserva debe existir (404 si no)
      2. Reserva debe estar en estado Programada (1) o EnCurso (2)
      3. No se puede cancelar: Completada (3), NoShow (4) o Cancelada (5)
      
      ESTADOS EN LOS QUE SE PUEDE CANCELAR:
      - Estado 1 (Programada): Cliente cancela antes de llegar
      - Estado 2 (EnCurso): Cliente cancela después de haber llegado pero antes de terminar
      
      MOTIVO:
      - Opcional pero recomendado para auditoría
      - Máx 255 caracteres
    x-code-samples:
      - lang: curl
        source: |
          curl -X POST http://localhost:5000/api/reservas/10/cancelar \\
            -H "Content-Type: application/json" \\
            -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
            -d '{
              "motivo": "Cliente pidió cancelación por cambio de planes"
            }'
    """
    try:
        # Validar schema
        schema = ReservaCancelarSchema()
        data = schema.load(request.json or {})
        
        # Usuario autenticado
        current_user = get_jwt_identity()
        
        # Cancelar
        result = ReservaService.cancelar_reserva(
            current_user,
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
    Marcar reserva como NoShow (cliente no llegó).
    ---
    tags:
      - Reservas
    summary: "Paso 4C: Marcar como NoShow"
    description: Marca una reserva como NoShow cuando el cliente no llega dentro de la ventana de tolerancia. Cambia el estado a 4 (NoShow). Solo recepcionistas y administradores pueden realizar esta acción. Se usa típicamente cuando el cliente no se presenta después del tiempo de tolerancia transcurrido.
    parameters:
      - in: path
        name: reserva_id
        type: integer
        required: true
        description: "ID de la reserva a marcar como NoShow. Ej: 10"
    responses:
      200:
        description: "Reserva marcada como NoShow exitosamente"
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Reserva marcada como NoShow"
            reserva:
              type: object
              properties:
                id_reserva:
                  type: integer
                  example: 10
                cliente_id:
                  type: integer
                  example: 1
                recepcionista_id:
                  type: integer
                  example: 2
                inicio:
                  type: string
                  format: date-time
                  example: "2025-11-18T19:00:00"
                fin_estimado:
                  type: string
                  format: date-time
                  example: "2025-11-18T20:30:00"
                estatus:
                  type: integer
                  example: 4
                  description: "Será 4 (NoShow)"
                estatus_display:
                  type: string
                  example: "No Show"
                tolerancia_min:
                  type: integer
                  example: 15
                notas:
                  type: string
                  example: "Mesa cerca de la ventana"
                hold_id:
                  type: integer
                  example: 5
                puede_iniciar:
                  type: boolean
                  example: false
                updated_at:
                  type: string
                  format: date-time
                  example: "2025-11-18T20:45:00"
      400:
        description: "Reserva no puede marcarse como NoShow"
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Solo se puede marcar NoShow si está programada (estatus=1)"
      403:
        description: "Sin permisos suficientes"
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Sin permisos para marcar como NoShow (requiere recepcionista/admin)"
      404:
        description: "Reserva no existe"
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Reserva 10 no existe"
      500:
        description: "Error interno del servidor"
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Error al marcar NoShow: ..."
    x-validation-notes: |
      VALIDACIONES INTERNAS:
      1. Reserva debe existir (404 si no)
      2. Reserva debe estar en estado Programada (estatus=1)
      3. Solo roles: recepcionista/admin (403 si no tiene permisos)
      
      CUÁNDO USAR:
      - Cuando ha pasado el tiempo de tolerancia desde la hora de inicio
      - Cuando el cliente no llegó a la mesa
      - Típicamente: inicio + tolerancia_min <= ahora
    x-code-samples:
      - lang: curl
        source: |
          curl -X POST http://localhost:5000/api/reservas/10/no-show \\
            -H "Content-Type: application/json" \\
            -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
            -d '{}'
    """
    try:
        # Usuario autenticado
        current_user = get_jwt_identity()    
        
        # Marcar
        result = ReservaService.marcar_no_show(current_user, reserva_id)
        
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
