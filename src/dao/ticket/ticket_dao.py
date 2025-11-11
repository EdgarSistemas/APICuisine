"""
TicketDAO - Data Access Object para ticket.Ticket
"""

from src.models.ticket import Ticket
from src.core.db.session_manager import get_db_session
from src.schemas.ticket_schema import TicketResponseSchema
import logging

logger = logging.getLogger(__name__)


class TicketDAO:
    """Data Access Object para Ticket"""
    
    @staticmethod
    def crear_ticket(usuario_id: int, notas: str, imagen_url: str = None) -> dict:
        """
        Crear nuevo ticket de incidencia.
        
        Args:
            usuario_id: ID del empleado que reporta
            notas: Descripción del problema
            imagen_url: URL de imagen (opcional)
            
        Returns:
            Dict serializado del ticket
        """
        schema = TicketResponseSchema()
        with get_db_session() as session:
            ticket = Ticket(
                usuario_id=usuario_id,
                notas=notas,
                imagen_url=imagen_url,
                estatus=1  # Registrada
            )
            session.add(ticket)
            session.commit()
            logger.info(f"Ticket creado: ID {ticket.id_ticket} por usuario {usuario_id}")
            return schema.dump(ticket)
    
    
    @staticmethod
    def obtener_ticket_por_id(ticket_id: int) -> dict:
        """
        Obtener ticket por ID.
        
        Args:
            ticket_id: ID del ticket
            
        Returns:
            Dict del ticket o None
        """
        schema = TicketResponseSchema()
        with get_db_session() as session:
            ticket = session.query(Ticket).filter(
                Ticket.id_ticket == ticket_id
            ).first()
            return schema.dump(ticket) if ticket else None
    
    
    @staticmethod
    def listar_tickets(usuario_id: int = None, estatus: int = None) -> list:
        """
        Listar tickets con filtros opcionales.
        
        Args:
            usuario_id: Filtrar por usuario (opcional)
            estatus: Filtrar por estatus (opcional)
            
        Returns:
            Lista de dicts de tickets
        """
        schema = TicketResponseSchema()
        with get_db_session() as session:
            query = session.query(Ticket)
            
            if usuario_id:
                query = query.filter(Ticket.usuario_id == usuario_id)
            
            if estatus:
                query = query.filter(Ticket.estatus == estatus)
            
            tickets = query.order_by(Ticket.created_at.desc()).all()
            return [schema.dump(t) for t in tickets]
    
    
    @staticmethod
    def actualizar_estatus_ticket(ticket_id: int, estatus: int) -> dict:
        """
        Actualizar estatus de ticket.
        
        Args:
            ticket_id: ID del ticket
            estatus: Nuevo estatus (1=Registrada, 2=EnProceso, 3=Completada, 4=Cancelada)
            
        Returns:
            Dict actualizado o None
        """
        schema = TicketResponseSchema()
        with get_db_session() as session:
            ticket = session.query(Ticket).filter(
                Ticket.id_ticket == ticket_id
            ).first()
            
            if not ticket:
                return None
            
            ticket.estatus = estatus
            session.commit()
            logger.info(f"Ticket {ticket_id} actualizado a estatus {estatus}")
            return schema.dump(ticket)
    
    
    @staticmethod
    def ticket_existe(ticket_id: int) -> bool:
        """
        Verificar si un ticket existe.
        
        Args:
            ticket_id: ID del ticket
            
        Returns:
            True si existe
        """
        with get_db_session() as session:
            existe = session.query(Ticket).filter(
                Ticket.id_ticket == ticket_id
            ).first()
            return existe is not None
