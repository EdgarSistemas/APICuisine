"""
Auth DAO - Acceso a datos de autenticación usando modelos declarativos
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy import and_, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.core.db.session_manager import get_db_session
from src.models.auth import Usuario, Rol, CodigoReset

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
    
    def obtener_usuario_por_email(self, email: str, plataforma: str) -> Optional[Dict[str, Any]]:
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
                roles = session.query(Rol).join(UsuarioRol, Rol.id_rol == UsuarioRol.rol_id).filter(UsuarioRol.usuario_id == usuario.id_usuario).all()
                
                # Obtener módulos del usuario mediante join manual
                # 1 pwa
                # 2 movil
                # 3 ambos
                # verificar de que plataforma viene la peticion y filtrar en la tabla RolModulo
                from src.models.auth import Modulo, RolModulo
                modulos = session.query(Modulo)\
                    .join(RolModulo, Modulo.id_modulo == RolModulo.modulo_id)\
                    .join(UsuarioRol, RolModulo.rol_id == UsuarioRol.rol_id)\
                    .filter(UsuarioRol.usuario_id == usuario.id_usuario)\
                    .filter(
                        or_(
                            and_(
                                plataforma == 'web',
                                or_(RolModulo.plataforma == 1, RolModulo.plataforma == 3)
                            ),
                            and_(
                                plataforma == 'movil',
                                or_(RolModulo.plataforma == 2, RolModulo.plataforma == 3)
                            )
                        )
                    )\
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
    
    def guardar_codigo_reset(self, usuario_id: int, codigo: str, expiracion=None) -> bool:
        """
        Guardar código de reset en la base de datos
        
        Args:
            usuario_id: ID del usuario
            codigo: Código de 6 dígitos
            expiracion: Datetime de expiración (opcional, se calcula automáticamente con timezone México)
            
        Returns:
            bool: True si se guardó correctamente
        """
        try:
            with get_db_session() as session:
                # Usar timezone de México pero guardar como naive
                tz_mexico = ZoneInfo("America/Mexico_City")
                ahora_mexico_aware = datetime.now(tz_mexico)
                ahora_mexico = ahora_mexico_aware.replace(tzinfo=None)
                
                # Si no se proporciona expiración, calcularla (15 minutos)
                if expiracion is None:
                    expiracion = ahora_mexico + timedelta(minutes=15)
                elif hasattr(expiracion, 'tzinfo') and expiracion.tzinfo is not None:
                    # Si viene con timezone, convertir a naive
                    expiracion = expiracion.replace(tzinfo=None)
                
                logger.info(f"Guardando código reset con expiracion: {expiracion} (hora México naive)")
                
                # Invalidar códigos anteriores del usuario
                session.query(CodigoReset)\
                    .filter(CodigoReset.usuario_id == usuario_id)\
                    .filter(CodigoReset.usado == False)\
                    .update({CodigoReset.usado: True})
                
                # Crear nuevo código
                nuevo_codigo = CodigoReset(
                    usuario_id=usuario_id,
                    codigo=codigo,
                    expiracion=expiracion,  # Naive datetime
                    usado=False
                )
                
                session.add(nuevo_codigo)
                session.commit()
                
                logger.info(f"Código de reset guardado para usuario {usuario_id} (hora México: {ahora_mexico})")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error al guardar código de reset: {str(e)}")
            return False
    
    def verificar_codigo_validacion(self, email: str, codigo: str) -> bool:
        """
        Verificar código de validación por email.
        Busca el usuario por email y verifica el código en codigo_reset.
        
        Args:
            email: Correo electrónico del usuario
            codigo: Código a verificar
            
        Returns:
            bool: True si el código es válido, False en caso contrario
        """
        try:
            with get_db_session() as session:
                # Buscar el usuario por email
                usuario = session.query(Usuario).filter(Usuario.email == email).first()
                
                if not usuario:
                    logger.warning(f"Usuario con email {email} no encontrado")
                    return False
                
                # Usar timezone de México - convertir a naive para comparar con BD
                tz_mexico = ZoneInfo("America/Mexico_City")
                ahora_mexico_aware = datetime.now(tz_mexico)
                ahora_mexico = ahora_mexico_aware.replace(tzinfo=None)  # Convertir a naive
                
                logger.info(f"Verificando código para usuario {usuario.id_usuario} - Hora actual México: {ahora_mexico}")
                
                # Buscar código válido
                codigo_obj = session.query(CodigoReset).filter(
                        CodigoReset.usuario_id == usuario.id_usuario,
                        CodigoReset.codigo == codigo,
                        CodigoReset.usado == False,
                        CodigoReset.expiracion > ahora_mexico
                    ).first()
                
                if codigo_obj:
                    minutos_restantes = (codigo_obj.expiracion - ahora_mexico).total_seconds() / 60
                    logger.info(f"✓ Código válido encontrado - Expira: {codigo_obj.expiracion} (quedan {minutos_restantes:.1f} min)")
                    return True
                
                # Si no es válido, buscar por qué
                codigo_cualquiera = session.query(CodigoReset).filter(
                        CodigoReset.usuario_id == usuario.id_usuario,
                        CodigoReset.codigo == codigo
                    ).first()
                
                if not codigo_cualquiera:
                    logger.warning(f"✗ Código '{codigo}' NO EXISTE en la BD para usuario {usuario.id_usuario}")
                elif codigo_cualquiera.usado:
                    logger.warning(f"✗ Código '{codigo}' YA FUE USADO")
                elif codigo_cualquiera.expiracion <= ahora_mexico:
                    logger.warning(f"✗ Código '{codigo}' EXPIRADO - Era válido hasta: {codigo_cualquiera.expiracion}, ahora son: {ahora_mexico}")
                else:
                    logger.warning(f"✗ Código '{codigo}' inválido por razón desconocida")
                
                return False
                    
        except SQLAlchemyError as e:
            logger.error(f"Error al verificar código de validación: {str(e)}")
            return False
    
    def verificar_codigo_reset(self, usuario_id: int, codigo: str) -> Dict[str, Any]:
        """
        Verificar si un código de reset es válido
        
        Args:
            usuario_id: ID del usuario
            codigo: Código de 6 dígitos
            
        Returns:
            Dict con 'valido' (bool) y 'mensaje' (str)
        """
        try:
            with get_db_session() as session:
                from datetime import datetime
                from zoneinfo import ZoneInfo
                
                # Convertir a naive para comparar con BD
                tz_mexico = ZoneInfo("America/Mexico_City")
                ahora_mexico_aware = datetime.now(tz_mexico)
                ahora_mexico = ahora_mexico_aware.replace(tzinfo=None)
                
                codigo_obj = session.query(CodigoReset).filter(
                    CodigoReset.usuario_id == usuario_id,
                    CodigoReset.codigo == codigo,
                    CodigoReset.usado == False,
                    CodigoReset.expiracion > ahora_mexico
                ).first()
                
                if codigo_obj:
                    logger.info(f"Código reset válido para usuario {usuario_id}")
                    return {'valido': True, 'mensaje': 'Código válido'}
                
                # Buscar si existe para dar mensaje más específico
                codigo_existente = session.query(CodigoReset).filter(
                    CodigoReset.usuario_id == usuario_id,
                    CodigoReset.codigo == codigo
                ).first()
                
                if codigo_existente:
                    if codigo_existente.usado:
                        mensaje = 'Código ya utilizado'
                        logger.warning(f"Código reset ya usado para usuario {usuario_id}")
                    else:
                        mensaje = 'Código expirado'
                        logger.warning(f"Código reset expirado para usuario {usuario_id}")
                else:
                    mensaje = 'Código inválido'
                    logger.warning(f"Código reset no encontrado para usuario {usuario_id}")
                
                return {'valido': False, 'mensaje': mensaje}
                
        except SQLAlchemyError as e:
            logger.error(f"Error al verificar código reset: {str(e)}")
            return {'valido': False, 'mensaje': 'Error interno'}
    
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

    def guardar_codigo_validacion(self, email: str, codigo: str, creado_en) -> bool:
        """
        Guardar código de validación de correo en codigo_reset.
        Busca el usuario por email y guarda en la misma tabla codigo_reset.

        Args:
            email: Correo electrónico
            codigo: Código de validación
            creado_en: No usado (se calcula automáticamente con timezone México)

        Returns:
            bool: True si se guardó correctamente
        """
        try:
            with get_db_session() as session:
                # Buscar el usuario por email
                usuario = session.query(Usuario).filter(Usuario.email == email).first()
                
                if not usuario:
                    logger.error(f"Usuario con email {email} no encontrado")
                    return False
                
                # Usar timezone de México pero guardar como naive en BD
                tz_mexico = ZoneInfo("America/Mexico_City")
                ahora_mexico_aware = datetime.now(tz_mexico)
                ahora_mexico = ahora_mexico_aware.replace(tzinfo=None)  # Convertir a naive
                expiracion = ahora_mexico + timedelta(minutes=10)
                
                logger.info(f"Guardando código con expiracion: {expiracion} (hora México naive)")
                
                # Invalidar códigos anteriores del usuario
                session.query(CodigoReset)\
                    .filter(CodigoReset.usuario_id == usuario.id_usuario)\
                    .filter(CodigoReset.usado == False)\
                    .update({CodigoReset.usado: True})
                
                # Crear nuevo código en codigo_reset
                nuevo_codigo = CodigoReset(
                    usuario_id=usuario.id_usuario,
                    codigo=codigo,
                    expiracion=expiracion,  # Naive datetime
                    usado=False
                )
                
                session.add(nuevo_codigo)
                session.commit()
                
                logger.info(f"Código de validación guardado en codigo_reset para usuario {usuario.id_usuario} (hora México: {ahora_mexico})")
                return True

        except SQLAlchemyError as e:
            logger.error(f"Error al guardar código de validación: {str(e)}")
            return False