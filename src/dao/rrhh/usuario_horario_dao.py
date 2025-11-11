"""
UsuarioHorarioDAO - Data Access Object para rrhh.UsuarioHorario
"""

from src.models.rrhh import UsuarioHorario
from src.core.db.session_manager import get_db_session
from src.schemas.rrhh_schema import UsuarioHorarioResponseSchema
from datetime import date
import logging

logger = logging.getLogger(__name__)


class UsuarioHorarioDAO:
    """Data Access Object para UsuarioHorario"""
    
    @staticmethod
    def asignar_horario(usuario_id: int, horario_id: int, fecha_inicio: date, fecha_fin: date = None) -> dict:
        """
        Asignar horario a un usuario.
        IMPORTANTE: Solo puede tener UN horario activo a la vez.
        """
        schema = UsuarioHorarioResponseSchema()
        
        with get_db_session() as session:
            # 1. Desactivar horarios anteriores del usuario
            session.query(UsuarioHorario).filter(
                UsuarioHorario.usuario_id == usuario_id,
                UsuarioHorario.es_activo == True
            ).update({"es_activo": False})
            
            # 2. Crear nueva asignación
            asignacion = UsuarioHorario(
                usuario_id=usuario_id,
                horario_id=horario_id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                es_recurring=True,
                es_activo=True
            )
            session.add(asignacion)
            session.commit()
            
            logger.info(f"Horario {horario_id} asignado a usuario {usuario_id}")
            return schema.dump(asignacion)
    
    
    @staticmethod
    def obtener_horario_activo_usuario(usuario_id: int) -> dict:
        """Obtener horario activo del usuario"""
        schema = UsuarioHorarioResponseSchema()
        with get_db_session() as session:
            asignacion = session.query(UsuarioHorario).filter(
                UsuarioHorario.usuario_id == usuario_id,
                UsuarioHorario.es_activo == True
            ).first()
            return schema.dump(asignacion) if asignacion else None
    
    
    @staticmethod
    def listar_asignaciones_por_horario(horario_id: int) -> list:
        """Listar todos los usuarios asignados a un horario"""
        schema = UsuarioHorarioResponseSchema()
        with get_db_session() as session:
            asignaciones = session.query(UsuarioHorario).filter(
                UsuarioHorario.horario_id == horario_id,
                UsuarioHorario.es_activo == True
            ).all()
            return [schema.dump(a) for a in asignaciones]
    
    
    @staticmethod
    def desactivar_horario_usuario(usuario_id: int) -> bool:
        """Desactivar horario activo del usuario"""
        with get_db_session() as session:
            result = session.query(UsuarioHorario).filter(
                UsuarioHorario.usuario_id == usuario_id,
                UsuarioHorario.es_activo == True
            ).update({"es_activo": False})
            session.commit()
            return result > 0
