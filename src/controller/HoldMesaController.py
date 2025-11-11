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
    POST /api/holds
    
    Crear hold temporal de mesa.
    Cliente o recepcionista puede crear hold durante proceso de reserva.
    
    Body:
    {
        "mesa_id": 5,
        "actor_tipo": 1,  // 1=Cliente, 2=Recepcionista
        "inicio": "2025-11-15T19:00:00",
        "fin_estimado": "2025-11-15T21:00:00",
        "ttl_minutes": 5,  // Opcional, default 5
        "notas": "Mesa para 4 personas"  // Opcional
    }
    
    Returns:
        200: Hold creado con datos y expires_at
        400: Validación fallida
        409: Mesa no disponible
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
    GET /api/holds/{hold_id}
    
    Obtener detalles de un hold.
    
    Returns:
        200: Datos del hold
        404: Hold no existe
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
    GET /api/holds?mesa_id=5
    
    Listar holds activos (no expirados).
    
    Query params:
        - mesa_id (opcional): Filtrar por mesa
    
    Returns:
        200: Lista de holds activos
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
    POST /api/holds/{hold_id}/cancelar
    
    Cancelar hold activo.
    Usuario puede cancelar si es dueño del hold.
    
    Body (opcional):
    {
        "motivo": "Ya no necesito la mesa"
    }
    
    Returns:
        200: Hold cancelado
        403: Sin permisos
        404: Hold no existe
        400: Hold no está activo
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
    POST /api/holds/disponibilidad
    
    Verificar si una mesa está disponible en un rango de fechas.
    Útil antes de crear hold.
    
    Body:
    {
        "mesa_id": 5,
        "inicio": "2025-11-15T19:00:00",
        "fin_estimado": "2025-11-15T21:00:00"
    }
    
    Returns:
        200: {disponible: true/false, mensaje: "..."}
        400: Datos inválidos
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
