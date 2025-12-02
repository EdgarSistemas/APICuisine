"""
NotificationService - Servicio centralizado de notificaciones push

Maneja todas las notificaciones del sistema hacia PWA y móvil via FCM.
Se integra con los servicios de Pedidos, Reservas, Mesas, etc.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import pytz

from src.services.firebase_service import FirebaseService
from src.core.utils.stock_alerts import PushTokenDAO
from src.core.db.session_manager import get_db_session

logger = logging.getLogger(__name__)
TZ_MEXICO = pytz.timezone('America/Mexico_City')


class NotificationService:
    """
    Servicio centralizado para envío de notificaciones push.
    
    Categorías:
    - Pedidos: nuevo, item listo, completado, pagado, cancelado
    - Reservas: nueva, modificada, en curso, completada, no-show, cancelada, recordatorio
    - Holds: creado, confirmado, expirado, cancelado
    - Mesas: ocupada, limpieza, disponible, fuera de servicio
    - Pagos: pendiente, confirmado, anulado
    - Especiales: llamar mesero, incidencia, calificación
    """
    
    # =========================================================================
    # UTILIDADES INTERNAS
    # =========================================================================
    
    @staticmethod
    def _obtener_tokens_por_rol(rol: str, sucursal_id: int = None) -> List[str]:
        """Obtiene tokens de usuarios por rol y opcionalmente por sucursal"""
        try:
            filtros = {'rol': rol}
            if sucursal_id:
                filtros['sucursal_id'] = sucursal_id
            
            usuarios = PushTokenDAO.obtener_usuarios_con_push_tokens(
                filtros_usuario=filtros,
                filtros_push_token={'es_activo': True}
            )
            
            tokens = []
            for usuario in usuarios:
                for token_info in usuario.get('push_tokens', []):
                    tokens.append(token_info['token'])
            
            return tokens
        except Exception as e:
            logger.error(f"Error obteniendo tokens por rol {rol}: {e}")
            return []
    
    @staticmethod
    def _obtener_tokens_usuario(usuario_id: int) -> List[str]:
        """Obtiene todos los tokens activos de un usuario"""
        try:
            return PushTokenDAO.obtener_todos_push_tokens_por_usuario_id(
                usuario_id, 
                solo_activos=True
            )
        except Exception as e:
            logger.error(f"Error obteniendo tokens de usuario {usuario_id}: {e}")
            return []
    
    @staticmethod
    def _enviar(tokens: List[str], titulo: str, mensaje: str, data: Dict = None) -> Dict:
        """Envía notificación a lista de tokens"""
        if not tokens:
            logger.warning(f"Sin tokens para enviar: {titulo}")
            return {"success": False, "error": "Sin tokens disponibles"}
        
        try:
            resultado = FirebaseService.send_notification_to_multiple(
                tokens=tokens,
                title=titulo,
                body=mensaje,
                data=data or {}
            )
            logger.info(f"Notificación enviada: {titulo} -> {len(tokens)} dispositivos")
            return resultado
        except Exception as e:
            logger.error(f"Error enviando notificación: {e}")
            return {"success": False, "error": str(e)}
    
    # =========================================================================
    # NOTIFICACIONES DE PEDIDOS
    # =========================================================================
    
    @classmethod
    def notificar_pedido_creado(cls, pedido_id: int, mesa_num: str, cant_items: int, sucursal_id: int) -> Dict:
        """Notifica a cocina cuando se crea un nuevo pedido"""
        tokens = cls._obtener_tokens_por_rol('COCINA', sucursal_id)
        return cls._enviar(
            tokens=tokens,
            titulo="🍳 Nuevo Pedido",
            mensaje=f"Mesa {mesa_num} - {cant_items} items",
            data={"tipo": "pedido_nuevo", "pedido_id": str(pedido_id), "mesa": mesa_num}
        )
    
    @classmethod
    def notificar_item_listo(cls, pedido_id: int, producto: str, mesa_num: str, mesero_id: int) -> Dict:
        """Notifica al mesero cuando un item está listo en cocina"""
        tokens = cls._obtener_tokens_usuario(mesero_id)
        return cls._enviar(
            tokens=tokens,
            titulo="✅ Pedido Listo",
            mensaje=f"{producto} listo - Mesa {mesa_num}",
            data={"tipo": "item_listo", "pedido_id": str(pedido_id), "mesa": mesa_num}
        )
    
    @classmethod
    def notificar_pedido_completo(cls, pedido_id: int, mesa_num: str, total: float, sucursal_id: int) -> Dict:
        """Notifica a caja cuando un pedido está listo para cobrar"""
        tokens = cls._obtener_tokens_por_rol('CAJA', sucursal_id)
        return cls._enviar(
            tokens=tokens,
            titulo="💵 Pedido Cerrado",
            mensaje=f"Mesa {mesa_num} - ${total:,.2f}",
            data={"tipo": "pedido_completo", "pedido_id": str(pedido_id), "total": str(total)}
        )
    
    @classmethod
    def notificar_pedido_pagado(cls, pedido_id: int, mesa_num: str, total: float, sucursal_id: int, mesero_id: int = None) -> Dict:
        """Notifica cuando un pedido fue pagado"""
        tokens_gerencia = cls._obtener_tokens_por_rol('GERENTE', sucursal_id)
        tokens_mesero = cls._obtener_tokens_usuario(mesero_id) if mesero_id else []
        
        tokens = list(set(tokens_gerencia + tokens_mesero))
        return cls._enviar(
            tokens=tokens,
            titulo="💰 Pago Recibido",
            mensaje=f"Mesa {mesa_num} - ${total:,.2f}",
            data={"tipo": "pedido_pagado", "pedido_id": str(pedido_id)}
        )
    
    @classmethod
    def notificar_pedido_cancelado(cls, pedido_id: int, mesa_num: str, sucursal_id: int) -> Dict:
        """Notifica cuando un pedido fue cancelado"""
        tokens_cocina = cls._obtener_tokens_por_rol('COCINA', sucursal_id)
        tokens_mesero = cls._obtener_tokens_por_rol('MESERO', sucursal_id)
        
        tokens = list(set(tokens_cocina + tokens_mesero))
        return cls._enviar(
            tokens=tokens,
            titulo="❌ Pedido Cancelado",
            mensaje=f"Mesa {mesa_num} cancelado",
            data={"tipo": "pedido_cancelado", "pedido_id": str(pedido_id)}
        )
    
    @classmethod
    def notificar_item_cancelado(cls, pedido_id: int, producto: str, mesa_num: str, sucursal_id: int) -> Dict:
        """Notifica a cocina cuando un item fue cancelado"""
        tokens = cls._obtener_tokens_por_rol('COCINA', sucursal_id)
        return cls._enviar(
            tokens=tokens,
            titulo="🚫 Item Cancelado",
            mensaje=f"{producto} - Mesa {mesa_num}",
            data={"tipo": "item_cancelado", "pedido_id": str(pedido_id)}
        )
    
    # =========================================================================
    # NOTIFICACIONES DE RESERVAS
    # =========================================================================
    
    @classmethod
    def notificar_reserva_creada(cls, reserva_id: int, cliente_nombre: str, fecha_hora: str, 
                                  mesa_num: str, sucursal_id: int, cliente_id: int = None) -> Dict:
        """Notifica cuando se crea una reserva"""
        tokens_recepcion = cls._obtener_tokens_por_rol('RECEPCION', sucursal_id)
        tokens_cliente = cls._obtener_tokens_usuario(cliente_id) if cliente_id else []
        
        # Enviar a recepción
        cls._enviar(
            tokens=tokens_recepcion,
            titulo="📅 Nueva Reserva",
            mensaje=f"{cliente_nombre} - {fecha_hora} - Mesa {mesa_num}",
            data={"tipo": "reserva_nueva", "reserva_id": str(reserva_id)}
        )
        
        # Enviar confirmación al cliente
        if tokens_cliente:
            return cls._enviar(
                tokens=tokens_cliente,
                titulo="✅ Reserva Confirmada",
                mensaje=f"Tu reserva para {fecha_hora} está confirmada",
                data={"tipo": "reserva_confirmada", "reserva_id": str(reserva_id)}
            )
        
        return {"success": True}
    
    @classmethod
    def notificar_reserva_modificada(cls, reserva_id: int, fecha_hora: str, 
                                      sucursal_id: int, cliente_id: int = None) -> Dict:
        """Notifica cuando una reserva fue modificada"""
        tokens_recepcion = cls._obtener_tokens_por_rol('RECEPCION', sucursal_id)
        tokens_cliente = cls._obtener_tokens_usuario(cliente_id) if cliente_id else []
        
        tokens = list(set(tokens_recepcion + tokens_cliente))
        return cls._enviar(
            tokens=tokens,
            titulo="📝 Reserva Modificada",
            mensaje=f"Cambios en reserva para {fecha_hora}",
            data={"tipo": "reserva_modificada", "reserva_id": str(reserva_id)}
        )
    
    @classmethod
    def notificar_reserva_en_curso(cls, reserva_id: int, cliente_nombre: str, 
                                    mesa_num: str, mesero_id: int) -> Dict:
        """Notifica al mesero asignado cuando el cliente llegó"""
        tokens = cls._obtener_tokens_usuario(mesero_id)
        return cls._enviar(
            tokens=tokens,
            titulo="👋 Cliente Llegó",
            mensaje=f"{cliente_nombre} en Mesa {mesa_num}",
            data={"tipo": "reserva_en_curso", "reserva_id": str(reserva_id), "mesa": mesa_num}
        )
    
    @classmethod
    def notificar_reserva_completada(cls, reserva_id: int, mesa_num: str, sucursal_id: int) -> Dict:
        """Notifica a recepción cuando una reserva finalizó"""
        tokens = cls._obtener_tokens_por_rol('RECEPCION', sucursal_id)
        return cls._enviar(
            tokens=tokens,
            titulo="✔️ Reserva Finalizada",
            mensaje=f"Mesa {mesa_num} liberada",
            data={"tipo": "reserva_completada", "reserva_id": str(reserva_id)}
        )
    
    @classmethod
    def notificar_reserva_noshow(cls, reserva_id: int, cliente_nombre: str, 
                                  mesa_num: str, sucursal_id: int) -> Dict:
        """Notifica cuando un cliente no llegó (no-show)"""
        tokens_recepcion = cls._obtener_tokens_por_rol('RECEPCION', sucursal_id)
        tokens_gerencia = cls._obtener_tokens_por_rol('GERENTE', sucursal_id)
        
        tokens = list(set(tokens_recepcion + tokens_gerencia))
        return cls._enviar(
            tokens=tokens,
            titulo="⚠️ No Show",
            mensaje=f"{cliente_nombre} no llegó - Mesa {mesa_num} liberada",
            data={"tipo": "reserva_noshow", "reserva_id": str(reserva_id)}
        )
    
    @classmethod
    def notificar_reserva_cancelada(cls, reserva_id: int, fecha_hora: str, 
                                     sucursal_id: int, cliente_id: int = None) -> Dict:
        """Notifica cuando una reserva fue cancelada"""
        tokens_recepcion = cls._obtener_tokens_por_rol('RECEPCION', sucursal_id)
        tokens_cliente = cls._obtener_tokens_usuario(cliente_id) if cliente_id else []
        
        # Notificar a recepción
        cls._enviar(
            tokens=tokens_recepcion,
            titulo="❌ Reserva Cancelada",
            mensaje=f"Reserva para {fecha_hora} cancelada",
            data={"tipo": "reserva_cancelada", "reserva_id": str(reserva_id)}
        )
        
        # Notificar al cliente
        if tokens_cliente:
            return cls._enviar(
                tokens=tokens_cliente,
                titulo="Reserva Cancelada",
                mensaje=f"Tu reserva para {fecha_hora} ha sido cancelada",
                data={"tipo": "reserva_cancelada", "reserva_id": str(reserva_id)}
            )
        
        return {"success": True}
    
    @classmethod
    def notificar_recordatorio_reserva(cls, reserva_id: int, fecha_hora: str, 
                                        mesa_num: str, cliente_id: int) -> Dict:
        """Envía recordatorio al cliente antes de su reserva"""
        tokens = cls._obtener_tokens_usuario(cliente_id)
        return cls._enviar(
            tokens=tokens,
            titulo="🍽️ Recordatorio de Reserva",
            mensaje=f"Tu reserva es hoy a las {fecha_hora}",
            data={"tipo": "recordatorio_reserva", "reserva_id": str(reserva_id), "mesa": mesa_num}
        )
    
    # =========================================================================
    # NOTIFICACIONES DE HOLD MESA
    # =========================================================================
    
    @classmethod
    def notificar_hold_creado(cls, hold_id: int, mesa_num: str, minutos: int, sucursal_id: int) -> Dict:
        """Notifica a recepción cuando se crea un hold"""
        tokens = cls._obtener_tokens_por_rol('RECEPCION', sucursal_id)
        return cls._enviar(
            tokens=tokens,
            titulo="⏳ Mesa en Hold",
            mensaje=f"Mesa {mesa_num} apartada por {minutos} min",
            data={"tipo": "hold_creado", "hold_id": str(hold_id)}
        )
    
    @classmethod
    def notificar_hold_confirmado(cls, hold_id: int, mesa_num: str, 
                                   sucursal_id: int, cliente_id: int = None) -> Dict:
        """Notifica cuando un hold se convierte en reserva"""
        tokens_recepcion = cls._obtener_tokens_por_rol('RECEPCION', sucursal_id)
        tokens_cliente = cls._obtener_tokens_usuario(cliente_id) if cliente_id else []
        
        tokens = list(set(tokens_recepcion + tokens_cliente))
        return cls._enviar(
            tokens=tokens,
            titulo="✅ Hold Confirmado",
            mensaje=f"Mesa {mesa_num} reservada exitosamente",
            data={"tipo": "hold_confirmado", "hold_id": str(hold_id)}
        )
    
    @classmethod
    def notificar_hold_expirado(cls, hold_id: int, mesa_num: str, cliente_id: int = None) -> Dict:
        """Notifica al cliente cuando su hold expiró"""
        if not cliente_id:
            return {"success": False, "error": "Sin cliente_id"}
        
        tokens = cls._obtener_tokens_usuario(cliente_id)
        return cls._enviar(
            tokens=tokens,
            titulo="⏰ Hold Expirado",
            mensaje=f"Tu mesa {mesa_num} fue liberada por tiempo",
            data={"tipo": "hold_expirado", "hold_id": str(hold_id)}
        )
    
    # =========================================================================
    # NOTIFICACIONES DE MESAS
    # =========================================================================
    
    @classmethod
    def notificar_mesa_requiere_limpieza(cls, mesa_id: int, mesa_num: str, sucursal_id: int) -> Dict:
        """Notifica al personal de limpieza"""
        tokens = cls._obtener_tokens_por_rol('LIMPIEZA', sucursal_id)
        # Si no hay rol específico, notificar a meseros
        if not tokens:
            tokens = cls._obtener_tokens_por_rol('MESERO', sucursal_id)
        
        return cls._enviar(
            tokens=tokens,
            titulo="🧹 Limpieza Requerida",
            mensaje=f"Mesa {mesa_num} necesita limpieza",
            data={"tipo": "mesa_limpieza", "mesa_id": str(mesa_id)}
        )
    
    @classmethod
    def notificar_mesa_disponible(cls, mesa_id: int, mesa_num: str, sucursal_id: int) -> Dict:
        """Notifica a recepción cuando una mesa está disponible"""
        tokens = cls._obtener_tokens_por_rol('RECEPCION', sucursal_id)
        return cls._enviar(
            tokens=tokens,
            titulo="🟢 Mesa Disponible",
            mensaje=f"Mesa {mesa_num} lista",
            data={"tipo": "mesa_disponible", "mesa_id": str(mesa_id)}
        )
    
    # =========================================================================
    # NOTIFICACIONES DE PAGOS
    # =========================================================================
    
    @classmethod
    def notificar_pago_pendiente(cls, pago_id: int, mesa_num: str, total: float, sucursal_id: int) -> Dict:
        """Notifica a caja sobre pago pendiente"""
        tokens = cls._obtener_tokens_por_rol('CAJA', sucursal_id)
        return cls._enviar(
            tokens=tokens,
            titulo="💳 Pago Pendiente",
            mensaje=f"Mesa {mesa_num} - ${total:,.2f}",
            data={"tipo": "pago_pendiente", "pago_id": str(pago_id)}
        )
    
    @classmethod
    def notificar_pago_confirmado(cls, pago_id: int, total: float, 
                                   sucursal_id: int, cliente_id: int = None) -> Dict:
        """Notifica cuando un pago fue confirmado"""
        tokens_gerencia = cls._obtener_tokens_por_rol('GERENTE', sucursal_id)
        tokens_cliente = cls._obtener_tokens_usuario(cliente_id) if cliente_id else []
        
        # Notificar a gerencia
        cls._enviar(
            tokens=tokens_gerencia,
            titulo="💰 Pago Confirmado",
            mensaje=f"Pago de ${total:,.2f} recibido",
            data={"tipo": "pago_confirmado", "pago_id": str(pago_id)}
        )
        
        # Notificar al cliente
        if tokens_cliente:
            return cls._enviar(
                tokens=tokens_cliente,
                titulo="✅ Pago Recibido",
                mensaje=f"Gracias por tu pago de ${total:,.2f}",
                data={"tipo": "pago_confirmado", "pago_id": str(pago_id)}
            )
        
        return {"success": True}
    
    # =========================================================================
    # NOTIFICACIONES ESPECIALES
    # =========================================================================
    
    @classmethod
    def notificar_llamar_mesero(cls, mesa_id: int, mesa_num: str, mesero_id: int) -> Dict:
        """Notifica al mesero cuando un cliente lo llama"""
        tokens = cls._obtener_tokens_usuario(mesero_id)
        return cls._enviar(
            tokens=tokens,
            titulo="🔔 Te Llaman",
            mensaje=f"Mesa {mesa_num} te necesita",
            data={"tipo": "llamar_mesero", "mesa_id": str(mesa_id), "mesa": mesa_num}
        )
    
    @classmethod
    def notificar_nueva_calificacion(cls, calificacion_id: int, estrellas: int, 
                                      mesa_num: str, sucursal_id: int) -> Dict:
        """Notifica a gerencia sobre nueva calificación"""
        tokens = cls._obtener_tokens_por_rol('GERENTE', sucursal_id)
        emoji = "⭐" * estrellas
        return cls._enviar(
            tokens=tokens,
            titulo="📊 Nueva Calificación",
            mensaje=f"{emoji} - Mesa {mesa_num}",
            data={"tipo": "calificacion", "calificacion_id": str(calificacion_id)}
        )
    
    @classmethod
    def notificar_nueva_incidencia(cls, ticket_id: int, tipo: str, 
                                    descripcion: str, sucursal_id: int) -> Dict:
        """Notifica sobre nueva incidencia/ticket"""
        tokens = cls._obtener_tokens_por_rol('GERENTE', sucursal_id)
        return cls._enviar(
            tokens=tokens,
            titulo="🚨 Nueva Incidencia",
            mensaje=f"{tipo}: {descripcion[:50]}...",
            data={"tipo": "incidencia", "ticket_id": str(ticket_id)}
        )
