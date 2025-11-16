"""
SolicitudVacacionesService - Lógica de negocio para solicitudes de vacaciones
"""

from src.dao.rrhh import SolicitudVacacionesDAO, UsuarioHorarioDAO
from src.schemas.rrhh_schema import SolicitudVacacionesCreateSchema, AprobarVacacionesSchema
from datetime import date
import logging

logger = logging.getLogger(__name__)


class SolicitudVacacionesService:
    """Servicio para gestión de solicitudes de vacaciones"""
    
    @staticmethod
    def crear_solicitud(usuario_id: int, data: dict) -> dict:
        """
        Crear solicitud de vacaciones.
        
        Expected data:
        {
            "fecha_inicio": "2025-02-01",
            "fecha_fin": "2025-02-15",
            "motivo": "Vacaciones familiares"  # Opcional
        }
        """
        schema = SolicitudVacacionesCreateSchema()
        errors = schema.validate(data)
        if errors:
            return {"success": False, "errors": errors, "solicitud": None}
        
        try:
            # Obtener horario activo del empleado
            horario_activo = UsuarioHorarioDAO.obtener_horario_activo(usuario_id)
            if not horario_activo:
                return {
                    "success": False,
                    "error": "No tienes un horario asignado",
                    "solicitud": None
                }
            
            resultado = SolicitudVacacionesDAO.crear_solicitud(
                usuario_horario_id=horario_activo['id_usuario_horario'],
                fecha_inicio=data['fecha_inicio'],
                fecha_fin=data['fecha_fin'],
                motivo=data.get('motivo')
            )
            
            if resultado['success']:
                logger.info(f"Solicitud de vacaciones creada por usuario {usuario_id}")
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error al crear solicitud: {str(e)}")
            return {"success": False, "error": str(e), "solicitud": None}
    
    
    @staticmethod
    def listar_solicitudes_usuario(usuario_id: int, estatus: int = None) -> dict:
        """Listar solicitudes del empleado"""
        try:
            solicitudes = SolicitudVacacionesDAO.listar_solicitudes(
                usuario_id=usuario_id,
                estatus=estatus
            )
            return {"success": True, "solicitudes": solicitudes, "count": len(solicitudes)}
        except Exception as e:
            logger.error(f"Error al listar solicitudes: {str(e)}")
            return {"success": False, "error": str(e), "solicitudes": []}
    
    
    @staticmethod
    def listar_solicitudes_sucursal(sucursal_id: int, estatus: int = None) -> dict:
        """Listar solicitudes de una sucursal (ADMIN/Gerente)"""
        try:
            solicitudes = SolicitudVacacionesDAO.listar_solicitudes(
                sucursal_id=sucursal_id,
                estatus=estatus
            )
            return {"success": True, "solicitudes": solicitudes, "count": len(solicitudes)}
        except Exception as e:
            logger.error(f"Error al listar solicitudes: {str(e)}")
            return {"success": False, "error": str(e), "solicitudes": []}
    
    
    @staticmethod
    def obtener_solicitud(id_solicitud: int) -> dict:
        """Obtener solicitud por ID"""
        try:
            solicitud = SolicitudVacacionesDAO.obtener_por_id(id_solicitud)
            if not solicitud:
                return {"success": False, "error": "Solicitud no encontrada", "solicitud": None}
            return {"success": True, "solicitud": solicitud}
        except Exception as e:
            logger.error(f"Error al obtener solicitud: {str(e)}")
            return {"success": False, "error": str(e), "solicitud": None}
    
    
    @staticmethod
    def aprobar_solicitud(id_solicitud: int, gerente_id: int, data: dict = None) -> dict:
        """
        Aprobar solicitud de vacaciones.
        Solo gerente de sucursal puede aprobar.
        
        Expected data: {} (sin campos, solo para validación)
        """
        if data is None:
            data = {}
            
        schema = AprobarVacacionesSchema()
        errors = schema.validate(data)
        if errors:
            return {"success": False, "errors": errors, "solicitud": None}
        
        try:
            # TODO: Validar que gerente_id sea gerente de la sucursal
            # Esto se puede hacer en el controller verificando el rol
            
            resultado = SolicitudVacacionesDAO.aprobar_solicitud(
                id_solicitud=id_solicitud,
                revisado_por=gerente_id
            )
            
            if resultado['success']:
                logger.info(f"Solicitud {id_solicitud} aprobada por gerente {gerente_id}")
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error al aprobar solicitud: {str(e)}")
            return {"success": False, "error": str(e), "solicitud": None}
    
    
    @staticmethod
    def rechazar_solicitud(id_solicitud: int, gerente_id: int, data: dict = None) -> dict:
        """
        Rechazar solicitud de vacaciones.
        
        Expected data: {} (sin campos requeridos)
        """
        if data is None:
            data = {}
            
        schema = AprobarVacacionesSchema()
        errors = schema.validate(data)
        if errors:
            return {"success": False, "errors": errors, "solicitud": None}
        
        try:
            resultado = SolicitudVacacionesDAO.rechazar_solicitud(
                id_solicitud=id_solicitud,
                revisado_por=gerente_id
            )
            
            if resultado['success']:
                logger.info(f"Solicitud {id_solicitud} rechazada por gerente {gerente_id}")
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error al rechazar solicitud: {str(e)}")
            return {"success": False, "error": str(e), "solicitud": None}
    
    
    @staticmethod
    def contar_pendientes(sucursal_id: int = None) -> dict:
        """Contar solicitudes pendientes"""
        try:
            count = SolicitudVacacionesDAO.contar_solicitudes_pendientes(sucursal_id)
            return {"success": True, "count": count}
        except Exception as e:
            logger.error(f"Error al contar pendientes: {str(e)}")
            return {"success": False, "error": str(e), "count": 0}
    
    
    @staticmethod
    def verificar_vacaciones_activas(usuario_id: int, fecha: date = None) -> dict:
        """Verificar si empleado tiene vacaciones activas en una fecha específica"""
        try:
            fecha = fecha or date.today()
            vacaciones = SolicitudVacacionesDAO.obtener_vacaciones_activas(usuario_id, fecha)
            tiene_vacaciones = len(vacaciones) > 0
            
            return {
                "success": True,
                "tiene_vacaciones": tiene_vacaciones,
                "vacaciones": vacaciones
            }
        except Exception as e:
            logger.error(f"Error al verificar vacaciones: {str(e)}")
            return {"success": False, "error": str(e), "tiene_vacaciones": False}
