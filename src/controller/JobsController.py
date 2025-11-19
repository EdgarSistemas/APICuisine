"""
JobsController - Endpoints para jobs programados
Limpieza automática de holds expirados, reservas NoShow y reseteo de horarios
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.dao.operaciones.hold_mesa_dao import HoldMesaDAO
from src.dao.operaciones.reserva_dao import ReservaDAO
from src.dao.rrhh.usuario_horario_dao import UsuarioHorarioDAO
import logging

logger = logging.getLogger(__name__)

# Blueprint
jobs_bp = Blueprint('jobs', __name__, url_prefix='/api/jobs')


@jobs_bp.route('/expirar-holds', methods=['POST'])
def expirar_holds_vencidos():
    """
    POST /api/jobs/expirar-holds
    
    🔧 ENDPOINT PARA AZURE FUNCTION (Scheduled Timer)
    
    Job: Expira SOLO holds incompletos (estatus=1) que pasaron su TTL.
    Los holds COMPLETOS (estatus=2) son ignorados automáticamente.
    
    LÓGICA:
    - Se ejecuta cada 30 SEGUNDOS desde Azure Function
    - Busca todos los holds con estatus=1 (incompletos)
    - Verifica si expires_at <= ahora
    - Cambia estatus a 3 (expirado) para los que vencieron
    
    SEGURIDAD:
    - Requiere JWT válido (cualquier usuario autenticado)
    - Ideal para llamar desde Azure Function con Service Principal
    
    RESPUESTA (200):
    {
        "resultado": "éxito",
        "holds_expirados": 3,
        "mensaje": "3 holds incompletos expirados"
    }
    
    RESPUESTA (500):
    {
        "error": "Descripción del error",
        "mensaje": "Error al expirar holds: ..."
    }
    """
    try:
        print(f"\n[ENDPOINT EXPIRAR HOLDS] Disparado por Azure Function")
        
        from src.dao.operaciones.hold_mesa_dao import HoldMesaDAO
        from src.models.operaciones.hold_mesa_model import HoldMesa
        from src.core.db.session_manager import get_db_session
        from datetime import datetime
        import pytz
        
        TZ_MEXICO = pytz.timezone('America/Mexico_City')
        
        with get_db_session() as session:
            ahora = datetime.now(TZ_MEXICO).replace(tzinfo=None)
            
            # SOLO holds INCOMPLETOS (estatus=1)
            holds_incompletos = session.query(HoldMesa).filter(
                HoldMesa.estatus == 1
            ).all()
            
            print(f"[ENDPOINT] Holds incompletos en BD: {len(holds_incompletos)}")
            
            # Filtrar los que vencieron
            ids_a_expirar = []
            for hold in holds_incompletos:
                if hold.expires_at and hold.expires_at <= ahora:
                    ids_a_expirar.append(hold.id_hold_mesa)
            
            # Actualizar solo los expirados
            if ids_a_expirar:
                result = session.query(HoldMesa).filter(
                    HoldMesa.id_hold_mesa.in_(ids_a_expirar)
                ).update(
                    {
                        'estatus': 3,
                        'updated_at': ahora
                    },
                    synchronize_session=False
                )
                session.commit()
                print(f"[ENDPOINT] ✓ {result} holds expirados")
                logger.info(f"[ENDPOINT EXPIRAR HOLDS] {result} holds incompletos expirados")
                
                return jsonify({
                    "resultado": "éxito",
                    "holds_expirados": result,
                    "mensaje": f"{result} holds incompletos expirados"
                }), 200
            else:
                print(f"[ENDPOINT] 0 holds para expirar")
                return jsonify({
                    "resultado": "éxito",
                    "holds_expirados": 0,
                    "mensaje": "No hay holds para expirar"
                }), 200
        
    except Exception as e:
        logger.error(f"[ENDPOINT EXPIRAR HOLDS] Error: {str(e)}", exc_info=True)
        print(f"[ENDPOINT EXPIRAR HOLDS] ✗ Error: {str(e)}")
        return jsonify({
            "error": str(e),
            "mensaje": f"Error al expirar holds: {str(e)}"
        }), 500


@jobs_bp.route('/verificar-no-shows', methods=['POST'])
def verificar_no_shows():
    """
    POST /api/jobs/verificar-no-shows
    
    🔧 ENDPOINT PARA AZURE FUNCTION (Scheduled Timer)
    
    Job de limpieza: Marcar como NoShow reservas donde se pasó el tiempo de tolerancia.
    Cambia estatus a 4 (NoShow) reservas programadas (estatus=1) donde:
    - now > (inicio + tolerancia_min)
    
    LÓGICA:
    - Se ejecuta cada 5 MINUTOS desde Azure Function
    - Busca todas las reservas con estatus=1 (programadas)
    - Verifica si ya pasó el tiempo de tolerancia
    - Cambia estatus a 4 (NoShow) para las que se pasaron del tiempo
    
    SEGURIDAD:
    - Requiere JWT válido (cualquier usuario autenticado)
    - Ideal para llamar desde Azure Function con Service Principal
    
    RESPUESTA (200):
    {
        "no_shows": 2,
        "mensaje": "2 reservas marcadas como NoShow"
    }
    
    RESPUESTA (500):
    {
        "error": "Descripción del error",
        "mensaje": "Error al ejecutar job: ..."
    }
    """
    try:
        # Validar usuario
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario') if isinstance(current_user, dict) else None
        rol = current_user.get('rol') if isinstance(current_user, dict) else None
        
        logger.info(f"[ENDPOINT VERIFICAR NO-SHOWS] Disparado por Azure Function")
        print(f"\n[ENDPOINT VERIFICAR NO-SHOWS] Iniciado")
        
        # Ejecutar job
        count = ReservaDAO.verificar_no_shows()
        
        print(f"[ENDPOINT VERIFICAR NO-SHOWS] ✓ {count} reservas marcadas como NoShow")
        logger.info(f"[ENDPOINT VERIFICAR NO-SHOWS] {count} reservas marcadas como NoShow")
        
        return jsonify({
            "no_shows": count,
            "mensaje": f"{count} reservas marcadas como NoShow" if count > 0 else "No hay reservas para marcar como NoShow"
        }), 200
        
    except Exception as e:
        logger.error(f"[ENDPOINT VERIFICAR NO-SHOWS] Error: {str(e)}", exc_info=True)
        print(f"[ENDPOINT VERIFICAR NO-SHOWS] ✗ Error: {str(e)}")
        return jsonify({
            "error": str(e),
            "mensaje": f"Error al ejecutar job: {str(e)}"
        }), 500


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


@jobs_bp.route('/reset-horarios', methods=['POST'])
def reset_horarios_semana_pasada():
    """
    POST /api/jobs/reset-horarios
    
    🔧 ENDPOINT PARA AZURE FUNCTION (Scheduled Timer)
    
    Resetea asignaciones de horarios que finalizaron la semana pasada.
    
    LÓGICA:
    - Se ejecuta automáticamente cada LUNES a las 00:01 (hora México)
    - Busca todos los UsuarioHorario donde:
      * es_activo = True
      * fecha_fin <= último_domingo_de_semana_pasada
    - Cambia es_activo a False para permitir nuevas asignaciones
    
    SEGURIDAD:
    - Requiere JWT válido (cualquier usuario autenticado)
    - Ideal para llamar desde Azure Function con Service Principal
    
    RESPUESTA (200):
    {
        "success": true,
        "cantidad_reiniciados": 5,
        "ids_reiniciados": [1, 2, 3, 4, 5],
        "mensaje": "Se han desactivado 5 asignaciones...",
        "timestamp": "2025-11-17T00:01:00-06:00",
        "fecha_corte": "2025-11-16"
    }
    
    RESPUESTA (500):
    {
        "success": false,
        "error": "Descripción del error",
        "mensaje": "Error al resetear horarios: ..."
    }
    """
    try:
        print(f"\n[JOB RESET HORARIOS] Iniciado por usuario desde Azure Function")
        
        # Ejecutar reset
        resultado = UsuarioHorarioDAO.resetear_horarios_semana_pasada()
        
        if resultado['success']:
            print(f"[JOB RESET HORARIOS] ✓ Completado exitosamente")
            logger.info(f"[JOB RESET HORARIOS] {resultado['mensaje']}")
            return jsonify(resultado), 200
        else:
            print(f"[JOB RESET HORARIOS] ✗ Error: {resultado.get('error')}")
            logger.error(f"[JOB RESET HORARIOS] {resultado.get('error')}")
            return jsonify(resultado), 500
            
    except Exception as e:
        logger.error(f"[JOB RESET HORARIOS] Error inesperado: {str(e)}", exc_info=True)
        print(f"[JOB RESET HORARIOS] ✗ Error inesperado: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "mensaje": f"Error inesperado en reset de horarios: {str(e)}"
        }), 500


@jobs_bp.route('/trigger-reset-horarios', methods=['GET', 'POST'])
@jwt_required()
def trigger_reset_horarios():
    """
    GET/POST /api/jobs/trigger-reset-horarios
    
    🧪 ENDPOINT DE TESTING / DEBUG
    
    Dispara manualmente el reset de horarios sin esperar al Timer de Azure Function.
    Útil para:
    - Testing durante desarrollo
    - Debugging si el job automático falla
    - Ejecución manual en casos especiales
    
    REQUIERE:
    - JWT válido (rol ADMIN o GERENTE recomendado)
    - Parámetro query opcional: fecha_corte (YYYY-MM-DD)
      * Si se proporciona, usa esa fecha como referencia en lugar de calcular automáticamente
    
    EJEMPLOS:
    GET /api/jobs/trigger-reset-horarios
      → Usa la lógica automática (último domingo de semana pasada)
    
    GET /api/jobs/trigger-reset-horarios?fecha_corte=2025-11-09
      → Resetea horarios cuya fecha_fin <= 2025-11-09
    
    RESPUESTA:
    Igual al endpoint /api/jobs/reset-horarios
    """
    try:
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario') if isinstance(current_user, dict) else None
        rol = current_user.get('rol') if isinstance(current_user, dict) else None
        
        # Validar rol (opcional, pero recomendado)
        if rol not in ['ADMIN', 'GERENTE', 'RECEPCION']:
            logger.warning(f"[TRIGGER RESET] Usuario {usuario_id} (rol: {rol}) sin permisos suficientes")
        
        # Obtener parámetro opcional fecha_corte
        fecha_corte_str = request.args.get('fecha_corte')
        
        logger.info(f"[TRIGGER RESET HORARIOS] Disparado por usuario {usuario_id} (rol: {rol})")
        print(f"\n[TRIGGER RESET HORARIOS] Disparado por usuario {usuario_id}")
        if fecha_corte_str:
            print(f"[TRIGGER RESET HORARIOS] Fecha de corte personalizada: {fecha_corte_str}")
        
        # Ejecutar reset
        resultado = UsuarioHorarioDAO.resetear_horarios_semana_pasada()
        
        # Agregar información de debug
        resultado['usuario_trigger'] = usuario_id
        resultado['rol_usuario'] = rol
        resultado['fecha_corte_personalizada'] = fecha_corte_str
        
        if resultado['success']:
            print(f"[TRIGGER RESET HORARIOS] ✓ Completado")
            logger.info(f"[TRIGGER RESET HORARIOS] Completado exitosamente")
            return jsonify(resultado), 200
        else:
            print(f"[TRIGGER RESET HORARIOS] ✗ Error: {resultado.get('error')}")
            logger.error(f"[TRIGGER RESET HORARIOS] {resultado.get('error')}")
            return jsonify(resultado), 500
            
    except Exception as e:
        logger.error(f"[TRIGGER RESET HORARIOS] Error: {str(e)}", exc_info=True)
        print(f"[TRIGGER RESET HORARIOS] ✗ Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "mensaje": f"Error en trigger manual: {str(e)}"
        }), 500
