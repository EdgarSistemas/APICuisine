"""
AsistenciaService - Lógica de negocio para check-in/check-out
"""

from src.dao.rrhh import AsistenciaDAO, UsuarioHorarioDAO
from src.services.rrhh.turno_clave_service import TurnoClaveService
from src.schemas.rrhh_schema import CheckInSchema, CheckOutSchema
from datetime import date
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class AsistenciaService:
    """Servicio para gestión de asistencia"""
    
    @staticmethod
    def notificar_tardanza(usuario_id: int, sucursal_id: int, minutos_retraso: int):
        """
        Notificar tardanza al gerente de sucursal.
        TODO: Implementar integración con sistema de notificaciones
        """
        logger.warning(f"TARDANZA DETECTADA - Usuario {usuario_id}, Sucursal {sucursal_id}, Retraso: {minutos_retraso} min")
        # TODO: Enviar email/push notification al gerente
        # TODO: Obtener gerente de sucursal desde BD
        # TODO: Enviar notificación
        pass
    
    
    @staticmethod
    def hacer_checkin(usuario_id: int, data: dict) -> dict:
        """
        Realizar check-in del empleado.
        
        Expected data:
        {
            "codigo": "123456",
            "lat": 19.432608,  # Opcional
            "lng": -99.133209,  # Opcional
            "device_info": "iPhone 12",  # Opcional
            "ip_address": "192.168.1.10"  # Opcional
        }
        """
        schema = CheckInSchema()
        errors = schema.validate(data)
        if errors:
            return {"success": False, "errors": errors, "asistencia": None}
        
        try:
            # 1. Validar código
            validacion = TurnoClaveService.validar_codigo_para_checkin(
                codigo=data['codigo'],
                usuario_id=usuario_id
            )
            
            if not validacion['valido']:
                return {
                    "success": False,
                    "error": validacion['error'],
                    "asistencia": None
                }
            
            # 2. Registrar check-in
            resultado = AsistenciaDAO.registrar_checkin(
                usuario_id=usuario_id,
                usuario_horario_id=validacion['usuario_horario_id'],
                turno_clave_id=validacion['turno_clave_id'],
                codigo_usuario=data['codigo'],
                lat=Decimal(str(data['lat'])) if data.get('lat') else None,
                lng=Decimal(str(data['lng'])) if data.get('lng') else None,
                device_info=data.get('device_info'),
                ip_address=data.get('ip_address')
            )
            
            if not resultado['success']:
                return resultado
            
            # 3. Si hay tardanza, notificar al gerente
            if resultado.get('tardanza'):
                AsistenciaService.notificar_tardanza(
                    usuario_id=usuario_id,
                    sucursal_id=resultado.get('sucursal_id'),
                    minutos_retraso=0  # TODO: Calcular minutos exactos
                )
            
            logger.info(f"Check-in exitoso para usuario {usuario_id} - Tardanza: {resultado.get('tardanza')}")
            return resultado
            
        except Exception as e:
            logger.error(f"Error en check-in: {str(e)}")
            return {"success": False, "error": str(e), "asistencia": None}
    
    
    @staticmethod
    def hacer_checkout(usuario_id: int, data: dict) -> dict:
        """
        Realizar check-out del empleado.
        No requiere código.
        
        Expected data:
        {
            "lat": 19.432608,  # Opcional
            "lng": -99.133209,  # Opcional
            "device_info": "iPhone 12",  # Opcional
            "ip_address": "192.168.1.10",  # Opcional
            "notas": "Salida anticipada por cita médica"  # Opcional
        }
        """
        schema = CheckOutSchema()
        errors = schema.validate(data)
        if errors:
            return {"success": False, "errors": errors, "asistencia": None}
        
        try:
            # Obtener horario activo
            horario_activo = UsuarioHorarioDAO.obtener_horario_activo(usuario_id)
            if not horario_activo:
                return {
                    "success": False,
                    "error": "No tienes un horario asignado",
                    "asistencia": None
                }
            
            resultado = AsistenciaDAO.registrar_checkout(
                usuario_id=usuario_id,
                usuario_horario_id=horario_activo['id_usuario_horario'],
                lat=Decimal(str(data['lat'])) if data.get('lat') else None,
                lng=Decimal(str(data['lng'])) if data.get('lng') else None,
                device_info=data.get('device_info'),
                ip_address=data.get('ip_address'),
                notas=data.get('notas')
            )
            
            if resultado['success']:
                logger.info(f"Check-out exitoso para usuario {usuario_id}")
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error en check-out: {str(e)}")
            return {"success": False, "error": str(e), "asistencia": None}
    
    
    @staticmethod
    def obtener_historial(usuario_id: int, fecha_inicio: date = None, 
                         fecha_fin: date = None, limit: int = 50) -> dict:
        """Obtener historial de asistencias del empleado"""
        try:
            asistencias = AsistenciaDAO.listar_asistencias(
                usuario_id=usuario_id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                limit=limit
            )
            return {"success": True, "asistencias": asistencias, "count": len(asistencias)}
        except Exception as e:
            logger.error(f"Error al obtener historial: {str(e)}")
            return {"success": False, "error": str(e), "asistencias": []}
    
    
    @staticmethod
    def obtener_asistencias_sucursal(sucursal_id: int, fecha_inicio: date = None,
                                     fecha_fin: date = None, limit: int = 100) -> dict:
        """Obtener asistencias de una sucursal (ADMIN)"""
        try:
            asistencias = AsistenciaDAO.listar_asistencias(
                sucursal_id=sucursal_id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                limit=limit
            )
            return {"success": True, "asistencias": asistencias, "count": len(asistencias)}
        except Exception as e:
            logger.error(f"Error al obtener asistencias: {str(e)}")
            return {"success": False, "error": str(e), "asistencias": []}
    
    
    @staticmethod
    def contar_tardanzas(usuario_id: int, fecha_inicio: date = None, 
                        fecha_fin: date = None) -> dict:
        """Contar tardanzas de un empleado"""
        try:
            count = AsistenciaDAO.contar_tardanzas(
                usuario_id=usuario_id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin
            )
            return {"success": True, "count": count}
        except Exception as e:
            logger.error(f"Error al contar tardanzas: {str(e)}")
            return {"success": False, "error": str(e), "count": 0}
