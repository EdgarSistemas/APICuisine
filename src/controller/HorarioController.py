"""
HorarioController - Endpoints para gestión de horarios (ADMIN)
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.rrhh.horario_service import HorarioService
import logging

logger = logging.getLogger(__name__)

horario_bp = Blueprint('horarios', __name__, url_prefix='/api/horarios')


@horario_bp.route('', methods=['POST'])
@jwt_required()
def crear_horario():
    """
    Crear horario con sus detalles.
    
    Body:
    {
        "sucursal_id": 1,
        "clave": "TURNO_MANANA",
        "nombre": "Turno Matutino",
        "descripcion": "9AM-5PM",
        "detalles": [
            {
                "dia_semana": 1,
                "hora_inicio": "09:00",
                "hora_fin": "17:00",
                "turno_idx": 1,
                "tolerancia_min": 10
            }
        ]
    }
    """
    try:
        current_user = get_jwt_identity()
        user_role = current_user.get('rol') if isinstance(current_user, dict) else None
        
        if user_role not in ['ADMIN', 'GERENTE']:
            return jsonify({
                "success": False,
                "error": "Acceso denegado. Se requiere rol ADMIN o GERENTE"
            }), 403
        
        data = request.get_json()
        resultado = HorarioService.crear_horario(data)
        
        if not resultado['success']:
            return jsonify(resultado), 400
        
        return jsonify(resultado), 201
        
    except Exception as e:
        logger.error(f"Error en crear_horario: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@horario_bp.route('/<int:id_horario>', methods=['GET'])
@jwt_required()
def obtener_horario(id_horario):
    """Obtener horario por ID"""
    try:
        resultado = HorarioService.obtener_horario(id_horario)
        
        if not resultado['success']:
            return jsonify(resultado), 404
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en obtener_horario: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@horario_bp.route('', methods=['GET'])
@jwt_required()
def listar_horarios():
    """
    Listar horarios.
    
    Query params:
    - sucursal_id: int
    - es_activo: bool (default: true)
    - limit: int (default: 100)
    - offset: int (default: 0)
    """
    try:
        sucursal_id = request.args.get('sucursal_id', type=int)
        es_activo = request.args.get('es_activo', 'true').lower() == 'true'
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        resultado = HorarioService.listar_horarios(
            sucursal_id=sucursal_id,
            es_activo=es_activo,
            limit=limit,
            offset=offset
        )
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en listar_horarios: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@horario_bp.route('/<int:id_horario>', methods=['PUT'])
@jwt_required()
def actualizar_horario(id_horario):
    """
    Actualizar información del horario (no los detalles).
    
    Body:
    {
        "clave": "TURNO_MANANA_2",
        "nombre": "Turno Matutino Modificado",
        "descripcion": "Nueva descripción"
    }
    """
    try:
        current_user = get_jwt_identity()
        user_role = current_user.get('rol') if isinstance(current_user, dict) else None
        
        if user_role not in ['ADMIN', 'GERENTE']:
            return jsonify({
                "success": False,
                "error": "Acceso denegado. Se requiere rol ADMIN o GERENTE"
            }), 403
        
        data = request.get_json()
        resultado = HorarioService.actualizar_horario(id_horario, data)
        
        if not resultado['success']:
            return jsonify(resultado), 400
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en actualizar_horario: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@horario_bp.route('/<int:id_horario>', methods=['DELETE'])
@jwt_required()
def desactivar_horario(id_horario):
    """Desactivar horario (soft delete)"""
    try:
        current_user = get_jwt_identity()
        user_role = current_user.get('rol') if isinstance(current_user, dict) else None
        
        if user_role != 'ADMIN':
            return jsonify({
                "success": False,
                "error": "Acceso denegado. Se requiere rol ADMIN"
            }), 403
        
        resultado = HorarioService.desactivar_horario(id_horario)
        
        if not resultado['success']:
            return jsonify(resultado), 400
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en desactivar_horario: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
