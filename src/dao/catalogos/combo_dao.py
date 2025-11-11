"""
ComboDAO - Data Access Object para catalogos.Combo y ComboProducto
"""

from src.models import Combo, ComboProducto, Producto
from src.core.db.session_manager import get_db_session
from src.schemas.combo_schema import ComboResponseSchema, ComboProductoResponseSchema
import logging

logger = logging.getLogger(__name__)


class ComboDAO:
    """Data Access Object para Combo"""
    
    @staticmethod
    def crear_combo(nombre: str, precio: float, descripcion: str = None, 
                   imagen_url: str = None) -> dict:
        """
        Crear nuevo combo.
        
        Args:
            nombre: Nombre del combo
            precio: Precio del combo
            descripcion: Descripción (opcional)
            imagen_url: URL de imagen (opcional)
            
        Returns:
            Dict serializado del combo
        """
        schema = ComboResponseSchema()
        with get_db_session() as session:
            combo = Combo(
                nombre=nombre,
                precio=precio,
                descripcion=descripcion,
                imagen_url=imagen_url,
                es_activo=True
            )
            session.add(combo)
            session.commit()
            logger.info(f"Combo creado: {nombre} (ID: {combo.id_combo})")
            return schema.dump(combo)
    
    
    @staticmethod
    def obtener_combo_por_id(combo_id: int) -> dict:
        """
        Obtener combo por ID.
        
        Args:
            combo_id: ID del combo
            
        Returns:
            Dict del combo o None
        """
        schema = ComboResponseSchema()
        with get_db_session() as session:
            combo = session.query(Combo).filter(
                Combo.id_combo == combo_id
            ).first()
            return schema.dump(combo) if combo else None
    
    
    @staticmethod
    def obtener_combo_detallado(combo_id: int) -> dict:
        """
        Obtener combo con lista de productos (sin receta).
        Datos completos para GET by ID.
        Solo retorna combos ACTIVOS.
        
        Args:
            combo_id: ID del combo
            
        Returns:
            {
                id_combo, nombre, descripcion, imagen_url, precio,
                productos: [{id_combo_producto, producto_id, cantidad, producto: {...}}],
                es_activo, created_at, updated_at
            }
        """
        with get_db_session() as session:
            combo = session.query(Combo).filter(
                Combo.id_combo == combo_id,
                Combo.es_activo == True
            ).first()
            
            if not combo:
                return None
            
            # Construir respuesta con datos completos
            resultado = {
                "id_combo": combo.id_combo,
                "nombre": combo.nombre,
                "descripcion": combo.descripcion,
                "imagen_url": combo.imagen_url,
                "precio": float(combo.precio),
                "es_activo": combo.es_activo,
                "created_at": combo.created_at.strftime('%Y-%m-%d %H:%M:%S') if combo.created_at else None,
                "updated_at": combo.updated_at.strftime('%Y-%m-%d %H:%M:%S') if combo.updated_at else None,
                "productos": []
            }
            
            # Obtener productos del combo
            combo_productos = session.query(ComboProducto).filter(
                ComboProducto.combo_id == combo_id
            ).all()
            
            for combo_producto in combo_productos:
                producto = session.query(Producto).filter(
                    Producto.id_producto == combo_producto.producto_id
                ).first()
                
                if producto:
                    producto_dict = {
                        "id_combo_producto": combo_producto.id_combo_producto,
                        "producto_id": combo_producto.producto_id,
                        "cantidad": combo_producto.cantidad,
                        "producto": {
                            "id_producto": producto.id_producto,
                            "codigo": producto.codigo,
                            "nombre": producto.nombre,
                            "descripcion": producto.descripcion,
                            "imagen_url": producto.imagen_url,
                            "precio": float(producto.precio)
                        }
                    }
                    resultado["productos"].append(producto_dict)
            
            return resultado
    
    
    @staticmethod
    def obtener_todos_los_combos(solo_activos: bool = True) -> list:
        """
        Obtener todos los combos.
        
        Args:
            solo_activos: Si True, solo combos activos
            
        Returns:
            Lista de dicts de combos
        """
        schema = ComboResponseSchema()
        with get_db_session() as session:
            query = session.query(Combo)
            
            if solo_activos:
                query = query.filter(Combo.es_activo == True)
            
            combos = query.order_by(Combo.nombre).all()
            return [schema.dump(c) for c in combos]
    
    
    @staticmethod
    def actualizar_combo(combo_id: int, nombre: str = None, precio: float = None,
                        descripcion: str = None, imagen_url: str = None, 
                        es_activo: bool = None) -> dict:
        """
        Actualizar combo.
        
        Args:
            combo_id: ID del combo
            nombre: Nuevo nombre (opcional)
            precio: Nuevo precio (opcional)
            descripcion: Nueva descripción (opcional)
            imagen_url: Nueva URL de imagen (opcional)
            es_activo: Nuevo estado (opcional)
            
        Returns:
            Dict actualizado o None
        """
        schema = ComboResponseSchema()
        with get_db_session() as session:
            combo = session.query(Combo).filter(
                Combo.id_combo == combo_id
            ).first()
            
            if not combo:
                return None
            
            if nombre is not None:
                combo.nombre = nombre
            if precio is not None:
                combo.precio = precio
            if descripcion is not None:
                combo.descripcion = descripcion
            if imagen_url is not None:
                combo.imagen_url = imagen_url
            if es_activo is not None:
                combo.es_activo = es_activo
            
            session.commit()
            logger.info(f"Combo actualizado: {combo_id}")
            return schema.dump(combo)
    
    
    @staticmethod
    def eliminar_combo_soft(combo_id: int) -> bool:
        """
        Eliminar combo (soft delete).
        
        Args:
            combo_id: ID del combo
            
        Returns:
            True si se eliminó, False si no existe
        """
        with get_db_session() as session:
            combo = session.query(Combo).filter(
                Combo.id_combo == combo_id
            ).first()
            
            if not combo:
                return False
            
            combo.es_activo = False
            session.commit()
            logger.info(f"Combo eliminado (soft): {combo_id}")
            return True
    
    
    @staticmethod
    def combo_existe(combo_id: int) -> bool:
        """
        Verificar si un combo existe.
        
        Args:
            combo_id: ID del combo
            
        Returns:
            True si existe
        """
        with get_db_session() as session:
            existe = session.query(Combo).filter(
                Combo.id_combo == combo_id
            ).first()
            return existe is not None


class ComboProductoDAO:
    """Data Access Object para ComboProducto"""
    
    @staticmethod
    def agregar_producto_a_combo(combo_id: int, producto_id: int, cantidad: int = 1) -> dict:
        """
        Agregar un producto a un combo.
        
        Args:
            combo_id: ID del combo
            producto_id: ID del producto
            cantidad: Cantidad (default: 1)
            
        Returns:
            Dict serializado del combo-producto
        """
        schema = ComboProductoResponseSchema()
        with get_db_session() as session:
            combo_producto = ComboProducto(
                combo_id=combo_id,
                producto_id=producto_id,
                cantidad=cantidad
            )
            session.add(combo_producto)
            session.commit()
            logger.info(f"Producto {producto_id} agregado a combo {combo_id}")
            return schema.dump(combo_producto)
    
    
    @staticmethod
    def obtener_productos_de_combo(combo_id: int) -> list:
        """
        Obtener todos los productos de un combo.
        
        Args:
            combo_id: ID del combo
            
        Returns:
            Lista de dicts de combo-productos
        """
        schema = ComboProductoResponseSchema()
        with get_db_session() as session:
            items = session.query(ComboProducto).filter(
                ComboProducto.combo_id == combo_id
            ).order_by(ComboProducto.created_at).all()
            return [schema.dump(item) for item in items]
    
    
    @staticmethod
    def actualizar_cantidad_producto(combo_producto_id: int, cantidad: int) -> dict:
        """
        Actualizar cantidad de un producto en el combo.
        
        Args:
            combo_producto_id: ID del combo-producto
            cantidad: Nueva cantidad
            
        Returns:
            Dict actualizado o None
        """
        schema = ComboProductoResponseSchema()
        with get_db_session() as session:
            item = session.query(ComboProducto).filter(
                ComboProducto.id_combo_producto == combo_producto_id
            ).first()
            
            if not item:
                return None
            
            item.cantidad = cantidad
            session.commit()
            logger.info(f"Cantidad actualizada: combo-producto {combo_producto_id}")
            return schema.dump(item)
    
    
    @staticmethod
    def remover_producto_de_combo(combo_producto_id: int) -> bool:
        """
        Remover un producto de un combo.
        
        Args:
            combo_producto_id: ID del combo-producto
            
        Returns:
            True si se removió, False si no existe
        """
        with get_db_session() as session:
            item = session.query(ComboProducto).filter(
                ComboProducto.id_combo_producto == combo_producto_id
            ).first()
            
            if not item:
                return False
            
            session.delete(item)
            session.commit()
            logger.info(f"Producto removido de combo: {combo_producto_id}")
            return True
    
    
    @staticmethod
    def combo_producto_existe(combo_producto_id: int) -> bool:
        """
        Verificar si un combo-producto existe.
        
        Args:
            combo_producto_id: ID del combo-producto
            
        Returns:
            True si existe
        """
        with get_db_session() as session:
            existe = session.query(ComboProducto).filter(
                ComboProducto.id_combo_producto == combo_producto_id
            ).first()
            return existe is not None
    
    
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
