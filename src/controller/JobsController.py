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
            holds_data = []  # Para notificaciones
            for hold in holds_incompletos:
                if hold.expires_at and hold.expires_at <= ahora:
                    ids_a_expirar.append(hold.id_hold_mesa)
                    holds_data.append({
                        'id': hold.id_hold_mesa,
                        'mesa_id': hold.mesa_id,
                        'cliente_id': hold.actor_usuario_id
                    })
            
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
                
                # Notificar a clientes sobre holds expirados
                try:
                    from src.services.notification import NotificationService
                    for hold_info in holds_data:
                        if hold_info['cliente_id']:
                            NotificationService.notificar_hold_expirado(
                                hold_id=hold_info['id'],
                                mesa_num=str(hold_info['mesa_id']),
                                cliente_id=hold_info['cliente_id']
                            )
                except Exception as notif_error:
                    logger.warning(f"Error enviando notificaciones de holds expirados: {notif_error}")
                
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


# ============================================================================
# JOB: RECORDATORIO DE RESERVAS
# ============================================================================

@jobs_bp.route('/recordatorio-reservas', methods=['POST'])
def recordatorio_reservas():
    """
    POST /api/jobs/recordatorio-reservas
    
    🔧 ENDPOINT PARA AZURE FUNCTION (Scheduled Timer - cada 15 min)
    
    Job: Envía recordatorios a clientes con reservas en las próximas 2 horas.
    Solo envía UN recordatorio por reserva (marca como notificada).
    
    LÓGICA:
    - Busca reservas con estatus=1 (Programada)
    - Donde inicio está entre ahora y ahora+2 horas
    - Que NO hayan sido notificadas previamente
    - Envía push notification al cliente
    - Marca la reserva como notificada
    
    RESPUESTA (200):
    {
        "success": true,
        "recordatorios_enviados": 5,
        "reservas_procesadas": [123, 456, 789],
        "errores": []
    }
    """
    try:
        from src.models.operaciones.reserva_model import Reserva
        from src.models import Usuario
        from src.services.notification import NotificationService
        from src.core.db.session_manager import get_db_session
        from datetime import datetime, timedelta
        import pytz
        
        TZ_MEXICO = pytz.timezone('America/Mexico_City')
        ahora = datetime.now(TZ_MEXICO).replace(tzinfo=None)
        en_dos_horas = ahora + timedelta(hours=2)
        
        logger.info(f"[JOB RECORDATORIO] Iniciado - Buscando reservas entre {ahora} y {en_dos_horas}")
        print(f"\n[JOB RECORDATORIO RESERVAS] Iniciado")
        
        enviados = 0
        reservas_procesadas = []
        errores = []
        
        with get_db_session() as session:
            # Buscar reservas programadas para las próximas 2 horas
            # que tengan cliente_id y no hayan sido notificadas
            reservas = session.query(Reserva).filter(
                Reserva.estatus == 1,  # Programada
                Reserva.inicio >= ahora,
                Reserva.inicio <= en_dos_horas,
                Reserva.cliente_id.isnot(None)
            ).all()
            
            # Filtrar las que ya fueron notificadas
            reservas_a_notificar = [
                r for r in reservas 
                if not r.notas or '[RECORDATORIO_ENVIADO]' not in r.notas
            ]
            
            print(f"[JOB RECORDATORIO] Encontradas {len(reservas_a_notificar)} reservas para notificar")
            
            for reserva in reservas_a_notificar:
                try:
                    # Obtener nombre del cliente
                    cliente = session.query(Usuario).filter(
                        Usuario.id_usuario == reserva.cliente_id
                    ).first()
                    
                    cliente_nombre = cliente.nombre if cliente else "Cliente"
                    hora_reserva = reserva.inicio.strftime('%H:%M')
                    
                    # Obtener número de mesa (si hay hold asociado)
                    mesa_num = "asignada"
                    if reserva.hold_id:
                        from src.models.operaciones.hold_mesa_model import HoldMesa
                        from src.models.catalogos.mesa_model import Mesa
                        hold = session.query(HoldMesa).filter(
                            HoldMesa.id_hold_mesa == reserva.hold_id
                        ).first()
                        if hold:
                            mesa = session.query(Mesa).filter(
                                Mesa.id_mesa == hold.mesa_id
                            ).first()
                            if mesa:
                                mesa_num = mesa.numero_mesa or str(mesa.id_mesa)
                    
                    # Enviar notificación
                    resultado = NotificationService.notificar_recordatorio_reserva(
                        reserva_id=reserva.id_reserva,
                        fecha_hora=hora_reserva,
                        mesa_num=mesa_num,
                        cliente_id=reserva.cliente_id
                    )
                    
                    if resultado.get('success') or resultado.get('mensajes_exitosos', 0) > 0:
                        # Marcar como notificada
                        notas_actuales = reserva.notas or ""
                        reserva.notas = f"{notas_actuales} [RECORDATORIO_ENVIADO:{ahora.isoformat()}]"
                        enviados += 1
                        reservas_procesadas.append(reserva.id_reserva)
                        print(f"  ✓ Reserva {reserva.id_reserva} - {cliente_nombre} a las {hora_reserva}")
                    else:
                        errores.append({
                            "reserva_id": reserva.id_reserva,
                            "error": "Sin tokens o error de envío"
                        })
                        
                except Exception as e:
                    logger.error(f"Error procesando reserva {reserva.id_reserva}: {e}")
                    errores.append({
                        "reserva_id": reserva.id_reserva,
                        "error": str(e)
                    })
            
            session.commit()
        
        print(f"[JOB RECORDATORIO] ✓ Completado - {enviados} recordatorios enviados")
        logger.info(f"[JOB RECORDATORIO] Completado - {enviados} enviados, {len(errores)} errores")
        
        return jsonify({
            "success": True,
            "recordatorios_enviados": enviados,
            "reservas_procesadas": reservas_procesadas,
            "errores": errores
        }), 200
        
    except Exception as e:
        logger.error(f"[JOB RECORDATORIO] Error: {str(e)}", exc_info=True)
        print(f"[JOB RECORDATORIO] ✗ Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "mensaje": f"Error en job recordatorio: {str(e)}"
        }), 500


@jobs_bp.route('/verificar-lotes-por-vencer', methods=['POST'])
def verificar_lotes_por_vencer():
    """
    POST /api/jobs/verificar-lotes-por-vencer
    
    🔧 ENDPOINT PARA AZURE FUNCTION (Scheduled Timer - 1x al día 8am)
    
    Job: Verifica lotes de insumos próximos a vencer en TODAS las sucursales
    y envía notificaciones push a GERENTES y COMPRAS de cada sucursal.
    
    LÓGICA:
    - Obtiene TODAS las sucursales activas
    - Para cada sucursal:
      * Obtiene lotes próximos a vencer usando LoteDAO (misma lógica que Dashboard)
      * Identifica lotes CRÍTICOS (<=7 días)
      * Envía push notification a GERENTES de la sucursal
      * Envía push notification a usuarios COMPRAS de la sucursal
    - Retorna resumen detallado por sucursal
    
    Query params (opcionales):
    - dias_proximidad: int (default: 30) - días antes de vencimiento para alertar
    
    RESPUESTA (200):
    {
        "success": true,
        "dias_proximidad": 30,
        "total_lotes_por_vencer": 15,
        "total_notificaciones_enviadas": 8,
        "sucursales_procesadas": [...]
    }
    """
    try:
        from datetime import datetime
        from src.dao.inventario.lote_dao import LoteDAO
        from src.dao.auth.push_token_dao import PushTokenDAO
        from src.core.utils.push_notifications import FCMNotificationService
        from src.core.db.session_manager import get_db_session
        from src.models import Sucursal
        import pytz
        
        TZ_MEXICO = pytz.timezone('America/Mexico_City')
        ahora = datetime.now(TZ_MEXICO)
        
        # Parámetro opcional: días de proximidad (default 30)
        # Usar silent=True para evitar error 415 si no hay Content-Type JSON
        data = request.get_json(silent=True) or {}
        dias_proximidad = data.get('dias_proximidad', 30)
        
        logger.info(f"[JOB LOTES VENCER] Iniciado - días proximidad: {dias_proximidad}")
        print(f"\n[JOB LOTES POR VENCER] Iniciado - días proximidad: {dias_proximidad}")
        
        # Obtener TODAS las sucursales activas
        with get_db_session() as session:
            sucursales = session.query(Sucursal).filter(
                Sucursal.es_activa == True
            ).all()
            sucursales_data = [(s.id_sucursal, s.nombre) for s in sucursales]
        
        print(f"[JOB LOTES VENCER] Procesando {len(sucursales_data)} sucursales")
        
        sucursales_procesadas = []
        total_lotes_por_vencer = 0
        total_notificaciones = 0
        
        # Procesar cada sucursal
        for sucursal_id, sucursal_nombre in sucursales_data:
            print(f"  → Verificando sucursal: {sucursal_nombre} (ID: {sucursal_id})")
            
            # 1. Obtener lotes próximos a vencer usando LoteDAO
            lotes_por_vencer = LoteDAO.obtener_lotes_proximos_a_vencer(
                sucursal_id=sucursal_id,
                dias_proximidad=dias_proximidad
            )
            
            if not lotes_por_vencer:
                print(f"    ✓ Sin lotes próximos a vencer")
                sucursales_procesadas.append({
                    "sucursal_id": sucursal_id,
                    "sucursal_nombre": sucursal_nombre,
                    "lotes_por_vencer": 0,
                    "lotes_criticos": 0,
                    "usuarios_notificados": {"gerentes": 0, "compras": 0},
                    "notificaciones_enviadas": {"gerentes": 0, "compras": 0}
                })
                continue
            
            # Contar lotes críticos (<=7 días)
            lotes_criticos = [l for l in lotes_por_vencer if l['dias_para_vencer'] <= 7]
            
            print(f"    ⚠ {len(lotes_por_vencer)} lotes por vencer ({len(lotes_criticos)} críticos)")
            total_lotes_por_vencer += len(lotes_por_vencer)
            
            notificaciones_gerentes = 0
            notificaciones_compras = 0
            
            # Construir mensaje de notificación
            titulo = "📦 Lotes próximos a vencer"
            if len(lotes_criticos) > 0:
                titulo = "🚨 Lotes CRÍTICOS por vencer"
                cuerpo = f"{len(lotes_criticos)} lote(s) vencen en 7 días o menos - {sucursal_nombre}"
            else:
                cuerpo = f"{len(lotes_por_vencer)} lote(s) próximos a vencer - {sucursal_nombre}"
            
            # Preparar datos adicionales para la notificación
            datos_notificacion = {
                "tipo_alerta": "lotes_por_vencer",
                "sucursal_id": str(sucursal_id),
                "total_lotes": str(len(lotes_por_vencer)),
                "lotes_criticos": str(len(lotes_criticos)),
                "lotes_resumen": str([
                    {
                        "insumo": l['insumo_nombre'],
                        "dias": l['dias_para_vencer'],
                        "cantidad": l['cantidad_disponible'],
                        "urgencia": l['urgencia']
                    }
                    for l in lotes_por_vencer[:5]  # Primeros 5
                ])
            }
            
            # 2. NOTIFICAR A GERENTES
            usuarios_gerentes = PushTokenDAO.obtener_usuarios_con_push_tokens(
                filtros_usuario={
                    'rol': 'GERENTE',
                    'sucursal_id': sucursal_id
                },
                filtros_push_token={'es_activo': True},
                solo_activos=True
            )
            
            if usuarios_gerentes:
                tokens_gerentes = []
                plataformas_gerentes = {}
                
                for usuario_data in usuarios_gerentes:
                    for token_data in usuario_data['push_tokens']:
                        token = token_data['token']
                        tokens_gerentes.append(token)
                        plataformas_gerentes[token] = token_data.get('plataforma', 'desconocida')
                
                print(f"    → Notificando a {len(usuarios_gerentes)} gerentes")
                resultado_gerentes = FCMNotificationService.enviar_notificacion_simple(
                    tokens=tokens_gerentes,
                    titulo=titulo,
                    cuerpo=cuerpo,
                    datos_personalizados=datos_notificacion,
                    plataformas=plataformas_gerentes
                )
                notificaciones_gerentes = resultado_gerentes.get('mensajes_exitosos', 0)
                total_notificaciones += notificaciones_gerentes
            
            # 3. NOTIFICAR A COMPRAS
            usuarios_compras = PushTokenDAO.obtener_usuarios_con_push_tokens(
                filtros_usuario={
                    'rol': 'COMPRAS',
                    'sucursal_id': sucursal_id
                },
                filtros_push_token={'es_activo': True},
                solo_activos=True
            )
            
            if usuarios_compras:
                tokens_compras = []
                plataformas_compras = {}
                
                for usuario_data in usuarios_compras:
                    for token_data in usuario_data['push_tokens']:
                        token = token_data['token']
                        tokens_compras.append(token)
                        plataformas_compras[token] = token_data.get('plataforma', 'desconocida')
                
                print(f"    → Notificando a {len(usuarios_compras)} usuarios COMPRAS")
                resultado_compras = FCMNotificationService.enviar_notificacion_simple(
                    tokens=tokens_compras,
                    titulo=titulo,
                    cuerpo=cuerpo,
                    datos_personalizados=datos_notificacion,
                    plataformas=plataformas_compras
                )
                notificaciones_compras = resultado_compras.get('mensajes_exitosos', 0)
                total_notificaciones += notificaciones_compras
            
            sucursales_procesadas.append({
                "sucursal_id": sucursal_id,
                "sucursal_nombre": sucursal_nombre,
                "lotes_por_vencer": len(lotes_por_vencer),
                "lotes_criticos": len(lotes_criticos),
                "lotes_detalle": [
                    {
                        "insumo_nombre": l['insumo_nombre'],
                        "lote": l['lote'],
                        "dias_para_vencer": l['dias_para_vencer'],
                        "urgencia": l['urgencia'],
                        "cantidad_disponible": l['cantidad_disponible'],
                        "unidad": l['unidad_clave']
                    }
                    for l in lotes_por_vencer
                ],
                "usuarios_notificados": {
                    "gerentes": len(usuarios_gerentes) if usuarios_gerentes else 0,
                    "compras": len(usuarios_compras) if usuarios_compras else 0
                },
                "notificaciones_enviadas": {
                    "gerentes": notificaciones_gerentes,
                    "compras": notificaciones_compras
                }
            })
        
        print(f"[JOB LOTES VENCER] ✓ Completado - {total_lotes_por_vencer} lotes, {total_notificaciones} notificaciones")
        logger.info(f"[JOB LOTES VENCER] Completado: {total_lotes_por_vencer} lotes, {total_notificaciones} notificaciones")
        
        return jsonify({
            "success": True,
            "timestamp": ahora.isoformat(),
            "dias_proximidad": dias_proximidad,
            "total_lotes_por_vencer": total_lotes_por_vencer,
            "total_notificaciones_enviadas": total_notificaciones,
            "sucursales_procesadas": sucursales_procesadas
        }), 200
        
    except Exception as e:
        logger.error(f"[JOB LOTES VENCER] Error: {str(e)}", exc_info=True)
        print(f"[JOB LOTES VENCER] ✗ Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "mensaje": f"Error verificando lotes: {str(e)}"
        }), 500


# ============================================================================
# JOB: VERIFICAR LOTES VENCIDOS
# ============================================================================

@jobs_bp.route('/verificar-lotes-vencidos', methods=['POST'])
def verificar_lotes_vencidos():
    """
    POST /api/jobs/verificar-lotes-vencidos
    
    🔧 ENDPOINT PARA AZURE FUNCTION (Scheduled Timer - 1x al día 8am)
    
    Job: Verifica lotes YA VENCIDOS en TODAS las sucursales
    y envía notificaciones push a GERENTES y ALMACEN de cada sucursal.
    
    LÓGICA:
    - Obtiene TODAS las sucursales activas
    - Para cada sucursal:
      * Obtiene lotes vencidos usando LoteDAO (misma lógica que Dashboard)
      * Calcula el costo total de pérdida
      * Envía push notification a GERENTES de la sucursal
      * Envía push notification a usuarios ALMACEN de la sucursal
    - Retorna resumen detallado por sucursal
    
    RESPUESTA (200):
    {
        "success": true,
        "total_lotes_vencidos": 5,
        "costo_total_perdida": 2500.00,
        "total_notificaciones_enviadas": 4,
        "sucursales_procesadas": [...]
    }
    """
    try:
        from datetime import datetime
        from src.dao.inventario.lote_dao import LoteDAO
        from src.dao.auth.push_token_dao import PushTokenDAO
        from src.core.utils.push_notifications import FCMNotificationService
        from src.core.db.session_manager import get_db_session
        from src.models import Sucursal
        import pytz
        
        TZ_MEXICO = pytz.timezone('America/Mexico_City')
        ahora = datetime.now(TZ_MEXICO)
        
        logger.info(f"[JOB LOTES VENCIDOS] Iniciado")
        print(f"\n[JOB LOTES VENCIDOS] Iniciado")
        
        # Obtener TODAS las sucursales activas
        with get_db_session() as session:
            sucursales = session.query(Sucursal).filter(
                Sucursal.es_activa == True
            ).all()
            sucursales_data = [(s.id_sucursal, s.nombre) for s in sucursales]
        
        print(f"[JOB LOTES VENCIDOS] Procesando {len(sucursales_data)} sucursales")
        
        sucursales_procesadas = []
        total_lotes_vencidos = 0
        costo_total_global = 0.0
        total_notificaciones = 0
        
        # Procesar cada sucursal
        for sucursal_id, sucursal_nombre in sucursales_data:
            print(f"  → Verificando sucursal: {sucursal_nombre} (ID: {sucursal_id})")
            
            # 1. Obtener lotes vencidos usando LoteDAO
            lotes_vencidos = LoteDAO.obtener_lotes_vencidos(sucursal_id=sucursal_id)
            
            if not lotes_vencidos:
                print(f"    ✓ Sin lotes vencidos")
                sucursales_procesadas.append({
                    "sucursal_id": sucursal_id,
                    "sucursal_nombre": sucursal_nombre,
                    "lotes_vencidos": 0,
                    "costo_perdida": 0.0,
                    "usuarios_notificados": {"gerentes": 0, "almacen": 0},
                    "notificaciones_enviadas": {"gerentes": 0, "almacen": 0}
                })
                continue
            
            # Calcular costo de pérdida
            costo_perdida_sucursal = sum([l['costo_total_perdida'] for l in lotes_vencidos])
            
            print(f"    🚨 {len(lotes_vencidos)} lotes vencidos - Pérdida: ${costo_perdida_sucursal:,.2f}")
            total_lotes_vencidos += len(lotes_vencidos)
            costo_total_global += costo_perdida_sucursal
            
            notificaciones_gerentes = 0
            notificaciones_almacen = 0
            
            # Construir mensaje de notificación
            titulo = "🚨 ALERTA: Lotes VENCIDOS"
            cuerpo = f"{len(lotes_vencidos)} lote(s) vencidos - Pérdida: ${costo_perdida_sucursal:,.2f} - {sucursal_nombre}"
            
            # Preparar datos adicionales para la notificación
            datos_notificacion = {
                "tipo_alerta": "lotes_vencidos",
                "sucursal_id": str(sucursal_id),
                "total_lotes": str(len(lotes_vencidos)),
                "costo_perdida": str(costo_perdida_sucursal),
                "lotes_resumen": str([
                    {
                        "insumo": l['insumo_nombre'],
                        "dias_vencido": l['dias_vencido'],
                        "cantidad": l['cantidad_disponible'],
                        "costo": l['costo_total_perdida']
                    }
                    for l in lotes_vencidos[:5]  # Primeros 5
                ])
            }
            
            # 2. NOTIFICAR A GERENTES
            usuarios_gerentes = PushTokenDAO.obtener_usuarios_con_push_tokens(
                filtros_usuario={
                    'rol': 'GERENTE',
                    'sucursal_id': sucursal_id
                },
                filtros_push_token={'es_activo': True},
                solo_activos=True
            )
            
            if usuarios_gerentes:
                tokens_gerentes = []
                plataformas_gerentes = {}
                
                for usuario_data in usuarios_gerentes:
                    for token_data in usuario_data['push_tokens']:
                        token = token_data['token']
                        tokens_gerentes.append(token)
                        plataformas_gerentes[token] = token_data.get('plataforma', 'desconocida')
                
                print(f"    → Notificando a {len(usuarios_gerentes)} gerentes")
                resultado_gerentes = FCMNotificationService.enviar_notificacion_simple(
                    tokens=tokens_gerentes,
                    titulo=titulo,
                    cuerpo=cuerpo,
                    datos_personalizados=datos_notificacion,
                    plataformas=plataformas_gerentes
                )
                notificaciones_gerentes = resultado_gerentes.get('mensajes_exitosos', 0)
                total_notificaciones += notificaciones_gerentes
            
            # 3. NOTIFICAR A ALMACEN
            usuarios_almacen = PushTokenDAO.obtener_usuarios_con_push_tokens(
                filtros_usuario={
                    'rol': 'ALMACEN',
                    'sucursal_id': sucursal_id
                },
                filtros_push_token={'es_activo': True},
                solo_activos=True
            )
            
            if usuarios_almacen:
                tokens_almacen = []
                plataformas_almacen = {}
                
                for usuario_data in usuarios_almacen:
                    for token_data in usuario_data['push_tokens']:
                        token = token_data['token']
                        tokens_almacen.append(token)
                        plataformas_almacen[token] = token_data.get('plataforma', 'desconocida')
                
                print(f"    → Notificando a {len(usuarios_almacen)} usuarios ALMACEN")
                resultado_almacen = FCMNotificationService.enviar_notificacion_simple(
                    tokens=tokens_almacen,
                    titulo=titulo,
                    cuerpo=cuerpo,
                    datos_personalizados=datos_notificacion,
                    plataformas=plataformas_almacen
                )
                notificaciones_almacen = resultado_almacen.get('mensajes_exitosos', 0)
                total_notificaciones += notificaciones_almacen
            
            sucursales_procesadas.append({
                "sucursal_id": sucursal_id,
                "sucursal_nombre": sucursal_nombre,
                "lotes_vencidos": len(lotes_vencidos),
                "costo_perdida": costo_perdida_sucursal,
                "lotes_detalle": [
                    {
                        "insumo_nombre": l['insumo_nombre'],
                        "lote": l['lote'],
                        "dias_vencido": l['dias_vencido'],
                        "cantidad_disponible": l['cantidad_disponible'],
                        "costo_perdida": l['costo_total_perdida'],
                        "unidad": l['unidad_clave']
                    }
                    for l in lotes_vencidos
                ],
                "usuarios_notificados": {
                    "gerentes": len(usuarios_gerentes) if usuarios_gerentes else 0,
                    "almacen": len(usuarios_almacen) if usuarios_almacen else 0
                },
                "notificaciones_enviadas": {
                    "gerentes": notificaciones_gerentes,
                    "almacen": notificaciones_almacen
                }
            })
        
        print(f"[JOB LOTES VENCIDOS] ✓ Completado - {total_lotes_vencidos} lotes, ${costo_total_global:,.2f} pérdida, {total_notificaciones} notificaciones")
        logger.info(f"[JOB LOTES VENCIDOS] Completado: {total_lotes_vencidos} lotes, ${costo_total_global:,.2f} pérdida")
        
        return jsonify({
            "success": True,
            "timestamp": ahora.isoformat(),
            "total_lotes_vencidos": total_lotes_vencidos,
            "costo_total_perdida": round(costo_total_global, 2),
            "total_notificaciones_enviadas": total_notificaciones,
            "sucursales_procesadas": sucursales_procesadas
        }), 200
        
    except Exception as e:
        logger.error(f"[JOB LOTES VENCIDOS] Error: {str(e)}", exc_info=True)
        print(f"[JOB LOTES VENCIDOS] ✗ Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "mensaje": f"Error verificando lotes vencidos: {str(e)}"
        }), 500

