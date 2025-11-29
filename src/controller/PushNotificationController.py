"""
PushNotificationController - Endpoints REST para gestión de notificaciones push
Arquitectura n-capas: Controller → Service → DAO → Database
Con documentación Swagger completa para todos los endpoints
"""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.core.utils.push_notifications import (
    FCMNotificationService,
    inicializar_firebase
)
from src.core.utils.stock_alerts import StockAlertDAO, PushTokenDAO
from src.dao.inventario.lote_dao import LoteDAO

logger = logging.getLogger(__name__)

# Blueprint para notificaciones push
bp = Blueprint('push_notifications', __name__, url_prefix='/api/push-notifications')

# Firebase se inicializará de forma perezosa (lazy) cuando sea necesario
# NO se intenta al importar el módulo para evitar problemas en Azure
firebase_init_success = False


def _asegurar_firebase_inicializado():
    """
    Asegura que Firebase esté inicializado antes de enviar notificaciones.
    Se ejecuta de forma perezosa solo cuando se necesita.
    """
    global firebase_init_success
    if not firebase_init_success:
        try:
            firebase_init_success = inicializar_firebase()
            if firebase_init_success:
                logger.info("✅ Firebase inicializado correctamente")
            else:
                logger.error(
                    "❌ Firebase no se inicializó correctamente.\n"
                    "Las notificaciones push NO funcionarán.\n"
                    "Verifica:\n"
                    "- El archivo de credenciales existe en: src/config/push-notifications-cuisine-firebase-adminsdk-fbsvc-fd0c21cd4a.json\n"
                    "- O configura: FIREBASE_CREDENTIALS_PATH o GOOGLE_APPLICATION_CREDENTIALS"
                )
        except Exception as e:
            logger.error(f"❌ Error al inicializar Firebase: {str(e)}", exc_info=True)
            firebase_init_success = False
    return firebase_init_success

# Variable de configuración para Azure Functions (en producción, usar variables de entorno)
AZURE_FUNCTION_SECRET_KEY = "azure-stock-alerts-2025"  # TODO: Usar env variable


# ============================================================================
# POST /api/push-notifications/send-simple - Enviar Notificación Simple
# ============================================================================
@bp.route('/send-simple', methods=['POST'])
@jwt_required()
def enviar_notificacion_simple():
    """
    Envía una notificación simple a múltiples dispositivos.
    Solo ADMIN
    ---
    tags:
      - Push Notifications
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - tokens
            - titulo
            - cuerpo
          properties:
            tokens:
              type: array
              items:
                type: string
              example: ["token1", "token2"]
              description: Lista de push tokens (máximo 500)
            titulo:
              type: string
              example: "Notificación importante"
            cuerpo:
              type: string
              example: "Este es el contenido del mensaje"
            datos_personalizados:
              type: object
              example: {"clave": "valor"}
              description: Datos adicionales (opcional)
            icono:
              type: string
              example: "ic_notification"
              description: URL del icono (opcional)
    responses:
      200:
        description: Notificación enviada
        schema:
          type: object
          properties:
            success:
              type: boolean
            mensajes_exitosos:
              type: integer
            mensajes_fallidos:
              type: integer
            tokens_fallidos:
              type: array
      400:
        description: Datos inválidos
    """
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        tokens = data.get('tokens', [])
        titulo = data.get('titulo')
        cuerpo = data.get('cuerpo')
        
        if not tokens or not titulo or not cuerpo:
            return jsonify({
                'success': False,
                'error': 'MISSING_REQUIRED_FIELDS',
                'message': 'Debe proporcionar tokens, titulo y cuerpo'
            }), 400
        
        if not isinstance(tokens, list):
            return jsonify({
                'success': False,
                'error': 'INVALID_TOKENS_FORMAT',
                'message': 'tokens debe ser un array'
            }), 400
        
        datos_personalizados = data.get('datos_personalizados')
        icono = data.get('icono')
        
        # Asegurar que Firebase está inicializado
        if not _asegurar_firebase_inicializado():
            return jsonify({
                'success': False,
                'error': 'FIREBASE_NOT_INITIALIZED',
                'message': 'Firebase no está inicializado. Verifica las credenciales.'
            }), 500
        
        # Enviar notificación
        resultado = FCMNotificationService.enviar_notificacion_simple(
            tokens=tokens,
            titulo=titulo,
            cuerpo=cuerpo,
            datos_personalizados=datos_personalizados,
            icono=icono
        )
        
        logger.info(f"Notificación simple enviada por usuario {get_jwt_identity()}: {resultado['mensajes_exitosos']} exitosas")
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en enviar_notificacion_simple: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# POST /api/push-notifications/stock-bajo - Enviar Alerta de Stock Bajo
# ============================================================================
@bp.route('/stock-bajo', methods=['POST'])
def enviar_alerta_stock_bajo():
    """
    Envía notificación personalizada para alertas de stock bajo.
    Solo ADMIN o GERENTE
    ---
    tags:
      - Push Notifications
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - insumo_nombre
            - cantidad_actual
            - minimo_stock
            - unidad
            - tokens
          properties:
            insumo_nombre:
              type: string
              example: "Harina Premium"
            cantidad_actual:
              type: number
              example: 5.0
            minimo_stock:
              type: number
              example: 10.0
            unidad:
              type: string
              example: "kg"
            tokens:
              type: array
              items:
                type: string
              example: ["token1", "token2"]
            sucursal_nombre:
              type: string
              example: "Sucursal Centro"
              description: Nombre de la sucursal (opcional)
    responses:
      200:
        description: Alerta enviada
      400:
        description: Datos inválidos
    """
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        insumo_nombre = data.get('insumo_nombre')
        cantidad_actual = data.get('cantidad_actual')
        minimo_stock = data.get('minimo_stock')
        unidad = data.get('unidad')
        tokens = data.get('tokens', [])
        
        if not all([insumo_nombre, cantidad_actual, minimo_stock, unidad, tokens]):
            return jsonify({
                'success': False,
                'error': 'MISSING_REQUIRED_FIELDS',
                'message': 'Faltan campos requeridos'
            }), 400
        
        sucursal_nombre = data.get('sucursal_nombre')
        
        # Asegurar que Firebase está inicializado
        if not _asegurar_firebase_inicializado():
            return jsonify({
                'success': False,
                'error': 'FIREBASE_NOT_INITIALIZED',
                'message': 'Firebase no está inicializado. Verifica las credenciales.'
            }), 500
        
        # Enviar alerta
        resultado = FCMNotificationService.enviar_notificacion_stock_bajo(
            insumo_nombre=insumo_nombre,
            cantidad_actual=cantidad_actual,
            minimo_stock=minimo_stock,
            unidad=unidad,
            tokens=tokens,
            sucursal_nombre=sucursal_nombre
        )
        
        logger.info(f"Alerta stock bajo enviada: {insumo_nombre}")
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en enviar_alerta_stock_bajo: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# POST /api/push-notifications/stock-bajo-por-sucursal - Enviar Alertas para Sucursal
# ============================================================================
@bp.route('/stock-bajo-por-sucursal', methods=['POST'])
@jwt_required()
def enviar_alertas_stock_bajo_sucursal():
    """
    Obtiene insumos con stock bajo de una sucursal y envía notificación a gerentes/admins.
    Solo ADMIN o GERENTE de la sucursal
    ---
    tags:
      - Push Notifications
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - sucursal_id
          properties:
            sucursal_id:
              type: integer
              example: 1
              description: ID de la sucursal
            enviar_a_grupo:
              type: string
              enum: ["gerentes", "admins", "all"]
              example: "gerentes"
              default: "gerentes"
              description: A quién enviar la notificación
    responses:
      200:
        description: Alertas enviadas
        schema:
          type: object
          properties:
            success:
              type: boolean
            insumos_bajo_stock:
              type: integer
            usuarios_notificados:
              type: integer
            notificaciones_enviadas:
              type: integer
      400:
        description: Datos inválidos
    """
    try:
        data = request.get_json()
        
        sucursal_id = data.get('sucursal_id')
        if not sucursal_id:
            return jsonify({
                'success': False,
                'error': 'MISSING_SUCURSAL_ID',
                'message': 'Debe proporcionar sucursal_id'
            }), 400
        
        enviar_a_grupo = data.get('enviar_a_grupo', 'gerentes').lower()
        
        # 1. Obtener insumos con stock bajo
        insumos_bajo_stock = StockAlertDAO.obtener_insumos_stock_bajo(
            sucursal_id=sucursal_id,
            solo_activos=True
        )
        
        if not insumos_bajo_stock:
            return jsonify({
                'success': True,
                'message': 'No hay insumos con stock bajo',
                'insumos_bajo_stock': 0,
                'usuarios_notificados': 0,
                'notificaciones_enviadas': 0
            }), 200
        
        # 2. Obtener usuarios y push tokens según el grupo
        if enviar_a_grupo == 'gerentes':
            usuarios_push = PushTokenDAO.obtener_usuarios_con_push_tokens(
                filtros_usuario={'rol': 'GERENTE', 'sucursal_id': sucursal_id},
                filtros_push_token={'es_activo': True}
            )
        elif enviar_a_grupo == 'admins':
            usuarios_push = PushTokenDAO.obtener_usuarios_con_push_tokens(
                filtros_usuario={'rol': 'ADMIN'},
                filtros_push_token={'es_activo': True}
            )
        elif enviar_a_grupo == 'all':
            usuarios_push = PushTokenDAO.obtener_usuarios_con_push_tokens(
                filtros_usuario={'sucursal_id': sucursal_id},
                filtros_push_token={'es_activo': True}
            )
        else:
            return jsonify({
                'success': False,
                'error': 'INVALID_GRUPO',
                'message': 'enviar_a_grupo debe ser: gerentes, admins o all'
            }), 400
        
        if not usuarios_push:
            return jsonify({
                'success': True,
                'message': f'No hay usuarios activos con push tokens en el grupo {enviar_a_grupo}',
                'insumos_bajo_stock': len(insumos_bajo_stock),
                'usuarios_notificados': 0,
                'notificaciones_enviadas': 0
            }), 200
        
        # 3. Extraer todos los tokens
        todos_tokens = []
        for usuario_data in usuarios_push:
            for token_info in usuario_data['push_tokens']:
                todos_tokens.append(token_info['token'])
        
        # Asegurar que Firebase está inicializado
        if not _asegurar_firebase_inicializado():
            return jsonify({
                'success': False,
                'error': 'FIREBASE_NOT_INITIALIZED',
                'message': 'Firebase no está inicializado. Verifica las credenciales.'
            }), 500
        
        # 4. Enviar notificación de múltiples insumos
        resultado_envio = FCMNotificationService.enviar_notificacion_multiple_insumos(
            insumos_bajo_stock=insumos_bajo_stock,
            tokens=todos_tokens
        )
        
        return jsonify({
            'success': resultado_envio['success'],
            'insumos_bajo_stock': len(insumos_bajo_stock),
            'usuarios_notificados': len(usuarios_push),
            'notificaciones_enviadas': resultado_envio['mensajes_exitosos'],
            'notificaciones_fallidas': resultado_envio['mensajes_fallidos'],
            'tokens_fallidos_count': len(resultado_envio['tokens_fallidos']),
            'insumos': [
                {
                    'nombre': ins['nombre'],
                    'cantidad_actual': ins['cantidad_actual'],
                    'minimo_stock': ins['minimo_stock'],
                    'unidad': ins['unidad_clave']
                }
                for ins in insumos_bajo_stock
            ]
        }), 200
        
    except Exception as e:
        logger.error(f"Error en enviar_alertas_stock_bajo_sucursal: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# POST /api/push-notifications/consultar-usuarios - Consultar Usuarios con Push Tokens
# ============================================================================
@bp.route('/consultar-usuarios', methods=['POST'])
@jwt_required()
def consultar_usuarios_push():
    """
    Consulta usuarios y extrae sus push tokens con filtros dinámicos.
    Solo ADMIN
    ---
    tags:
      - Push Notifications
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            filtros_usuario:
              type: object
              description: Filtros para usuario (id_usuario, email, nombre, rol, sucursal_id, es_cliente)
              example:
                rol: "GERENTE"
                sucursal_id: 1
            filtros_push_token:
              type: object
              description: Filtros para push token (plataforma, es_activo)
              example:
                plataforma: "android"
                es_activo: true
            solo_activos:
              type: boolean
              example: true
              default: true
    responses:
      200:
        description: Usuarios con push tokens encontrados
        schema:
          type: object
          properties:
            success:
              type: boolean
            cantidad_usuarios:
              type: integer
            data:
              type: array
              items:
                type: object
                properties:
                  usuario:
                    type: object
                  push_tokens:
                    type: array
      400:
        description: Datos inválidos
    """
    try:
        data = request.get_json()
        
        filtros_usuario = data.get('filtros_usuario')
        filtros_push_token = data.get('filtros_push_token')
        solo_activos = data.get('solo_activos', True)
        
        # Consultar usuarios con push tokens
        usuarios = PushTokenDAO.obtener_usuarios_con_push_tokens(
            filtros_usuario=filtros_usuario,
            filtros_push_token=filtros_push_token,
            solo_activos=solo_activos
        )
        
        return jsonify({
            'success': True,
            'cantidad_usuarios': len(usuarios),
            'filtros_aplicados': {
                'usuario': filtros_usuario,
                'push_token': filtros_push_token,
                'solo_activos': solo_activos
            },
            'data': usuarios
        }), 200
        
    except Exception as e:
        logger.error(f"Error en consultar_usuarios_push: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# POST /api/push-notifications/verificar-stock-todas-sucursales
# ============================================================================
@bp.route('/verificar-stock-todas-sucursales', methods=['POST'])
def verificar_stock_todas_sucursales():
    """
    Verifica stock bajo en TODAS las sucursales y notifica a GERENTES y COMPRAS.
    
    Endpoint optimizado para Azure Functions (sin autenticación JWT).
    
    Flujo:
    1. Para cada sucursal activa
    2. Obtiene insumos con stock bajo
    3. Notifica a GERENTES de esa sucursal
    4. Notifica a usuarios con rol COMPRAS de esa sucursal
    5. Retorna resumen de verificaciones
    
    ---
    tags:
      - Push Notifications
    parameters:
      - in: body
        name: body
        required: false
        schema:
          type: object
          properties:
            secret_key:
              type: string
              example: "azure-stock-alerts-2025"
              description: Clave secreta para autorizar Azure Functions (requerida)
    responses:
      200:
        description: Verificación completada
        schema:
          type: object
          properties:
            success:
              type: boolean
            timestamp:
              type: string
            sucursales_procesadas:
              type: array
              items:
                type: object
                properties:
                  sucursal_id:
                    type: integer
                  insumos_bajo_stock:
                    type: integer
                  usuarios_notificados:
                    type: object
                    properties:
                      gerentes:
                        type: integer
                      compras:
                        type: integer
                  notificaciones_enviadas:
                    type: object
                    properties:
                      gerentes:
                        type: integer
                      compras:
                        type: integer
            total_insumos_bajo:
              type: integer
            total_notificaciones_enviadas:
              type: integer
      401:
        description: Clave secreta inválida
      500:
        description: Error interno
    """
    try:        
        from datetime import datetime
        from zoneinfo import ZoneInfo
        tz_mexico = ZoneInfo("America/Mexico_City")
        
        # Asegurar que Firebase está inicializado ANTES de procesar
        if not _asegurar_firebase_inicializado():
            return jsonify({
                'success': False,
                'error': 'FIREBASE_NOT_INITIALIZED',
                'message': 'Firebase no está inicializado. Verifica las credenciales.'
            }), 500
        
        logger.info(f"[{datetime.now(tz_mexico)}] Iniciando verificación de stock en todas sucursales")
        
        # Obtener todas las sucursales activas
        from src.core.db.session_manager import get_db_session
        from src.models import Sucursal
        
        with get_db_session() as session:
            sucursales = session.query(Sucursal).filter(
                Sucursal.es_activa == True
            ).all()
            sucursal_ids = [s.id_sucursal for s in sucursales]
        
        logger.info(f"Procesando {len(sucursal_ids)} sucursales: {sucursal_ids}")
        
        sucursales_procesadas = []
        total_insumos_bajo = 0
        total_notificaciones = 0
        
        # Procesar cada sucursal
        for sucursal_id in sucursal_ids:
            logger.info(f"Verificando sucursal {sucursal_id}")
            
            # 1. Obtener insumos con stock bajo
            insumos_bajo_stock = StockAlertDAO.obtener_insumos_stock_bajo(
                sucursal_id=sucursal_id,
                solo_activos=True
            )
            
            if not insumos_bajo_stock:
                logger.info(f"Sucursal {sucursal_id}: Sin insumos bajo stock")
                sucursales_procesadas.append({
                    "sucursal_id": sucursal_id,
                    "insumos_bajo_stock": 0,
                    "usuarios_notificados": {"gerentes": 0, "compras": 0},
                    "notificaciones_enviadas": {"gerentes": 0, "compras": 0}
                })
                continue
            
            logger.warning(f"Sucursal {sucursal_id}: {len(insumos_bajo_stock)} insumos bajo stock")
            total_insumos_bajo += len(insumos_bajo_stock)
            
            notificaciones_gerentes = 0
            notificaciones_compras = 0
            
            # 2. NOTIFICAR A GERENTES
            logger.info(f"Sucursal {sucursal_id}: Obteniendo gerentes...")
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
                plataformas_gerentes = {}  # token -> plataforma
                
                for usuario_data in usuarios_gerentes:
                    for token_data in usuario_data['push_tokens']:
                        token = token_data['token']
                        tokens_gerentes.append(token)
                        plataformas_gerentes[token] = token_data.get('plataforma', 'desconocida')
                
                logger.info(f"Sucursal {sucursal_id}: Enviando alerta a {len(usuarios_gerentes)} gerentes ({len(tokens_gerentes)} tokens)")
                resultado_gerentes = FCMNotificationService.enviar_notificacion_multiple_insumos(
                    insumos_bajo_stock=insumos_bajo_stock,
                    tokens=tokens_gerentes,
                    plataformas=plataformas_gerentes,
                    sucursal_nombre=f"Sucursal {sucursal_id} - ALERTA GERENTES"
                )
                notificaciones_gerentes = resultado_gerentes['mensajes_exitosos']
                total_notificaciones += notificaciones_gerentes
                logger.info(f"Sucursal {sucursal_id}: {notificaciones_gerentes} notificaciones a gerentes")
            
            # 3. NOTIFICAR A COMPRAS
            logger.info(f"Sucursal {sucursal_id}: Obteniendo usuarios de COMPRAS...")
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
                plataformas_compras = {}  # token -> plataforma
                
                for usuario_data in usuarios_compras:
                    for token_data in usuario_data['push_tokens']:
                        token = token_data['token']
                        tokens_compras.append(token)
                        plataformas_compras[token] = token_data.get('plataforma', 'desconocida')
                
                logger.info(f"Sucursal {sucursal_id}: Enviando alerta a {len(usuarios_compras)} usuarios COMPRAS ({len(tokens_compras)} tokens)")
                resultado_compras = FCMNotificationService.enviar_notificacion_multiple_insumos(
                    insumos_bajo_stock=insumos_bajo_stock,
                    tokens=tokens_compras,
                    plataformas=plataformas_compras,
                    sucursal_nombre=f"Sucursal {sucursal_id} - ALERTA COMPRAS"
                )
                notificaciones_compras = resultado_compras['mensajes_exitosos']
                total_notificaciones += notificaciones_compras
                logger.info(f"Sucursal {sucursal_id}: {notificaciones_compras} notificaciones a compras")
            
            sucursales_procesadas.append({
                "sucursal_id": sucursal_id,
                "insumos_bajo_stock": len(insumos_bajo_stock),
                "usuarios_notificados": {
                    "gerentes": len(usuarios_gerentes),
                    "compras": len(usuarios_compras)
                },
                "notificaciones_enviadas": {
                    "gerentes": notificaciones_gerentes,
                    "compras": notificaciones_compras
                }
            })
        
        logger.info(f"Verificación completada: {total_insumos_bajo} insumos bajo stock, {total_notificaciones} notificaciones totales")
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now(tz_mexico).isoformat(),
            'sucursales_procesadas': sucursales_procesadas,
            'total_insumos_bajo': total_insumos_bajo,
            'total_notificaciones_enviadas': total_notificaciones
        }), 200
        
    except Exception as e:
        logger.error(f"Error en verificar_stock_todas_sucursales: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# POST /api/push-notifications/verificar-lotes-por-vencer-todas-sucursales
# ============================================================================
@bp.route('/verificar-lotes-por-vencer-todas-sucursales', methods=['POST'])
def verificar_lotes_por_vencer_todas_sucursales():
    """
    Verifica lotes próximos a vencer en TODAS las sucursales y notifica a GERENTES y COMPRAS.
    
    Endpoint optimizado para Azure Functions (sin autenticación JWT).
    
    Flujo:
    1. Para cada sucursal activa
    2. Obtiene lotes próximos a vencer (default 30 días)
    3. Notifica a GERENTES de esa sucursal
    4. Notifica a usuarios con rol COMPRAS de esa sucursal
    5. Retorna resumen de verificaciones
    
    ---
    tags:
      - Push Notifications
    parameters:
      - in: body
        name: body
        required: false
        schema:
          type: object
          properties:
            dias_proximidad:
              type: integer
              example: 30
              default: 30
              description: Días de anticipación para considerar lote como próximo a vencer
    responses:
      200:
        description: Verificación completada
        schema:
          type: object
          properties:
            success:
              type: boolean
            timestamp:
              type: string
            dias_proximidad:
              type: integer
            sucursales_procesadas:
              type: array
              items:
                type: object
                properties:
                  sucursal_id:
                    type: integer
                  lotes_por_vencer:
                    type: integer
                  lotes_criticos:
                    type: integer
                  usuarios_notificados:
                    type: object
                  notificaciones_enviadas:
                    type: object
            total_lotes_por_vencer:
              type: integer
            total_notificaciones_enviadas:
              type: integer
      500:
        description: Error interno
    """
    try:
        from datetime import datetime
        from zoneinfo import ZoneInfo
        tz_mexico = ZoneInfo("America/Mexico_City")
        
        data = request.get_json() or {}
        dias_proximidad = data.get('dias_proximidad', 30)
        
        # Asegurar que Firebase está inicializado ANTES de procesar
        if not _asegurar_firebase_inicializado():
            return jsonify({
                'success': False,
                'error': 'FIREBASE_NOT_INITIALIZED',
                'message': 'Firebase no está inicializado. Verifica las credenciales.'
            }), 500
        
        logger.info(f"[{datetime.now(tz_mexico)}] Iniciando verificación de lotes por vencer (días: {dias_proximidad})")
        
        # Obtener todas las sucursales activas
        from src.core.db.session_manager import get_db_session
        from src.models import Sucursal
        
        with get_db_session() as session:
            sucursales = session.query(Sucursal).filter(
                Sucursal.es_activa == True
            ).all()
            sucursales_data = [(s.id_sucursal, s.nombre) for s in sucursales]
        
        logger.info(f"Procesando {len(sucursales_data)} sucursales")
        
        sucursales_procesadas = []
        total_lotes_por_vencer = 0
        total_notificaciones = 0
        
        # Procesar cada sucursal
        for sucursal_id, sucursal_nombre in sucursales_data:
            logger.info(f"Verificando lotes en sucursal {sucursal_id}")
            
            # 1. Obtener lotes próximos a vencer
            lotes_por_vencer = LoteDAO.obtener_lotes_proximos_a_vencer(
                sucursal_id=sucursal_id,
                dias_proximidad=dias_proximidad
            )
            
            if not lotes_por_vencer:
                logger.info(f"Sucursal {sucursal_id}: Sin lotes próximos a vencer")
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
            
            logger.warning(f"Sucursal {sucursal_id}: {len(lotes_por_vencer)} lotes por vencer ({len(lotes_criticos)} críticos)")
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
            
            # Preparar datos adicionales
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
                
                logger.info(f"Sucursal {sucursal_id}: Enviando alerta lotes a {len(usuarios_gerentes)} gerentes")
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
                
                logger.info(f"Sucursal {sucursal_id}: Enviando alerta lotes a {len(usuarios_compras)} usuarios COMPRAS")
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
        
        logger.info(f"Verificación lotes completada: {total_lotes_por_vencer} lotes por vencer, {total_notificaciones} notificaciones")
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now(tz_mexico).isoformat(),
            'dias_proximidad': dias_proximidad,
            'sucursales_procesadas': sucursales_procesadas,
            'total_lotes_por_vencer': total_lotes_por_vencer,
            'total_notificaciones_enviadas': total_notificaciones
        }), 200
        
    except Exception as e:
        logger.error(f"Error en verificar_lotes_por_vencer_todas_sucursales: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# POST /api/push-notifications/verificar-campanias-vencidas
# ============================================================================
@bp.route('/verificar-campanias-vencidas', methods=['POST'])
def verificar_campanias_vencidas():
    """
    Verifica cupones y campañas vencidas, actualiza estatus y notifica a MARKETING.
    
    Endpoint optimizado para Azure Functions (sin autenticación JWT).
    
    Flujo:
    1. Busca cupones con fecha_vigencia < NOW() y estatus = 0 (no usado)
    2. Marca esos cupones con estatus = 2 (vencido)
    3. Verifica campañas activas sin cupones disponibles
    4. Desactiva campañas que ya no tienen cupones vigentes
    5. Notifica a usuarios con rol MARKETING sobre los cambios
    
    Estatus de CampaniaUsuario:
        - 0: No usado (disponible)
        - 1: Usado
        - 2: Vencido
    
    Estatus de Campania:
        - 0: Inactiva
        - 1: Activa
    
    ---
    tags:
      - Push Notifications
    parameters:
      - in: body
        name: body
        required: false
        schema:
          type: object
          properties:
            solo_verificar:
              type: boolean
              default: false
              description: Si true, solo verifica sin actualizar estatus
    responses:
      200:
        description: Verificación completada
        schema:
          type: object
          properties:
            success:
              type: boolean
            timestamp:
              type: string
            cupones_vencidos:
              type: object
              properties:
                total_encontrados:
                  type: integer
                total_actualizados:
                  type: integer
                detalle:
                  type: array
            campanias_desactivadas:
              type: object
              properties:
                total:
                  type: integer
                detalle:
                  type: array
            notificaciones_marketing:
              type: object
              properties:
                usuarios_notificados:
                  type: integer
                notificaciones_enviadas:
                  type: integer
      500:
        description: Error interno
    """
    try:
        from datetime import datetime
        from zoneinfo import ZoneInfo
        from src.dao.marketing.campania_dao import CampaniaDAO
        
        tz_mexico = ZoneInfo("America/Mexico_City")
        
        data = request.get_json() or {}
        solo_verificar = data.get('solo_verificar', False)
        
        logger.info(f"[{datetime.now(tz_mexico)}] Iniciando verificación de campañas vencidas (solo_verificar={solo_verificar})")
        
        # 1. Obtener cupones vencidos no marcados
        cupones_vencidos = CampaniaDAO.obtener_cupones_vencidos_no_marcados()
        
        cupones_actualizados = 0
        campanias_afectadas = []
        
        # 2. Marcar cupones como vencidos (si no es solo verificación)
        if not solo_verificar and cupones_vencidos:
            resultado_cupones = CampaniaDAO.marcar_cupones_vencidos()
            cupones_actualizados = resultado_cupones['cupones_actualizados']
            campanias_afectadas = resultado_cupones['campanias_afectadas']
            logger.info(f"Cupones marcados como vencidos: {cupones_actualizados}")
        
        # 3. Verificar campañas sin cupones activos
        campanias_sin_cupones = CampaniaDAO.verificar_campanias_sin_cupones_activos()
        
        campanias_desactivadas = []
        
        # 4. Desactivar campañas sin cupones (si no es solo verificación)
        if not solo_verificar and campanias_sin_cupones:
            resultado_campanias = CampaniaDAO.desactivar_campanias_sin_cupones()
            campanias_desactivadas = resultado_campanias['detalle']
            logger.info(f"Campañas desactivadas: {len(campanias_desactivadas)}")
        
        # 5. Notificar a MARKETING si hay cambios
        notificaciones_enviadas = 0
        usuarios_marketing_notificados = 0
        
        if (cupones_actualizados > 0 or len(campanias_desactivadas) > 0) and not solo_verificar:
            # Asegurar que Firebase está inicializado
            if _asegurar_firebase_inicializado():
                # Obtener usuarios de MARKETING con push tokens
                usuarios_marketing = PushTokenDAO.obtener_usuarios_con_push_tokens(
                    filtros_usuario={'rol': 'MARKETING'},
                    filtros_push_token={'es_activo': True},
                    solo_activos=True
                )
                
                if usuarios_marketing:
                    tokens_marketing = []
                    plataformas_marketing = {}
                    
                    for usuario_data in usuarios_marketing:
                        for token_data in usuario_data['push_tokens']:
                            token = token_data['token']
                            tokens_marketing.append(token)
                            plataformas_marketing[token] = token_data.get('plataforma', 'desconocida')
                    
                    usuarios_marketing_notificados = len(usuarios_marketing)
                    
                    # Construir mensaje
                    titulo = "📊 Actualización de Campañas"
                    partes_mensaje = []
                    
                    if cupones_actualizados > 0:
                        partes_mensaje.append(f"{cupones_actualizados} cupón(es) vencido(s)")
                    
                    if len(campanias_desactivadas) > 0:
                        partes_mensaje.append(f"{len(campanias_desactivadas)} campaña(s) desactivada(s)")
                    
                    cuerpo = " | ".join(partes_mensaje)
                    
                    datos_notificacion = {
                        "tipo_alerta": "campanias_vencidas",
                        "cupones_vencidos": str(cupones_actualizados),
                        "campanias_desactivadas": str(len(campanias_desactivadas)),
                        "timestamp": datetime.now(tz_mexico).isoformat()
                    }
                    
                    logger.info(f"Enviando notificación a {len(tokens_marketing)} tokens de MARKETING")
                    
                    resultado_notif = FCMNotificationService.enviar_notificacion_simple(
                        tokens=tokens_marketing,
                        titulo=titulo,
                        cuerpo=cuerpo,
                        datos_personalizados=datos_notificacion,
                        plataformas=plataformas_marketing
                    )
                    notificaciones_enviadas = resultado_notif.get('mensajes_exitosos', 0)
        
        respuesta = {
            'success': True,
            'timestamp': datetime.now(tz_mexico).isoformat(),
            'modo': 'verificacion' if solo_verificar else 'actualizacion',
            'cupones_vencidos': {
                'total_encontrados': len(cupones_vencidos),
                'total_actualizados': cupones_actualizados,
                'detalle': cupones_vencidos[:20] if cupones_vencidos else []  # Max 20 para respuesta
            },
            'campanias_sin_cupones': {
                'total_encontradas': len(campanias_sin_cupones),
                'detalle': campanias_sin_cupones
            },
            'campanias_desactivadas': {
                'total': len(campanias_desactivadas),
                'detalle': campanias_desactivadas
            },
            'notificaciones_marketing': {
                'usuarios_notificados': usuarios_marketing_notificados,
                'notificaciones_enviadas': notificaciones_enviadas
            }
        }
        
        logger.info(f"Verificación completada: {len(cupones_vencidos)} cupones vencidos, {len(campanias_desactivadas)} campañas desactivadas")
        
        return jsonify(respuesta), 200
        
    except Exception as e:
        logger.error(f"Error en verificar_campanias_vencidas: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500
