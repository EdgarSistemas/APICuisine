"""
ProductoRecetaDAO - Data Access Object para catalogos.ProductoReceta y ProductoRecetaItem
"""

from src.models import ProductoReceta, ProductoRecetaItem, Producto, Insumo
from src.core.db.session_manager import get_db_session
from src.schemas.producto_receta_schema import (
    ProductoRecetaResponseSchema,
    ProductoRecetaDetailSchema,
    ProductoRecetaItemResponseSchema
)
import logging

logger = logging.getLogger(__name__)


class ProductoRecetaDAO:
    """Data Access Object para ProductoReceta"""
    
    @staticmethod
    def crear_receta(producto_id: int, nombre: str) -> dict:
        """
        Crear nueva receta para un producto.
        
        Args:
            producto_id: ID del producto
            nombre: Nombre de la receta
            
        Returns:
            Dict serializado de la receta
        """
        schema = ProductoRecetaResponseSchema()
        with get_db_session() as session:
            receta = ProductoReceta(producto_id=producto_id, nombre=nombre, es_activa=True)
            session.add(receta)
            session.commit()
            return schema.dump(receta)
    
    
    @staticmethod
    def obtener_receta_por_id(receta_id: int) -> dict:
        """Obtener receta por ID con todos sus items"""
        schema = ProductoRecetaDetailSchema()
        with get_db_session() as session:
            receta = session.query(ProductoReceta).filter_by(id_receta=receta_id).first()
            if receta:
                return schema.dump(receta)
            return None
    
    
    @staticmethod
    def obtener_recetas_por_producto(producto_id: int, solo_activas: bool = True) -> list:
        """Obtener todas las recetas de un producto"""
        schema = ProductoRecetaResponseSchema()
        with get_db_session() as session:
            query = session.query(ProductoReceta).filter_by(producto_id=producto_id)
            if solo_activas:
                query = query.filter_by(es_activa=True)
            recetas = query.all()
            return [schema.dump(r) for r in recetas]
    
    
    @staticmethod
    def obtener_receta_activa_producto(producto_id: int) -> dict:
        """Obtener la receta activa de un producto (solo 1 por producto)"""
        schema = ProductoRecetaDetailSchema()
        with get_db_session() as session:
            receta = session.query(ProductoReceta).filter_by(
                producto_id=producto_id,
                es_activa=True
            ).first()
            if receta:
                return schema.dump(receta)
            return None
    
    
    @staticmethod
    def actualizar_receta(receta_id: int, nombre: str = None, es_activa: bool = None) -> dict:
        """Actualizar receta"""
        schema = ProductoRecetaResponseSchema()
        with get_db_session() as session:
            receta = session.query(ProductoReceta).filter_by(id_receta=receta_id).first()
            
            if not receta:
                return None
            
            if nombre is not None:
                receta.nombre = nombre
            if es_activa is not None:
                receta.es_activa = es_activa
            
            session.commit()
            return schema.dump(receta)
    
    
    @staticmethod
    def eliminar_receta_soft(receta_id: int) -> bool:
        """Soft delete: marcar receta como inactiva"""
        with get_db_session() as session:
            receta = session.query(ProductoReceta).filter_by(id_receta=receta_id).first()
            
            if not receta:
                return False
            
            receta.es_activa = False
            session.commit()
            return True
    
    
    # ========== Helper Methods ==========
    
    @staticmethod
    def receta_existe(receta_id: int) -> bool:
        """Verificar si receta existe"""
        with get_db_session() as session:
            return session.query(ProductoReceta).filter_by(id_receta=receta_id).first() is not None
    
    
    @staticmethod
    def producto_existe(producto_id: int) -> bool:
        """Verificar si producto existe"""
        with get_db_session() as session:
            return session.query(Producto).filter_by(id_producto=producto_id).first() is not None


class ProductoRecetaItemDAO:
    """Data Access Object para ProductoRecetaItem"""
    
    @staticmethod
    def agregar_insumo_a_receta(receta_id: int, insumo_id: int, cantidad: float) -> dict:
        """
        Agregar insumo a receta.
        
        Args:
            receta_id: ID de receta
            insumo_id: ID del insumo
            cantidad: Cantidad en unidad base del insumo
            
        Returns:
            Dict serializado del item
        """
        schema = ProductoRecetaItemResponseSchema()
        with get_db_session() as session:
            item = ProductoRecetaItem(
                receta_id=receta_id,
                insumo_id=insumo_id,
                cantidad=cantidad
            )
            session.add(item)
            session.commit()
            return schema.dump(item)
    
    
    @staticmethod
    def obtener_insumos_receta(receta_id: int) -> list:
        """Obtener todos los insumos de una receta"""
        schema = ProductoRecetaItemResponseSchema()
        with get_db_session() as session:
            items = session.query(ProductoRecetaItem).filter_by(receta_id=receta_id).all()
            return [schema.dump(item) for item in items]
    
    
    @staticmethod
    def actualizar_cantidad(receta_item_id: int, cantidad: float) -> dict:
        """Actualizar cantidad de insumo en receta"""
        schema = ProductoRecetaItemResponseSchema()
        with get_db_session() as session:
            item = session.query(ProductoRecetaItem).filter_by(id_receta_item=receta_item_id).first()
            
            if not item:
                return None
            
            item.cantidad = cantidad
            session.commit()
            return schema.dump(item)
    
    
    @staticmethod
    def remover_insumo_de_receta(receta_item_id: int) -> bool:
        """Remover insumo de receta"""
        with get_db_session() as session:
            item = session.query(ProductoRecetaItem).filter_by(id_receta_item=receta_item_id).first()
            
            if not item:
                return False
            
            session.delete(item)
            session.commit()
            return True
    
    
    # ========== Helper Methods ==========
    
    @staticmethod
    def receta_item_existe(receta_item_id: int) -> bool:
        """Verificar si item de receta existe"""
        with get_db_session() as session:
            return session.query(ProductoRecetaItem).filter_by(id_receta_item=receta_item_id).first() is not None
    
    
    @staticmethod
    def insumo_existe(insumo_id: int) -> bool:
        """Verificar si insumo existe"""
        with get_db_session() as session:
            return session.query(Insumo).filter_by(id_insumo=insumo_id).first() is not None
    
    
    @staticmethod
    def insumo_ya_en_receta(receta_id: int, insumo_id: int) -> bool:
        """Verificar si insumo ya está en la receta (evitar duplicados)"""
        with get_db_session() as session:
            return session.query(ProductoRecetaItem).filter_by(
                receta_id=receta_id,
                insumo_id=insumo_id
            ).first() is not None
