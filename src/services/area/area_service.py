"""
AreaService - Lógica de negocio para Áreas
Validaciones, reglas de negocio, transacciones
"""

from src.dao.catalogos.area_dao import AreaDAO
from src.core.utils.multitenant import es_admin, validar_acceso_sucursal
import logging

logger = logging.getLogger(__name__)


class AreaService:
    """Service para lógica de negocio de Areas"""
    
    @staticmethod
    def crear_area(usuario_id: int, sucursal_id: int, nombre: str, descripcion: str = None) -> dict:
        """
        Crear un área (solo ADMIN).
        
        Validaciones:
        - Usuario debe ser ADMIN
        - Sucursal debe existir
        - Nombre no puede estar vacío
        
        Args:
            usuario_id: ID del usuario que crea
            sucursal_id: ID de sucursal
            nombre: Nombre del área
            descripcion: Descripción opcional
            
        Returns:
            {"success": True/False, "data": Area, "error": str}
        """
        # Validación 1: Solo ADMIN
        if not es_admin(usuario_id):
            logger.warning(f"Usuario {usuario_id} intentó crear área sin permisos")
            return {
                "success": False,
                "error": "Solo ADMIN puede crear áreas"
            }
        
        # Validación 2: Sucursal existe
        if not AreaDAO.sucursal_existe(sucursal_id):
            logger.warning(f"Intento de crear área en sucursal inexistente: {sucursal_id}")
            return {
                "success": False,
                "error": f"Sucursal {sucursal_id} no existe"
            }
        
        # Validación 3: Nombre válido
        if not nombre or len(nombre.strip()) == 0:
            return {
                "success": False,
                "error": "El nombre del área no puede estar vacío"
            }
        
        try:
            area = AreaDAO.crear_area(sucursal_id, nombre, descripcion)
            logger.info(f"Área '{nombre}' creada por usuario {usuario_id}")
            
            return {
                "success": True,
                "data": area.to_dict() if hasattr(area, 'to_dict') else {
                    "id_area": area.get("id_area"),
                    "sucursal_id": area.get("sucursal_id"),
                    "nombre": area.get("nombre"),
                    "descripcion": area.get("descripcion"),
                    "es_activa": area.get("es_activa"),
                    "created_at": area.get("created_at") if area.get("created_at") else None
                },
                "message": "Área creada exitosamente"
            }
        
        except Exception as e:
            logger.error(f"Error creando área: {str(e)}")
            return {
                "success": False,
                "error": "Error interno al crear área"
            }
    
    
    @staticmethod
    def obtener_areas(usuario_id: int, sucursal_id: int = None) -> dict:
        """
        Obtener áreas.
        
        Lógica:
        - ADMIN: ve TODAS las áreas (si sucursal_id=None) o solo de una sucursal
        - Empleado: ve solo áreas de su(s) sucursal(es)
        
        Args:
            usuario_id: ID del usuario
            sucursal_id: ID de sucursal (opcional, para filtrado)
            
        Returns:
            {"success": True, "data": [areas], "total": int}
        """
        try:
            # Si ADMIN y no especifica sucursal, ve TODAS
            if es_admin(usuario_id) and sucursal_id is None:
                areas = AreaDAO.obtener_todas_las_areas(solo_activas=True)
            
            # Si hay sucursal_id específica
            elif sucursal_id:
                # Validar acceso a esa sucursal
                if not es_admin(usuario_id):
                    if not validar_acceso_sucursal(usuario_id, sucursal_id):
                        logger.warning(f"Usuario {usuario_id} intentó ver áreas de sucursal {sucursal_id} sin acceso")
                        return {
                            "success": False,
                            "error": "No tiene acceso a esa sucursal"
                        }
                
                areas = AreaDAO.obtener_areas_por_sucursal(sucursal_id, solo_activas=True)
            
            else:
                return {
                    "success": False,
                    "error": "Debe especificar sucursal_id"
                }
            
            areas_data = [
                area.to_dict() if hasattr(area, 'to_dict') else {
                    "id_area": area.get("id_area"),
                    "sucursal_id": area.get("sucursal_id"),
                    "nombre": area.get("nombre"),
                    "descripcion": area.get("descripcion"),
                    "es_activa": area.get("es_activa"),
                    "created_at": area.get("created_at") if area.get("created_at") else None
                }
                for area in areas
            ]
            
            return {
                "success": True,
                "data": areas_data,
                "total": len(areas_data)
            }
        
        except Exception as e:
            logger.error(f"Error obteniendo áreas: {str(e)}")
            return {
                "success": False,
                "error": "Error interno"
            }
    
    
    @staticmethod
    def obtener_area(usuario_id: int, area_id: int) -> dict:
        """
        Obtener un área específica.
        
        Validaciones:
        - Área debe existir
        - Usuario debe tener acceso a la sucursal
        
        Args:
            usuario_id: ID del usuario
            area_id: ID del área
            
        Returns:
            {"success": True, "data": area} o error
        """
        try:
            area = AreaDAO.obtener_area_por_id(area_id)
            
            if not area:
                return {
                    "success": False,
                    "error": "Área no existe"
                }
            
            # Validar acceso
            if not es_admin(usuario_id):
                if not validar_acceso_sucursal(usuario_id, area.sucursal_id):
                    logger.warning(f"Usuario {usuario_id} intentó ver área de sucursal {area.sucursal_id} sin acceso")
                    return {
                        "success": False,
                        "error": "No tiene acceso a esa sucursal"
                    }
            
            area_data = area.to_dict() if hasattr(area, 'to_dict') else {
                "id_area": area.get("id_area"),
                "sucursal_id": area.get("sucursal_id"),
                "nombre": area.get("nombre"),
                "descripcion": area.get("descripcion"),
                "es_activa": area.get("es_activa"),
                "created_at": area.get("created_at") if area.get("created_at") else None
            }
            
            return {
                "success": True,
                "data": area_data
            }
        
        except Exception as e:
            logger.error(f"Error obteniendo área {area_id}: {str(e)}")
            return {
                "success": False,
                "error": "Error interno"
            }
    
    
    @staticmethod
    def actualizar_area(usuario_id: int, area_id: int, nombre: str = None, 
                       descripcion: str = None) -> dict:
        """
        Actualizar un área (solo ADMIN).
        
        Args:
            usuario_id: ID del usuario
            area_id: ID del área
            nombre: Nuevo nombre (opcional)
            descripcion: Nueva descripción (opcional)
            
        Returns:
            {"success": True, "data": area} o error
        """
        # Validación 1: Solo ADMIN
        if not es_admin(usuario_id):
            logger.warning(f"Usuario {usuario_id} intentó actualizar área sin permisos")
            return {
                "success": False,
                "error": "Solo ADMIN puede actualizar áreas"
            }
        
        try:
            area = AreaDAO.obtener_area_por_id(area_id)
            
            if not area:
                return {
                    "success": False,
                    "error": "Área no existe"
                }
            
            # Actualizar
            area_actualizada = AreaDAO.actualizar_area(area_id, nombre, descripcion)
            logger.info(f"Área {area_id} actualizada por usuario {usuario_id}")
            
            area_data = area_actualizada.to_dict() if hasattr(area_actualizada, 'to_dict') else {
                "id_area": area_actualizada.get("id_area"),
                "sucursal_id": area_actualizada.get("sucursal_id"),
                "nombre": area_actualizada.get("nombre"),
                "descripcion": area_actualizada.get("descripcion"),
                "es_activa": area_actualizada.get("es_activa"),
                "created_at": area_actualizada.get("created_at") if area_actualizada.get("created_at") else None
            }
            
            return {
                "success": True,
                "data": area_data,
                "message": "Área actualizada"
            }
        
        except Exception as e:
            logger.error(f"Error actualizando área {area_id}: {str(e)}")
            return {
                "success": False,
                "error": "Error interno"
            }
    
    
    @staticmethod
    def eliminar_area(usuario_id: int, area_id: int) -> dict:
        """
        Eliminar un área (soft delete, solo ADMIN).
        
        Args:
            usuario_id: ID del usuario
            area_id: ID del área
            
        Returns:
            {"success": True/False}
        """
        # Validación 1: Solo ADMIN
        if not es_admin(usuario_id):
            logger.warning(f"Usuario {usuario_id} intentó eliminar área sin permisos")
            return {
                "success": False,
                "error": "Solo ADMIN puede eliminar áreas"
            }
        
        try:
            resultado = AreaDAO.eliminar_area_soft(area_id)
            
            if not resultado:
                return {
                    "success": False,
                    "error": "Área no existe"
                }
            
            logger.info(f"Área {area_id} eliminada (soft) por usuario {usuario_id}")
            
            return {
                "success": True,
                "message": "Área eliminada"
            }
        
        except Exception as e:
            logger.error(f"Error eliminando área {area_id}: {str(e)}")
            return {
                "success": False,
                "error": "Error interno"
            }
