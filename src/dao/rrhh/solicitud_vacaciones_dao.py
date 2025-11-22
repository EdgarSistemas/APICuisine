"""
SolicitudVacacionesDAO - Data Access Object para rrhh.SolicitudVacaciones
"""

from src.models.rrhh import SolicitudVacaciones, UsuarioHorario, Horario
from src.models.auth import Usuario
from src.core.db.session_manager import get_db_session
from src.schemas.rrhh_schema import SolicitudVacacionesResponseSchema
from datetime import date, datetime
from sqlalchemy import and_, func
import logging

logger = logging.getLogger(__name__)


class SolicitudVacacionesDAO:
    """Data Access Object para SolicitudVacaciones"""
    
    @staticmethod
    def crear_solicitud(usuario_horario_id: int, fecha_inicio: date, fecha_fin: date, motivo: str = None) -> dict:
        """
        Crear solicitud de vacaciones.
        
        Args:
            usuario_horario_id: ID de la asignación de horario del empleado
            fecha_inicio: Fecha inicial de vacaciones
            fecha_fin: Fecha final de vacaciones
            motivo: Motivo de la solicitud (opcional)
            
        Returns:
            Dict con la solicitud creada
        """
        schema = SolicitudVacacionesResponseSchema()
        
        with get_db_session() as session:
            # Validar que el horario_usuario_id existe
            horario_usuario = session.query(UsuarioHorario).filter(
                UsuarioHorario.id_usuario_horario == usuario_horario_id,
                UsuarioHorario.es_activo == True
            ).first()
            
            if not horario_usuario:
                return {
                    "success": False,
                    "error": "Asignación de horario no encontrada o inactiva",
                    "solicitud": None
                }
            
            # Validar que fecha_fin >= fecha_inicio
            if fecha_fin < fecha_inicio:
                return {
                    "success": False,
                    "error": "La fecha de fin debe ser mayor o igual a la fecha de inicio",
                    "solicitud": None
                }
            
            # Validar que no haya solapamiento con otras solicitudes aprobadas del mismo usuario
            usuario_id = horario_usuario.usuario_id
            solapamiento = session.query(SolicitudVacaciones).join(
                UsuarioHorario, SolicitudVacaciones.horario_usuario_id == UsuarioHorario.id_usuario_horario
            ).filter(
                UsuarioHorario.usuario_id == usuario_id,
                SolicitudVacaciones.estatus == 2,  # Aprobada
                and_(
                    SolicitudVacaciones.fecha_inicio <= fecha_fin,
                    SolicitudVacaciones.fecha_fin >= fecha_inicio
                )
            ).first()
            
            if solapamiento:
                return {
                    "success": False,
                    "error": f"Ya tienes vacaciones aprobadas del {solapamiento.fecha_inicio} al {solapamiento.fecha_fin}",
                    "solicitud": None
                }
            
            # Crear solicitud
            solicitud = SolicitudVacaciones(
                horario_usuario_id=usuario_horario_id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                motivo=motivo,
                estatus=1,  # Pendiente
                created_at=datetime.now()
            )
            session.add(solicitud)
            session.commit()
            session.refresh(solicitud)
            
            logger.info(f"Solicitud de vacaciones creada: ID {solicitud.id_solicitud} para horario_usuario {usuario_horario_id}")
            return {
                "success": True,
                "solicitud": schema.dump(solicitud)
            }
    
    
    @staticmethod
    def listar_solicitudes(usuario_id: int = None, sucursal_id: int = None,
                          estatus: int = None, limit: int = 100, offset: int = 0) -> list:
        """
        Listar solicitudes de vacaciones.
        
        Args:
            usuario_id: Filtrar por usuario solicitante
            sucursal_id: Filtrar por sucursal
            estatus: 1=Pendiente, 2=Aprobada, 3=Rechazada
            limit: Máximo de registros
            offset: Paginación
        """
        schema = SolicitudVacacionesResponseSchema(many=True)
        
        with get_db_session() as session:
            query = session.query(SolicitudVacaciones)
            
            # Filtrar por usuario
            if usuario_id:
                query = query.join(UsuarioHorario, SolicitudVacaciones.horario_usuario_id == UsuarioHorario.id_usuario_horario).filter(
                    UsuarioHorario.usuario_id == usuario_id
                )
            
            # Filtrar por sucursal
            if sucursal_id:
                query = query.join(UsuarioHorario, SolicitudVacaciones.horario_usuario_id == UsuarioHorario.id_usuario_horario).join(
                    Horario, UsuarioHorario.horario_id == Horario.id_horario
                ).filter(
                    Horario.sucursal_id == sucursal_id
                )
            
            # Filtrar por estatus
            if estatus:
                query = query.filter(SolicitudVacaciones.estatus == estatus)
            
            # Ordenar por fecha de creación descendente
            query = query.order_by(SolicitudVacaciones.created_at.desc())
            query = query.limit(limit).offset(offset)
            
            solicitudes = query.all()
            return schema.dump(solicitudes)
    
    
    @staticmethod
    def obtener_por_id(id_solicitud: int) -> dict:
        """Obtener solicitud por ID"""
        schema = SolicitudVacacionesResponseSchema()
        with get_db_session() as session:
            solicitud = session.query(SolicitudVacaciones).filter(
                SolicitudVacaciones.id_solicitud == id_solicitud
            ).first()
            return schema.dump(solicitud) if solicitud else None
    
    
    @staticmethod
    def aprobar_solicitud(id_solicitud: int, revisado_por: int) -> dict:
        """
        Aprobar solicitud de vacaciones.
        Solo el gerente de la sucursal puede aprobar.
        
        Args:
            id_solicitud: ID de la solicitud
            revisado_por: ID del gerente que aprueba
        """
        schema = SolicitudVacacionesResponseSchema()
        
        with get_db_session() as session:
            solicitud = session.query(SolicitudVacaciones).filter(
                SolicitudVacaciones.id_solicitud == id_solicitud
            ).first()
            
            if not solicitud:
                return {"success": False, "error": "Solicitud no encontrada", "solicitud": None}
            
            if solicitud.estatus != 1:
                return {
                    "success": False,
                    "error": f"La solicitud ya fue {'aprobada' if solicitud.estatus == 2 else 'rechazada'}",
                    "solicitud": schema.dump(solicitud)
                }
            
            # Actualizar solicitud
            solicitud.estatus = 2  # Aprobada
            session.commit()
            session.refresh(solicitud)
            
            logger.info(f"Solicitud {id_solicitud} aprobada por gerente {revisado_por}")
            return {
                "success": True,
                "solicitud": schema.dump(solicitud)
            }
    
    
    @staticmethod
    def rechazar_solicitud(id_solicitud: int, revisado_por: int, notas_gerente: str = None) -> dict:
        """
        Rechazar solicitud de vacaciones.
        
        Args:
            id_solicitud: ID de la solicitud
            revisado_por: ID del gerente que rechaza
            notas_gerente: Notas/motivo del rechazo (ignorado, para compatibilidad)
        """
        schema = SolicitudVacacionesResponseSchema()
        
        with get_db_session() as session:
            solicitud = session.query(SolicitudVacaciones).filter(
                SolicitudVacaciones.id_solicitud == id_solicitud
            ).first()
            
            if not solicitud:
                return {"success": False, "error": "Solicitud no encontrada", "solicitud": None}
            
            if solicitud.estatus != 1:
                return {
                    "success": False,
                    "error": f"La solicitud ya fue {'aprobada' if solicitud.estatus == 2 else 'rechazada'}",
                    "solicitud": schema.dump(solicitud)
                }
            
            # Actualizar solicitud
            solicitud.estatus = 3  # Rechazada
            session.commit()
            session.refresh(solicitud)
            
            logger.info(f"Solicitud {id_solicitud} rechazada por gerente {revisado_por}")
            return {
                "success": True,
                "solicitud": schema.dump(solicitud)
            }
    
    
    @staticmethod
    def contar_solicitudes_pendientes(sucursal_id: int = None) -> int:
        """Contar solicitudes pendientes (estatus=1)"""
        with get_db_session() as session:
            query = session.query(func.count(SolicitudVacaciones.id_solicitud)).filter(
                SolicitudVacaciones.estatus == 1
            )
            
            if sucursal_id:
                query = query.join(UsuarioHorario, SolicitudVacaciones.horario_usuario_id == UsuarioHorario.id_usuario_horario).join(
                    Horario, UsuarioHorario.horario_id == Horario.id_horario
                ).filter(
                    Horario.sucursal_id == sucursal_id
                )
            
            return query.scalar() or 0
    
    
    @staticmethod
    def obtener_vacaciones_activas(usuario_id: int, fecha: date = None) -> list:
        """
        Obtener vacaciones aprobadas activas para un usuario.
        
        Args:
            usuario_id: ID del usuario
            fecha: Fecha a verificar (default: hoy)
        """
        schema = SolicitudVacacionesResponseSchema(many=True)
        fecha = fecha or date.today()
        
        with get_db_session() as session:
            solicitudes = session.query(SolicitudVacaciones).join(
                UsuarioHorario, SolicitudVacaciones.horario_usuario_id == UsuarioHorario.id_usuario_horario
            ).filter(
                UsuarioHorario.usuario_id == usuario_id,
                SolicitudVacaciones.estatus == 2,  # Aprobada
                SolicitudVacaciones.fecha_inicio <= fecha,
                SolicitudVacaciones.fecha_fin >= fecha
            ).all()
            
            return schema.dump(solicitudes)
