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
    def crear_solicitud(usuario_id: int, usuario_horario_id: int, fecha_inicio: date,
                       fecha_fin: date, motivo: str = None) -> dict:
        """
        Crear solicitud de vacaciones.
        
        Args:
            usuario_id: ID del empleado solicitante
            usuario_horario_id: ID de la asignación de horario
            fecha_inicio: Fecha inicial de vacaciones
            fecha_fin: Fecha final de vacaciones
            motivo: Motivo de la solicitud (opcional)
            
        Returns:
            Dict con la solicitud creada
        """
        schema = SolicitudVacacionesResponseSchema()
        
        with get_db_session() as session:
            # 1. Validar que fecha_fin >= fecha_inicio
            if fecha_fin < fecha_inicio:
                return {
                    "success": False,
                    "error": "La fecha de fin debe ser mayor o igual a la fecha de inicio",
                    "solicitud": None
                }
            
            # 2. Validar que no haya solapamiento con otras solicitudes aprobadas
            solapamiento = session.query(SolicitudVacaciones).filter(
                SolicitudVacaciones.usuario_id == usuario_id,
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
            
            # 3. Crear solicitud
            solicitud = SolicitudVacaciones(
                usuario_id=usuario_id,
                usuario_horario_id=usuario_horario_id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                motivo=motivo,
                estatus=1,  # Pendiente
                solicitado_en=datetime.now(),
                revisado_por=None,
                revisado_en=None,
                notas_gerente=None
            )
            session.add(solicitud)
            session.commit()
            
            logger.info(f"Solicitud de vacaciones creada: ID {solicitud.id_solicitud} para usuario {usuario_id}")
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
            
            if usuario_id:
                query = query.filter(SolicitudVacaciones.usuario_id == usuario_id)
            
            if sucursal_id:
                query = query.join(UsuarioHorario).join(Horario).filter(
                    Horario.sucursal_id == sucursal_id
                )
            
            if estatus:
                query = query.filter(SolicitudVacaciones.estatus == estatus)
            
            query = query.order_by(SolicitudVacaciones.solicitado_en.desc())
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
    def aprobar_solicitud(id_solicitud: int, revisado_por: int, notas_gerente: str = None) -> dict:
        """
        Aprobar solicitud de vacaciones.
        Solo el gerente de la sucursal puede aprobar.
        
        Args:
            id_solicitud: ID de la solicitud
            revisado_por: ID del gerente que aprueba
            notas_gerente: Notas del gerente (opcional)
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
            solicitud.revisado_por = revisado_por
            solicitud.revisado_en = datetime.now()
            solicitud.notas_gerente = notas_gerente
            
            # TODO: Desactivar UsuarioHorario para esas fechas (opcional)
            # Esto se puede hacer en el servicio si se requiere
            
            session.commit()
            
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
            notas_gerente: Motivo del rechazo (opcional pero recomendado)
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
            solicitud.revisado_por = revisado_por
            solicitud.revisado_en = datetime.now()
            solicitud.notas_gerente = notas_gerente or "Sin motivo especificado"
            
            session.commit()
            
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
                query = query.join(UsuarioHorario).join(Horario).filter(
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
            solicitudes = session.query(SolicitudVacaciones).filter(
                SolicitudVacaciones.usuario_id == usuario_id,
                SolicitudVacaciones.estatus == 2,  # Aprobada
                SolicitudVacaciones.fecha_inicio <= fecha,
                SolicitudVacaciones.fecha_fin >= fecha
            ).all()
            
            return schema.dump(solicitudes)
