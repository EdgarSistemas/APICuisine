"""
SolicitudVacacionesController - Endpoints para solicitudes de vacaciones
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.rrhh.solicitud_vacaciones_service import SolicitudVacacionesService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

solicitud_vacaciones_bp = Blueprint('solicitud_vacaciones', __name__, url_prefix='/api/vacaciones')


@solicitud_vacaciones_bp.route('', methods=['POST'])
@jwt_required()
def crear_solicitud():
    """
    Crear solicitud de vacaciones.
    
    Body:
    {
        "fecha_inicio": "2025-02-01",
        "fecha_fin": "2025-02-15",
        "motivo": "Vacaciones familiares"  # Opcional
    }
    """
    try:
        current_user = get_jwt_identity()
        user_id = current_user.get('id_usuario') if isinstance(current_user, dict) else None
        
        data = request.get_json()
        
        # Convertir fechas string a date
        if isinstance(data.get('fecha_inicio'), str):
            data['fecha_inicio'] = datetime.strptime(data['fecha_inicio'], '%Y-%m-%d').date()
        if isinstance(data.get('fecha_fin'), str):
            data['fecha_fin'] = datetime.strptime(data['fecha_fin'], '%Y-%m-%d').date()
        
        resultado = SolicitudVacacionesService.crear_solicitud(
            usuario_id=user_id,
            data=data
        )
        
        if not resultado['success']:
            return jsonify(resultado), 400
        
        return jsonify(resultado), 201
        
    except Exception as e:
        logger.error(f"Error en crear_solicitud: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@solicitud_vacaciones_bp.route('/mis-solicitudes', methods=['GET'])
@jwt_required()
def listar_mis_solicitudes():
    """
    Listar solicitudes del empleado.
    
    Query params:
    - estatus: int (1=Pendiente, 2=Aprobada, 3=Rechazada)
    """
    try:
        current_user = get_jwt_identity()
        user_id = current_user.get('id_usuario') if isinstance(current_user, dict) else None
        
        estatus = request.args.get('estatus', type=int)
        
        resultado = SolicitudVacacionesService.listar_solicitudes_usuario(
            usuario_id=user_id,
            estatus=estatus
        )
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en listar_mis_solicitudes: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@solicitud_vacaciones_bp.route('/sucursal/<int:sucursal_id>', methods=['GET'])
@jwt_required()
def listar_solicitudes_sucursal(sucursal_id):
    """
    Listar solicitudes de una sucursal (ADMIN/Gerente).
    
    Query params:
    - estatus: int (1=Pendiente, 2=Aprobada, 3=Rechazada)
    """
    try:
        current_user = get_jwt_identity()
        user_role = current_user.get('rol') if isinstance(current_user, dict) else None
        
        if user_role not in ['ADMIN', 'GERENTE']:
            return jsonify({
                "success": False,
                "error": "Acceso denegado. Se requiere rol ADMIN o GERENTE"
            }), 403
        
        estatus = request.args.get('estatus', type=int)
        
        resultado = SolicitudVacacionesService.listar_solicitudes_sucursal(
            sucursal_id=sucursal_id,
            estatus=estatus
        )
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en listar_solicitudes_sucursal: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@solicitud_vacaciones_bp.route('/<int:id_solicitud>', methods=['GET'])
@jwt_required()
def obtener_solicitud(id_solicitud):
    """
    Obtener solicitud por ID.
    El empleado solo puede ver sus propias solicitudes.
    """
    try:
        current_user = get_jwt_identity()
        user_id = current_user.get('id_usuario') if isinstance(current_user, dict) else None
        user_role = current_user.get('rol') if isinstance(current_user, dict) else None
        
        resultado = SolicitudVacacionesService.obtener_solicitud(id_solicitud)
        
        if not resultado['success']:
            return jsonify(resultado), 404
        
        # Validar permisos
        solicitud = resultado['solicitud']
        if user_role not in ['ADMIN', 'GERENTE'] and solicitud['usuario_id'] != user_id:
            return jsonify({"success": False, "error": "No autorizado"}), 403
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en obtener_solicitud: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@solicitud_vacaciones_bp.route('/<int:id_solicitud>/aprobar', methods=['POST'])
@jwt_required()
def aprobar_solicitud(id_solicitud):
    """
    Aprobar solicitud de vacaciones (solo Gerente/Admin).
    
    Body:
    {
        "notas_gerente": "Aprobado por buen desempeño"  # Opcional
    }
    """
    try:
        current_user = get_jwt_identity()
        user_id = current_user.get('id_usuario') if isinstance(current_user, dict) else None
        user_role = current_user.get('rol') if isinstance(current_user, dict) else None
        
        if user_role not in ['ADMIN', 'GERENTE']:
            return jsonify({
                "success": False,
                "error": "Acceso denegado. Se requiere rol ADMIN o GERENTE"
            }), 403
        
        data = request.get_json() or {}
        
        resultado = SolicitudVacacionesService.aprobar_solicitud(
            id_solicitud=id_solicitud,
            gerente_id=user_id,
            data=data
        )
        
        if not resultado['success']:
            return jsonify(resultado), 400
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en aprobar_solicitud: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@solicitud_vacaciones_bp.route('/<int:id_solicitud>/rechazar', methods=['POST'])
@jwt_required()
def rechazar_solicitud(id_solicitud):
    """
    Rechazar solicitud de vacaciones (solo Gerente/Admin).
    
    Body:
    {
        "notas_gerente": "Período muy ocupado"  # Recomendado
    }
    """
    try:
        current_user = get_jwt_identity()
        user_id = current_user.get('id_usuario') if isinstance(current_user, dict) else None
        user_role = current_user.get('rol') if isinstance(current_user, dict) else None
        
        if user_role not in ['ADMIN', 'GERENTE']:
            return jsonify({
                "success": False,
                "error": "Acceso denegado. Se requiere rol ADMIN o GERENTE"
            }), 403
        
        data = request.get_json() or {}
        
        resultado = SolicitudVacacionesService.rechazar_solicitud(
            id_solicitud=id_solicitud,
            gerente_id=user_id,
            data=data
        )
        
        if not resultado['success']:
            return jsonify(resultado), 400
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en rechazar_solicitud: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@solicitud_vacaciones_bp.route('/pendientes/count', methods=['GET'])
@jwt_required()
def contar_pendientes():
    """
    Contar solicitudes pendientes.
    
    Query params:
    - sucursal_id: int (opcional)
    """
    try:
        current_user = get_jwt_identity()
        user_role = current_user.get('rol') if isinstance(current_user, dict) else None
        
        if user_role not in ['ADMIN', 'GERENTE']:
            return jsonify({
                "success": False,
                "error": "Acceso denegado. Se requiere rol ADMIN o GERENTE"
            }), 403
        
        sucursal_id = request.args.get('sucursal_id', type=int)
        
        resultado = SolicitudVacacionesService.contar_pendientes(sucursal_id)
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en contar_pendientes: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
