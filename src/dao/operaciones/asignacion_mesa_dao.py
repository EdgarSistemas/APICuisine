"""
AsignacionMesaDAO - Data Access Object para operaciones.AsignacionMesa
Queries para CRUD de asignaciones de mesas a meseros
"""

from src.models import AsignacionMesa, Mesa, Area
from src.core.db.session_manager import get_db_session
from src.schemas.asignacion_mesa_schema import AsignacionMesaResponseSchema
from src.schemas.mesa_schema import MesaResponseSchema
import logging

logger = logging.getLogger(__name__)


class AsignacionMesaDAO:
    """Data Access Object para AsignacionMesa"""
    
    @staticmethod
    def asignar_mesero(mesa_id: int, usuario_id: int) -> dict:
        """
        Asignar un mesero a una mesa.
        
        IMPORTANTE: Primero desactivar cualquier asignación anterior de esta mesa
        (para mantener solo 1 mesero activo por mesa).
        
        Args:
            mesa_id: ID de la mesa
            usuario_id: ID del mesero (usuario)
            
        Returns:
            Dict serializado de la asignación
        """
        schema = AsignacionMesaResponseSchema()
        with get_db_session() as session:
            # Desactivar asignaciones previas de esta mesa
            asignaciones_previas = session.query(AsignacionMesa).filter(
                AsignacionMesa.mesa_id == mesa_id,
                AsignacionMesa.es_activa == True
            ).all()
            
            for asig in asignaciones_previas:
                asig.es_activa = False
            
            # Crear nueva asignación
            asignacion = AsignacionMesa(
                mesa_id=mesa_id,
                usuario_id=usuario_id,
                es_activa=True
            )
            session.add(asignacion)
            session.flush()
            session.refresh(asignacion)
            session.commit()
            logger.info(f"Mesero {usuario_id} asignado a mesa {mesa_id}")
            return schema.dump(asignacion)
    
    
    @staticmethod
    def desasignar_mesero(asignacion_id: int) -> bool:
        """
        Desasignar un mesero de una mesa (soft delete).
        
        Args:
            asignacion_id: ID de la asignación
            
        Returns:
            True si se desasignó, False si no existe
        """
        with get_db_session() as session:
            asignacion = session.query(AsignacionMesa).filter(
                AsignacionMesa.id_asignacion_mesa == asignacion_id
            ).first()
            
            if not asignacion:
                return False
            
            asignacion.es_activa = False
            session.commit()
            logger.info(f"Asignación {asignacion_id} desactivada")
            return True
    
    
    @staticmethod
    def obtener_asignacion_por_id(asignacion_id: int) -> bool:
        """
        Verificar si una asignación existe.
        
        Args:
            asignacion_id: ID de la asignación
            
        Returns:
            True si existe, False si no
        """
        with get_db_session() as session:
            asignacion = session.query(AsignacionMesa).filter(
                AsignacionMesa.id_asignacion_mesa == asignacion_id
            ).first()
            return asignacion is not None
    
    
    @staticmethod
    def obtener_asignaciones_por_mesa(mesa_id: int, solo_activas: bool = True) -> list:
        """
        Obtener todas las asignaciones de una mesa.
        
        Args:
            mesa_id: ID de la mesa
            solo_activas: Si True, solo asignaciones activas
            
        Returns:
            Lista de dicts de AsignacionMesa
        """
        schema = AsignacionMesaResponseSchema()
        with get_db_session() as session:
            query = session.query(AsignacionMesa).filter(AsignacionMesa.mesa_id == mesa_id)
            
            if solo_activas:
                query = query.filter(AsignacionMesa.es_activa == True)
            
            asignaciones = query.order_by(AsignacionMesa.created_at.desc()).all()
            return [schema.dump(a) for a in asignaciones]
    
    
    @staticmethod
    def obtener_mesas_por_mesero(usuario_id: int, solo_activas: bool = True) -> list:
        """
        Obtener todas las mesas asignadas a un mesero.
        
        Args:
            usuario_id: ID del mesero
            solo_activas: Si True, solo asignaciones activas
            
        Returns:
            Lista de dicts de Mesas
        """
        schema = MesaResponseSchema()
        with get_db_session() as session:
            query = session.query(Mesa).join(AsignacionMesa).filter(
                AsignacionMesa.usuario_id == usuario_id
            )
            
            if solo_activas:
                query = query.filter(AsignacionMesa.es_activa == True)
            
            mesas = query.order_by(Mesa.codigo_mesa).all()
            return [schema.dump(m) for m in mesas]
    
    
    @staticmethod
    def obtener_asignacion_activa_mesa(mesa_id: int) -> dict:
        """
        Obtener la asignación ACTIVA de una mesa (debe haber solo 1).
        
        Args:
            mesa_id: ID de la mesa
            
        Returns:
            Dict de AsignacionMesa (la activa) o None
        """
        schema = AsignacionMesaResponseSchema()
        with get_db_session() as session:
            asignacion = session.query(AsignacionMesa).filter(
                AsignacionMesa.mesa_id == mesa_id,
                AsignacionMesa.es_activa == True
            ).first()
            return schema.dump(asignacion) if asignacion else None
    
    
    @staticmethod
    def mesa_existe(mesa_id: int) -> bool:
        """
        Verificar si una mesa existe.
        
        Args:
            mesa_id: ID de la mesa
            
        Returns:
            True si existe
        """
        with get_db_session() as session:
            existe = session.query(Mesa).filter(Mesa.id_mesa == mesa_id).first()
            return existe is not None
    
    
    @staticmethod
    def usuario_existe(usuario_id: int) -> bool:
        """
        Verificar si un usuario existe.
        
        Args:
            usuario_id: ID del usuario
            
        Returns:
            True si existe
        """
        from src.models import Usuario
        with get_db_session() as session:
            existe = session.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
            return existe is not None
    
    
    @staticmethod
    def obtener_sucursal_de_mesa(mesa_id: int) -> int:
        """
        Obtener sucursal_id de una mesa (via Area).
        
        Args:
            mesa_id: ID de la mesa
            
        Returns:
            sucursal_id o None
        """
        with get_db_session() as session:
            resultado = session.query(Area.sucursal_id).join(Mesa).filter(
                Mesa.id_mesa == mesa_id
            ).first()
            return resultado[0] if resultado else None
