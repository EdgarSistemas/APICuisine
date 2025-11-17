"""
push_notifications.py - Utilidades para envío de notificaciones push vía Firebase Cloud Messaging

Funciones para:
1. Inicializar Firebase Admin SDK
2. Enviar notificaciones a múltiples dispositivos
3. Manejo de errores y reintentos
"""

import logging
import os
import json
import requests
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from zoneinfo import ZoneInfo

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("Firebase Admin SDK no está instalado. Las notificaciones no funcionarán.")

logger = logging.getLogger(__name__)

# Configuración global de Firebase
_firebase_initialized = False
_credentials_path = None


def inicializar_firebase(credentials_path: Optional[str] = None) -> bool:
    """
    Inicializa Firebase Admin SDK con el archivo de credenciales.
    
    Intenta cargar credenciales en este orden:
    1. Ruta explícita pasada como parámetro
    2. Variable de entorno FIREBASE_CREDENTIALS_PATH
    3. Variable de entorno GOOGLE_APPLICATION_CREDENTIALS
    4. Ruta por defecto en src/config/
    
    Args:
        credentials_path (str): Ruta al archivo JSON de credenciales de Firebase (opcional)
    
    Returns:
        bool: True si se inicializó correctamente, False en caso de error
        
    Example:
        inicializar_firebase('/ruta/a/firebase-adminsdk.json')
    """
    global _firebase_initialized, _credentials_path
    
    if not FIREBASE_AVAILABLE:
        logger.error("❌ Firebase Admin SDK no está instalado")
        return False
    
    if _firebase_initialized:
        logger.info("✅ Firebase ya estaba inicializado")
        return True
    
    try:
        # Determinar ruta de credenciales (orden de prioridad)
        final_credentials_path = None
        
        # 1. Parámetro explícito
        if credentials_path and os.path.exists(credentials_path):
            final_credentials_path = credentials_path
            logger.debug(f"Usando credentials_path del parámetro: {credentials_path}")
        
        # 2. Variable de entorno FIREBASE_CREDENTIALS_PATH
        if not final_credentials_path:
            env_path = os.environ.get('FIREBASE_CREDENTIALS_PATH')
            if env_path and os.path.exists(env_path):
                final_credentials_path = env_path
                logger.debug(f"Usando FIREBASE_CREDENTIALS_PATH: {env_path}")
        
        # 3. Variable de entorno GOOGLE_APPLICATION_CREDENTIALS
        if not final_credentials_path:
            env_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
            if env_path and os.path.exists(env_path):
                final_credentials_path = env_path
                logger.debug(f"Usando GOOGLE_APPLICATION_CREDENTIALS: {env_path}")
        
        # 4. Ruta por defecto en src/config/
        if not final_credentials_path:
            default_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'config',
                'push-notifications-cuisine-firebase-adminsdk-fbsvc-fd0c21cd4a.json'
            )
            if os.path.exists(default_path):
                final_credentials_path = default_path
                logger.debug(f"Usando ruta por defecto: {default_path}")
        
        if not final_credentials_path:
            logger.error(
                "❌ No se encontró archivo de credenciales de Firebase.\n"
                "   Opciones:\n"
                "   1. Asegurar que el archivo existe en: src/config/push-notifications-cuisine-firebase-adminsdk-fbsvc-fd0c21cd4a.json\n"
                "   2. O configurar variable de entorno: FIREBASE_CREDENTIALS_PATH=/ruta/al/archivo.json\n"
                "   3. O configurar variable de entorno: GOOGLE_APPLICATION_CREDENTIALS=/ruta/al/archivo.json"
            )
            return False
        
        # Inicializar Firebase
        cred = credentials.Certificate(final_credentials_path)
        firebase_admin.initialize_app(cred)
        
        _firebase_initialized = True
        _credentials_path = final_credentials_path
        logger.info(f"✅ Firebase inicializado correctamente desde: {final_credentials_path}")
        return True
        
    except FileNotFoundError as e:
        logger.error(f"❌ Archivo de credenciales no encontrado: {str(e)}")
        return False
    except ValueError as e:
        logger.error(f"❌ Error al procesar credenciales JSON: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Error inesperado inicializando Firebase: {str(e)}", exc_info=True)
        return False


class FCMNotificationService:
    """Servicio para envío de notificaciones push vía Firebase Cloud Messaging"""
    
    @staticmethod
    def enviar_notificacion_simple(
        tokens: List[str],
        titulo: str,
        cuerpo: str,
        datos_personalizados: Optional[Dict[str, str]] = None,
        icono: Optional[str] = None,
        imagen: Optional[str] = None,
        plataformas: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Envía una notificación a uno o múltiples dispositivos.
        
        Args:
            tokens (List[str]): Lista de push tokens (máximo 500 por llamada)
            titulo (str): Título de la notificación
            cuerpo (str): Cuerpo del mensaje
            datos_personalizados (Dict): Datos adicionales para enviar (opcional)
            icono (str): URL del icono (opcional)
            imagen (str): URL de la imagen de la notificación (opcional)
            plataformas (Dict): Mapeo token -> plataforma ej: {'token1': 'web', 'token2': 'android'} (opcional)
            
        Returns:
            Dict con:
            {
                "success": bool,
                "mensajes_exitosos": int,
                "mensajes_fallidos": int,
                "tokens_fallidos": List[str],
                "detalles_error": List[Dict],
                "timestamp": str (ISO format)
            }
            
        Example:
            resultado = FCMNotificationService.enviar_notificacion_simple(
                tokens=['token1', 'token2'],
                titulo='Stock Bajo',
                cuerpo='Harina: 5kg disponibles',
                datos_personalizados={'insumo_id': '123'}
            )
        """
        if not _firebase_initialized:
            logger.error("Firebase no está inicializado")
            return {
                "success": False,
                "error": "Firebase no inicializado",
                "mensajes_exitosos": 0,
                "mensajes_fallidos": len(tokens),
                "tokens_fallidos": tokens,
                "detalles_error": [{"mensaje": "Firebase no inicializado"}],
                "timestamp": datetime.now(ZoneInfo("America/Mexico_City")).isoformat()
            }
        
        if not tokens:
            logger.warning("No hay tokens para enviar notificaciones")
            return {
                "success": False,
                "error": "Lista de tokens vacía",
                "mensajes_exitosos": 0,
                "mensajes_fallidos": 0,
                "tokens_fallidos": [],
                "detalles_error": [],
                "timestamp": datetime.now(ZoneInfo("America/Mexico_City")).isoformat()
            }
        
        if len(tokens) > 500:
            logger.warning(f"Se proporcionaron {len(tokens)} tokens. FCM permite máximo 500 por llamada.")
            # Procesar en lotes de 500
            return FCMNotificationService._enviar_en_lotes(
                tokens, titulo, cuerpo, datos_personalizados, icono, imagen, plataformas
            )
        
        try:
            # Enviar a múltiples dispositivos
            mensajes_exitosos = 0
            mensajes_fallidos = 0
            tokens_fallidos = []
            detalles_error = []
            
            # Construir notificación una sola vez
            notificacion = messaging.Notification(
                title=titulo,
                body=cuerpo,
                image=imagen
            )
            
            # Enviar a cada token individualmente con manejo de errores robusto
            for token in tokens:
                try:
                    # Detectar plataforma del token
                    plataforma = None
                    if plataformas and token in plataformas:
                        plataforma = plataformas[token]
                    
                    # Construir mensaje adaptado a la plataforma
                    msg_kwargs = {
                        "token": token,
                        "notification": notificacion,
                        "data": datos_personalizados or {}
                    }
                    
                    # Para tokens web, agregar configuración específica
                    if plataforma == 'web':
                        # Webpush config recomendado para PWA
                        webpush_config = messaging.WebpushConfig(
                            headers={
                                "TTL": "3600"  # 1 hora
                            },
                            notification=messaging.WebpushNotification(
                                title=titulo,
                                body=cuerpo,
                                icon=icono or ""
                            )
                        )
                        msg_kwargs["webpush"] = webpush_config
                        logger.info(f"Token web detectado: {token[:30]}... - Usando WebpushConfig")
                    
                    msg = messaging.Message(**msg_kwargs)
                    
                    # Log detallado del token para debugging
                    logger.info(f"Enviando a token {token[:30]}... (plataforma: {plataforma or 'desconocida'}, longitud: {len(token)} chars)")
                    
                    resp = messaging.send(msg, dry_run=False)
                    logger.info(f"Mensaje enviado exitosamente: {resp}")
                    mensajes_exitosos += 1
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.warning(f"Token {token[:30]}... (plataforma: {plataforma or 'desconocida'}) falló: {error_msg}")
                    mensajes_fallidos += 1
                    tokens_fallidos.append(token)
                    detalles_error.append({
                        "token": token[:30] + "...",
                        "plataforma": plataforma or "desconocida",
                        "error": error_msg
                    })
            
            # Si al menos uno fue exitoso, marcar como success
            resultado = {
                "success": mensajes_exitosos > 0,
                "mensajes_exitosos": mensajes_exitosos,
                "mensajes_fallidos": mensajes_fallidos,
                "tokens_fallidos": tokens_fallidos,
                "detalles_error": detalles_error,
                 "timestamp": datetime.now(ZoneInfo("America/Mexico_City")).isoformat()
            }
            
            logger.info(f"Notificaciones: {mensajes_exitosos} exitosas, {mensajes_fallidos} fallidas")
            return resultado
            
        except Exception as e:
            logger.error(f"Error enviando notificación: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "mensajes_exitosos": 0,
                "mensajes_fallidos": len(tokens),
                "tokens_fallidos": tokens,
                "detalles_error": [{"mensaje": str(e)}],
                "timestamp": datetime.now(ZoneInfo("America/Mexico_City")).isoformat()
            }
    
    
    @staticmethod
    def _enviar_en_lotes(
        tokens: List[str],
        titulo: str,
        cuerpo: str,
        datos_personalizados: Optional[Dict[str, str]] = None,
        icono: Optional[str] = None,
        imagen: Optional[str] = None,
        plataformas: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Envía notificaciones en lotes de 500 tokens (límite de FCM).
        
        Returns:
            Dict con resultados acumulados de todos los lotes
        """
        resultados_totales = {
            "success": True,
            "mensajes_exitosos": 0,
            "mensajes_fallidos": 0,
            "tokens_fallidos": [],
            "detalles_error": [],
            "lotes_procesados": 0,
            "timestamp": datetime.now(ZoneInfo("America/Mexico_City")).isoformat()
        }
        
        for i in range(0, len(tokens), 500):
            lote = tokens[i:i+500]
            # Extraer plataformas para este lote
            plataformas_lote = None
            if plataformas:
                plataformas_lote = {t: plataformas[t] for t in lote if t in plataformas}
            
            resultado_lote = FCMNotificationService.enviar_notificacion_simple(
                lote, titulo, cuerpo, datos_personalizados, icono, imagen, plataformas_lote
            )
            
            resultados_totales["mensajes_exitosos"] += resultado_lote["mensajes_exitosos"]
            resultados_totales["mensajes_fallidos"] += resultado_lote["mensajes_fallidos"]
            resultados_totales["tokens_fallidos"].extend(resultado_lote["tokens_fallidos"])
            resultados_totales["detalles_error"].extend(resultado_lote["detalles_error"])
            resultados_totales["lotes_procesados"] += 1
            
            if not resultado_lote["success"]:
                resultados_totales["success"] = False
        
        return resultados_totales
    
    
    @staticmethod
    def enviar_notificacion_stock_bajo(
        insumo_nombre: str,
        cantidad_actual: float,
        minimo_stock: float,
        unidad: str,
        tokens: List[str],
        sucursal_nombre: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envía notificación personalizada para alertas de stock bajo.
        
        Args:
            insumo_nombre (str): Nombre del insumo
            cantidad_actual (float): Cantidad actual
            minimo_stock (float): Mínimo stock configurado
            unidad (str): Unidad de medida (kg, L, unidad, etc.)
            tokens (List[str]): Lista de push tokens
            sucursal_nombre (str): Nombre de la sucursal (opcional)
            
        Returns:
            Dict con resultado del envío
            
        Example:
            FCMNotificationService.enviar_notificacion_stock_bajo(
                insumo_nombre='Harina Premium',
                cantidad_actual=5.0,
                minimo_stock=10.0,
                unidad='kg',
                tokens=['token1', 'token2'],
                sucursal_nombre='Sucursal Centro'
            )
        """
        titulo = "⚠️ Stock Bajo"
        cuerpo = f"{insumo_nombre}: {cantidad_actual} {unidad} (mín: {minimo_stock} {unidad})"
        if sucursal_nombre:
            cuerpo += f" - {sucursal_nombre}"
        
        datos = {
            "tipo_alerta": "stock_bajo",
            "insumo_nombre": insumo_nombre,
            "cantidad_actual": str(cantidad_actual),
            "minimo_stock": str(minimo_stock),
            "unidad": unidad
        }
        
        return FCMNotificationService.enviar_notificacion_simple(
            tokens=tokens,
            titulo=titulo,
            cuerpo=cuerpo,
            datos_personalizados=datos,
            icono="ic_warning"
        )
    
    
    @staticmethod
    def enviar_notificacion_multiple_insumos(
        insumos_bajo_stock: List[Dict[str, Any]],
        tokens: List[str],
        sucursal_nombre: Optional[str] = None,
        plataformas: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Envía una notificación sobre múltiples insumos con stock bajo.
        
        Args:
            insumos_bajo_stock (List[Dict]): Lista de insumos con estructura:
                [
                    {
                        "nombre": str,
                        "cantidad_actual": float,
                        "minimo_stock": float,
                        "unidad_clave": str
                    }
                ]
            tokens (List[str]): Lista de push tokens
            sucursal_nombre (str): Nombre de la sucursal (opcional)
            plataformas (Dict): Mapeo token -> plataforma (opcional)
            
        Returns:
            Dict con resultado del envío
        """
        cantidad = len(insumos_bajo_stock)
        titulo = "📦 Alertas de Stock"
        cuerpo = f"{cantidad} insumo{'s' if cantidad > 1 else ''} con stock bajo"
        if sucursal_nombre:
            cuerpo += f" - {sucursal_nombre}"
        
        # Crear lista de insumos en datos
        datos = {
            "tipo_alerta": "multiples_insumos",
            "cantidad_insumos": str(cantidad),
            "insumos": json.dumps([
                {
                    "nombre": ins["nombre"],
                    "cantidad": ins["cantidad_actual"],
                    "minimo": ins["minimo_stock"],
                    "unidad": ins["unidad_clave"]
                }
                for ins in insumos_bajo_stock[:10]  # Máximo 10 en datos
            ])
        }
        
        return FCMNotificationService.enviar_notificacion_simple(
            tokens=tokens,
            titulo=titulo,
            cuerpo=cuerpo,
            datos_personalizados=datos,
            icono="ic_inventory",
            plataformas=plataformas
        )


def inicializar_y_enviar_notificaciones(
    tokens: List[str],
    titulo: str,
    cuerpo: str,
    datos_personalizados: Optional[Dict[str, str]] = None,
    credentials_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Función de conveniencia que inicializa Firebase y envía notificaciones en una sola llamada.
    
    Args:
        tokens (List[str]): Lista de push tokens
        titulo (str): Título del mensaje
        cuerpo (str): Cuerpo del mensaje
        datos_personalizados (Dict): Datos adicionales (opcional)
        credentials_path (str): Ruta a credenciales de Firebase (opcional)
        
    Returns:
        Dict con resultado del envío
    """
    if not inicializar_firebase(credentials_path):
        return {
            "success": False,
            "error": "No se pudo inicializar Firebase",
            "mensajes_exitosos": 0,
            "mensajes_fallidos": len(tokens)
        }
    
    return FCMNotificationService.enviar_notificacion_simple(
        tokens=tokens,
        titulo=titulo,
        cuerpo=cuerpo,
        datos_personalizados=datos_personalizados
    )
