"""
Auth DAO - Acceso a datos de autenticación usando modelos declarativos
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from src.core.db.session_manager import get_db_session
from src.models.auth import Usuario, Rol, CodigoReset, CodigoValidacion

logger = logging.getLogger(__name__)

class AuthDAO:
    """DAO para operaciones de autenticación usando modelos declarativos"""
    
    def autenticar_usuario(self, email: str, password_hash: str) -> Optional[Dict[str, Any]]:
        """
        Autenticar usuario por email y password hash
        
        Args:
            email: Email del usuario
            password_hash: Password hasheado del usuario
            
        Returns:
            Dict con datos del usuario autenticado o None si falla
        """
        try:
            with get_db_session() as session:
                usuario = session.query(Usuario)\
                    .options(joinedload(Usuario.roles))\
                    .filter(
                        Usuario.email == email,
                        Usuario.hash_password == password_hash,
                        Usuario.es_activo == True
                    ).first()
                
                if usuario:
                    return self._usuario_to_dict(usuario)
                return None
                
        except SQLAlchemyError as e:
            logger.error(f"Error al autenticar usuario {email}: {str(e)}")
            raise RuntimeError(f"Error en base de datos: {str(e)}")
    
    def obtener_usuario_por_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Obtener usuario por email para validación
        
        Args:
            email: Email del usuario
            
        Returns:
            Dict con datos del usuario o None si no existe
        """
        try:
            with get_db_session() as session:
                # Obtener usuario básico
                usuario = session.query(Usuario)\
                    .filter(Usuario.email == email)\
                    .first()
                
                if not usuario:
                    return None
                
                # Obtener roles del usuario mediante join manual
                from src.models.auth import Rol, UsuarioRol
                roles = session.query(Rol)\
                    .join(UsuarioRol, Rol.id_rol == UsuarioRol.rol_id)\
                    .filter(UsuarioRol.usuario_id == usuario.id_usuario)\
                    .all()
                
                # Obtener módulos del usuario mediante join manual  
                from src.models.auth import Modulo, RolModulo
                modulos = session.query(Modulo)\
                    .join(RolModulo, Modulo.id_modulo == RolModulo.modulo_id)\
                    .join(UsuarioRol, RolModulo.rol_id == UsuarioRol.rol_id)\
                    .filter(UsuarioRol.usuario_id == usuario.id_usuario)\
                    .filter(RolModulo.habilitado == True)\
                    .filter(Modulo.es_activo == True)\
                    .all()
                
                # Obtener sucursales asignadas al usuario
                from src.models.auth import UsuarioSucursal
                from src.models.catalogos.sucursal import Sucursal
                sucursales = session.query(Sucursal, UsuarioSucursal)\
                    .join(UsuarioSucursal, Sucursal.id_sucursal == UsuarioSucursal.sucursal_id)\
                    .filter(UsuarioSucursal.usuario_id == usuario.id_usuario)\
                    .filter(Sucursal.es_activa == True)\
                    .all()
                
                # Convertir a diccionario con datos completos
                user_dict = self._usuario_to_dict_completo(usuario, roles, modulos, sucursales, include_password=True)
                return user_dict
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener usuario por email {email}: {str(e)}")
            raise RuntimeError(f"Error en base de datos: {str(e)}")
    
    def _usuario_to_dict(self, usuario, include_password=False) -> Dict[str, Any]:
        """Convertir usuario a diccionario con nombres del esquema"""
        user_dict = {
            'id_usuario': usuario.id_usuario,
            'email': usuario.email,
            'nombre': usuario.nombre,
            'apellido': usuario.apellido,
            'telefono': usuario.telefono,
            'es_activo': usuario.es_activo,
            'es_cliente': usuario.es_cliente,
            'acepta_marketing': usuario.acepta_marketing,
            'tipo_acceso': usuario.tipo_acceso,
            'created_at': usuario.created_at.isoformat() if usuario.created_at else None,
            'updated_at': usuario.updated_at.isoformat() if usuario.updated_at else None,
            'roles': [{'id_rol': r.id_rol, 'nombre': r.nombre} for r in usuario.roles]
        }
        
        if include_password:
            user_dict['hash_password'] = usuario.hash_password
            
        return user_dict
    
    def _usuario_to_dict_completo(self, usuario, roles, modulos, sucursales=None, include_password=False) -> Dict[str, Any]:
        """Convertir usuario a diccionario con roles, módulos y sucursales completos"""
        user_dict = {
            'id_usuario': usuario.id_usuario,
            'email': usuario.email,
            'nombre': usuario.nombre,
            'apellido': usuario.apellido,
            'telefono': usuario.telefono,
            'es_activo': usuario.es_activo,
            'es_cliente': usuario.es_cliente,
            'acepta_marketing': usuario.acepta_marketing,
            'tipo_acceso': usuario.tipo_acceso,
            'created_at': usuario.created_at.isoformat() if usuario.created_at else None,
            'updated_at': usuario.updated_at.isoformat() if usuario.updated_at else None,
            'roles': [{'id_rol': r.id_rol, 'nombre': r.nombre, 'descripcion': r.descripcion} for r in roles],
            'modulos': [{'id_modulo': m.id_modulo, 'nombre': m.nombre, 'clave': m.clave, 'descripcion': m.descripcion} for m in modulos],
            'sucursales': []
        }
        
        # Agregar sucursales si se proporcionaron
        if sucursales:
            user_dict['sucursales'] = [
                {
                    'sucursal_id': sucursal.id_sucursal,
                    'codigo_sucursal': sucursal.codigo_sucursal,
                    'nombre': sucursal.nombre,
                    'telefono': sucursal.telefono,
                    'direccion': sucursal.direccion
                }
                for sucursal, usuario_sucursal in sucursales
            ]
        
        if include_password:
            user_dict['hash_password'] = usuario.hash_password
            
        return user_dict
    
    # === MÉTODOS PARA CÓDIGOS DE RESET ===
    
    def guardar_codigo_reset(self, usuario_id: int, codigo: str, expiracion) -> bool:
        """
        Guardar código de reset en la base de datos
        
        Args:
            usuario_id: ID del usuario
            codigo: Código de 6 dígitos
            expiracion: Datetime de expiración
            
        Returns:
            bool: True si se guardó correctamente
        """
        try:
            with get_db_session() as session:
                # Invalidar códigos anteriores del usuario
                session.query(CodigoReset)\
                    .filter(CodigoReset.usuario_id == usuario_id)\
                    .filter(CodigoReset.usado == False)\
                    .update({CodigoReset.usado: True})
                
                # Crear nuevo código
                nuevo_codigo = CodigoReset(
                    usuario_id=usuario_id,
                    codigo=codigo,
                    expiracion=expiracion,
                    usado=False
                )
                
                session.add(nuevo_codigo)
                session.commit()
                
                logger.info(f"Código de reset guardado para usuario {usuario_id}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error al guardar código de reset: {str(e)}")
            return False
    
    def verificar_codigo_reset(self, usuario_id: int, codigo: str) -> Dict[str, Any]:
        """
        Verificar código de reset
        
        Args:
            usuario_id: ID del usuario
            codigo: Código a verificar
            
        Returns:
            Dict con resultado de la verificación
        """
        try:
            with get_db_session() as session:
                from datetime import datetime
                
                ahora = datetime.utcnow()  # Usar UTC para consistencia con BD
                
                codigo_obj = session.query(CodigoReset)\
                    .filter(
                        CodigoReset.usuario_id == usuario_id,
                        CodigoReset.codigo == codigo,
                        CodigoReset.usado == False,
                        CodigoReset.expiracion > ahora
                    ).first()
                
                if codigo_obj:
                    logger.info(f"Código válido encontrado para usuario {usuario_id} - Expira: {codigo_obj.expiracion} UTC, Ahora: {ahora} UTC")
                    return {
                        'valido': True,
                        'mensaje': 'Código válido'
                    }
                else:
                    # Verificar si existe pero está expirado o usado
                    codigo_existente = session.query(CodigoReset)\
                        .filter(
                            CodigoReset.usuario_id == usuario_id,
                            CodigoReset.codigo == codigo
                        ).first()
                    
                    if codigo_existente:
                        if codigo_existente.usado:
                            mensaje = 'Código ya utilizado'
                            logger.warning(f"Código ya usado para usuario {usuario_id}")
                        else:
                            mensaje = f'Código expirado (exp: {codigo_existente.expiracion} UTC, ahora: {ahora} UTC)'
                            logger.warning(f"Código expirado para usuario {usuario_id}: {codigo_existente.expiracion} vs {ahora}")
                    else:
                        mensaje = 'Código inválido'
                        logger.warning(f"Código no encontrado para usuario {usuario_id}")
                    
                    return {
                        'valido': False,
                        'mensaje': mensaje
                    }
                
        except SQLAlchemyError as e:
            logger.error(f"Error al verificar código de reset: {str(e)}")
            return {
                'valido': False,
                'mensaje': 'Error interno'
            }
    
    def invalidar_codigo_reset(self, usuario_id: int) -> bool:
        """
        Invalidar todos los códigos de reset de un usuario
        
        Args:
            usuario_id: ID del usuario
            
        Returns:
            bool: True si se invalidaron correctamente
        """
        try:
            with get_db_session() as session:
                from datetime import datetime
                
                ahora = datetime.utcnow()  # Usar UTC para consistencia
                
                session.query(CodigoReset)\
                    .filter(CodigoReset.usuario_id == usuario_id)\
                    .filter(CodigoReset.usado == False)\
                    .update({
                        CodigoReset.usado: True,
                        CodigoReset.used_at: ahora
                    })
                
                session.commit()
                logger.info(f"Códigos de reset invalidados para usuario {usuario_id}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error al invalidar códigos de reset: {str(e)}")
            return False
    
    # === MÉTODOS PARA CÓDIGOS DE VALIDACIÓN ===
    
    def guardar_codigo_validacion(self, email: str, codigo: str, expiracion) -> bool:
        """
        Guardar código de validación de correo en la base de datos

        Args:
            email: Correo electrónico
            codigo: Código de validación
            expiracion: Fecha y hora de expiración

        Returns:
            bool: True si se guardó correctamente
        """
        try:
            with get_db_session() as session:
                # Invalidar códigos anteriores para el mismo correo
                session.query(CodigoValidacion)\
                    .filter(CodigoValidacion.email == email)\
                    .filter(CodigoValidacion.usado == False)\
                    .update({CodigoValidacion.usado: True})

                # Crear nuevo código
                nuevo_codigo = CodigoValidacion(
                    email=email,
                    codigo=codigo,
                    expiracion=expiracion,
                    usado=False
                )

                session.add(nuevo_codigo)
                session.commit()

                logger.info(f"Código de validación guardado para correo {email}")
                return True

        except SQLAlchemyError as e:
            logger.error(f"Error al guardar código de validación: {str(e)}")
            return False