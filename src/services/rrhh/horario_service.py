"""
HorarioService - Lógica de negocio para Horarios
"""

from src.dao.rrhh import HorarioDAO
from src.schemas.rrhh_schema import HorarioCreateSchema, HorarioUpdateSchema
from datetime import date, datetime
import logging

logger = logging.getLogger(__name__)


class HorarioService:
    """Servicio para gestión de horarios"""
    
    @staticmethod
    def crear_horario(data: dict) -> dict:
        """
        Crear horario con sus detalles.
        
        Expected data:
        {
            "sucursal_id": 1,
            "clave": "TURNO_MANANA",
            "nombre": "Turno Matutino",
            "descripcion": "9AM-5PM",
            "detalles": [
                {
                    "dia_semana": 1,
                    "hora_inicio": "09:00",
                    "hora_fin": "17:00",
                    "turno_idx": 1,
                    "tolerancia_min": 10
                },
                ...
            ]
        }
        """
        schema = HorarioCreateSchema()
        errors = schema.validate(data)
        if errors:
            return {"success": False, "errors": errors, "horario": None}
        
        try:
            # Validar que detalles tenga al menos 1 día
            if not data.get('detalles') or len(data['detalles']) == 0:
                return {
                    "success": False,
                    "error": "Debe incluir al menos un día en los detalles del horario",
                    "horario": None
                }
            
            # Validar que no haya días duplicados
            dias = [d['dia_semana'] for d in data['detalles']]
            if len(dias) != len(set(dias)):
                return {
                    "success": False,
                    "error": "No puede haber días de semana duplicados",
                    "horario": None
                }
            
            horario = HorarioDAO.crear_horario_con_detalles(
                sucursal_id=data['sucursal_id'],
                clave=data['clave'],
                nombre=data['nombre'],
                descripcion=data.get('descripcion'),
                detalles=data['detalles']
            )
            
            logger.info(f"Horario creado: {data['clave']} - ID {horario['horario']['id_horario']}")
            return {"success": True, "horario": horario['horario'], "detalles": horario['detalles']}
            
        except Exception as e:
            logger.error(f"Error al crear horario: {str(e)}")
            return {"success": False, "error": str(e), "horario": None}
    
    
    @staticmethod
    def obtener_horario(id_horario: int) -> dict:
        """Obtener horario por ID con sus detalles completos"""
        try:
            resultado = HorarioDAO.obtener_horario_con_detalles(id_horario)
            
            if not resultado:
                return {
                    "success": False,
                    "error": "Horario no encontrado",
                    "horario": None
                }
            
            return {
                "success": True,
                "horario": resultado['horario'],
                "detalles": resultado['detalles']
            }
        except Exception as e:
            logger.error(f"Error al obtener horario: {str(e)}")
            return {"success": False, "error": str(e), "horario": None}
    
    
    @staticmethod
    def listar_horarios_por_sucursal(sucursal_id: int) -> dict:
        """Listar horarios activos de una sucursal con sus detalles"""
        try:
            horarios_con_detalles = HorarioDAO.listar_horarios(
                sucursal_id=sucursal_id,
                solo_activos=True
            )
            return {
                "success": True,
                "horarios": horarios_con_detalles,
                "count": len(horarios_con_detalles)
            }
        except Exception as e:
            logger.error(f"Error al listar horarios: {str(e)}")
            return {"success": False, "error": str(e), "horarios": []}
    
    
    @staticmethod
    def actualizar_horario(id_horario: int, data: dict) -> dict:
        """
        Actualizar información del horario (no los detalles).
        
        Para actualizar detalles, debe desactivar y crear nuevo horario.
        """
        schema = HorarioUpdateSchema()
        errors = schema.validate(data)
        if errors:
            return {"success": False, "errors": errors, "horario": None}
        
        try:
            # Verificar que existe
            if not HorarioDAO.horario_existe(id_horario):
                return {"success": False, "error": "Horario no encontrado", "horario": None}
            
            horario = HorarioDAO.actualizar_horario(id_horario, data)
            logger.info(f"Horario actualizado: ID {id_horario}")
            return {"success": True, "horario": horario}
            
        except Exception as e:
            logger.error(f"Error al actualizar horario: {str(e)}")
            return {"success": False, "error": str(e), "horario": None}
    
    
    @staticmethod
    def desactivar_horario(id_horario: int) -> dict:
        """Desactivar horario (soft delete)"""
        try:
            if not HorarioDAO.horario_existe(id_horario):
                return {"success": False, "error": "Horario no encontrado"}
            
            HorarioDAO.desactivar_horario(id_horario)
            logger.info(f"Horario desactivado: ID {id_horario}")
            return {"success": True, "message": "Horario desactivado correctamente"}
            
        except Exception as e:
            logger.error(f"Error al desactivar horario: {str(e)}")
            return {"success": False, "error": str(e)}
    
    
    @staticmethod
    def obtener_horario_usuario(usuario_id: int) -> dict:
        """Obtener horario activo de un usuario con detalles completos"""
        try:
            resultado = HorarioDAO.obtener_horario_usuario(usuario_id)
            
            if not resultado:
                return {
                    "success": False,
                    "error": "No se encontró horario activo para este usuario",
                    "data": None
                }
            
            return {
                "success": True,
                "data": resultado
            }
        except Exception as e:
            logger.error(f"Error al obtener horario de usuario: {str(e)}")
            return {"success": False, "error": str(e), "data": None}
    
    
    @staticmethod
    def obtener_codigo_turno(horario_id: int, fecha_str: str) -> dict:
        """Obtener código de turno para un horario y fecha específicos"""
        try:
            # Convertir string a date
            try:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                return {
                    "success": False,
                    "error": "Formato de fecha inválido. Use YYYY-MM-DD",
                    "codigo": None
                }
            
            resultado = HorarioDAO.obtener_codigo_turno(horario_id, fecha)
            
            if not resultado:
                return {
                    "success": False,
                    "error": "No se encontró código de turno para este horario y fecha",
                    "codigo": None
                }
            
            return {
                "success": True,
                "codigo": resultado
            }
        except Exception as e:
            logger.error(f"Error al obtener código de turno: {str(e)}")
            return {"success": False, "error": str(e), "codigo": None}
    
    
    @staticmethod
    def asignar_horario_a_usuario(usuario_id: int, horario_id: int, fecha_inicio_str: str, fecha_fin_str: str = None) -> dict:
        """Asignar horario a un usuario"""
        try:
            # Validar y convertir fecha_inicio
            try:
                fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
            except ValueError:
                return {
                    "success": False,
                    "error": "Formato de fecha_inicio inválido. Use YYYY-MM-DD",
                    "asignacion": None
                }
            
            # Validar y convertir fecha_fin si se proporciona
            fecha_fin = None
            if fecha_fin_str:
                try:
                    fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
                    # Validar que fecha_fin sea posterior a fecha_inicio
                    if fecha_fin <= fecha_inicio:
                        return {
                            "success": False,
                            "error": "La fecha_fin debe ser posterior a fecha_inicio",
                            "asignacion": None
                        }
                except ValueError:
                    return {
                        "success": False,
                        "error": "Formato de fecha_fin inválido. Use YYYY-MM-DD",
                        "asignacion": None
                    }
            
            resultado = HorarioDAO.asignar_horario_a_usuario(
                usuario_id=usuario_id,
                horario_id=horario_id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin
            )
            
            if resultado.get('error') == 'HORARIO_NO_ENCONTRADO':
                return {
                    "success": False,
                    "error": "Horario no encontrado o no está activo",
                    "asignacion": None
                }
            
            if resultado.get('error') == 'USUARIO_YA_TIENE_HORARIO':
                return {
                    "success": False,
                    "error": f"El usuario ya tiene un horario activo asignado (ID: {resultado.get('horario_actual')}). No se permite más de un horario activo por usuario.",
                    "asignacion": None
                }
            
            return {
                "success": True,
                "asignacion": resultado['data'],
                "message": "Horario asignado exitosamente al usuario"
            }
            
        except Exception as e:
            logger.error(f"Error al asignar horario a usuario: {str(e)}")
            return {"success": False, "error": str(e), "asignacion": None}
    
    
    @staticmethod
    def generar_codigos_turno(fecha_generacion: str = None, expira_horas: int = 2) -> tuple:
        """
        Genera códigos de turno para el día especificado usando timezone de México.
        Si no se especifica fecha, usa hoy en zona de México.
        """
        try:
            from zoneinfo import ZoneInfo
            
            # Obtener fecha actual en timezone de México
            tz_mexico = ZoneInfo("America/Mexico_City")
            
            # Parsear fecha si viene como string
            if fecha_generacion:
                fecha = datetime.strptime(fecha_generacion, '%Y-%m-%d').date()
            else:
                # Usar fecha de México, no UTC
                fecha = datetime.now(tz_mexico).date()
            
            logger.info(f"Generando códigos para fecha (México): {fecha}")
            
            resultado = HorarioDAO.generar_codigos_turno_dia(fecha, expira_horas, tz_mexico=tz_mexico)
            
            if not resultado:
                return {"error": "No se pudieron generar códigos"}, 500
            
            return resultado, 200
            
        except ValueError as e:
            logger.error(f"Fecha inválida: {str(e)}")
            return {"error": "Formato de fecha inválido. Use YYYY-MM-DD"}, 400
        except Exception as e:
            logger.error(f"Error al generar códigos: {str(e)}")
            return {"error": str(e)}, 500
