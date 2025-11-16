"""
HorarioDAO - Data Access Object para rrhh.Horario
"""

from src.models.rrhh import Horario, HorarioDetalle
from src.models.rrhh.usuario_horario_model import UsuarioHorario
from src.models.rrhh.turno_clave_model import TurnoClave
from src.core.db.session_manager import get_db_session
from src.schemas.rrhh_schema import HorarioResponseSchema, HorarioDetalleResponseSchema
from datetime import time, date, datetime, timedelta
import logging
import random
import string

logger = logging.getLogger(__name__)


class HorarioDAO:
    """Data Access Object para Horario"""
    
    @staticmethod
    def crear_horario_con_detalles(sucursal_id: int, clave: str, nombre: str, descripcion: str, detalles: list) -> dict:
        """
        Crear horario con sus detalles en una sola transacción.
        
        Args:
            sucursal_id: ID de sucursal (NULL = global)
            clave: Clave única del horario
            nombre: Nombre descriptivo
            descripcion: Descripción (opcional)
            detalles: Lista de dicts con dia_semana, hora_inicio, hora_fin, tolerancia_min
            
        Returns:
            Dict con horario y detalles creados
        """
        schema_horario = HorarioResponseSchema()
        schema_detalle = HorarioDetalleResponseSchema()
        
        with get_db_session() as session:
            # 1. Crear Horario
            horario = Horario(
                sucursal_id=sucursal_id,
                clave=clave,
                nombre=nombre,
                descripcion=descripcion,
                es_activo=True
            )
            session.add(horario)
            session.flush()
            
            # 2. Crear HorarioDetalles
            detalles_creados = []
            for detalle_data in detalles:
                # Convertir strings de hora a objetos time si es necesario
                hora_inicio = detalle_data['hora_inicio']
                hora_fin = detalle_data['hora_fin']
                
                if isinstance(hora_inicio, str):
                    hora_inicio = time.fromisoformat(hora_inicio)
                if isinstance(hora_fin, str):
                    hora_fin = time.fromisoformat(hora_fin)
                
                detalle = HorarioDetalle(
                    horario_id=horario.id_horario,
                    dia_semana=detalle_data['dia_semana'],
                    hora_inicio=hora_inicio,
                    hora_fin=hora_fin,
                    turno_idx=detalle_data.get('turno_idx', 1),
                    tolerancia_min=detalle_data.get('tolerancia_min', 10),
                    es_activo=True
                )
                session.add(detalle)
                session.flush()
                detalles_creados.append(schema_detalle.dump(detalle))
            
            session.commit()
            
            logger.info(f"Horario creado: {clave} con {len(detalles_creados)} detalles")
            
            return {
                "horario": schema_horario.dump(horario),
                "detalles": detalles_creados
            }
    
    @staticmethod
    def obtener_horario_por_id(horario_id: int) -> dict:
        """Obtener solo el horario por ID (sin detalles)"""
        schema = HorarioResponseSchema()
        with get_db_session() as session:
            horario = session.query(Horario).filter(
                Horario.id_horario == horario_id
            ).first()
            return schema.dump(horario) if horario else None
    
    
    @staticmethod
    def obtener_horario_con_detalles(horario_id: int) -> dict:
        """Obtener horario por ID con todos sus detalles"""
        schema_horario = HorarioResponseSchema()
        schema_detalle = HorarioDetalleResponseSchema()
        
        with get_db_session() as session:
            horario = session.query(Horario).filter(
                Horario.id_horario == horario_id
            ).first()
            
            if not horario:
                return None
            
            detalles = session.query(HorarioDetalle).filter(
                HorarioDetalle.horario_id == horario_id,
                HorarioDetalle.es_activo == True
            ).order_by(HorarioDetalle.dia_semana).all()
            
            return {
                "horario": schema_horario.dump(horario),
                "detalles": [schema_detalle.dump(d) for d in detalles]
            }
    
    @staticmethod
    def obtener_detalles_horario(horario_id: int) -> list:
        """Obtener detalles de un horario"""
        schema = HorarioDetalleResponseSchema()
        with get_db_session() as session:
            detalles = session.query(HorarioDetalle).filter(
                HorarioDetalle.horario_id == horario_id,
                HorarioDetalle.es_activo == True
            ).order_by(HorarioDetalle.dia_semana).all()
            return [schema.dump(d) for d in detalles]
    
    @staticmethod
    def listar_horarios(sucursal_id: int = None, solo_activos: bool = True) -> list:
        """Listar horarios con sus detalles"""
        schema_horario = HorarioResponseSchema()
        schema_detalle = HorarioDetalleResponseSchema()
        
        with get_db_session() as session:
            query = session.query(Horario)
            
            if sucursal_id:
                query = query.filter(Horario.sucursal_id == sucursal_id)
            
            if solo_activos:
                query = query.filter(Horario.es_activo == True)
            
            horarios = query.order_by(Horario.nombre).all()
            
            # Para cada horario, obtener sus detalles
            resultado = []
            for horario in horarios:
                detalles = session.query(HorarioDetalle).filter(
                    HorarioDetalle.horario_id == horario.id_horario,
                    HorarioDetalle.es_activo == True
                ).order_by(HorarioDetalle.dia_semana).all()
                
                resultado.append({
                    "horario": schema_horario.dump(horario),
                    "detalles": [schema_detalle.dump(d) for d in detalles]
                })
            
            return resultado
    
    @staticmethod
    def horario_existe(horario_id: int) -> bool:
        """Verificar si un horario existe"""
        with get_db_session() as session:
            existe = session.query(Horario).filter(
                Horario.id_horario == horario_id
            ).first()
            return existe is not None
    
    @staticmethod
    def clave_existe(clave: str) -> bool:
        """Verificar si una clave ya existe"""
        with get_db_session() as session:
            existe = session.query(Horario).filter(
                Horario.clave == clave
            ).first()
            return existe is not None
    
    
    @staticmethod
    def actualizar_horario(horario_id: int, datos: dict) -> dict:
        """Actualizar información básica del horario (no los detalles)"""
        schema = HorarioResponseSchema()
        
        with get_db_session() as session:
            horario = session.query(Horario).filter(
                Horario.id_horario == horario_id
            ).first()
            
            if not horario:
                return None
            
            # Actualizar campos
            if 'nombre' in datos:
                horario.nombre = datos['nombre']
            if 'clave' in datos:
                horario.clave = datos['clave']
            if 'descripcion' in datos:
                horario.descripcion = datos['descripcion']
            if 'es_activo' in datos:
                horario.es_activo = datos['es_activo']
            
            session.commit()
            session.refresh(horario)
            
            logger.info(f"Horario actualizado: ID {horario_id}")
            return schema.dump(horario)
    
    
    @staticmethod
    def desactivar_horario(horario_id: int) -> bool:
        """Desactivar horario (soft delete)"""
        with get_db_session() as session:
            horario = session.query(Horario).filter(
                Horario.id_horario == horario_id
            ).first()
            
            if not horario:
                return False
            
            horario.es_activo = False
            session.commit()
            
            logger.info(f"Horario desactivado: ID {horario_id}")
            return True
    
    
    @staticmethod
    def obtener_horario_usuario(usuario_id: int, fecha_consulta: date = None) -> dict:
        """Obtener horario activo asignado a un usuario con detalles completos"""
        schema_horario = HorarioResponseSchema()
        schema_detalle = HorarioDetalleResponseSchema()
        
        if not fecha_consulta:
            fecha_consulta = date.today()
        
        with get_db_session() as session:
            # Buscar asignación activa del usuario que esté vigente en la fecha consultada
            asignacion = session.query(UsuarioHorario).filter(
                UsuarioHorario.usuario_id == usuario_id,
                UsuarioHorario.es_activo == True,
                UsuarioHorario.fecha_inicio <= fecha_consulta,
                (UsuarioHorario.fecha_fin >= fecha_consulta) | (UsuarioHorario.fecha_fin == None)
            ).first()
            
            if not asignacion:
                return None
            
            # Obtener el horario completo
            horario = session.query(Horario).filter(
                Horario.id_horario == asignacion.horario_id
            ).first()
            
            if not horario:
                return None
            
            # Obtener detalles del horario
            detalles = session.query(HorarioDetalle).filter(
                HorarioDetalle.horario_id == horario.id_horario,
                HorarioDetalle.es_activo == True
            ).order_by(HorarioDetalle.dia_semana).all()
            
            return {
                "usuario_horario": {
                    "id_usuario_horario": asignacion.id_usuario_horario,
                    "usuario_id": asignacion.usuario_id,
                    "fecha_inicio": asignacion.fecha_inicio.isoformat() if asignacion.fecha_inicio else None,
                    "fecha_fin": asignacion.fecha_fin.isoformat() if asignacion.fecha_fin else None,
                    "es_recurring": asignacion.es_recurring
                },
                "horario": schema_horario.dump(horario),
                "detalles": [schema_detalle.dump(d) for d in detalles]
            }
    
    
    @staticmethod
    def obtener_codigo_turno(horario_id: int, fecha: date) -> dict:
        """Obtener código de turno para un horario y fecha específicos"""
        with get_db_session() as session:
            turno = session.query(TurnoClave).filter(
                TurnoClave.horario_id == horario_id,
                TurnoClave.fecha == fecha,
                TurnoClave.es_activo == True
            ).first()
            
            if not turno:
                return None
            
            return {
                "id_turno_clave": turno.id_turno_clave,
                "horario_id": turno.horario_id,
                "sucursal_id": turno.sucursal_id,
                "fecha": turno.fecha.isoformat(),
                "turno_idx": turno.turno_idx,
                "codigo": turno.codigo,
                "es_activo": turno.es_activo,
                "generado_en": turno.generado_en.isoformat() if turno.generado_en else None,
                "expira_en": turno.expira_en.isoformat() if turno.expira_en else None,
                "uso_maximo": turno.uso_maximo,
                "usos_count": turno.usos_count
            }
    
    
    @staticmethod
    def asignar_horario_a_usuario(usuario_id: int, horario_id: int, fecha_inicio: date, fecha_fin: date = None) -> dict:
        """Asignar un horario a un usuario"""
        with get_db_session() as session:
            # Verificar que el horario existe y está activo
            horario = session.query(Horario).filter(
                Horario.id_horario == horario_id,
                Horario.es_activo == True
            ).first()
            
            if not horario:
                return {"error": "HORARIO_NO_ENCONTRADO", "data": None}
            
            # Verificar si el usuario ya tiene un horario activo
            horario_activo_existente = session.query(UsuarioHorario).filter(
                UsuarioHorario.usuario_id == usuario_id,
                UsuarioHorario.es_activo == True
            ).first()
            
            if horario_activo_existente:
                return {
                    "error": "USUARIO_YA_TIENE_HORARIO",
                    "data": None,
                    "horario_actual": horario_activo_existente.horario_id
                }
            
            # Crear nueva asignación
            nueva_asignacion = UsuarioHorario(
                usuario_id=usuario_id,
                horario_id=horario_id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                es_recurring=True,
                es_activo=True
            )
            
            session.add(nueva_asignacion)
            session.commit()
            session.refresh(nueva_asignacion)
            
            logger.info(f"Horario {horario_id} asignado a usuario {usuario_id}")
            
            return {
                "error": None,
                "data": {
                    "id_usuario_horario": nueva_asignacion.id_usuario_horario,
                    "usuario_id": nueva_asignacion.usuario_id,
                    "horario_id": nueva_asignacion.horario_id,
                    "fecha_inicio": nueva_asignacion.fecha_inicio.isoformat(),
                    "fecha_fin": nueva_asignacion.fecha_fin.isoformat() if nueva_asignacion.fecha_fin else None,
                    "es_recurring": nueva_asignacion.es_recurring,
                    "es_activo": nueva_asignacion.es_activo
                }
            }
    
    
    @staticmethod
    def generar_codigos_turno_dia(fecha_generacion: date = None, expira_horas: int = 2, tz_mexico=None) -> dict:
        """
        Genera códigos de turno para todos los horarios activos del día especificado usando timezone de México.
        Por cada HorarioDetalle que coincida con el día de la semana, crea un TurnoClave.
        """
        from zoneinfo import ZoneInfo
        
        if not tz_mexico:
            tz_mexico = ZoneInfo("America/Mexico_City")
        
        if not fecha_generacion:
            # Usar fecha de México
            fecha_generacion = datetime.now(tz_mexico).date()
        
        # Obtener día de la semana (1=Lunes, 7=Domingo)
        dia_semana = fecha_generacion.isoweekday()
        
        logger.info(f"Generando códigos para fecha México: {fecha_generacion} (día {dia_semana})")
        
        with get_db_session() as session:
            # Buscar todos los HorarioDetalle activos que correspondan al día de hoy
            detalles_hoy = session.query(HorarioDetalle).join(
                Horario, HorarioDetalle.horario_id == Horario.id_horario
            ).filter(
                HorarioDetalle.dia_semana == dia_semana,
                HorarioDetalle.es_activo == True,
                Horario.es_activo == True
            ).all()
            
            logger.info(f"Encontrados {len(detalles_hoy)} detalles para día {dia_semana}")
            
            codigos_generados = []
            codigos_existentes = []
            
            for detalle in detalles_hoy:
                # Verificar si ya existe un código para este horario_detalle en esta fecha
                codigo_existente = session.query(TurnoClave).filter(
                    TurnoClave.horario_detalle_id == detalle.id_detalle,
                    TurnoClave.fecha == fecha_generacion,
                    TurnoClave.es_activo == True
                ).first()
                
                if codigo_existente:
                    codigos_existentes.append({
                        "id_turno_clave": codigo_existente.id_turno_clave,
                        "horario_id": codigo_existente.horario_id,
                        "horario_detalle_id": codigo_existente.horario_detalle_id,
                        "codigo": codigo_existente.codigo,
                        "fecha": codigo_existente.fecha.isoformat(),
                        "expira_en": codigo_existente.expira_en.isoformat() if codigo_existente.expira_en else None,
                        "ya_existia": True
                    })
                    logger.info(f"Código ya existe para detalle {detalle.id_detalle}: {codigo_existente.codigo}")
                    continue
                
                # Generar código alfanumérico de 6 caracteres
                codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                
                # Calcular hora de expiración (hora_inicio del turno + expira_horas) en timezone México
                # Combinar fecha + hora_inicio
                dt_inicio = datetime.combine(fecha_generacion, detalle.hora_inicio)
                # Crear datetime con timezone México
                dt_inicio_mexico = dt_inicio.replace(tzinfo=tz_mexico)
                # Agregar horas de expiración
                hora_expiracion = dt_inicio_mexico + timedelta(hours=expira_horas)
                # Guardar como naive (sin timezone) en BD
                hora_expiracion_naive = hora_expiracion.replace(tzinfo=None)
                
                # Crear TurnoClave con datetime naive
                turno_clave = TurnoClave(
                    horario_id=detalle.horario_id,
                    horario_detalle_id=detalle.id_detalle,
                    sucursal_id=detalle.horario.sucursal_id,
                    fecha=fecha_generacion,
                    turno_idx=detalle.turno_idx,
                    codigo=codigo,
                    es_activo=True,
                    expira_en=hora_expiracion_naive,  # Guardar como naive
                    uso_maximo=0,  # ilimitado
                    usos_count=0
                )
                
                session.add(turno_clave)
                session.flush()
                
                logger.info(f"Código creado: {codigo} para detalle {detalle.id_detalle}, expira: {hora_expiracion_naive}")
                
                codigos_generados.append({
                    "id_turno_clave": turno_clave.id_turno_clave,
                    "horario_id": turno_clave.horario_id,
                    "horario_detalle_id": turno_clave.horario_detalle_id,
                    "codigo": turno_clave.codigo,
                    "fecha": turno_clave.fecha.isoformat(),
                    "hora_inicio": detalle.hora_inicio.isoformat(),
                    "hora_fin": detalle.hora_fin.isoformat(),
                    "expira_en": turno_clave.expira_en.isoformat() if turno_clave.expira_en else None,
                    "ya_existia": False
                })
            
            session.commit()
            
            logger.info(f"Códigos generados para {fecha_generacion} (México): {len(codigos_generados)} nuevos, {len(codigos_existentes)} ya existían")
            
            return {
                "fecha": fecha_generacion.isoformat(),
                "dia_semana": dia_semana,
                "timezone": "America/Mexico_City",
                "codigos_generados": codigos_generados,
                "codigos_existentes": codigos_existentes,
                "total_codigos": len(codigos_generados) + len(codigos_existentes)
            }
