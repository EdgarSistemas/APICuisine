"""
TurnoClaveService - Lógica de negocio para códigos de turno
"""

from src.dao.rrhh import TurnoClaveDAO, HorarioDAO, UsuarioHorarioDAO
from src.schemas.rrhh_schema import GenerarCodigoSchema
from datetime import date, datetime
import logging

logger = logging.getLogger(__name__)


class TurnoClaveService:
    """Servicio para gestión de códigos de turno"""
    
    @staticmethod
    def generar_codigo(data: dict) -> dict:
        """
        Generar código de turno para una fecha específica.
        Este endpoint es llamado por Azure Function.
        
        Expected data:
        {
            "sucursal_id": 1,
            "horario_id": 1,
            "fecha": "2025-01-10",
            "expira_en_horas": 2,  # Opcional, default: 2
            "uso_maximo": 0,  # Opcional, 0 = ilimitado
            "generado_por": null  # null si es Azure Function
        }
        """
        schema = GenerarCodigoSchema()
        errors = schema.validate(data)
        if errors:
            return {"success": False, "errors": errors, "turno": None}
        
        try:
            # Validar que el horario existe
            if not HorarioDAO.horario_existe(data['horario_id']):
                return {"success": False, "error": "El horario no existe", "turno": None}
            
            # Validar que la fecha no sea pasada
            fecha_solicitada = data['fecha']
            if fecha_solicitada < date.today():
                return {
                    "success": False,
                    "error": "No se puede generar código para fechas pasadas",
                    "turno": None
                }
            
            turno = TurnoClaveDAO.generar_turno_clave(
                sucursal_id=data['sucursal_id'],
                horario_id=data['horario_id'],
                fecha=fecha_solicitada,
                expira_en_horas=data.get('expira_en_horas', 2),
                uso_maximo=data.get('uso_maximo', 0),
                generado_por=data.get('generado_por')
            )
            
            logger.info(f"Código generado para horario {data['horario_id']} en fecha {fecha_solicitada}")
            return {"success": True, "turno": turno}
            
        except Exception as e:
            logger.error(f"Error al generar código: {str(e)}")
            return {"success": False, "error": str(e), "turno": None}
    
    
    @staticmethod
    def validar_codigo_para_checkin(codigo: str, usuario_id: int) -> dict:
        """
        Validar código para check-in.
        Valida todas las reglas de negocio.
        
        Args:
            codigo: Código de 6 dígitos
            usuario_id: ID del empleado
            
        Returns:
            {
                "valido": bool,
                "turno_clave_id": int,
                "usuario_horario_id": int,
                "error": str
            }
        """
        try:
            # 1. Obtener horario activo del empleado
            horario_activo = UsuarioHorarioDAO.obtener_horario_activo(usuario_id)
            if not horario_activo:
                return {
                    "valido": False,
                    "turno_clave_id": None,
                    "usuario_horario_id": None,
                    "error": "No tienes un horario asignado"
                }
            
            # 2. Validar código con TurnoClaveDAO
            validacion = TurnoClaveDAO.validar_codigo(
                codigo=codigo,
                usuario_id=usuario_id,
                horario_id=horario_activo['horario_id']
            )
            
            if not validacion['valido']:
                return {
                    "valido": False,
                    "turno_clave_id": None,
                    "usuario_horario_id": None,
                    "error": validacion['error']
                }
            
            # 3. Código válido
            return {
                "valido": True,
                "turno_clave_id": validacion['turno']['id_turno_clave'],
                "usuario_horario_id": horario_activo['id_usuario_horario'],
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Error al validar código: {str(e)}")
            return {
                "valido": False,
                "turno_clave_id": None,
                "usuario_horario_id": None,
                "error": str(e)
            }
    
    
    @staticmethod
    def obtener_codigo_activo(sucursal_id: int, horario_id: int, fecha: date = None) -> dict:
        """Obtener código activo para una fecha específica"""
        try:
            fecha = fecha or date.today()
            turno = TurnoClaveDAO.obtener_codigo_activo(
                sucursal_id=sucursal_id,
                horario_id=horario_id,
                fecha=fecha
            )
            
            if not turno:
                return {
                    "success": False,
                    "error": "No hay código activo para esta fecha",
                    "turno": None
                }
            
            return {"success": True, "turno": turno}
            
        except Exception as e:
            logger.error(f"Error al obtener código activo: {str(e)}")
            return {"success": False, "error": str(e), "turno": None}
    
    
    @staticmethod
    def desactivar_codigos_expirados() -> dict:
        """
        Desactivar todos los códigos expirados.
        Puede ser llamado por un job programado.
        """
        try:
            count = TurnoClaveDAO.desactivar_codigos_expirados()
            logger.info(f"Se desactivaron {count} códigos expirados")
            return {
                "success": True,
                "message": f"Se desactivaron {count} códigos expirados",
                "count": count
            }
        except Exception as e:
            logger.error(f"Error al desactivar códigos: {str(e)}")
            return {"success": False, "error": str(e), "count": 0}
