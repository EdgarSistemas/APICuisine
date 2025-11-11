"""
MejoraDAO - Data Access Object para servicio.Mejoras
"""

from src.models.servicio import Mejora
from src.core.db.session_manager import get_db_session
from src.schemas.servicio_schema import MejoraResponseSchema
import logging

logger = logging.getLogger(__name__)


class MejoraDAO:
    """Data Access Object para Mejoras"""
    
    @staticmethod
    def crear_mejora(cliente_id: int, notas: str) -> dict:
        """
        Crear nueva sugerencia de mejora.
        
        Args:
            cliente_id: ID del cliente que sugiere
            notas: Descripción de la sugerencia
            
        Returns:
            Dict serializado de la mejora
        """
        schema = MejoraResponseSchema()
        with get_db_session() as session:
            mejora = Mejora(
                cliente_id=cliente_id,
                notas=notas,
                estatus=1  # Registrada
            )
            session.add(mejora)
            session.commit()
            logger.info(f"Mejora creada: ID {mejora.id_mejora} por cliente {cliente_id}")
            return schema.dump(mejora)
    
    
    @staticmethod
    def obtener_mejora_por_id(mejora_id: int) -> dict:
        """
        Obtener mejora por ID.
        
        Args:
            mejora_id: ID de la mejora
            
        Returns:
            Dict de la mejora o None
        """
        schema = MejoraResponseSchema()
        with get_db_session() as session:
            mejora = session.query(Mejora).filter(
                Mejora.id_mejora == mejora_id
            ).first()
            return schema.dump(mejora) if mejora else None
    
    
    @staticmethod
    def listar_mejoras(cliente_id: int = None, estatus: int = None) -> list:
        """
        Listar mejoras con filtros opcionales.
        
        Args:
            cliente_id: Filtrar por cliente (opcional)
            estatus: Filtrar por estatus (opcional)
            
        Returns:
            Lista de dicts de mejoras
        """
        schema = MejoraResponseSchema()
        with get_db_session() as session:
            query = session.query(Mejora)
            
            if cliente_id:
                query = query.filter(Mejora.cliente_id == cliente_id)
            
            if estatus:
                query = query.filter(Mejora.estatus == estatus)
            
            mejoras = query.order_by(Mejora.created_at.desc()).all()
            return [schema.dump(m) for m in mejoras]
