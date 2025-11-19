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
    
    
    @staticmethod
    def resetear_horarios_semana_pasada() -> dict:
        """
        Resetea los horarios que terminaron la semana pasada (lunes a las 00:01 México).
        
        LÓGICA:
        1. Obtiene la fecha actual en zona México
        2. Calcula el inicio de semana pasada (lunes)
        3. Busca UsuarioHorario donde:
           - es_activo = True
           - fecha_fin <= último_domingo_semana_pasada
        4. Cambia es_activo a False para esos registros
        
        Returns:
            {
                "success": True/False,
                "cantidad_reiniciados": int,
                "mensaje": str,
                "ids_reiniciados": [...]
            }
        """
        from datetime import datetime, timedelta
        import pytz
        
        TZ_MEXICO = pytz.timezone('America/Mexico_City')
        
        try:
            with get_db_session() as session:
                # Obtener fecha actual en México
                ahora_mexico = datetime.now(TZ_MEXICO)
                fecha_actual = ahora_mexico.date()
                
                # Calcular el último domingo (fin de semana pasada)
                # Si hoy es lunes, el domingo pasado fue ayer
                dias_desde_lunes = fecha_actual.weekday()  # 0=Lunes, 6=Domingo
                fecha_ultimo_domingo = fecha_actual - timedelta(days=dias_desde_lunes + 1)
                
                print(f"\n[RESET HORARIOS] Ejecutado en México: {ahora_mexico}")
                print(f"[RESET HORARIOS] Fecha actual: {fecha_actual}")
                print(f"[RESET HORARIOS] Último domingo (fin de semana pasada): {fecha_ultimo_domingo}")
                
                # Buscar asignaciones donde fecha_fin <= último_domingo Y están activas
                asignaciones_a_resetear = session.query(UsuarioHorario).filter(
                    UsuarioHorario.es_activo == True,
                    UsuarioHorario.fecha_fin <= fecha_ultimo_domingo
                ).all()
                
                ids_reiniciados = [a.id_usuario_horario for a in asignaciones_a_resetear]
                
                print(f"[RESET HORARIOS] Horarios a resetear: {len(asignaciones_a_resetear)}")
                for a in asignaciones_a_resetear:
                    print(f"  - ID={a.id_usuario_horario}, Usuario={a.usuario_id}, Fin={a.fecha_fin}")
                
                # Cambiar es_activo a False
                if ids_reiniciados:
                    cantidad = session.query(UsuarioHorario).filter(
                        UsuarioHorario.id_usuario_horario.in_(ids_reiniciados)
                    ).update({"es_activo": False}, synchronize_session=False)
                    session.commit()
                    
                    print(f"[RESET HORARIOS] ✓ {cantidad} horarios reiniciados")
                    logger.info(f"[RESET HORARIOS] Se reiniciaron {cantidad} asignaciones de horario")
                    
                    return {
                        "success": True,
                        "cantidad_reiniciados": cantidad,
                        "ids_reiniciados": ids_reiniciados,
                        "mensaje": f"Se han desactivado {cantidad} asignaciones de horario que terminaron semana pasada",
                        "timestamp": ahora_mexico.isoformat(),
                        "fecha_corte": str(fecha_ultimo_domingo)
                    }
                else:
                    print(f"[RESET HORARIOS] No hay horarios para resetear")
                    return {
                        "success": True,
                        "cantidad_reiniciados": 0,
                        "ids_reiniciados": [],
                        "mensaje": "No hay asignaciones de horario para resetear",
                        "timestamp": ahora_mexico.isoformat(),
                        "fecha_corte": str(fecha_ultimo_domingo)
                    }
                
        except Exception as e:
            logger.error(f"[RESET HORARIOS] Error: {str(e)}", exc_info=True)
            print(f"[RESET HORARIOS] ✗ Error: {str(e)}")
            return {
                "success": False,
                "cantidad_reiniciados": 0,
                "error": str(e),
                "mensaje": f"Error al resetear horarios: {str(e)}"
            }
