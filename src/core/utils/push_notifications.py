"""
push_notifications.py - Utilidades para envío de notificaciones push vía Firebase Cloud Messaging

NOTA: Este módulo ahora es un wrapper de compatibilidad.
      El código real está en:
        - src/services/keyvault_service.py (Azure Key Vault)
        - src/services/firebase_service.py (Firebase Cloud Messaging)

Uso directo (recomendado):
    from src.services.firebase_service import FirebaseService
    FirebaseService.send_notification(token, "Título", "Cuerpo")
    
Uso legacy (este módulo):
    from src.core.utils.push_notifications import inicializar_firebase, FCMNotificationService
    inicializar_firebase()
    FCMNotificationService.enviar_notificacion_simple(tokens, "Título", "Cuerpo")
"""

import logging
from typing import List, Dict, Any, Optional

# Importar el nuevo servicio
from src.services.firebase_service import FirebaseService

logger = logging.getLogger(__name__)

# Variables globales de compatibilidad
_firebase_initialized = False
FIREBASE_AVAILABLE = True


def inicializar_firebase(credentials_path: Optional[str] = None) -> bool:
    """
    Inicializa Firebase Admin SDK.
    
    NOTA: Las credenciales ahora se obtienen desde Azure Key Vault.
          El parámetro credentials_path se ignora.
    
    Returns:
        bool: True si se inicializó correctamente
    """
    global _firebase_initialized
    
    result = FirebaseService.initialize()
    _firebase_initialized = result
    return result


class FCMNotificationService:
    """
    Wrapper de compatibilidad para FirebaseService.
    
    Uso recomendado: usar FirebaseService directamente.
    """
    
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
        """Envía notificación a múltiples dispositivos."""
        return FirebaseService.send_notification_to_multiple(
            tokens=tokens,
            title=titulo,
            body=cuerpo,
            data=datos_personalizados,
            image=imagen,
            icon=icono,
            plataformas=plataformas
        )
    
    @staticmethod
    def enviar_notificacion_stock_bajo(
        insumo_nombre: str,
        cantidad_actual: float,
        minimo_stock: float,
        unidad: str,
        tokens: List[str],
        sucursal_nombre: Optional[str] = None
    ) -> Dict[str, Any]:
        """Envía alerta de stock bajo."""
        return FirebaseService.send_stock_alert(
            tokens=tokens,
            insumo_nombre=insumo_nombre,
            cantidad_actual=cantidad_actual,
            minimo_stock=minimo_stock,
            unidad=unidad,
            sucursal_nombre=sucursal_nombre
        )
    
    @staticmethod
    def enviar_notificacion_multiple_insumos(
        insumos_bajo_stock: List[Dict[str, Any]],
        tokens: List[str],
        sucursal_nombre: Optional[str] = None,
        plataformas: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Envía alerta de múltiples insumos."""
        return FirebaseService.send_multiple_stock_alerts(
            tokens=tokens,
            insumos=insumos_bajo_stock,
            sucursal_nombre=sucursal_nombre,
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
    Función de conveniencia que inicializa Firebase y envía notificaciones.
    """
    return FirebaseService.send_notification_to_multiple(
        tokens=tokens,
        title=titulo,
        body=cuerpo,
        data=datos_personalizados
    )
