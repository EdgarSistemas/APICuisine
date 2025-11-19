"""
HoldMesaController - Endpoints REST para HoldMesa
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from src.services.operaciones.hold_mesa_service import HoldMesaService
from src.dao.operaciones.hold_mesa_dao import HoldMesaDAO
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
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
            type: object
            properties:
              mesa_id:
                type: integer
                description: ID de la mesa a bloquear (requerido)
              actor_tipo:
                type: integer
                description: Tipo de actor que crea el hold - 1=Cliente, 2=Recepcionista
              horas:
                type: integer
                description: Numero de horas a apartar la mesa
              inicio:
                type: string
                format: 'yyyy-mm-dd hh:mm:ss'
                pattern: '^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'
                description: Fecha y hora estimada de fin del hold (formato yyyy-mm-dd hh:mm:ss)
                example: "2025-11-18 00:16:58"
              ttl_minutes:
                type: integer
                default: 3
                description: Minutos que durará el hold antes de expirar automáticamente (por defecto 3)
              notas:
                type: string
                description: Notas o comentarios adicionales sobre el hold (opcional)
    responses:
      201:
        description: Hold creado exitosamente
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Hold creado exitosamente"
            hold:
              type: object
              properties:
                id_hold_mesa:
                  type: integer
                  description: ID único del hold creado
                mesa_id:
                  type: integer
                  description: ID de la mesa
                estatus:
                  type: integer
                  description: "1=Activo, 2=Cancelado, 3=Expirado"
                actor_usuario_id:
                  type: integer
                  description: ID del usuario que creó el hold
                inicio:
                  type: string
                  format: date-time
                fin_estimado:
                  type: string
                  format: date-time
                fechahora_expiracion:
                  type: string
                  format: date-time
                  description: Fecha exacta en que expirará el hold
      400:
        description: Validación fallida o datos inválidos
        schema:
          type: object
          properties:
            error:
              type: string
            detalles:
              type: object
              description: Detalles de errores de validación
      409:
        description: Mesa no disponible en ese período
    """
    try:
        # Validar schema
        schema = HoldMesaCreateSchema()
        data = schema.load(request.json)
        
        # Usuario autenticado
        current_user = get_jwt_identity()
        
        # Crear hold
        result = HoldMesaService.crear_hold(
            usuario_id=current_user,
            mesa_id=data['mesa_id'],
            actor_tipo=data['actor_tipo'],
            inicio=data['inicio'],
            horas=data['horas'],
            ttl_minutes=data.get('ttl_minutes', 3),
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
      - in: body
        name: body
        required: false
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
              example: "Hold cancelado exitosamente"
            hold:
              type: object
              properties:
                id_hold_mesa:
                  type: integer
                  description: ID del hold cancelado
                mesa_id:
                  type: integer
                  description: ID de la mesa
                estatus:
                  type: integer
                  description: "2=Cancelado"
                actor_usuario_id:
                  type: integer
                  description: ID del usuario que creó el hold
                inicio:
                  type: string
                  format: date-time
                fin_estimado:
                  type: string
                  format: date-time
                fechahora_expiracion:
                  type: string
                  format: date-time
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
        # Obtener body - request.get_json() maneja mejor el Content-Type
        data = request.get_json(force=True, silent=True) or {}
        
        # Validar schema (motivo opcional)
        schema = HoldMesaCancelarSchema()
        data = schema.load(data)
        
        # Usuario autenticado
        current_user = get_jwt_identity()
        
        # Cancelar a través del service
        result = HoldMesaService.cancelar_hold(current_user, hold_id)
        
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
        logger.error(f"Error en cancelar_hold: {str(e)}", exc_info=True)
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@hold_mesa_bp.route('/<int:hold_id>/confirmar', methods=['POST'])
@jwt_required()
def confirmar_hold_endpoint(hold_id):
    """
    Confirmar hold y validar TTL
    ---
    tags:
      - Holds
    summary: Confirmar hold (cambiar a completo)
    description: |
      Confirma un hold (cambiar estatus de 1→2 "Completo").
      
      VALIDACIONES:
      1. Hold existe
      2. Hold está activo (estatus=1)
      3. Hold no ha expirado (expires_at > now)
      4. Hay tiempo restante en el TTL
      
      Una vez confirmado (estatus=2), el job de expiración lo IGNORA.
      El hold está "seguro" y listo para crear reserva.
    parameters:
      - in: path
        name: hold_id
        type: integer
        required: true
        description: ID del hold a confirmar
    responses:
      200:
        description: Hold confirmado exitosamente
        schema:
          type: object
          properties:
            message:
              type: string
            hold:
              type: object
              description: Hold actualizado con estatus=2
            tiempo_restante_min:
              type: number
              format: float
              description: Minutos restantes del TTL
      404:
        description: Hold no existe
      410:
        description: Hold expirado o no activo (no se puede confirmar)
      500:
        description: Error interno
    """
    try:
        import pytz
        
        TZ_MEXICO = pytz.timezone('America/Mexico_City')
        
        # Obtener hold
        hold = HoldMesaDAO.obtener_hold_por_id(hold_id)
        if not hold:
            print(f"[CONFIRMAR_HOLD] ✗ Hold {hold_id} no existe")
            return jsonify({"error": f"Hold {hold_id} no existe"}), 404
        
        # Validación 1: Hold debe estar activo (estatus=1)
        if hold['estatus'] != 1:
            print(f"[CONFIRMAR_HOLD] ✗ Hold {hold_id} no está activo (estatus={hold['estatus']})")
            return jsonify({
                "error": f"Hold no está activo (estatus={hold['estatus']})"
            }), 410
        
        # Validación 2: Hold no debe estar expirado
        ahora = datetime.now(TZ_MEXICO).replace(tzinfo=None)
        
        # holds_expires_at viene del DAO como datetime, puede tener tzinfo
        holds_expires_at = hold.get('expires_at')
        if holds_expires_at is None:
            print(f"[CONFIRMAR_HOLD] ✗ Hold {hold_id} no tiene expires_at")
            return jsonify({
                "error": "Hold no tiene fecha de expiración configurada"
            }), 410
        
        # Asegurar que expires_at es datetime sin timezone
        if isinstance(holds_expires_at, str):
            try:
                holds_expires_at = datetime.fromisoformat(holds_expires_at.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                holds_expires_at = datetime.fromisoformat(holds_expires_at)
        
        # Remover timezone si existe
        if hasattr(holds_expires_at, 'tzinfo') and holds_expires_at.tzinfo is not None:
            holds_expires_at = holds_expires_at.replace(tzinfo=None)
        
        # Comparar
        if holds_expires_at <= ahora:
            tiempo_pasado = (ahora - holds_expires_at).total_seconds() / 60
            print(f"[CONFIRMAR_HOLD] ✗ Hold {hold_id} expirado hace {tiempo_pasado:.1f}min")
            return jsonify({
                "error": f"Hold expirado hace {tiempo_pasado:.1f} minutos"
            }), 410
        
        # Validación 3: Calcular tiempo restante
        tiempo_restante = (holds_expires_at - ahora).total_seconds() / 60
        
        if tiempo_restante < 0:
            print(f"[CONFIRMAR_HOLD] ✗ Hold {hold_id} expirado (tiempo negativo)")
            return jsonify({
                "error": f"Hold expirado hace {abs(tiempo_restante):.1f} minutos"
            }), 410
        
        # CONFIRMAR: cambiar estatus a 2 (Completo)
        success = HoldMesaDAO.cambiar_estatus(hold_id, estatus=2)
        
        if not success:
            print(f"[CONFIRMAR_HOLD] ✗ Error al cambiar estatus de hold {hold_id}")
            return jsonify({
                "error": f"Error al confirmar hold {hold_id}"
            }), 500
        
        # Obtener hold actualizado
        hold_confirmado = HoldMesaDAO.obtener_hold_por_id(hold_id)
        
        print(f"[CONFIRMAR_HOLD] ✓ Hold {hold_id} confirmado (estatus 1→2), TTL={tiempo_restante:.1f}min restantes")
        logger.info(f"Hold {hold_id} confirmado con {tiempo_restante:.1f}min restantes")
        
        return jsonify({
            "message": "Hold confirmado. Ahora puedes crear la reserva.",
            "hold": hold_confirmado,
            "tiempo_restante_min": round(tiempo_restante, 2)
        }), 200
        
    except Exception as e:
        logger.error(f"Error en confirmar_hold: {str(e)}", exc_info=True)
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
    description: Verifica si una mesa está disponible para reservar en un rango de fechas específico.
    parameters:
      - in: body
        name: body
        required: true
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
              example: 1
            inicio:
              type: string
              format: date-time
              description: Fecha/hora inicio (ISO format)
              example: "2025-11-18T19:00:00"
            fin_estimado:
              type: string
              format: date-time
              description: Fecha/hora fin estimado (ISO format)
              example: "2025-11-18T21:00:00"
    responses:
      200:
        description: Verificación completada
        schema:
          type: object
          properties:
            disponible:
              type: boolean
            mensaje:
              type: string
      400:
        description: Datos inválidos
      500:
        description: Error interno
    """
    try:
        # Validar que request.json no sea None
        if not request.json:
            return jsonify({"error": "Body JSON es requerido"}), 400
        
        data = request.json
        
        # Validar campos requeridos
        if not all(k in data for k in ['mesa_id', 'inicio', 'fin_estimado']):
            return jsonify({"error": "Faltan campos requeridos: mesa_id, inicio, fin_estimado"}), 400
        
        # Parsear fechas
        try:
            inicio = datetime.fromisoformat(data['inicio'].replace('Z', '+00:00'))
            fin_estimado = datetime.fromisoformat(data['fin_estimado'].replace('Z', '+00:00'))
        except (ValueError, AttributeError) as e:
            return jsonify({"error": f"Formato de fecha inválido: {str(e)}"}), 400
        
        # Verificar disponibilidad a través del service
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
        logger.error(f"Error de validación en verificar_disponibilidad: {str(e)}")
        return jsonify({"error": f"Formato de fecha inválido: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Error en verificar_disponibilidad: {str(e)}", exc_info=True)
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@hold_mesa_bp.route('/admin/limpiar-expirados', methods=['POST'])
@jwt_required()
def limpiar_holds_expirados():
    """
    [ADMIN] Limpiar holds expirados manualmente
    ---
    tags:
      - Holds
      - Admin
    summary: Limpiar holds expirados (manual)
    description: Ejecuta manualmente la expiración de holds. Útil para debugging, testing y limpieza manual sin esperar al scheduler. Solo disponible para admin/recepcionista.
    security:
      - Bearer: []
    responses:
      200:
        description: Limpieza completada
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Se expiraron 3 holds"
            cantidad_expirados:
              type: integer
              example: 3
      500:
        description: Error interno
    """
    try:
        # TODO: Verificar que usuario sea admin/recepcionista
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario')
        
        result = HoldMesaService.limpiar_holds_expirados_manual()
        
        if result['success']:
            logger.info(f"[ADMIN] Usuario {usuario_id} ejecutó limpieza manual de holds: {result['cantidad_expirados']} expirados")
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error en limpiar_holds_expirados: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500
