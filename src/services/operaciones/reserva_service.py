"""
ReservaService - Business Logic para Reserva
Gestión de reservaciones confirmadas de mesas
"""

from datetime import datetime
from src.dao.operaciones.reserva_dao import ReservaDAO
from src.dao.operaciones.hold_mesa_dao import HoldMesaDAO
from src.dao.catalogos.mesa_dao import MesaDAO
import logging
import pytz

logger = logging.getLogger(__name__)

# Zona horaria de México
TZ_MEXICO = pytz.timezone('America/Mexico_City')


class ReservaService:
    """Service para Reserva"""
    
    @staticmethod
    def crear_reserva(
        usuario_id: int,
        cliente_id: int,
        recepcionista_id: int,
        inicio: datetime,
        fin_estimado: datetime,
        tolerancia_min: int = None,
        notas: str = None,
        hold_id: int = None
    ) -> dict:
        """
        Crear reserva confirmada.
        
        Si viene desde un hold (hold_id), se valida que el hold esté activo
        y se marca como confirmado.
        
        VALIDACIONES:
        1. Si viene hold_id, debe existir y estar activo
        2. Mesa debe estar disponible (si no viene de hold)
        
        Args:
            usuario_id: ID del usuario autenticado
            cliente_id: ID del cliente que reserva
            recepcionista_id: ID del recepcionista (si aplica)
            inicio: Fecha/hora inicio
            fin_estimado: Fecha/hora fin estimado
            tolerancia_min: Minutos de tolerancia para NoShow
            notas: Notas adicionales
            hold_id: ID del hold origen (opcional)
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            # Si viene de hold, validar que existe y está activo
            if hold_id:
                hold = HoldMesaDAO.obtener_hold_por_id(hold_id)
                
                if not hold:
                    return {"success": False, "error": f"Hold {hold_id} no existe"}
                
                if hold['estatus'] not in (1,2):
                    return {"success": False, "error": f"Hold {hold_id} no está activo (estatus={hold['estatus']})"}
                
                # Verificar que no expiró (usar zona de México)
                ahora_mexico = datetime.now(TZ_MEXICO).replace(tzinfo=None)
                
                # Convertir expires_at a datetime si es string
                expires_at = hold['expires_at']
                if isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                    if expires_at.tzinfo:
                        expires_at = expires_at.astimezone(TZ_MEXICO).replace(tzinfo=None)
                elif expires_at.tzinfo:
                    expires_at = expires_at.replace(tzinfo=None)
                
                if ahora_mexico > expires_at:
                    return {"success": False, "error": f"Hold {hold_id} ya expiró"}
                
                # Hold validado - usar fechas del payload (ya parseadas correctamente por Marshmallow)
                # NO sobrescribir con fechas del hold, usar las que envió el cliente
                
            else:
                # Validación manual (sin hold)
                # Por ahora permitimos, pero idealmente siempre debe venir de hold
                logger.warning(f"Reserva creada sin hold previo por usuario {usuario_id}")
            
            # Crear reserva
            reserva = ReservaDAO.crear_reserva(
                cliente_id=cliente_id,
                recepcionista_id=recepcionista_id,
                inicio=inicio,
                fin_estimado=fin_estimado,
                tolerancia_min=tolerancia_min,
                notas=notas,
                hold_id=hold_id
            )
            
            # Si venía de hold, marcarlo como confirmado
            if hold_id:
                HoldMesaDAO.confirmar_hold(hold_id)
                logger.info(f"Hold {hold_id} confirmado y convertido a reserva {reserva['id_reserva']}")
            
            logger.info(f"Reserva creada: ID {reserva['id_reserva']} para cliente {cliente_id}")
            return {"success": True, "data": reserva}
            
        except Exception as e:
            logger.error(f"Error en ReservaService.crear_reserva: {str(e)}")
            return {"success": False, "error": f"Error al crear reserva: {str(e)}"}
    
    
    @staticmethod
    def obtener_reserva(reserva_id: int) -> dict:
        """
        Obtener reserva por ID.
        
        Args:
            reserva_id: ID de la reserva
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            reserva = ReservaDAO.obtener_reserva_por_id(reserva_id)
            
            if not reserva:
                return {"success": False, "error": f"Reserva {reserva_id} no existe"}
            
            return {"success": True, "data": reserva}
            
        except Exception as e:
            logger.error(f"Error en ReservaService.obtener_reserva: {str(e)}")
            return {"success": False, "error": f"Error al obtener reserva: {str(e)}"}
    
    
    @staticmethod
    def listar_reservas(
        usuario_id: int,
        sucursal_id: int = None,
        cliente_id: int = None,
        estatus: int = None,
        fecha_desde: datetime = None,
        fecha_hasta: datetime = None
    ) -> dict:
        """
        Listar reservas con filtros.
        
        - Clientes solo ven sus propias reservas
        - Recepcionistas/Admins ven todas
        
        Args:
            usuario_id: ID del usuario autenticado
            sucursal_id: Filtrar por sucursal
            cliente_id: Filtrar por cliente
            estatus: Filtrar por estatus
            fecha_desde: Desde fecha
            fecha_hasta: Hasta fecha
            
        Returns:
            {success: bool, data?: list, error?: str}
        """
        try:
            # TODO: Implementar verificación de rol
            # Por ahora permitimos filtrar libremente
            
            reservas = ReservaDAO.listar_reservas(
                sucursal_id=sucursal_id,
                cliente_id=cliente_id,
                estatus=estatus,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta
            )
            
            return {"success": True, "data": reservas}
            
        except Exception as e:
            logger.error(f"Error en ReservaService.listar_reservas: {str(e)}")
            return {"success": False, "error": f"Error al listar reservas: {str(e)}"}
    
    
    @staticmethod
    def listar_reservas_por_mesero(usuario_id: int) -> dict:
        """
        Listar reservas asignadas a un mesero.
        Ordenadas por estatus (de menor a mayor).
        
        Args:
            usuario_id: ID del mesero (usuario)
            
        Returns:
            {success: bool, data?: list, error?: str}
        """
        try:
            reservas = ReservaDAO.listar_reservas_por_mesero(usuario_id)
            return {"success": True, "data": reservas}
            
        except Exception as e:
            logger.error(f"Error en ReservaService.listar_reservas_por_mesero: {str(e)}")
            return {"success": False, "error": f"Error al listar reservas del mesero: {str(e)}"}
    
    
    @staticmethod
    def iniciar_reserva(usuario_id: int, reserva_id: int) -> dict:
        """
        Iniciar reserva (cliente llegó).
        Cambia estatus a 2 (EnCurso).
        
        VALIDACIONES:
        1. Reserva existe
        2. Reserva está programada (estatus=1)
        3. Está dentro de la ventana de tolerancia:
           - ANTES: Se puede iniciar desde (inicio - tolerancia_min)
           - DESPUÉS: Deadline es (inicio + tolerancia_min), pasado ese tiempo = NoShow automático
        
        Args:
            usuario_id: ID del usuario autenticado
            reserva_id: ID de la reserva
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            from datetime import timedelta
            
            # VALIDACIÓN 1: Reserva existe
            reserva = ReservaDAO.obtener_reserva_por_id(reserva_id)
            if not reserva:
                return {"success": False, "error": f"Reserva {reserva_id} no existe"}
            
            # VALIDACIÓN 2: Está programada
            if reserva['estatus'] != 1:
                return {"success": False, "error": f"Reserva {reserva_id} no está programada (estatus={reserva['estatus']})"}
            
            # VALIDACIÓN 3: Está dentro de la ventana de tolerancia
            ahora_mexico = datetime.now(TZ_MEXICO).replace(tzinfo=None)
            inicio_reserva = reserva['inicio']
            tolerancia = reserva['tolerancia_min'] or 15
            
            # Convertir inicio_reserva a datetime si es string
            if isinstance(inicio_reserva, str):
                inicio_reserva = datetime.fromisoformat(inicio_reserva.replace('Z', '+00:00'))
                if inicio_reserva.tzinfo:
                    inicio_reserva = inicio_reserva.astimezone(TZ_MEXICO).replace(tzinfo=None)
            
            ventana_inicio = inicio_reserva - timedelta(minutes=tolerancia)
            ventana_fin = inicio_reserva + timedelta(minutes=tolerancia)
            
            # Aún no llegó a la ventana de llegada
            if ahora_mexico < ventana_inicio:
                return {
                    "success": False,
                    "error": f"Aún no es hora de iniciar. La reserva es a las {inicio_reserva.strftime('%H:%M')}, puedes llegar desde {ventana_inicio.strftime('%H:%M')}"
                }
            
            # Pasó la ventana de tolerancia (deadline para presentarse)
            if ahora_mexico > ventana_fin:
                return {
                    "success": False,
                    "error": f"Ya pasó la ventana de tolerancia. Límite era {ventana_fin.strftime('%H:%M')}. Esta reserva debe marcarse como NoShow."
                }
            
            # Está en ventana válida - iniciar
            reserva_actualizada = ReservaDAO.iniciar_reserva(reserva_id)
            
            logger.info(f"Reserva {reserva_id} iniciada por usuario {usuario_id}")
            return {"success": True, "data": reserva_actualizada}
            
        except Exception as e:
            logger.error(f"Error en ReservaService.iniciar_reserva: {str(e)}")
            return {"success": False, "error": f"Error al iniciar reserva: {str(e)}"}
    
    
    @staticmethod
    def completar_reserva(usuario_id: int, reserva_id: int) -> dict:
        """
        Completar reserva (cliente terminó).
        Cambia estatus a 3 (Completada).
        
        VALIDACIONES:
        1. Reserva existe
        2. Reserva está en curso (estatus=2)
        
        Args:
            usuario_id: ID del usuario autenticado
            reserva_id: ID de la reserva
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            # VALIDACIÓN 1: Reserva existe
            reserva = ReservaDAO.obtener_reserva_por_id(reserva_id)
            if not reserva:
                return {"success": False, "error": f"Reserva {reserva_id} no existe"}
            
            # VALIDACIÓN 2: Está en curso
            if reserva['estatus'] != 2:
                return {"success": False, "error": f"Reserva {reserva_id} no está en curso (estatus={reserva['estatus']})"}
            
            # Completar
            reserva_actualizada = ReservaDAO.completar_reserva(reserva_id)
            
            logger.info(f"Reserva {reserva_id} completada por usuario {usuario_id}")
            return {"success": True, "data": reserva_actualizada}
            
        except Exception as e:
            logger.error(f"Error en ReservaService.completar_reserva: {str(e)}")
            return {"success": False, "error": f"Error al completar reserva: {str(e)}"}
    
    
    @staticmethod
    def cancelar_reserva(usuario_id: int, reserva_id: int, motivo: str = None) -> dict:
        """
        Cancelar reserva.
        Cambia estatus a 5 (Cancelada).
        
        VALIDACIONES:
        1. Reserva existe
        2. Reserva está programada o en curso (estatus 1 o 2)
        
        Args:
            usuario_id: ID del usuario autenticado
            reserva_id: ID de la reserva
            motivo: Motivo de cancelación
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            # VALIDACIÓN 1: Reserva existe
            reserva = ReservaDAO.obtener_reserva_por_id(reserva_id)
            if not reserva:
                return {"success": False, "error": f"Reserva {reserva_id} no existe"}
            
            # VALIDACIÓN 2: Está programada o en curso
            if reserva['estatus'] not in [1, 2]:
                return {"success": False, "error": f"No se puede cancelar. Reserva en estatus {reserva['estatus']}"}
            
            # Cancelar
            reserva_actualizada = ReservaDAO.cancelar_reserva(reserva_id, motivo)
            
            logger.info(f"Reserva {reserva_id} cancelada por usuario {usuario_id}: {motivo}")
            return {"success": True, "data": reserva_actualizada}
            
        except Exception as e:
            logger.error(f"Error en ReservaService.cancelar_reserva: {str(e)}")
            return {"success": False, "error": f"Error al cancelar reserva: {str(e)}"}
    
    
    @staticmethod
    def marcar_no_show(usuario_id: int, reserva_id: int) -> dict:
        """
        Marcar manualmente como NoShow.
        Cambia estatus a 4.
        
        Solo recepcionistas/admins pueden hacer esto.
        
        Args:
            usuario_id: ID del usuario autenticado
            reserva_id: ID de la reserva
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            # TODO: Validar que usuario sea recepcionista/admin
            
            # VALIDACIÓN: Reserva existe y está programada
            reserva = ReservaDAO.obtener_reserva_por_id(reserva_id)
            if not reserva:
                return {"success": False, "error": f"Reserva {reserva_id} no existe"}
            
            if reserva['estatus'] != 1:
                return {"success": False, "error": f"Solo se puede marcar NoShow si está programada (estatus=1)"}
            
            # Marcar
            reserva_actualizada = ReservaDAO.marcar_no_show(reserva_id)
            
            logger.info(f"Reserva {reserva_id} marcada como NoShow por usuario {usuario_id}")
            return {"success": True, "data": reserva_actualizada}
            
        except Exception as e:
            logger.error(f"Error en ReservaService.marcar_no_show: {str(e)}")
            return {"success": False, "error": f"Error al marcar NoShow: {str(e)}"}
