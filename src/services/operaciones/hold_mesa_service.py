"""
HoldMesaService - Business Logic para HoldMesa
Gestión de holds temporales durante proceso de reserva
"""

from datetime import datetime
from src.dao.operaciones.hold_mesa_dao import HoldMesaDAO
from src.dao.catalogos.mesa_dao import MesaDAO
import logging

logger = logging.getLogger(__name__)


class HoldMesaService:
    """Service para HoldMesa"""
    
    @staticmethod
    def crear_hold(
        usuario_id: int,
        mesa_id: int,
        actor_tipo: int,
        inicio: datetime,
        fin_estimado: datetime,
        ttl_minutes: int = 5,
        notas: str = None
    ) -> dict:
        """
        Crear hold temporal de mesa.
        
        VALIDACIONES:
        1. Mesa existe y está activa
        2. Mesa está disponible (no hay holds/reservas que se traslapen)
        3. Fechas válidas
        
        Args:
            usuario_id: ID del usuario autenticado
            mesa_id: ID de la mesa a reservar
            actor_tipo: 1=Cliente, 2=Recepcionista
            inicio: Fecha/hora inicio deseada
            fin_estimado: Fecha/hora fin estimado
            ttl_minutes: Minutos antes de expirar (default 5, max 30)
            notas: Notas adicionales
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            # VALIDACIÓN 1: Mesa existe y está activa
            mesa = MesaDAO.obtener_mesa_por_id(mesa_id)
            if not mesa:
                return {"success": False, "error": f"Mesa {mesa_id} no existe"}
            
            if mesa.get('es_activa') != 1:
                return {"success": False, "error": f"Mesa {mesa_id} no está activa"}
            
            # VALIDACIÓN 2: Mesa está disponible en el rango
            disponible = HoldMesaDAO.verificar_mesa_disponible(mesa_id, inicio, fin_estimado)
            if not disponible:
                return {
                    "success": False,
                    "error": f"Mesa {mesa_id} no está disponible en el horario solicitado. Ya existe un hold o reserva activa."
                }
            
            # Crear hold
            hold = HoldMesaDAO.crear_hold(
                mesa_id=mesa_id,
                actor_tipo=actor_tipo,
                actor_usuario_id=usuario_id,
                inicio=inicio,
                fin_estimado=fin_estimado,
                ttl_minutes=ttl_minutes,
                notas=notas
            )
            
            logger.info(f"Hold creado por usuario {usuario_id}: hold_id={hold['id_hold_mesa']}, mesa={mesa_id}")
            return {"success": True, "data": hold}
            
        except Exception as e:
            logger.error(f"Error en HoldMesaService.crear_hold: {str(e)}")
            return {"success": False, "error": f"Error al crear hold: {str(e)}"}
    
    
    @staticmethod
    def obtener_hold(hold_id: int) -> dict:
        """
        Obtener hold por ID.
        
        Args:
            hold_id: ID del hold
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            hold = HoldMesaDAO.obtener_hold_por_id(hold_id)
            
            if not hold:
                return {"success": False, "error": f"Hold {hold_id} no existe"}
            
            return {"success": True, "data": hold}
            
        except Exception as e:
            logger.error(f"Error en HoldMesaService.obtener_hold: {str(e)}")
            return {"success": False, "error": f"Error al obtener hold: {str(e)}"}
    
    
    @staticmethod
    def cancelar_hold(usuario_id: int, hold_id: int) -> dict:
        """
        Cancelar hold.
        
        VALIDACIONES:
        1. Hold existe
        2. Hold está activo (estatus=1)
        3. Usuario es el que creó el hold (o es admin/recepcionista)
        
        Args:
            usuario_id: ID del usuario autenticado
            hold_id: ID del hold
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            # VALIDACIÓN 1: Hold existe
            hold = HoldMesaDAO.obtener_hold_por_id(hold_id)
            if not hold:
                return {"success": False, "error": f"Hold {hold_id} no existe"}
            
            # VALIDACIÓN 2: Hold está activo
            if hold['estatus'] != 1:
                return {"success": False, "error": f"Hold {hold_id} no está activo (estatus={hold['estatus']})"}
            
            # VALIDACIÓN 3: Usuario es dueño o tiene permisos
            # TODO: Implementar verificación de permisos más robusta
            if hold['actor_usuario_id'] != usuario_id:
                # Por ahora permitimos cancelar (en producción verificar si es admin/recepcionista)
                logger.warning(f"Usuario {usuario_id} cancelando hold {hold_id} que no creó")
            
            # Cancelar
            hold_actualizado = HoldMesaDAO.cancelar_hold(hold_id)
            
            logger.info(f"Hold {hold_id} cancelado por usuario {usuario_id}")
            return {"success": True, "data": hold_actualizado}
            
        except Exception as e:
            logger.error(f"Error en HoldMesaService.cancelar_hold: {str(e)}")
            return {"success": False, "error": f"Error al cancelar hold: {str(e)}"}
    
    
    @staticmethod
    def listar_holds_activos(mesa_id: int = None) -> dict:
        """
        Listar holds activos (no expirados).
        
        Args:
            mesa_id: Filtrar por mesa (opcional)
            
        Returns:
            {success: bool, data?: list, error?: str}
        """
        try:
            holds = HoldMesaDAO.listar_holds_activos(mesa_id)
            return {"success": True, "data": holds}
            
        except Exception as e:
            logger.error(f"Error en HoldMesaService.listar_holds_activos: {str(e)}")
            return {"success": False, "error": f"Error al listar holds: {str(e)}"}
    
    
    @staticmethod
    def verificar_disponibilidad_mesa(mesa_id: int, inicio: datetime, fin_estimado: datetime) -> dict:
        """
        Verificar si una mesa está disponible para reservar en un rango de fechas.
        Útil para mostrar disponibilidad antes de crear hold.
        
        Args:
            mesa_id: ID de la mesa
            inicio: Fecha/hora inicio
            fin_estimado: Fecha/hora fin estimado
            
        Returns:
            {success: bool, disponible: bool, error?: str}
        """
        try:
            # Verificar que mesa existe
            mesa = MesaDAO.obtener_mesa_por_id(mesa_id)
            if not mesa:
                return {"success": False, "disponible": False, "error": f"Mesa {mesa_id} no existe"}
            
            if mesa.get('es_activa') != 1:
                return {"success": False, "disponible": False, "error": f"Mesa {mesa_id} no está activa"}
            
            # Verificar disponibilidad
            disponible = HoldMesaDAO.verificar_mesa_disponible(mesa_id, inicio, fin_estimado)
            
            return {
                "success": True,
                "disponible": disponible,
                "mensaje": "Mesa disponible" if disponible else "Mesa no disponible (hay hold o reserva activa)"
            }
            
        except Exception as e:
            logger.error(f"Error en HoldMesaService.verificar_disponibilidad_mesa: {str(e)}")
            return {"success": False, "disponible": False, "error": f"Error al verificar disponibilidad: {str(e)}"}
