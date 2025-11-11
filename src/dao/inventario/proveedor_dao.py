"""
ProveedorDAO - Data Access Object para inventario.Proveedor
"""

from src.models import Proveedor
from src.core.db.session_manager import get_db_session
from src.schemas.proveedor_schema import ProveedorResponseSchema
import logging

logger = logging.getLogger(__name__)


class ProveedorDAO:
    """Data Access Object para Proveedor"""
    
    @staticmethod
    def crear_proveedor(nombre: str, telefono: str = None, email: str = None) -> dict:
        """
        Crear nuevo proveedor.
        
        Args:
            nombre: Nombre del proveedor
            telefono: Teléfono (opcional)
            email: Email (opcional)
            
        Returns:
            Dict serializado del proveedor
        """
        schema = ProveedorResponseSchema()
        with get_db_session() as session:
            proveedor = Proveedor(
                nombre=nombre,
                telefono=telefono,
                email=email,
                es_activo=True
            )
            session.add(proveedor)
            session.commit()
            logger.info(f"Proveedor creado: {nombre} (ID: {proveedor.id_proveedor})")
            return schema.dump(proveedor)
    
    
    @staticmethod
    def obtener_proveedor_por_id(proveedor_id: int) -> dict:
        """
        Obtener proveedor por ID (solo activos).
        
        Args:
            proveedor_id: ID del proveedor
            
        Returns:
            Dict del proveedor o None
        """
        schema = ProveedorResponseSchema()
        with get_db_session() as session:
            proveedor = session.query(Proveedor).filter(
                Proveedor.id_proveedor == proveedor_id,
                Proveedor.es_activo == True
            ).first()
            return schema.dump(proveedor) if proveedor else None
    
    
    @staticmethod
    def obtener_todos_proveedores(solo_activos: bool = True) -> list:
        """
        Obtener todos los proveedores.
        
        Args:
            solo_activos: Si True, solo proveedores activos
            
        Returns:
            Lista de dicts de proveedores
        """
        schema = ProveedorResponseSchema()
        with get_db_session() as session:
            query = session.query(Proveedor)
            
            if solo_activos:
                query = query.filter(Proveedor.es_activo == True)
            
            query = query.order_by(Proveedor.nombre)
            proveedores = query.all()
            return schema.dump(proveedores, many=True)
    
    
    @staticmethod
    def actualizar_proveedor(proveedor_id: int, nombre: str = None, 
                            telefono: str = None, email: str = None) -> dict:
        """
        Actualizar proveedor.
        
        Args:
            proveedor_id: ID del proveedor
            nombre: Nuevo nombre (opcional)
            telefono: Nuevo teléfono (opcional)
            email: Nuevo email (opcional)
            
        Returns:
            Dict del proveedor actualizado o None
        """
        schema = ProveedorResponseSchema()
        with get_db_session() as session:
            proveedor = session.query(Proveedor).filter(
                Proveedor.id_proveedor == proveedor_id
            ).first()
            
            if not proveedor:
                return None
            
            if nombre is not None:
                proveedor.nombre = nombre
            if telefono is not None:
                proveedor.telefono = telefono
            if email is not None:
                proveedor.email = email
            
            session.commit()
            logger.info(f"Proveedor actualizado: {proveedor_id}")
            return schema.dump(proveedor)
    
    
    @staticmethod
    def eliminar_proveedor(proveedor_id: int) -> bool:
        """
        Eliminar proveedor (soft delete).
        
        Args:
            proveedor_id: ID del proveedor
            
        Returns:
            True si se eliminó, False si no existe
        """
        with get_db_session() as session:
            proveedor = session.query(Proveedor).filter(
                Proveedor.id_proveedor == proveedor_id
            ).first()
            
            if not proveedor:
                return False
            
            proveedor.es_activo = False
            session.commit()
            logger.info(f"Proveedor eliminado (soft): {proveedor_id}")
            return True
    
    
    @staticmethod
    def proveedor_existe(proveedor_id: int) -> bool:
        """
        Verificar si un proveedor existe y está activo.
        
        Args:
            proveedor_id: ID del proveedor
            
        Returns:
            True si existe
        """
        with get_db_session() as session:
            existe = session.query(Proveedor).filter(
                Proveedor.id_proveedor == proveedor_id,
                Proveedor.es_activo == True
            ).first()
            return existe is not None
