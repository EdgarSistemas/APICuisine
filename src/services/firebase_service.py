"""
FirebaseService - Servicio para notificaciones push vía Firebase Cloud Messaging

Obtiene credenciales desde Azure Key Vault y envía notificaciones.

Uso:
    # Enviar notificación simple
    response = FirebaseService.send_notification(token, "Título", "Cuerpo")
    
    # Enviar a múltiples dispositivos
    result = FirebaseService.send_notification_to_multiple(tokens, "Título", "Cuerpo")
"""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

import firebase_admin
from firebase_admin import credentials, messaging

from src.services.keyvault_service import KeyVaultService

logger = logging.getLogger(__name__)


class FirebaseService:
    """
    Servicio para envío de notificaciones push vía Firebase Cloud Messaging.
    
    Las credenciales se obtienen automáticamente desde Azure Key Vault.
    La inicialización es lazy (se hace en la primera llamada).
    """
    
    _initialized = False
    _keyvault_secret_name = "config-firebase-2"
    
    @classmethod
    def initialize(cls) -> bool:
        """
        Inicializa Firebase Admin SDK con credenciales desde Key Vault.
        
        Returns:
            bool: True si se inicializó correctamente
        """
        if cls._initialized:
            logger.debug("✅ Firebase ya estaba inicializado")
            return True
        
        try:
            # Obtener credenciales desde Key Vault
            logger.info("Obteniendo credenciales de Firebase desde Key Vault...")
            keyvault = KeyVaultService()
            firebase_credentials = keyvault.get_secret_as_json(cls._keyvault_secret_name)
            
            # Validar campos requeridos
            required_fields = ['type', 'project_id', 'private_key', 'client_email']
            missing = [f for f in required_fields if f not in firebase_credentials]
            if missing:
                raise ValueError(f"Credenciales incompletas, faltan: {missing}")
            
            # Inicializar Firebase
            cred = credentials.Certificate(firebase_credentials)
            firebase_admin.initialize_app(cred)
            cls._initialized = True
            
            logger.info(f"✅ Firebase inicializado (project: {firebase_credentials.get('project_id')})")
            return True
            
        except ValueError as e:
            if "already initialized" in str(e):
                cls._initialized = True
                logger.info("✅ Firebase ya estaba inicializado en otro lugar")
                return True
            logger.error(f"❌ Error inicializando Firebase: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Error inicializando Firebase: {str(e)}", exc_info=True)
            return False
    
    @classmethod
    def send_notification(
        cls, 
        token: str, 
        title: str, 
        body: str,
        data: Optional[Dict[str, str]] = None,
        image: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envía una notificación a un dispositivo.
        
        Args:
            token: Push token del dispositivo
            title: Título de la notificación
            body: Cuerpo del mensaje
            data: Datos adicionales (opcional)
            image: URL de imagen (opcional)
            
        Returns:
            Dict con resultado del envío
        """
        if not cls.initialize():
            return {
                "success": False,
                "error": "Firebase no inicializado",
                "token": token[:30] + "..."
            }
        
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                    image=image
                ),
                data=data or {},
                token=token
            )
            
            response = messaging.send(message)
            logger.info(f"✅ Notificación enviada: {response}")
            
            return {
                "success": True,
                "message_id": response,
                "token": token[:30] + "..."
            }
            
        except Exception as e:
            logger.warning(f"❌ Error enviando a token {token[:30]}...: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "token": token[:30] + "..."
            }
    
    @classmethod
    def send_notification_to_multiple(
        cls,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        image: Optional[str] = None,
        icon: Optional[str] = None,
        plataformas: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Envía una notificación a múltiples dispositivos.
        
        Args:
            tokens: Lista de push tokens (máximo 500 por llamada)
            title: Título de la notificación
            body: Cuerpo del mensaje
            data: Datos adicionales (opcional)
            image: URL de imagen (opcional)
            icon: URL del icono (opcional)
            plataformas: Mapeo token -> plataforma ej: {'token1': 'web'} (opcional)
            
        Returns:
            Dict con resumen del envío
        """
        if not cls.initialize():
            return {
                "success": False,
                "error": "Firebase no inicializado",
                "mensajes_exitosos": 0,
                "mensajes_fallidos": len(tokens),
                "tokens_fallidos": tokens,
                "timestamp": datetime.now(ZoneInfo("America/Mexico_City")).isoformat()
            }
        
        if not tokens:
            return {
                "success": False,
                "error": "Lista de tokens vacía",
                "mensajes_exitosos": 0,
                "mensajes_fallidos": 0,
                "tokens_fallidos": [],
                "timestamp": datetime.now(ZoneInfo("America/Mexico_City")).isoformat()
            }
        
        # Si hay más de 500 tokens, procesar en lotes
        if len(tokens) > 500:
            return cls._send_in_batches(tokens, title, body, data, image, icon, plataformas)
        
        mensajes_exitosos = 0
        mensajes_fallidos = 0
        tokens_fallidos = []
        detalles_error = []
        
        # Construir notificación base
        notificacion = messaging.Notification(
            title=title,
            body=body,
            image=image
        )
        
        for token in tokens:
            try:
                # Detectar plataforma
                plataforma = plataformas.get(token) if plataformas else None
                
                msg_kwargs = {
                    "token": token,
                    "notification": notificacion,
                    "data": data or {}
                }
                
                # Configuración específica para web
                if plataforma == 'web':
                    webpush_config = messaging.WebpushConfig(
                        headers={"TTL": "3600"},
                        notification=messaging.WebpushNotification(
                            title=title,
                            body=body,
                            icon=icon or ""
                        )
                    )
                    msg_kwargs["webpush"] = webpush_config
                
                msg = messaging.Message(**msg_kwargs)
                response = messaging.send(msg)
                
                logger.debug(f"✅ Enviado a {token[:30]}...: {response}")
                mensajes_exitosos += 1
                
            except Exception as e:
                logger.warning(f"❌ Falló {token[:30]}...: {str(e)}")
                mensajes_fallidos += 1
                tokens_fallidos.append(token)
                detalles_error.append({
                    "token": token[:30] + "...",
                    "plataforma": plataforma or "desconocida",
                    "error": str(e)
                })
        
        logger.info(f"📬 Notificaciones: {mensajes_exitosos} exitosas, {mensajes_fallidos} fallidas")
        
        return {
            "success": mensajes_exitosos > 0,
            "mensajes_exitosos": mensajes_exitosos,
            "mensajes_fallidos": mensajes_fallidos,
            "tokens_fallidos": tokens_fallidos,
            "detalles_error": detalles_error,
            "timestamp": datetime.now(ZoneInfo("America/Mexico_City")).isoformat()
        }
    
    @classmethod
    def _send_in_batches(
        cls,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        image: Optional[str] = None,
        icon: Optional[str] = None,
        plataformas: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Procesa tokens en lotes de 500."""
        
        resultado_total = {
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
            plataformas_lote = {t: plataformas[t] for t in lote if plataformas and t in plataformas}
            
            resultado_lote = cls.send_notification_to_multiple(
                lote, title, body, data, image, icon, plataformas_lote
            )
            
            resultado_total["mensajes_exitosos"] += resultado_lote["mensajes_exitosos"]
            resultado_total["mensajes_fallidos"] += resultado_lote["mensajes_fallidos"]
            resultado_total["tokens_fallidos"].extend(resultado_lote.get("tokens_fallidos", []))
            resultado_total["detalles_error"].extend(resultado_lote.get("detalles_error", []))
            resultado_total["lotes_procesados"] += 1
            
            if not resultado_lote["success"]:
                resultado_total["success"] = False
        
        return resultado_total
    
    @classmethod
    def send_stock_alert(
        cls,
        tokens: List[str],
        insumo_nombre: str,
        cantidad_actual: float,
        minimo_stock: float,
        unidad: str,
        sucursal_nombre: Optional[str] = None,
        plataformas: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Envía alerta de stock bajo.
        
        Args:
            tokens: Lista de push tokens
            insumo_nombre: Nombre del insumo
            cantidad_actual: Cantidad actual
            minimo_stock: Mínimo configurado
            unidad: Unidad de medida
            sucursal_nombre: Nombre de sucursal (opcional)
            plataformas: Mapeo token -> plataforma (opcional)
        """
        titulo = "⚠️ Stock Bajo"
        cuerpo = f"{insumo_nombre}: {cantidad_actual} {unidad} (mín: {minimo_stock} {unidad})"
        if sucursal_nombre:
            cuerpo += f" - {sucursal_nombre}"
        
        data = {
            "tipo_alerta": "stock_bajo",
            "insumo_nombre": insumo_nombre,
            "cantidad_actual": str(cantidad_actual),
            "minimo_stock": str(minimo_stock),
            "unidad": unidad
        }
        
        return cls.send_notification_to_multiple(
            tokens=tokens,
            title=titulo,
            body=cuerpo,
            data=data,
            icon="ic_warning",
            plataformas=plataformas
        )
    
    @classmethod
    def send_multiple_stock_alerts(
        cls,
        tokens: List[str],
        insumos: List[Dict[str, Any]],
        sucursal_nombre: Optional[str] = None,
        plataformas: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Envía alerta de múltiples insumos con stock bajo.
        
        Args:
            tokens: Lista de push tokens
            insumos: Lista de dicts con nombre, cantidad_actual, minimo_stock, unidad_clave
            sucursal_nombre: Nombre de sucursal (opcional)
            plataformas: Mapeo token -> plataforma (opcional)
        """
        cantidad = len(insumos)
        titulo = "📦 Alertas de Stock"
        cuerpo = f"{cantidad} insumo{'s' if cantidad > 1 else ''} con stock bajo"
        if sucursal_nombre:
            cuerpo += f" - {sucursal_nombre}"
        
        data = {
            "tipo_alerta": "multiples_insumos",
            "cantidad_insumos": str(cantidad),
            "insumos": json.dumps([
                {
                    "nombre": ins.get("nombre"),
                    "cantidad": ins.get("cantidad_actual"),
                    "minimo": ins.get("minimo_stock"),
                    "unidad": ins.get("unidad_clave")
                }
                for ins in insumos[:10]
            ])
        }
        
        return cls.send_notification_to_multiple(
            tokens=tokens,
            title=titulo,
            body=cuerpo,
            data=data,
            icon="ic_inventory",
            plataformas=plataformas
        )
