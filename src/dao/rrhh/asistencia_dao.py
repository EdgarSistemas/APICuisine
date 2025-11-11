"""
AsistenciaDAO - Data Access Object para rrhh.Asistencia
"""

from src.models.rrhh import Asistencia, UsuarioHorario, Horario, HorarioDetalle
from src.core.db.session_manager import get_db_session
from src.schemas.rrhh_schema import AsistenciaResponseSchema
from datetime import date, datetime, time, timedelta
from sqlalchemy import and_, func
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class AsistenciaDAO:
    """Data Access Object para Asistencia"""
    
    @staticmethod
    def registrar_checkin(usuario_id: int, usuario_horario_id: int, turno_clave_id: int,
                         codigo_usuario: str, lat: Decimal = None, lng: Decimal = None,
                         device_info: str = None, ip_address: str = None) -> dict:
        """
        Registrar entrada (check-in).
        
        Args:
            usuario_id: ID del usuario
            usuario_horario_id: ID de la asignación horario
            turno_clave_id: ID del turno clave validado
            codigo_usuario: Código de 6 dígitos ingresado
            lat: Latitud (opcional)
            lng: Longitud (opcional)
            device_info: Info del dispositivo
            ip_address: IP del dispositivo
            
        Returns:
            Dict con asistencia y detección de tardanza
        """
        schema = AsistenciaResponseSchema()
        
        with get_db_session() as session:
            # 1. Verificar que no exista check-in sin check-out
            ultima_asistencia = session.query(Asistencia).filter(
                Asistencia.usuario_id == usuario_id,
                Asistencia.tipo_evento == 1  # Check-in
            ).order_by(Asistencia.evento_ts.desc()).first()
            
            if ultima_asistencia:
                # Verificar si tiene check-out correspondiente
                tiene_checkout = session.query(Asistencia).filter(
                    Asistencia.usuario_id == usuario_id,
                    Asistencia.tipo_evento == 2,  # Check-out
                    Asistencia.evento_ts > ultima_asistencia.evento_ts
                ).first()
                
                if not tiene_checkout:
                    return {
                        "success": False,
                        "error": "Ya tienes un check-in activo. Debes hacer check-out primero.",
                        "asistencia": None
                    }
            
            # 2. Obtener horario detalle del día actual
            dia_semana = date.today().isoweekday()  # 1=Lunes, 7=Domingo
            usuario_horario = session.query(UsuarioHorario).filter(
                UsuarioHorario.id_usuario_horario == usuario_horario_id
            ).first()
            
            if not usuario_horario:
                return {"success": False, "error": "Asignación de horario no encontrada", "asistencia": None}
            
            detalle = session.query(HorarioDetalle).filter(
                HorarioDetalle.horario_id == usuario_horario.horario_id,
                HorarioDetalle.dia_semana == dia_semana
            ).first()
            
            if not detalle:
                return {
                    "success": False,
                    "error": f"No hay turno configurado para hoy ({dia_semana})",
                    "asistencia": None
                }
            
            # 3. Detectar tardanza
            ahora = datetime.now()
            hora_actual = ahora.time()
            hora_inicio = detalle.hora_inicio
            tolerancia_min = detalle.tolerancia_min or 10
            
            # Calcular hora límite con tolerancia
            hora_inicio_dt = datetime.combine(date.today(), hora_inicio)
            hora_limite = (hora_inicio_dt + timedelta(minutes=tolerancia_min)).time()
            
            es_tardanza = hora_actual > hora_limite
            observaciones = None
            
            if es_tardanza:
                # Calcular minutos de retraso
                minutos_retraso = (datetime.combine(date.today(), hora_actual) - 
                                  datetime.combine(date.today(), hora_limite)).total_seconds() / 60
                observaciones = f"Tardanza de {int(minutos_retraso)} minutos"
                logger.warning(f"Usuario {usuario_id} llegó tarde: {observaciones}")
            
            # 4. Crear registro de asistencia
            asistencia = Asistencia(
                usuario_id=usuario_id,
                usuario_horario_id=usuario_horario_id,
                tipo_evento=1,  # Check-in
                evento_ts=ahora,
                lat=lat,
                lng=lng,
                device_info=device_info,
                ip_address=ip_address,
                turno_clave_id=turno_clave_id,
                codigo_usuario=codigo_usuario,
                codigo_validado=True,  # Ya fue validado
                observaciones=observaciones
            )
            session.add(asistencia)
            session.commit()
            
            resultado = {
                "success": True,
                "asistencia": schema.dump(asistencia),
                "tardanza": es_tardanza,
                "sucursal_id": usuario_horario.horario.sucursal_id if usuario_horario.horario else None
            }
            
            logger.info(f"Check-in exitoso para usuario {usuario_id} - Tardanza: {es_tardanza}")
            return resultado
    
    
    @staticmethod
    def registrar_checkout(usuario_id: int, usuario_horario_id: int, lat: Decimal = None,
                          lng: Decimal = None, device_info: str = None, 
                          ip_address: str = None, notas: str = None) -> dict:
        """
        Registrar salida (check-out).
        No requiere código.
        """
        schema = AsistenciaResponseSchema()
        
        with get_db_session() as session:
            # 1. Verificar que exista un check-in sin check-out
            ultimo_checkin = session.query(Asistencia).filter(
                Asistencia.usuario_id == usuario_id,
                Asistencia.tipo_evento == 1
            ).order_by(Asistencia.evento_ts.desc()).first()
            
            if not ultimo_checkin:
                return {
                    "success": False,
                    "error": "No tienes un check-in registrado",
                    "asistencia": None
                }
            
            # Verificar si ya tiene check-out
            tiene_checkout = session.query(Asistencia).filter(
                Asistencia.usuario_id == usuario_id,
                Asistencia.tipo_evento == 2,
                Asistencia.evento_ts > ultimo_checkin.evento_ts
            ).first()
            
            if tiene_checkout:
                return {
                    "success": False,
                    "error": "Ya hiciste check-out",
                    "asistencia": None
                }
            
            # 2. Crear check-out
            asistencia = Asistencia(
                usuario_id=usuario_id,
                usuario_horario_id=usuario_horario_id,
                tipo_evento=2,  # Check-out
                evento_ts=datetime.now(),
                lat=lat,
                lng=lng,
                device_info=device_info,
                ip_address=ip_address,
                turno_clave_id=None,
                codigo_usuario=None,
                codigo_validado=None,
                observaciones=notas
            )
            session.add(asistencia)
            session.commit()
            
            logger.info(f"Check-out exitoso para usuario {usuario_id}")
            return {
                "success": True,
                "asistencia": schema.dump(asistencia)
            }
    
    
    @staticmethod
    def listar_asistencias(usuario_id: int = None, sucursal_id: int = None,
                          fecha_inicio: date = None, fecha_fin: date = None,
                          tipo_evento: int = None, limit: int = 100, offset: int = 0) -> list:
        """
        Listar asistencias con filtros.
        
        Args:
            usuario_id: Filtrar por usuario
            sucursal_id: Filtrar por sucursal
            fecha_inicio: Fecha desde
            fecha_fin: Fecha hasta
            tipo_evento: 1=Check-in, 2=Check-out
            limit: Máximo de registros
            offset: Paginación
        """
        schema = AsistenciaResponseSchema(many=True)
        
        with get_db_session() as session:
            query = session.query(Asistencia)
            
            if usuario_id:
                query = query.filter(Asistencia.usuario_id == usuario_id)
            
            if sucursal_id:
                query = query.join(UsuarioHorario).join(Horario).filter(
                    Horario.sucursal_id == sucursal_id
                )
            
            if fecha_inicio:
                query = query.filter(func.cast(Asistencia.evento_ts, sqlalchemy.Date) >= fecha_inicio)
            
            if fecha_fin:
                query = query.filter(func.cast(Asistencia.evento_ts, sqlalchemy.Date) <= fecha_fin)
            
            if tipo_evento:
                query = query.filter(Asistencia.tipo_evento == tipo_evento)
            
            query = query.order_by(Asistencia.evento_ts.desc())
            query = query.limit(limit).offset(offset)
            
            asistencias = query.all()
            return schema.dump(asistencias)
    
    
    @staticmethod
    def obtener_ultima_asistencia(usuario_id: int, tipo_evento: int = None) -> dict:
        """Obtener la última asistencia de un usuario"""
        schema = AsistenciaResponseSchema()
        
        with get_db_session() as session:
            query = session.query(Asistencia).filter(
                Asistencia.usuario_id == usuario_id
            )
            
            if tipo_evento:
                query = query.filter(Asistencia.tipo_evento == tipo_evento)
            
            asistencia = query.order_by(Asistencia.evento_ts.desc()).first()
            return schema.dump(asistencia) if asistencia else None
    
    
    @staticmethod
    def obtener_por_id(id_asistencia: int) -> dict:
        """Obtener asistencia por ID"""
        schema = AsistenciaResponseSchema()
        with get_db_session() as session:
            asistencia = session.query(Asistencia).filter(
                Asistencia.id_asistencia == id_asistencia
            ).first()
            return schema.dump(asistencia) if asistencia else None
    
    
    @staticmethod
    def contar_tardanzas(usuario_id: int, fecha_inicio: date = None, fecha_fin: date = None) -> int:
        """Contar tardanzas de un usuario en un período"""
        with get_db_session() as session:
            query = session.query(func.count(Asistencia.id_asistencia)).filter(
                Asistencia.usuario_id == usuario_id,
                Asistencia.tipo_evento == 1,
                Asistencia.observaciones.like('%Tardanza%')
            )
            
            if fecha_inicio:
                query = query.filter(func.cast(Asistencia.evento_ts, sqlalchemy.Date) >= fecha_inicio)
            
            if fecha_fin:
                query = query.filter(func.cast(Asistencia.evento_ts, sqlalchemy.Date) <= fecha_fin)
            
            return query.scalar() or 0
