"""
CategoriaMenuDAO - Data Access Object para catalogos.CategoriaMenu
"""

from src.models import CategoriaMenu, Producto, Combo, ComboProducto
from src.core.db.session_manager import get_db_session
from src.schemas.categoria_menu_schema import CategoriaMenuResponseSchema
from src.schemas.producto_schema import ProductoResponseSchema
from src.schemas.combo_schema import ComboResponseSchema
import logging

logger = logging.getLogger(__name__)


class CategoriaMenuDAO:
    """Data Access Object para CategoriaMenu"""
    
    @staticmethod
    def crear_categoria(nombre: str, descripcion: str = None) -> dict:
        """
        Crear nueva categoría de menú.
        
        Args:
            nombre: Nombre de la categoría
            descripcion: Descripción (opcional)
            
        Returns:
            Dict serializado de la categoría
        """
        schema = CategoriaMenuResponseSchema()
        with get_db_session() as session:
            categoria = CategoriaMenu(
                nombre=nombre,
                descripcion=descripcion,
                es_activa=True
            )
            session.add(categoria)
            session.commit()
            logger.info(f"Categoría de menú creada: {nombre}")
            return schema.dump(categoria)
    
    
    @staticmethod
    def obtener_categoria_por_id(categoria_id: int) -> dict:
        """
        Obtener categoría por ID.
        
        Args:
            categoria_id: ID de la categoría
            
        Returns:
            Dict de la categoría o None
        """
        schema = CategoriaMenuResponseSchema()
        producto_schema = ProductoResponseSchema()
        combo_schema = ComboResponseSchema()
        
        with get_db_session() as session:
            categoria = session.query(CategoriaMenu).filter(
                CategoriaMenu.id_categoria == categoria_id
            ).first()
            
            if not categoria:
                return None
            
            # Obtener productos de la categoría
            productos = session.query(Producto).filter(
                Producto.categoria_id == categoria_id,
                Producto.es_activo == True
            ).all()
            
            # Obtener combos que contienen productos de esta categoría
            combos_query = session.query(Combo).distinct().join(
                ComboProducto, Combo.id_combo == ComboProducto.combo_id
            ).join(
                Producto, ComboProducto.producto_id == Producto.id_producto
            ).filter(
                Producto.categoria_id == categoria_id,
                Combo.es_activo == True
            ).all()
            
            resultado = schema.dump(categoria)
            resultado['productos'] = [producto_schema.dump(p) for p in productos]
            resultado['combos'] = [combo_schema.dump(c) for c in combos_query]
            
            return resultado
    
    
    @staticmethod
    def obtener_todas_las_categorias(solo_activas: bool = True) -> list:
        """
        Obtener todas las categorías de menú.
        
        Args:
            solo_activas: Si True, solo categorías activas
            
        Returns:
            Lista de dicts de categorías
        """
        schema = CategoriaMenuResponseSchema()
        with get_db_session() as session:
            query = session.query(CategoriaMenu)
            
            if solo_activas:
                query = query.filter(CategoriaMenu.es_activa == True)
            
            categorias = query.order_by(CategoriaMenu.nombre).all()
            return [schema.dump(c) for c in categorias]
    
    
    @staticmethod
    def actualizar_categoria(categoria_id: int, nombre: str = None, 
                            descripcion: str = None) -> dict:
        """
        Actualizar categoría.
        
        Args:
            categoria_id: ID de la categoría
            nombre: Nuevo nombre (opcional)
            descripcion: Nueva descripción (opcional)
            es_activa: Nuevo estado (opcional)
            
        Returns:
            Dict actualizado o None
        """
        schema = CategoriaMenuResponseSchema()
        with get_db_session() as session:
            categoria = session.query(CategoriaMenu).filter(
                CategoriaMenu.id_categoria == categoria_id
            ).first()
            
            if not categoria:
                return None
            
            if nombre is not None:
                categoria.nombre = nombre
            if descripcion is not None:
                categoria.descripcion = descripcion
            
            session.commit()
            logger.info(f"Categoría actualizada: {categoria_id}")
            return schema.dump(categoria)
    
    
    @staticmethod
    def eliminar_categoria_soft(categoria_id: int) -> bool:
        """
        Eliminar categoría (soft delete).
        
        Args:
            categoria_id: ID de la categoría
            
        Returns:
            True si se eliminó, False si no existe
        """
        with get_db_session() as session:
            categoria = session.query(CategoriaMenu).filter(
                CategoriaMenu.id_categoria == categoria_id
            ).first()
            
            if not categoria:
                return False
            
            categoria.es_activa = False
            session.commit()
            logger.info(f"Categoría eliminada (soft): {categoria_id}")
            return True
    
    
    @staticmethod
    def categoria_existe(categoria_id: int) -> bool:
        """
        Verificar si una categoría existe.
        
        Args:
            categoria_id: ID de la categoría
            
        Returns:
            True si existe
        """
        with get_db_session() as session:
            existe = session.query(CategoriaMenu).filter(
                CategoriaMenu.id_categoria == categoria_id
            ).first()
            return existe is not None
