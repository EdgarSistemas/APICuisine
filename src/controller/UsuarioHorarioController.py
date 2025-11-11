"""
UsuarioHorarioController - Endpoints para asignación de horarios a empleados
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.rrhh.usuario_horario_service import UsuarioHorarioService
import logging

logger = logging.getLogger(__name__)

usuario_horario_bp = Blueprint('usuario_horarios', __name__, url_prefix='/api/usuario-horarios')


@usuario_horario_bp.route('', methods=['POST'])
@jwt_required()
def asignar_horario():
    """
    Asignar horario a un empleado.
    
    Body:
    {
        "usuario_id": 5,
        "horario_id": 1,
        "fecha_inicio": "2025-01-01",
        "fecha_fin": "2025-12-31"  # Opcional
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
        resultado = UsuarioHorarioService.asignar_horario(data)
        
        if not resultado['success']:
            return jsonify(resultado), 400
        
        return jsonify(resultado), 201
        
    except Exception as e:
        logger.error(f"Error en asignar_horario: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@usuario_horario_bp.route('/usuario/<int:usuario_id>/activo', methods=['GET'])
@jwt_required()
def obtener_horario_activo(usuario_id):
    """
    Obtener horario activo del empleado.
    El empleado solo puede ver su propio horario.
    """
    try:
        current_user = get_jwt_identity()
        user_id = current_user.get('id_usuario') if isinstance(current_user, dict) else None
        user_role = current_user.get('rol') if isinstance(current_user, dict) else None
        
        # Validar permisos
        if user_role not in ['ADMIN', 'GERENTE'] and user_id != usuario_id:
            return jsonify({"success": False, "error": "No autorizado"}), 403
        
        resultado = UsuarioHorarioService.obtener_horario_activo(usuario_id)
        
        if not resultado['success']:
            return jsonify(resultado), 404
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en obtener_horario_activo: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@usuario_horario_bp.route('/usuario/<int:usuario_id>', methods=['GET'])
@jwt_required()
def listar_horarios_usuario(usuario_id):
    """
    Listar todos los horarios asignados a un usuario.
    
    Query params:
    - es_activo: bool (opcional)
    """
    try:
        current_user = get_jwt_identity()
        user_id = current_user.get('id_usuario') if isinstance(current_user, dict) else None
        user_role = current_user.get('rol') if isinstance(current_user, dict) else None
        
        # Validar permisos
        if user_role not in ['ADMIN', 'GERENTE'] and user_id != usuario_id:
            return jsonify({"success": False, "error": "No autorizado"}), 403
        
        es_activo_str = request.args.get('es_activo')
        es_activo = None if es_activo_str is None else es_activo_str.lower() == 'true'
        
        resultado = UsuarioHorarioService.listar_horarios_usuario(usuario_id, es_activo)
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en listar_horarios_usuario: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@usuario_horario_bp.route('/<int:id_usuario_horario>', methods=['DELETE'])
@jwt_required()
def desactivar_asignacion(id_usuario_horario):
    """Desactivar asignación de horario"""
    try:
        current_user = get_jwt_identity()
        user_role = current_user.get('rol') if isinstance(current_user, dict) else None
        
        if user_role not in ['ADMIN', 'GERENTE']:
            return jsonify({
                "success": False,
                "error": "Acceso denegado. Se requiere rol ADMIN o GERENTE"
            }), 403
        
        resultado = UsuarioHorarioService.desactivar_asignacion(id_usuario_horario)
        
        if not resultado['success']:
            return jsonify(resultado), 400
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en desactivar_asignacion: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@usuario_horario_bp.route('/horario/<int:horario_id>/empleados', methods=['GET'])
@jwt_required()
def obtener_empleados_con_horario(horario_id):
    """
    Obtener lista de empleados con un horario específico.
    
    Query params:
    - es_activo: bool (default: true)
    """
    try:
        current_user = get_jwt_identity()
        user_role = current_user.get('rol') if isinstance(current_user, dict) else None
        
        if user_role not in ['ADMIN', 'GERENTE']:
            return jsonify({
                "success": False,
                "error": "Acceso denegado. Se requiere rol ADMIN o GERENTE"
            }), 403
        
        es_activo = request.args.get('es_activo', 'true').lower() == 'true'
        resultado = UsuarioHorarioService.obtener_empleados_con_horario(horario_id, es_activo)
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en obtener_empleados_con_horario: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
