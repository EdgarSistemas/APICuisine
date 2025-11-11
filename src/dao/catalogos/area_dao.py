"""
AreaDAO - Data Access Object para catalogos.Area
Queries específicas para CRUD de Áreas
"""

from src.models import Area, Sucursal
from src.core.db.session_manager import get_db_session
from src.schemas.area_schema import AreaResponseSchema
import logging

logger = logging.getLogger(__name__)


class AreaDAO:
    """Data Access Object para Area"""
    
    @staticmethod
    def crear_area(sucursal_id: int, nombre: str, descripcion: str = None) -> dict:
        """
        Crear nueva área en una sucursal.
        
        Args:
            sucursal_id: ID de la sucursal
            nombre: Nombre del área (ej: "Salón Principal")
            descripcion: Descripción opcional
            
        Returns:
            Dict serializado con los datos del área
            
        Raises:
            Exception si hay error en BD
        """
        schema = AreaResponseSchema()
        with get_db_session() as session:
            area = Area(
                sucursal_id=sucursal_id,
                nombre=nombre,
                descripcion=descripcion,
                es_activa=True
            )
            session.add(area)
            session.flush()  # Obtener el ID generado
            session.refresh(area)  # Refrescar para obtener created_at
            session.commit()
            
            # Serializar y retornar como dict
            logger.info(f"Área '{nombre}' creada en sucursal {sucursal_id}")
            return schema.dump(area)
    
    
    @staticmethod
    def obtener_area_por_id(area_id: int) -> dict:
        """
        Obtener área por ID.
        
        Args:
            area_id: ID del área
            
        Returns:
            Dict serializado o None si no existe
        """
        schema = AreaResponseSchema()
        with get_db_session() as session:
            area = session.query(Area).filter(Area.id_area == area_id).first()
            return schema.dump(area) if area else None
    
    
    @staticmethod
    def obtener_areas_por_sucursal(sucursal_id: int, solo_activas: bool = True) -> list:
        """
        Obtener todas las áreas de una sucursal.
        
        Args:
            sucursal_id: ID de la sucursal
            solo_activas: Si True, solo devuelve áreas activas
            
        Returns:
            Lista de dicts serializados
        """
        schema = AreaResponseSchema(many=True)
        with get_db_session() as session:
            query = session.query(Area).filter(Area.sucursal_id == sucursal_id)
            
            if solo_activas:
                query = query.filter(Area.es_activa == True)
            
            areas = query.order_by(Area.nombre).all()
            return schema.dump(areas)
    
    
    @staticmethod
    def obtener_todas_las_areas(solo_activas: bool = True) -> list:
        """
        Obtener TODAS las áreas (solo para ADMIN).
        
        Args:
            solo_activas: Si True, solo áreas activas
            
        Returns:
            Lista de dicts serializados
        """
        schema = AreaResponseSchema(many=True)
        with get_db_session() as session:
            query = session.query(Area)
            
            if solo_activas:
                query = query.filter(Area.es_activa == True)
            
            areas = query.order_by(Area.sucursal_id, Area.nombre).all()
            return schema.dump(areas)
    
    
    @staticmethod
    def actualizar_area(area_id: int, nombre: str = None, descripcion: str = None, 
                       es_activa: bool = None) -> dict:
        """
        Actualizar campos de un área.
        
        Args:
            area_id: ID del área
            nombre: Nuevo nombre (opcional)
            descripcion: Nueva descripción (opcional)
            es_activa: Nuevo estado (opcional)
            
        Returns:
            Dict serializado del área actualizada o None
        """
        schema = AreaResponseSchema()
        with get_db_session() as session:
            area = session.query(Area).filter(Area.id_area == area_id).first()
            
            if not area:
                return None
            
            if nombre is not None:
                area.nombre = nombre
            if descripcion is not None:
                area.descripcion = descripcion
            if es_activa is not None:
                area.es_activa = es_activa
            
            session.flush()
            session.refresh(area)
            session.commit()
            
            logger.info(f"Área {area_id} actualizada")
            return schema.dump(area)
    
    
    @staticmethod
    def eliminar_area_soft(area_id: int) -> bool:
        """
        Eliminar área (soft delete: marcar como inactiva).
        
        Args:
            area_id: ID del área
            
        Returns:
            True si se eliminó, False si no existe
        """
        with get_db_session() as session:
            area = session.query(Area).filter(Area.id_area == area_id).first()
            
            if not area:
                return False
            
            area.es_activa = False
            session.commit()
            logger.info(f"Área {area_id} marcada como inactiva")
            return True
    
    
    @staticmethod
    def sucursal_existe(sucursal_id: int) -> bool:
        """
        Verificar si una sucursal existe.
        
        Args:
            sucursal_id: ID de sucursal
            
        Returns:
            True si existe
        """
        with get_db_session() as session:
            existe = session.query(Sucursal).filter(
                Sucursal.id_sucursal == sucursal_id
            ).first()
            return existe is not None
    
    
    @staticmethod
    def area_pertenece_a_sucursal(area_id: int, sucursal_id: int) -> bool:
        """
        Verificar que un área pertenece a una sucursal.
        
        Args:
            area_id: ID del área
            sucursal_id: ID de sucursal
            
        Returns:
            True si el área pertenece a esa sucursal
        """
        with get_db_session() as session:
            area = session.query(Area).filter(
                Area.id_area == area_id,
                Area.sucursal_id == sucursal_id
            ).first()
            return area is not None
