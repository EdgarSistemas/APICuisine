"""
HorarioService - Lógica de negocio para Horarios
"""

from src.dao.rrhh import HorarioDAO
from src.schemas.rrhh_schema import HorarioCreateSchema, HorarioUpdateSchema
from datetime import date
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
                detalles_data=data['detalles']
            )
            
            logger.info(f"Horario creado: {horario['clave']} - ID {horario['id_horario']}")
            return {"success": True, "horario": horario}
            
        except Exception as e:
            logger.error(f"Error al crear horario: {str(e)}")
            return {"success": False, "error": str(e), "horario": None}
    
    
    @staticmethod
    def obtener_horario(id_horario: int) -> dict:
        """Obtener horario por ID"""
        try:
            horario = HorarioDAO.obtener_horario_por_id(id_horario)
            if not horario:
                return {"success": False, "error": "Horario no encontrado", "horario": None}
            return {"success": True, "horario": horario}
        except Exception as e:
            logger.error(f"Error al obtener horario: {str(e)}")
            return {"success": False, "error": str(e), "horario": None}
    
    
    @staticmethod
    def listar_horarios(sucursal_id: int = None, es_activo: bool = True,
                       limit: int = 100, offset: int = 0) -> dict:
        """Listar horarios con filtros"""
        try:
            horarios = HorarioDAO.listar_horarios(
                sucursal_id=sucursal_id,
                es_activo=es_activo,
                limit=limit,
                offset=offset
            )
            return {"success": True, "horarios": horarios, "count": len(horarios)}
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
