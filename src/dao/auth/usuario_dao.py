"""
Usuario DAO - Acceso a datos de usuarios usando modelos declarativos
"""

import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_
from sqlalchemy.orm import joinedload
from werkzeug.security import check_password_hash, generate_password_hash

from src.core.db.session_manager import get_db_session
from src.models.auth import Usuario, Rol, Modulo, UsuarioRol, UsuarioSucursal, RolModulo

logger = logging.getLogger(__name__)

class UsuarioDAO:
    """DAO para operaciones CRUD de usuarios usando modelos declarativos"""
    
    def crear_usuario(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear nuevo usuario con rol y sucursal
        
        Args:
            datos: Diccionario con datos del usuario, incluyendo sucursal_id y rol_id
            
        Returns:
            Dict con datos del usuario creado
        """
        try:
            with get_db_session() as session:
                # Crear usuario
                usuario_data = {k: v for k, v in datos.items() if k not in ['sucursal_id', 'rol_id']}
                usuario = Usuario(**usuario_data)
                
                session.add(usuario)
                session.flush()  # Para obtener el ID
                
                # Asignar a sucursal
                if 'sucursal_id' in datos and datos['sucursal_id'] is not None:
                    usuario_sucursal = UsuarioSucursal(
                        usuario_id=usuario.id_usuario,
                        sucursal_id=datos['sucursal_id']
                    )
                    session.add(usuario_sucursal)
                
                # Asignar rol
                if 'rol_id' in datos:
                    usuario_rol = UsuarioRol(
                        usuario_id=usuario.id_usuario,
                        rol_id=datos['rol_id']
                    )
                    session.add(usuario_rol)
                
                return self._usuario_to_dict(usuario, session)
                
        except SQLAlchemyError as e:
            logger.error(f"Error al crear usuario: {str(e)}")
            raise RuntimeError(f"Error en base de datos: {str(e)}")
    
    def obtener_por_id(self, usuario_id: int) -> Optional[Dict[str, Any]]:
        """Obtener usuario por ID con datos relacionados"""
        try:
            with get_db_session() as session:
                usuario = session.query(Usuario)\
                    .options(joinedload(Usuario.roles))\
                    .options(joinedload(Usuario.sucursales))\
                    .filter(Usuario.id_usuario == usuario_id)\
                    .first()
                
                if usuario:
                    return self._usuario_to_dict(usuario, session)
                return None
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener usuario {usuario_id}: {str(e)}")
            raise RuntimeError(f"Error en base de datos: {str(e)}")
    
    def obtener_por_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Obtener usuario por email con datos relacionados"""
        try:
            with get_db_session() as session:
                usuario = session.query(Usuario)\
                    .options(joinedload(Usuario.roles))\
                    .filter(Usuario.email == email)\
                    .first()
                
                if usuario:
                    return self._usuario_to_dict(usuario, session)
                return None
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener usuario por email {email}: {str(e)}")
            raise RuntimeError(f"Error en base de datos: {str(e)}")
    
    def listar_usuarios(self, filtros: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Listar usuarios con filtros opcionales"""
        try:
            with get_db_session() as session:
                query = session.query(Usuario)\
                    .options(joinedload(Usuario.roles))\
                    .options(joinedload(Usuario.sucursales))
                
                if filtros:
                    if 'es_activo' in filtros:
                        query = query.filter(Usuario.es_activo == filtros['es_activo'])
                    if 'sucursal_id' in filtros:
                        query = query.join(UsuarioSucursal).filter(
                            UsuarioSucursal.sucursal_id == filtros['sucursal_id']
                        )
                usuarios = query.where(Usuario.es_activo == True).all()
                return [self._usuario_to_dict(usuario, session) for usuario in usuarios]
                
        except SQLAlchemyError as e:
            logger.error(f"Error al listar usuarios: {str(e)}")
            raise RuntimeError(f"Error en base de datos: {str(e)}")
    
    def actualizar_usuario(self, usuario_id: int, datos: Dict[str, Any]) -> Dict[str, Any]:
        """Actualizar usuario existente"""
        try:
            with get_db_session() as session:
                usuario = session.query(Usuario).filter(
                    Usuario.id_usuario == usuario_id
                ).first()
                
                if not usuario:
                    raise ValueError(f"Usuario {usuario_id} no encontrado")
                
                # Actualizar campos del usuario
                for key, value in datos.items():
                    if key not in ['sucursal_id', 'rol_id'] and hasattr(usuario, key):
                        setattr(usuario, key, value)
                
                return self._usuario_to_dict(usuario, session)
                
        except SQLAlchemyError as e:
            logger.error(f"Error al actualizar usuario {usuario_id}: {str(e)}")
            raise RuntimeError(f"Error en base de datos: {str(e)}")
    
    def obtener_modulos_usuario(self, usuario_id: int) -> List[Dict[str, Any]]:
        """Obtener módulos permitidos para un usuario"""
        try:
            with get_db_session() as session:
                modulos = session.query(Modulo)\
                    .join(RolModulo, Modulo.id_modulo == RolModulo.modulo_id)\
                    .join(UsuarioRol, RolModulo.rol_id == UsuarioRol.rol_id)\
                    .filter(
                        and_(
                            UsuarioRol.usuario_id == usuario_id,
                            RolModulo.habilitado == True,
                            Modulo.es_activo == True
                        )
                    ).distinct().all()
                
                return [self._modulo_to_dict(modulo) for modulo in modulos]
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener módulos del usuario {usuario_id}: {str(e)}")
            raise RuntimeError(f"Error en base de datos: {str(e)}")
    
    def _usuario_to_dict(self, usuario, session) -> Dict[str, Any]:
        """Convertir usuario a diccionario con datos relacionados"""
        return {
            'id_usuario': usuario.id_usuario,
            'email': usuario.email,
            'nombre': usuario.nombre,
            'apellido': usuario.apellido,
            'telefono': usuario.telefono,
            'es_activo': usuario.es_activo,
            'es_cliente': usuario.es_cliente,
            'acepta_marketing': usuario.acepta_marketing,
            'tipo_acceso': usuario.tipo_acceso,
            'created_at': usuario.created_at.strftime('%Y-%m-%d %H:%M:%S') if usuario.created_at else None,
            'updated_at': usuario.updated_at.strftime('%Y-%m-%d %H:%M:%S') if usuario.updated_at else None,
            'roles': [{'id_rol': r.id_rol, 'nombre': r.nombre, 'descripcion': r.descripcion} for r in usuario.roles] if usuario.roles else [],
            'sucursales': [{'sucursal_id': s.sucursal_id} for s in usuario.sucursales] if usuario.sucursales else []
        }
    
    def _modulo_to_dict(self, modulo) -> Dict[str, Any]:
        """Convertir módulo a diccionario"""
        return {
            'id_modulo': modulo.id_modulo,
            'nombre': modulo.nombre,
            'clave': modulo.clave,
            'descripcion': modulo.descripcion,
            'es_activo': modulo.es_activo
        }
    
    def actualizar_password(self, usuario_id: int, nuevo_password_hash: str) -> bool:
        """
        Actualizar password del usuario
        
        Args:
            usuario_id: ID del usuario
            nuevo_password_hash: Nuevo password hasheado
            
        Returns:
            True si se actualizó correctamente, False en caso contrario
        """
        try:
            with get_db_session() as session:
                # Buscar usuario
                usuario = session.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
                
                if not usuario:
                    logger.warning(f"Usuario {usuario_id} no encontrado para actualizar password")
                    return False
                
                # Actualizar password
                usuario.hash_password = nuevo_password_hash
                
                session.commit()
                logger.info(f"Password actualizado para usuario {usuario_id}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error al actualizar password del usuario {usuario_id}: {str(e)}")
            return False

    def cambiar_password_con_actual(self, user_id: int, password_actual: str, nueva_password: str) -> Dict[str, Any]:
        """
        Cambiar password validando el password actual
        
        Args:
            user_id: ID del usuario
            password_actual: Password actual sin hashear
            nueva_password: Nueva password hasheada
            
        Returns:
            Dict con resultado de la operación
        """        
        try:
            with get_db_session() as session:
                # Buscar usuario
                usuario = session.query(Usuario).filter(Usuario.id_usuario == user_id).first()
                
                if not usuario:
                    return {
                        'success': False,
                        'error': 'USER_NOT_FOUND',
                        'message': 'Usuario no encontrado'
                    }
                
                # Verificar password actual
                if not check_password_hash(usuario.hash_password, password_actual):
                    return {
                        'success': False,
                        'error': 'CURRENT_PASSWORD_INCORRECT',
                        'message': 'La contraseña actual es incorrecta'
                    }
                
                # Hashear y actualizar password
                usuario.hash_password = generate_password_hash(nueva_password)
                session.commit()
                
                logger.info(f"Password cambiado exitosamente para usuario {user_id}")
                
                return {
                    'success': True,
                    'message': 'Contraseña actualizada exitosamente'
                }
                
        except SQLAlchemyError as e:
            logger.error(f"Error al cambiar password del usuario {user_id}: {str(e)}")
            return {
                'success': False,
                'error': 'DATABASE_ERROR',
                'message': 'Error en base de datos',
                'details': str(e)
            }
    
    def asignar_sucursal(self, usuario_id: int, sucursal_id: int) -> bool:
        """
        Asignar una sucursal adicional a un usuario
        
        Args:
            usuario_id: ID del usuario
            sucursal_id: ID de la sucursal
            
        Returns:
            True si se asignó correctamente
        """
        try:
            with get_db_session() as session:
                # Verificar si ya existe la asignación
                existe = session.query(UsuarioSucursal)\
                    .filter(UsuarioSucursal.usuario_id == usuario_id)\
                    .filter(UsuarioSucursal.sucursal_id == sucursal_id)\
                    .first()
                
                if not existe:
                    usuario_sucursal = UsuarioSucursal(
                        usuario_id=usuario_id,
                        sucursal_id=sucursal_id
                    )
                    session.add(usuario_sucursal)
                
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error al asignar sucursal {sucursal_id} a usuario {usuario_id}: {str(e)}")
            return False
