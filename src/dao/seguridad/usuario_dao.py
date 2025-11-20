"""
UsuarioDAO - Data Access Object para seguridad.Usuario
Queries para filtrar usuarios por rol y sucursal
"""

from src.models import Usuario, UsuarioSucursal, Sucursal
from src.models.auth import UsuarioRol
from src.core.db.session_manager import get_db_session
import logging

logger = logging.getLogger(__name__)


class UsuarioDAO:
    """Data Access Object para Usuario"""
    
    @staticmethod
    def obtener_usuarios_por_rol(rol_id: int, sucursal_id: int = None) -> list:
        """
        Obtener usuarios de un rol específico.
        
        Si sucursal_id es provided, filtra por usuarios asignados a esa sucursal.
        
        Args:
            rol_id: ID del rol (ej: 5 para Mesero)
            sucursal_id: ID de la sucursal (opcional)
            
        Returns:
            Lista de Usuario
        """
        with get_db_session() as session:
            # Hacer JOIN con UsuarioRol para acceder a rol_id
            query = session.query(Usuario).join(
                UsuarioRol, Usuario.id_usuario == UsuarioRol.usuario_id
            ).filter(UsuarioRol.rol_id == rol_id)
            
            # Si se filtra por sucursal, hacer JOIN con UsuarioSucursal
            if sucursal_id:
                query = query.join(UsuarioSucursal).filter(
                    UsuarioSucursal.sucursal_id == sucursal_id
                )
            
            usuarios = query.filter(Usuario.es_activo == True).order_by(Usuario.nombre).all()
            return usuarios
    
    
    @staticmethod
    def obtener_meseros_por_sucursal(sucursal_id: int) -> list:
        """
        Obtener todos los meseros (rol_id=5) de una sucursal.
        
        Args:
            sucursal_id: ID de la sucursal
            
        Returns:
            Lista de Usuario (solo Meseros)
        """
        return UsuarioDAO.obtener_usuarios_por_rol(rol_id=5, sucursal_id=sucursal_id)
    
    
    @staticmethod
    def obtener_usuarios_por_rol_y_sucursal(rol_id: int, sucursal_id: int) -> list:
        """
        Obtener usuarios filtrados por rol y sucursal (ambos obligatorios).
        
        Args:
            rol_id: ID del rol (obligatorio)
            sucursal_id: ID de la sucursal (obligatorio)
            
        Returns:
            Lista de dicts con datos del usuario
        """
        from src.schemas.usuario_schema import UsuarioResponseSchema
        
        schema = UsuarioResponseSchema()
        with get_db_session() as session:
            # JOIN con UsuarioRol y UsuarioSucursal para acceder a rol_id y sucursal_id
            usuarios = session.query(Usuario).join(
                UsuarioRol, Usuario.id_usuario == UsuarioRol.usuario_id
            ).join(
                UsuarioSucursal, Usuario.id_usuario == UsuarioSucursal.usuario_id
            ).filter(
                UsuarioRol.rol_id == rol_id,
                UsuarioSucursal.sucursal_id == sucursal_id,
                Usuario.es_activo == True
            ).order_by(Usuario.nombre.asc()).all()
            
            return [schema.dump(u) for u in usuarios]
    
    
    @staticmethod
    def obtener_usuario_por_id(usuario_id: int) -> Usuario:
        """
        Obtener usuario por ID.
        
        Args:
            usuario_id: ID del usuario
            
        Returns:
            Usuario o None
        """
        with get_db_session() as session:
            usuario = session.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
            return usuario
