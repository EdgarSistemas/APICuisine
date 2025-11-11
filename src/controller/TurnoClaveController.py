"""
TurnoClaveController - Endpoints para códigos de turno (Azure Function + ADMIN)
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.rrhh.turno_clave_service import TurnoClaveService
from datetime import date, datetime
import logging
import os

logger = logging.getLogger(__name__)

turno_clave_bp = Blueprint('turno_claves', __name__, url_prefix='/api/turnos')


@turno_clave_bp.route('/generar-codigo', methods=['POST'])
def generar_codigo_azure():
    """
    Endpoint especial para Azure Function.
    Genera código de 6 dígitos para un horario/fecha.
    
    Auth: Token especial en header X-Azure-Function-Key
    
    Body:
    {
        "sucursal_id": 1,
        "horario_id": 1,
        "fecha": "2025-01-10",
        "expira_en_horas": 2,
        "uso_maximo": 0
    }
    
    Response:
    {
        "success": true,
        "turno": {
            "id_turno_clave": 1,
            "codigo": "123456",
            "fecha": "2025-01-10",
            "expira_en": "2025-01-10T11:00:00",
            ...
        }
    }
    """
    try:
        # Validar token de Azure Function
        azure_key = request.headers.get('X-Azure-Function-Key')
        expected_key = os.getenv('AZURE_FUNCTION_KEY', 'dev-azure-key-12345')
        
        if azure_key != expected_key:
            logger.warning("Intento de acceso no autorizado a endpoint de Azure Function")
            return jsonify({"success": False, "error": "No autorizado"}), 401
        
        data = request.get_json()
        
        # Convertir fecha string a date si viene como string
        if isinstance(data.get('fecha'), str):
            data['fecha'] = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
        
        resultado = TurnoClaveService.generar_codigo(data)
        
        if not resultado['success']:
            return jsonify(resultado), 400
        
        return jsonify(resultado), 201
        
    except Exception as e:
        logger.error(f"Error en generar_codigo_azure: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@turno_clave_bp.route('/codigo-activo', methods=['GET'])
@jwt_required()
def obtener_codigo_activo():
    """
    Obtener código activo para una sucursal/horario/fecha.
    
    Query params:
    - sucursal_id: int (required)
    - horario_id: int (required)
    - fecha: string YYYY-MM-DD (default: hoy)
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
        horario_id = request.args.get('horario_id', type=int)
        fecha_str = request.args.get('fecha')
        
        if not sucursal_id or not horario_id:
            return jsonify({
                "success": False,
                "error": "Parámetros sucursal_id y horario_id son requeridos"
            }), 400
        
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else date.today()
        
        resultado = TurnoClaveService.obtener_codigo_activo(sucursal_id, horario_id, fecha)
        
        if not resultado['success']:
            return jsonify(resultado), 404
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en obtener_codigo_activo: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@turno_clave_bp.route('/desactivar-expirados', methods=['POST'])
@jwt_required()
def desactivar_codigos_expirados():
    """
    Desactivar todos los códigos expirados.
    Endpoint para jobs programados.
    """
    try:
        current_user = get_jwt_identity()
        user_role = current_user.get('rol') if isinstance(current_user, dict) else None
        
        if user_role != 'ADMIN':
            return jsonify({
                "success": False,
                "error": "Acceso denegado. Se requiere rol ADMIN"
            }), 403
        
        resultado = TurnoClaveService.desactivar_codigos_expirados()
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en desactivar_codigos_expirados: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
