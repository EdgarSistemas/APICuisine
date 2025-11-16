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
    
    Args:
        credentials_path (str): Ruta al archivo JSON de credenciales de Firebase
                              Si no se proporciona, intenta usar la ruta por defecto
    
    Returns:
        bool: True si se inicializó correctamente, False en caso de error
        
    Example:
        inicializar_firebase('/ruta/a/firebase-adminsdk.json')
    """
    global _firebase_initialized, _credentials_path
    
    if not FIREBASE_AVAILABLE:
        logger.error("Firebase Admin SDK no está instalado")
        return False
    
    if _firebase_initialized:
        logger.info("Firebase ya estaba inicializado")
        return True
    
    try:
        # Determinar ruta de credenciales
        if not credentials_path:
            # Buscar en la ruta por defecto del proyecto
            default_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'config',
                'push-notifications-cuisine-firebase-adminsdk-fbsvc-fd0c21cd4a.json'
            )
            credentials_path = default_path if os.path.exists(default_path) else None
        
        if not credentials_path:
            logger.error("No se encontró archivo de credenciales de Firebase")
            return False
        
        if not os.path.exists(credentials_path):
            logger.error(f"Archivo de credenciales no existe: {credentials_path}")
            return False
        
        # Inicializar Firebase
        cred = credentials.Certificate(credentials_path)
        firebase_admin.initialize_app(cred)
        
        _firebase_initialized = True
        _credentials_path = credentials_path
        logger.info(f"Firebase inicializado correctamente desde: {credentials_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error inicializando Firebase: {str(e)}")
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
        imagen: Optional[str] = None
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
                tokens, titulo, cuerpo, datos_personalizados, icono, imagen
            )
        
        try:
            # Construir notificación
            notificacion = messaging.Notification(
                title=titulo,
                body=cuerpo,
                image=imagen
            )
            
            # Construir opciones de Android
            config_android = messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    title=titulo,
                    body=cuerpo,
                    icon=icono or "ic_notification",
                    image=imagen
                )
            )
            
            # Construir opciones de WebPush
            config_web = messaging.WebpushConfig(
                notification=messaging.WebpushNotification(
                    title=titulo,
                    body=cuerpo,
                    icon=icono,
                    image=imagen
                )
            )
            
            # Enviar a múltiples dispositivos (uno por uno)
            mensajes_exitosos = 0
            mensajes_fallidos = 0
            tokens_fallidos = []
            detalles_error = []
            
            for token in tokens:
                try:
                    msg = messaging.Message(
                        token=token,
                        notification=notificacion,
                        data=datos_personalizados or {},
                        android=config_android,
                        webpush=config_web
                    )
                    messaging.send(msg)
                    mensajes_exitosos += 1
                except Exception as e:
                    mensajes_fallidos += 1
                    tokens_fallidos.append(token)
                    detalles_error.append({
                        "token": token[:20] + "...",
                        "error": str(e)
                    })
            
            resultado = {
                "success": mensajes_fallidos == 0,
                "mensajes_exitosos": mensajes_exitosos,
                "mensajes_fallidos": mensajes_fallidos,
                "tokens_fallidos": tokens_fallidos,
                "detalles_error": detalles_error,
                "timestamp": datetime.now(ZoneInfo("America/Mexico_City")).isoformat()
            }
            
            logger.info(f"Notificaciones enviadas: {mensajes_exitosos} exitosas, {mensajes_fallidos} fallidas")
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
        imagen: Optional[str] = None
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
            resultado_lote = FCMNotificationService.enviar_notificacion_simple(
                lote, titulo, cuerpo, datos_personalizados, icono, imagen
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
        sucursal_nombre: Optional[str] = None
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
            icono="ic_inventory"
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
