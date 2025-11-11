"""
ProductoDAO - Data Access Object para catalogos.Producto
"""

from src.models import Producto, CategoriaMenu, ProductoReceta, ProductoRecetaItem, Insumo, UnidadMedida
from src.core.db.session_manager import get_db_session
from src.schemas.producto_schema import ProductoResponseSchema
import logging

logger = logging.getLogger(__name__)


class ProductoDAO:
    """Data Access Object para Producto"""
    
    @staticmethod
    def crear_producto(categoria_id: int, nombre: str, precio: float, 
                      codigo: str = None, descripcion: str = None, 
                      imagen_url: str = None) -> dict:
        """
        Crear nuevo producto.
        
        Args:
            categoria_id: ID de la categoría
            nombre: Nombre del producto
            precio: Precio unitario
            codigo: Código del producto (opcional)
            descripcion: Descripción (opcional)
            imagen_url: URL de imagen (opcional)
            
        Returns:
            Dict serializado del producto
        """
        schema = ProductoResponseSchema()
        with get_db_session() as session:
            producto = Producto(
                categoria_id=categoria_id,
                nombre=nombre,
                precio=precio,
                codigo=codigo,
                descripcion=descripcion,
                imagen_url=imagen_url,
                es_activo=True
            )
            session.add(producto)
            session.commit()
            logger.info(f"Producto creado: {nombre} (ID: {producto.id_producto})")
            return schema.dump(producto)
    
    
    @staticmethod
    def obtener_producto_por_id(producto_id: int) -> dict:
        """
        Obtener producto por ID.
        
        Args:
            producto_id: ID del producto
            
        Returns:
            Dict del producto o None
        """
        schema = ProductoResponseSchema()
        with get_db_session() as session:
            producto = session.query(Producto).filter(
                Producto.id_producto == producto_id
            ).first()
            return schema.dump(producto) if producto else None
    
    
    @staticmethod
    def obtener_producto_detallado(producto_id: int) -> dict:
        """
        Obtener producto con categoría, receta e insumos (con unidad de medida).
        Datos completos para GET by ID.
        Solo retorna productos ACTIVOS.
        
        Args:
            producto_id: ID del producto
            
        Returns:
            {
                id_producto, codigo, nombre, descripcion, imagen_url, precio,
                categoria: {id_categoria, nombre, descripcion},
                receta: {
                    id_receta, nombre,
                    items: [{id_receta_item, insumo_id, cantidad, insumo: {...}}]
                },
                es_activo, created_at, updated_at
            }
        """
        with get_db_session() as session:
            producto = session.query(Producto).filter(
                Producto.id_producto == producto_id,
                Producto.es_activo == True
            ).first()
            
            if not producto:
                return None
            
            # Construir respuesta con datos completos
            resultado = {
                "id_producto": producto.id_producto,
                "codigo": producto.codigo,
                "nombre": producto.nombre,
                "descripcion": producto.descripcion,
                "imagen_url": producto.imagen_url,
                "precio": float(producto.precio),
                "es_activo": producto.es_activo,
                "created_at": producto.created_at.strftime('%Y-%m-%d %H:%M:%S') if producto.created_at else None,
                "updated_at": producto.updated_at.strftime('%Y-%m-%d %H:%M:%S') if producto.updated_at else None,
            }
            
            # Agregar categoría
            if producto.categoria:
                resultado["categoria"] = {
                    "id_categoria": producto.categoria.id_categoria,
                    "nombre": producto.categoria.nombre,
                    "descripcion": producto.categoria.descripcion
                }
            
            # Agregar receta con insumos
            receta = session.query(ProductoReceta).filter(
                ProductoReceta.producto_id == producto_id
            ).first()
            
            if receta:
                items = session.query(ProductoRecetaItem).filter(
                    ProductoRecetaItem.receta_id == receta.id_receta
                ).all()
                
                items_datos = []
                for item in items:
                    # Obtener insumo con unidad de medida
                    insumo = session.query(Insumo).filter(
                        Insumo.id_insumo == item.insumo_id
                    ).first()
                    
                    item_dict = {
                        "id_receta_item": item.id_receta_item,
                        "insumo_id": item.insumo_id,
                        "cantidad": float(item.cantidad),
                        "insumo": {
                            "id_insumo": insumo.id_insumo,
                            "nombre": insumo.nombre,
                            "unidad_medida": {
                                "id_unidad_medida": insumo.unidad_medida.id_unidad,
                                "clave": insumo.unidad_medida.clave,
                                "nombre": insumo.unidad_medida.nombre,
                            } if insumo.unidad_medida else None
                        }
                    }
                    items_datos.append(item_dict)
                
                resultado["receta"] = {
                    "id_receta": receta.id_receta,
                    "nombre": receta.nombre,
                    "items": items_datos
                }
            else:
                resultado["receta"] = None
            
            return resultado
    
    
    @staticmethod
    def obtener_productos_por_categoria(categoria_id: int, solo_activos: bool = True) -> list:
        """
        Obtener productos por categoría.
        
        Args:
            categoria_id: ID de la categoría
            solo_activos: Si True, solo productos activos
            
        Returns:
            Lista de dicts de productos
        """
        schema = ProductoResponseSchema()
        with get_db_session() as session:
            query = session.query(Producto).filter(Producto.categoria_id == categoria_id)
            
            if solo_activos:
                query = query.filter(Producto.es_activo == True)
            
            productos = query.order_by(Producto.nombre).all()
            return [schema.dump(p) for p in productos]
    
    
    @staticmethod
    def obtener_todos_los_productos(solo_activos: bool = True) -> list:
        """
        Obtener todos los productos activos.
        
        Args:
            solo_activos: Si True, solo productos activos
            
        Returns:
            Lista de dicts de productos
        """
        schema = ProductoResponseSchema()
        with get_db_session() as session:
            query = session.query(Producto)
            
            if solo_activos:
                query = query.filter(Producto.es_activo == True)
            
            productos = query.order_by(Producto.nombre).all()
            return [schema.dump(p) for p in productos]
    
    
    @staticmethod
    def obtener_producto_por_codigo(codigo: str) -> dict:
        """
        Obtener producto por código SKU.
        
        Args:
            codigo: Código del producto
            
        Returns:
            Dict del producto o None
        """
        schema = ProductoResponseSchema()
        with get_db_session() as session:
            producto = session.query(Producto).filter(
                Producto.codigo == codigo
            ).first()
            return schema.dump(producto) if producto else None
    
    
    @staticmethod
    def actualizar_producto(producto_id: int, nombre: str = None, 
                           precio: float = None, descripcion: str = None,
                           imagen_url: str = None) -> dict:
        """
        Actualizar producto.
        
        Args:
            producto_id: ID del producto
            nombre: Nuevo nombre (opcional)
            precio: Nuevo precio (opcional)
            descripcion: Nueva descripción (opcional)
            imagen_url: Nueva URL de imagen (opcional)
            
        Returns:
            Dict actualizado o None
        """
        schema = ProductoResponseSchema()
        with get_db_session() as session:
            producto = session.query(Producto).filter(
                Producto.id_producto == producto_id
            ).first()
            
            if not producto:
                return None
            
            if nombre is not None:
                producto.nombre = nombre
            if precio is not None:
                producto.precio = precio
            if descripcion is not None:
                producto.descripcion = descripcion
            if imagen_url is not None:
                producto.imagen_url = imagen_url
            
            session.commit()
            logger.info(f"Producto actualizado: {producto_id}")
            return schema.dump(producto)
    
    
    @staticmethod
    def eliminar_producto_soft(producto_id: int) -> bool:
        """
        Eliminar producto (soft delete).
        
        Args:
            producto_id: ID del producto
            
        Returns:
            True si se eliminó, False si no existe
        """
        with get_db_session() as session:
            producto = session.query(Producto).filter(
                Producto.id_producto == producto_id
            ).first()
            
            if not producto:
                return False
            
            producto.es_activo = False
            session.commit()
            logger.info(f"Producto eliminado (soft): {producto_id}")
            return True
    
    
    @staticmethod
    def producto_existe(producto_id: int) -> bool:
        """
        Verificar si un producto existe.
        
        Args:
            producto_id: ID del producto
            
        Returns:
            True si existe
        """
        with get_db_session() as session:
            existe = session.query(Producto).filter(
                Producto.id_producto == producto_id
            ).first()
            return existe is not None
    
    
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
