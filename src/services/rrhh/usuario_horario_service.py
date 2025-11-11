"""
UsuarioHorarioService - Lógica de negocio para asignación de horarios a empleados
"""

from src.dao.rrhh import UsuarioHorarioDAO, HorarioDAO
from src.schemas.rrhh_schema import AsignarHorarioSchema
from datetime import date
import logging

logger = logging.getLogger(__name__)


class UsuarioHorarioService:
    """Servicio para gestión de asignación de horarios"""
    
    @staticmethod
    def asignar_horario(data: dict) -> dict:
        """
        Asignar horario a un empleado.
        Desactiva automáticamente cualquier asignación previa.
        
        Expected data:
        {
            "usuario_id": 5,
            "horario_id": 1,
            "fecha_inicio": "2025-01-01",
            "fecha_fin": "2025-12-31"  # Opcional
        }
        """
        schema = AsignarHorarioSchema()
        errors = schema.validate(data)
        if errors:
            return {"success": False, "errors": errors, "asignacion": None}
        
        try:
            # Validar que el horario existe
            if not HorarioDAO.horario_existe(data['horario_id']):
                return {"success": False, "error": "El horario no existe", "asignacion": None}
            
            # Validar fecha_fin >= fecha_inicio
            if data.get('fecha_fin') and data['fecha_fin'] < data['fecha_inicio']:
                return {
                    "success": False,
                    "error": "La fecha de fin debe ser mayor o igual a la fecha de inicio",
                    "asignacion": None
                }
            
            asignacion = UsuarioHorarioDAO.asignar_horario(
                usuario_id=data['usuario_id'],
                horario_id=data['horario_id'],
                fecha_inicio=data['fecha_inicio'],
                fecha_fin=data.get('fecha_fin')
            )
            
            logger.info(f"Horario asignado al usuario {data['usuario_id']}: Horario ID {data['horario_id']}")
            return {"success": True, "asignacion": asignacion}
            
        except Exception as e:
            logger.error(f"Error al asignar horario: {str(e)}")
            return {"success": False, "error": str(e), "asignacion": None}
    
    
    @staticmethod
    def obtener_horario_activo(usuario_id: int) -> dict:
        """Obtener horario activo del empleado"""
        try:
            asignacion = UsuarioHorarioDAO.obtener_horario_activo(usuario_id)
            if not asignacion:
                return {
                    "success": False,
                    "error": "El usuario no tiene horario activo asignado",
                    "asignacion": None
                }
            return {"success": True, "asignacion": asignacion}
        except Exception as e:
            logger.error(f"Error al obtener horario activo: {str(e)}")
            return {"success": False, "error": str(e), "asignacion": None}
    
    
    @staticmethod
    def listar_horarios_usuario(usuario_id: int, es_activo: bool = None) -> dict:
        """Listar todos los horarios asignados a un usuario"""
        try:
            asignaciones = UsuarioHorarioDAO.listar_por_usuario(
                usuario_id=usuario_id,
                es_activo=es_activo
            )
            return {"success": True, "asignaciones": asignaciones, "count": len(asignaciones)}
        except Exception as e:
            logger.error(f"Error al listar horarios de usuario: {str(e)}")
            return {"success": False, "error": str(e), "asignaciones": []}
    
    
    @staticmethod
    def desactivar_asignacion(id_usuario_horario: int) -> dict:
        """Desactivar asignación de horario"""
        try:
            UsuarioHorarioDAO.desactivar_asignacion(id_usuario_horario)
            logger.info(f"Asignación desactivada: ID {id_usuario_horario}")
            return {"success": True, "message": "Asignación desactivada correctamente"}
        except Exception as e:
            logger.error(f"Error al desactivar asignación: {str(e)}")
            return {"success": False, "error": str(e)}
    
    
    @staticmethod
    def obtener_empleados_con_horario(horario_id: int, es_activo: bool = True) -> dict:
        """Obtener lista de empleados con un horario específico"""
        try:
            empleados = UsuarioHorarioDAO.obtener_empleados_por_horario(
                horario_id=horario_id,
                es_activo=es_activo
            )
            return {"success": True, "empleados": empleados, "count": len(empleados)}
        except Exception as e:
            logger.error(f"Error al obtener empleados por horario: {str(e)}")
            return {"success": False, "error": str(e), "empleados": []}
