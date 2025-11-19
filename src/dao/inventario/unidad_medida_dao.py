"""
UnidadMedidaDAO - Data Access Object para inventario.UnidadMedida
"""

from src.models import UnidadMedida
from src.core.db.session_manager import get_db_session
from src.schemas.unidad_medida_schema import UnidadMedidaResponseSchema
import logging

logger = logging.getLogger(__name__)


class UnidadMedidaDAO:
    """Data Access Object para UnidadMedida"""
    
    @staticmethod
    def crear_unidad_medida(clave: str, nombre: str) -> dict:
        """
        Crear una nueva unidad de medida.
        
        Args:
            clave: Clave única (kg, g, l, ml, pz, etc)
            nombre: Nombre descriptivo
            simbolo: Símbolo (opcional)
            
        Returns:
            Dict serializado de la unidad de medida
        """
        schema = UnidadMedidaResponseSchema()
        with get_db_session() as session:
            unidad = UnidadMedida(clave=clave, nombre=nombre)
            session.add(unidad)
            session.commit()
            logger.info(f"Unidad de medida creada: {clave} - {nombre}")
            return schema.dump(unidad)
    
    
    @staticmethod
    def obtener_unidad_por_id(unidad_id: int) -> dict:
        """
        Obtener unidad de medida por ID.
        
        Args:
            unidad_id: ID de la unidad
            
        Returns:
            Dict de la unidad o None
        """
        schema = UnidadMedidaResponseSchema()
        with get_db_session() as session:
            unidad = session.query(UnidadMedida).filter(
                UnidadMedida.id_unidad == unidad_id
            ).first()
            return schema.dump(unidad) if unidad else None
    
    
    @staticmethod
    def obtener_unidad_por_clave(clave: str) -> dict:
        """
        Obtener unidad de medida por clave.
        
        Args:
            clave: Clave de la unidad (kg, g, l, etc)
            
        Returns:
            Dict de la unidad o None
        """
        schema = UnidadMedidaResponseSchema()
        with get_db_session() as session:
            unidad = session.query(UnidadMedida).filter(
                UnidadMedida.clave == clave
            ).first()
            return schema.dump(unidad) if unidad else None
    
    
    @staticmethod
    def obtener_todas_las_unidades() -> list:
        """
        Obtener todas las unidades de medida.
        
        Returns:
            Lista de dicts de unidades
        """
        schema = UnidadMedidaResponseSchema()
        with get_db_session() as session:
            unidades = session.query(UnidadMedida).order_by(UnidadMedida.nombre).all()
            return [schema.dump(u) for u in unidades]
    
    
    @staticmethod
    def actualizar_unidad(unidad_id: int, clave: str = None, nombre: str = None) -> dict:
        """
        Actualizar unidad de medida.
        
        Args:
            unidad_id: ID de la unidad
            clave: Nueva clave (opcional)
            nombre: Nuevo nombre (opcional)
            
        Returns:
            Dict actualizado o None
        """
        schema = UnidadMedidaResponseSchema()
        with get_db_session() as session:
            unidad = session.query(UnidadMedida).filter(
                UnidadMedida.id_unidad == unidad_id
            ).first()
            
            if not unidad:
                return None
            
            if clave:
                unidad.clave = clave
            if nombre:
                unidad.nombre = nombre
            
            session.commit()
            logger.info(f"Unidad de medida actualizada: {unidad_id}")
            return schema.dump(unidad)
    
    
    @staticmethod
    def unidad_existe(unidad_id: int) -> bool:
        """
        Verificar si una unidad de medida existe.
        
        Args:
            unidad_id: ID de la unidad
            
        Returns:
            True si existe
        """
        with get_db_session() as session:
            existe = session.query(UnidadMedida).filter(
                UnidadMedida.id_unidad == unidad_id
            ).first()
            return existe is not None
    
    
    @staticmethod
    def clave_existe(clave: str) -> bool:
        """
        Verificar si una clave ya existe.
        
        Args:
            clave: Clave a verificar
            
        Returns:
            True si existe
        """
        with get_db_session() as session:
            existe = session.query(UnidadMedida).filter(
                UnidadMedida.clave == clave
            ).first()
            return existe is not None
