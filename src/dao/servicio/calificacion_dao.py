"""
CalificacionDAO - Data Access Object para servicio.Calificacion
"""

from src.models.servicio import Calificacion
from src.core.db.session_manager import get_db_session
from src.schemas.servicio_schema import CalificacionResponseSchema
import logging

logger = logging.getLogger(__name__)


class CalificacionDAO:
    """Data Access Object para Calificacion"""
    
    @staticmethod
    def crear_calificacion(cliente_id: int, pedido_id: int, empleado_id: int, calificacion: int, notas: str = None) -> dict:
        """
        Crear nueva calificación de servicio.
        
        Args:
            cliente_id: ID del cliente que califica
            pedido_id: ID del pedido
            empleado_id: ID del empleado (mesero) calificado
            calificacion: Calificación (1-10)
            notas: Comentarios adicionales (opcional)
            
        Returns:
            Dict serializado de la calificación
        """
        schema = CalificacionResponseSchema()
        with get_db_session() as session:
            calif = Calificacion(
                cliente_id=cliente_id,
                pedido_id=pedido_id,
                empleado_id=empleado_id,
                calificacion=calificacion,
                notas=notas,
                es_activo=1  # Registrada
            )
            session.add(calif)
            session.commit()
            logger.info(f"Calificación creada: pedido {pedido_id}, empleado {empleado_id}, calificación {calificacion}")
            return schema.dump(calif)
    
    
    @staticmethod
    def obtener_calificacion_por_id(calificacion_id: int) -> dict:
        """
        Obtener calificación por ID.
        
        Args:
            calificacion_id: ID de la calificación
            
        Returns:
            Dict de la calificación o None
        """
        schema = CalificacionResponseSchema()
        with get_db_session() as session:
            calif = session.query(Calificacion).filter(
                Calificacion.id_calificacion == calificacion_id
            ).first()
            return schema.dump(calif) if calif else None
    
    
    @staticmethod
    def listar_calificaciones(pedido_id: int = None, empleado_id: int = None, cliente_id: int = None) -> list:
        """
        Listar calificaciones con filtros opcionales.
        
        Args:
            pedido_id: Filtrar por pedido (opcional)
            empleado_id: Filtrar por empleado (opcional)
            cliente_id: Filtrar por cliente (opcional)
            
        Returns:
            Lista de dicts de calificaciones
        """
        schema = CalificacionResponseSchema()
        with get_db_session() as session:
            query = session.query(Calificacion).filter(Calificacion.es_activo == 1)
            
            if pedido_id:
                query = query.filter(Calificacion.pedido_id == pedido_id)
            
            if empleado_id:
                query = query.filter(Calificacion.empleado_id == empleado_id)
            
            if cliente_id:
                query = query.filter(Calificacion.cliente_id == cliente_id)
            
            calificaciones = query.order_by(Calificacion.created_at.desc()).all()
            return [schema.dump(c) for c in calificaciones]
    
    
    @staticmethod
    def obtener_promedio_empleado(empleado_id: int) -> float:
        """
        Obtener promedio de calificaciones de un empleado.
        
        Args:
            empleado_id: ID del empleado
            
        Returns:
            Promedio de calificaciones (0.0 si no tiene)
        """
        from sqlalchemy import func
        with get_db_session() as session:
            promedio = session.query(func.avg(Calificacion.calificacion)).filter(
                Calificacion.empleado_id == empleado_id,
                Calificacion.es_activo == 1
            ).scalar()
            return float(promedio) if promedio else 0.0
    
    
    @staticmethod
    def existe_calificacion_pedido(pedido_id: int, cliente_id: int) -> bool:
        """
        Verificar si ya existe calificación para un pedido por parte del cliente.
        
        Args:
            pedido_id: ID del pedido
            cliente_id: ID del cliente
            
        Returns:
            True si ya existe
        """
        with get_db_session() as session:
            existe = session.query(Calificacion).filter(
                Calificacion.pedido_id == pedido_id,
                Calificacion.cliente_id == cliente_id,
                Calificacion.es_activo == 1
            ).first()
            return existe is not None
