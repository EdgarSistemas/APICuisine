"""
AsistenciaController - Endpoints para check-in/check-out de empleados
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.rrhh.asistencia_service import AsistenciaService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

asistencia_bp = Blueprint('asistencias', __name__, url_prefix='/api/asistencias')


@asistencia_bp.route('/checkin', methods=['POST'])
@jwt_required()
def hacer_checkin():
    """
    Realizar check-in.
    
    Body:
    {
        "codigo": "123456",
        "lat": 19.432608,  # Opcional
        "lng": -99.133209,  # Opcional
        "device_info": "iPhone 12",  # Opcional
        "ip_address": "192.168.1.10"  # Opcional
    }
    
    Response:
    {
        "success": true,
        "asistencia": {...},
        "tardanza": false
    }
    """
    try:
        current_user = get_jwt_identity()
        user_id = current_user.get('id_usuario') if isinstance(current_user, dict) else None
        
        data = request.get_json()
        
        # Obtener IP del cliente si no viene en body
        if not data.get('ip_address'):
            data['ip_address'] = request.remote_addr
        
        resultado = AsistenciaService.hacer_checkin(
            usuario_id=user_id,
            data=data
        )
        
        if not resultado['success']:
            return jsonify(resultado), 400
        
        return jsonify(resultado), 201
        
    except Exception as e:
        logger.error(f"Error en hacer_checkin: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@asistencia_bp.route('/checkout', methods=['POST'])
@jwt_required()
def hacer_checkout():
    """
    Realizar check-out.
    No requiere código.
    
    Body:
    {
        "lat": 19.432608,  # Opcional
        "lng": -99.133209,  # Opcional
        "device_info": "iPhone 12",  # Opcional
        "ip_address": "192.168.1.10",  # Opcional
        "notas": "Salida anticipada"  # Opcional
    }
    """
    try:
        current_user = get_jwt_identity()
        user_id = current_user.get('id_usuario') if isinstance(current_user, dict) else None
        
        data = request.get_json() or {}
        
        # Obtener IP del cliente si no viene en body
        if not data.get('ip_address'):
            data['ip_address'] = request.remote_addr
        
        resultado = AsistenciaService.hacer_checkout(
            usuario_id=user_id,
            data=data
        )
        
        if not resultado['success']:
            return jsonify(resultado), 400
        
        return jsonify(resultado), 201
        
    except Exception as e:
        logger.error(f"Error en hacer_checkout: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@asistencia_bp.route('/historial', methods=['GET'])
@jwt_required()
def obtener_historial():
    """
    Obtener historial de asistencias del empleado.
    
    Query params:
    - fecha_inicio: YYYY-MM-DD (opcional)
    - fecha_fin: YYYY-MM-DD (opcional)
    - limit: int (default: 50)
    """
    try:
        current_user = get_jwt_identity()
        user_id = current_user.get('id_usuario') if isinstance(current_user, dict) else None
        
        fecha_inicio_str = request.args.get('fecha_inicio')
        fecha_fin_str = request.args.get('fecha_fin')
        limit = request.args.get('limit', 50, type=int)
        
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date() if fecha_inicio_str else None
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date() if fecha_fin_str else None
        
        resultado = AsistenciaService.obtener_historial(
            usuario_id=user_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            limit=limit
        )
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en obtener_historial: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@asistencia_bp.route('/sucursal/<int:sucursal_id>', methods=['GET'])
@jwt_required()
def obtener_asistencias_sucursal(sucursal_id):
    """
    Obtener asistencias de una sucursal (ADMIN/Gerente).
    
    Query params:
    - fecha_inicio: YYYY-MM-DD (opcional)
    - fecha_fin: YYYY-MM-DD (opcional)
    - limit: int (default: 100)
    """
    try:
        current_user = get_jwt_identity()
        user_role = current_user.get('rol') if isinstance(current_user, dict) else None
        
        if user_role not in ['ADMIN', 'GERENTE']:
            return jsonify({
                "success": False,
                "error": "Acceso denegado. Se requiere rol ADMIN o GERENTE"
            }), 403
        
        fecha_inicio_str = request.args.get('fecha_inicio')
        fecha_fin_str = request.args.get('fecha_fin')
        limit = request.args.get('limit', 100, type=int)
        
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date() if fecha_inicio_str else None
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date() if fecha_fin_str else None
        
        resultado = AsistenciaService.obtener_asistencias_sucursal(
            sucursal_id=sucursal_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            limit=limit
        )
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en obtener_asistencias_sucursal: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@asistencia_bp.route('/tardanzas/usuario/<int:usuario_id>', methods=['GET'])
@jwt_required()
def contar_tardanzas(usuario_id):
    """
    Contar tardanzas de un empleado.
    
    Query params:
    - fecha_inicio: YYYY-MM-DD (opcional)
    - fecha_fin: YYYY-MM-DD (opcional)
    """
    try:
        current_user = get_jwt_identity()
        user_role = current_user.get('rol') if isinstance(current_user, dict) else None
        
        if user_role not in ['ADMIN', 'GERENTE']:
            return jsonify({
                "success": False,
                "error": "Acceso denegado. Se requiere rol ADMIN o GERENTE"
            }), 403
        
        fecha_inicio_str = request.args.get('fecha_inicio')
        fecha_fin_str = request.args.get('fecha_fin')
        
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date() if fecha_inicio_str else None
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date() if fecha_fin_str else None
        
        resultado = AsistenciaService.contar_tardanzas(
            usuario_id=usuario_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en contar_tardanzas: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
