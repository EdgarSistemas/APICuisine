"""
JobsController - Endpoints para jobs programados
Limpieza automática de holds expirados y reservas NoShow
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.dao.operaciones.hold_mesa_dao import HoldMesaDAO
from src.dao.operaciones.reserva_dao import ReservaDAO
import logging

logger = logging.getLogger(__name__)

# Blueprint
jobs_bp = Blueprint('jobs', __name__, url_prefix='/api/jobs')


@jobs_bp.route('/expirar-holds', methods=['POST'])
@jwt_required()
def expirar_holds_vencidos():
    """
    POST /api/jobs/expirar-holds
    
    Job de limpieza: Expirar holds activos cuyo TTL haya pasado.
    Marca como expirados (estatus=3) todos los holds con expires_at <= now.
    
    Este endpoint debe ejecutarse periódicamente (cada 1-5 minutos).
    Se puede configurar con cron, Azure Function Timer, o APScheduler.
    
    Requiere autenticación JWT (puede ser un usuario de sistema).
    
    Returns:
        200: {expirados: int, mensaje: "..."}
    """
    try:
        # OPCIONAL: Validar que usuario tenga permisos de ADMIN o SYSTEM
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario')
        rol = current_user.get('rol')
        
        # Por ahora permitimos cualquier autenticado (en prod validar rol)
        logger.info(f"Job expirar-holds ejecutado por usuario {usuario_id} (rol: {rol})")
        
        # Ejecutar job
        count = HoldMesaDAO.expirar_holds_vencidos()
        
        return jsonify({
            "expirados": count,
            "mensaje": f"{count} holds expirados automáticamente" if count > 0 else "No hay holds por expirar"
        }), 200
        
    except Exception as e:
        logger.error(f"Error en job expirar-holds: {str(e)}")
        return jsonify({"error": f"Error al ejecutar job: {str(e)}"}), 500


@jobs_bp.route('/verificar-no-shows', methods=['POST'])
@jwt_required()
def verificar_no_shows():
    """
    POST /api/jobs/verificar-no-shows
    
    Job de limpieza: Marcar como NoShow reservas donde se pasó el tiempo de tolerancia.
    Cambia estatus a 4 (NoShow) reservas programadas (estatus=1) donde:
    - now > (inicio + tolerancia_min)
    
    Este endpoint debe ejecutarse periódicamente (cada 5-10 minutos).
    
    Requiere autenticación JWT (puede ser un usuario de sistema).
    
    Returns:
        200: {no_shows: int, mensaje: "..."}
    """
    try:
        # OPCIONAL: Validar permisos
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario')
        rol = current_user.get('rol')
        
        logger.info(f"Job verificar-no-shows ejecutado por usuario {usuario_id} (rol: {rol})")
        
        # Ejecutar job
        count = ReservaDAO.verificar_no_shows()
        
        return jsonify({
            "no_shows": count,
            "mensaje": f"{count} reservas marcadas como NoShow" if count > 0 else "No hay reservas para marcar como NoShow"
        }), 200
        
    except Exception as e:
        logger.error(f"Error en job verificar-no-shows: {str(e)}")
        return jsonify({"error": f"Error al ejecutar job: {str(e)}"}), 500


@jobs_bp.route('/status', methods=['GET'])
@jwt_required()
def status_jobs():
    """
    GET /api/jobs/status
    
    Obtener estadísticas de jobs.
    Útil para monitoreo.
    
    Returns:
        200: Estadísticas de holds y reservas
    """
    try:
        from datetime import datetime
        
        # Contar holds activos
        holds_activos = HoldMesaDAO.listar_holds_activos()
        
        # Contar reservas por estatus
        reservas_programadas = ReservaDAO.listar_reservas(estatus=1)
        reservas_en_curso = ReservaDAO.listar_reservas(estatus=2)
        
        return jsonify({
            "timestamp": datetime.now().isoformat(),
            "holds": {
                "activos": len(holds_activos),
                "descripcion": "Holds que no han expirado"
            },
            "reservas": {
                "programadas": len(reservas_programadas),
                "en_curso": len(reservas_en_curso),
                "descripcion": "Reservas activas en el sistema"
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error en status_jobs: {str(e)}")
        return jsonify({"error": f"Error al obtener status: {str(e)}"}), 500
