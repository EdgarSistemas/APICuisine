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
