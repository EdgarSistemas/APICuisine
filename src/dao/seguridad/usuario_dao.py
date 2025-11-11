"""
UsuarioDAO - Data Access Object para seguridad.Usuario
Queries para filtrar usuarios por rol y sucursal
"""

from src.models import Usuario, UsuarioSucursal, Sucursal
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
            query = session.query(Usuario).filter(Usuario.rol_id == rol_id)
            
            # Si se filtra por sucursal, hacer JOIN con UsuarioSucursal
            if sucursal_id:
                query = query.join(UsuarioSucursal).filter(
                    UsuarioSucursal.sucursal_id == sucursal_id
                )
            
            usuarios = query.filter(Usuario.activo == True).order_by(Usuario.nombre).all()
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
