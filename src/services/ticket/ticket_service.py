"""
TicketService - Business Logic para Tickets
"""

from src.dao.ticket.ticket_dao import TicketDAO
from src.core.utils.multitenant import es_admin
import logging

logger = logging.getLogger(__name__)


class TicketService:
    """Service para Tickets de incidencias"""
    
    @staticmethod
    def crear_ticket(usuario_id: int, notas: str, imagen_url: str = None) -> dict:
        """
        Crear nuevo ticket de incidencia.
        Cualquier usuario autenticado puede crear tickets.
        
        Args:
            usuario_id: ID del usuario que reporta
            notas: Descripción del problema
            imagen_url: URL de imagen (opcional)
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            # Validar que notas no esté vacío
            if not notas or len(notas.strip()) == 0:
                return {"success": False, "error": "Las notas son requeridas"}
            
            ticket = TicketDAO.crear_ticket(usuario_id, notas, imagen_url)
            return {"success": True, "data": ticket}
            
        except Exception as e:
            logger.error(f"Error en TicketService.crear_ticket: {str(e)}")
            return {"success": False, "error": f"Error al crear ticket: {str(e)}"}
    
    
    @staticmethod
    def obtener_ticket(ticket_id: int) -> dict:
        """
        Obtener ticket por ID.
        
        Args:
            ticket_id: ID del ticket
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            ticket = TicketDAO.obtener_ticket_por_id(ticket_id)
            
            if not ticket:
                return {"success": False, "error": f"Ticket {ticket_id} no existe"}
            
            return {"success": True, "data": ticket}
            
        except Exception as e:
            logger.error(f"Error en TicketService.obtener_ticket: {str(e)}")
            return {"success": False, "error": f"Error al obtener ticket: {str(e)}"}
    
    
    @staticmethod
    def listar_tickets(usuario_id: int, filtro_usuario_id: int = None, estatus: int = None) -> dict:
        """
        Listar tickets.
        - Usuarios normales solo ven sus propios tickets
        - ADMIN ve todos los tickets
        
        Args:
            usuario_id: ID del usuario autenticado
            filtro_usuario_id: Filtrar por usuario (opcional, solo ADMIN)
            estatus: Filtrar por estatus (opcional)
            
        Returns:
            {success: bool, data?: list, error?: str}
        """
        try:
            # Si no es admin, solo puede ver sus propios tickets
            if not es_admin(usuario_id):
                filtro_usuario_id = usuario_id
            
            tickets = TicketDAO.listar_tickets(filtro_usuario_id, estatus)
            return {"success": True, "data": tickets}
            
        except Exception as e:
            logger.error(f"Error en TicketService.listar_tickets: {str(e)}")
            return {"success": False, "error": f"Error al listar tickets: {str(e)}"}
    
    
    @staticmethod
    def actualizar_estatus(usuario_id: int, ticket_id: int, estatus: int) -> dict:
        """
        Actualizar estatus de ticket.
        Solo ADMIN puede cambiar estatus.
        
        Args:
            usuario_id: ID del usuario autenticado
            ticket_id: ID del ticket
            estatus: Nuevo estatus (1=Registrada, 2=EnProceso, 3=Completada, 4=Cancelada)
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó actualizar ticket sin permisos")
                return {"success": False, "error": "Solo administradores pueden actualizar estatus de tickets"}
            
            # VALIDACIÓN 2: Ticket existe
            if not TicketDAO.ticket_existe(ticket_id):
                return {"success": False, "error": f"Ticket {ticket_id} no existe"}
            
            # Actualizar
            ticket = TicketDAO.actualizar_estatus_ticket(ticket_id, estatus)
            return {"success": True, "data": ticket}
            
        except Exception as e:
            logger.error(f"Error en TicketService.actualizar_estatus: {str(e)}")
            return {"success": False, "error": f"Error al actualizar ticket: {str(e)}"}
