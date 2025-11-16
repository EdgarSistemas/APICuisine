"""
Servicio de autenticación principal usando Flask-JWT-Extended
"""

import logging
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, decode_token
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

from src.core.config import get_config
from src.dao.auth.usuario_dao import UsuarioDAO
from src.dao.auth.auth_dao import AuthDAO
from src.dao.auth.push_token_dao import PushTokenDAO
from src.services.email.email_service import EmailService
from src.services.auditoria.log_service import log_action

logger = logging.getLogger(__name__)

class AuthService:
    """Servicio principal de autenticación usando Flask-JWT-Extended"""
    
    def __init__(self):
        self.usuario_dao = UsuarioDAO()
        self.auth_dao = AuthDAO()
        self.push_token_dao = PushTokenDAO()
        self.email_service = EmailService()
        config = get_config()
        self.secret_key = config.SECRET_KEY
        self.token_expiration = getattr(config, 'JWT_EXPIRATION_HOURS', 1)  # 1 hora por defecto
    
    def registrar_usuario(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Registrar nuevo usuario con validaciones
        
        Args:
            datos: Datos del usuario incluyendo hash_password, email, etc.
            
        Returns:
            Dict con datos del usuario registrado (sin password)
        """
        try:
            # Validar email único
            if self.usuario_dao.obtener_por_email(datos['email']):
                raise ValueError("El email ya está registrado")
            
            # Hashear password
            if 'password' in datos:
                datos['hash_password'] = generate_password_hash(datos['password'])
                del datos['password']  # Remover password en texto plano
            
            # Crear usuario
            usuario = self.usuario_dao.crear_usuario(datos)
            
            # Log de la creación de usuario
            log_action('Usuario', 'CREATE', 
                      entidad_id=str(usuario['id_usuario']),
                      detalle={'email': usuario['email'], 'nombre': usuario['nombre']})
            
            # Remover datos sensibles antes de retornar
            if 'hash_password' in usuario:
                del usuario['hash_password']
            
            logger.info(f"Usuario {usuario['email']} registrado exitosamente")
            return usuario
            
        except Exception as e:
            logger.error(f"Error al registrar usuario: {str(e)}")
            raise
    
    def autenticar_usuario(self, email: str, password: str, push_token: Optional[str] = None, plataforma: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Autenticar usuario con email y password, opcionalmente guardar push token FCM
        
        Args:
            email: Email del usuario
            password: Password en texto plano
            push_token: Token FCM del dispositivo (opcional)
            plataforma: Plataforma del dispositivo ('android', 'web') (opcional)
            
        Returns:
            Dict con datos del usuario si la autenticación es exitosa, None en caso contrario
        """
        try:
            # Obtener usuario por email con password
            usuario = self.auth_dao.obtener_usuario_por_email(email, plataforma)
            
            if not usuario:
                logger.warning(f"Usuario no encontrado: {email}")
                return None
            
            # Verificar que el usuario esté activo
            if not usuario.get('es_activo', False):
                logger.warning(f"Usuario inactivo: {email}")
                return None
            
            # Verificar password
            if self._verificar_password(usuario, password):
                # Procesar push token si se proporciona
                if push_token and plataforma:
                    try:
                        # Verificar si el token ya existe para determinar si es nuevo dispositivo o reasignación
                        token_existente = self.push_token_dao.obtener_token_por_token(push_token)
                        
                        if token_existente:
                            if token_existente['usuario_id'] != usuario['id_usuario']:
                                logger.info(f"Reasignando token de dispositivo del usuario {token_existente['usuario_id']} al usuario {usuario['id_usuario']}")
                            else:
                                logger.info(f"Confirmando token existente para usuario {usuario['id_usuario']}")
                        else:
                            logger.info(f"Registrando nuevo token de dispositivo para usuario {usuario['id_usuario']}")
                        
                        # Crear o reasignar token al usuario actual
                        self.push_token_dao.crear_o_actualizar_token(
                            usuario_id=usuario['id_usuario'],
                            token=push_token,
                            plataforma=plataforma
                        )
                        logger.info(f"Push token procesado para usuario {email}, plataforma {plataforma}")
                    except Exception as token_error:
                        # No fallar la autenticación por errores de token
                        logger.warning(f"Error al procesar push token para {email}: {str(token_error)}")
                
                # Remover password antes de retornar
                if 'hash_password' in usuario:
                    del usuario['hash_password']
                
                # Log de login exitoso
                log_action('Usuario', 'LOGIN', 
                          entidad_id=str(usuario['id_usuario']),
                          usuario_id=usuario['id_usuario'],
                          detalle={'email': email, 'push_token_provided': bool(push_token)})
                
                logger.info(f"Usuario {email} autenticado exitosamente")
                return usuario
            else:
                # Log de intento de login fallido
                log_action('Usuario', 'LOGIN_FAILED', 
                          detalle={'email': email, 'motivo': 'password_incorrecto'})
                
                logger.warning(f"Password incorrecto para: {email}")
                return None
            
        except Exception as e:
            logger.error(f"Error al autenticar usuario {email}: {str(e)}")
            return None
    
    def generar_token(self, usuario: Dict[str, Any]) -> str:
        """
        Generar JWT token para usuario autenticado usando Flask-JWT-Extended
        
        Args:
            usuario: Datos del usuario
            
        Returns:
            JWT token string
        """
        try:
            # Verificar si es admin
            es_admin = self._es_administrador(usuario)
            roles = usuario.get('roles', [])
            
            # Preparar claims adicionales para el token
            additional_claims = {
                'email': usuario['email'],
                'nombre': usuario.get('nombre', ''),
                'apellido': usuario.get('apellido', ''),
                'es_cliente': usuario.get('es_cliente', False),
                'acepta_marketing': usuario.get('acepta_marketing', False),
                'tipo_acceso': usuario.get('tipo_acceso', ''),
                'es_admin': es_admin,
                'mostrar_empresas': es_admin,
                'roles': [rol['nombre'] for rol in roles],
                'modulos': [modulo['clave'] for modulo in usuario.get('modulos', [])]
            }
            
            # El identity es el ID del usuario
            token = create_access_token(
                identity=str(usuario['id_usuario']),
                expires_delta=timedelta(hours=24),
                additional_claims=additional_claims
            )
            
            return token
            
        except Exception as e:
            logger.error(f"Error al generar token: {str(e)}")
            raise
    
    def verificar_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verificar y decodificar JWT token usando Flask-JWT-Extended
        
        Args:
            token: JWT token string
            
        Returns:
            Payload decodificado si el token es válido, None en caso contrario
        """
        try:
            # Decodificar token usando Flask-JWT-Extended
            payload = decode_token(token)
            
            # Restructurar payload para mantener compatibilidad
            user_data = {
                'user_id': payload['sub'],  # 'sub' es el identity (user ID)
                'email': payload.get('email', ''),
                'nombre': payload.get('nombre', ''),
                'apellido': payload.get('apellido', ''),
                'roles': payload.get('roles', []),
                'modulos': payload.get('modulos', []),
                'exp': payload['exp'],
                'iat': payload['iat']
            }
            
            return user_data
            
        except ExpiredSignatureError:
            logger.warning("Token expirado")
            return None
        except InvalidTokenError:
            logger.warning("Token inválido")
            return None
        except Exception as e:
            logger.error(f"Error al verificar token: {str(e)}")
            return None
    
    def obtener_perfil_usuario(self, usuario_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtener perfil completo del usuario
        
        Args:
            usuario_id: ID del usuario
            
        Returns:
            Datos completos del perfil del usuario
        """
        try:
            usuario = self.usuario_dao.obtener_por_id(usuario_id)
            if not usuario:
                return None
            
            # Agregar módulos accesibles
            usuario['modulos'] = self.usuario_dao.obtener_modulos_usuario(usuario_id)
            
            return usuario
            
        except Exception as e:
            logger.error(f"Error al obtener perfil del usuario {usuario_id}: {str(e)}")
            return None
    
    def cambiar_password(self, usuario_id: int, password_actual: str, password_nuevo: str) -> Dict[str, Any]:
        """
        Cambiar password del usuario
        
        Args:
            usuario_id: ID del usuario
            password_actual: Password actual para verificación
            password_nuevo: Nuevo password
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Obtener usuario
            usuario = self.usuario_dao.obtener_por_id(usuario_id)
            if not usuario:
                return {
                    'success': False,
                    'error': 'USER_NOT_FOUND',
                    'message': 'Usuario no encontrado'
                }
            
            # Verificar password actual
            if not self._verificar_password(usuario, password_actual):
                return {
                    'success': False,
                    'error': 'INVALID_PASSWORD',
                    'message': 'Password actual incorrecto'
                }
            
            # Hashear nuevo password
            nuevo_password_hash = generate_password_hash(password_nuevo)
            
            # Actualizar password en la base de datos
            resultado = self.usuario_dao.actualizar_password(usuario_id, nuevo_password_hash)
            
            if resultado:
                logger.info(f"Password actualizado para usuario {usuario_id}")
                return {
                    'success': True,
                    'message': 'Password cambiado exitosamente'
                }
            else:
                return {
                    'success': False,
                    'error': 'UPDATE_ERROR',
                    'message': 'Error al actualizar password'
                }
                
        except Exception as e:
            logger.error(f"Error al cambiar password del usuario {usuario_id}: {str(e)}")
            return {
                'success': False,
                'error': 'INTERNAL_ERROR',
                'message': 'Error interno del servidor'
            }
    
    def renovar_token(self, token_actual: str) -> Optional[str]:
        """
        Renovar token JWT válido usando Flask-JWT-Extended
        
        Args:
            token_actual: Token JWT actual
            
        Returns:
            Nuevo token JWT si el actual es válido, None en caso contrario
        """
        try:
            # Verificar que el token actual sea válido
            payload = self.verificar_token(token_actual)
            if not payload:
                return None
            
            # Obtener usuario actualizado
            usuario_id = payload.get('user_id')
            usuario = self.usuario_dao.obtener_por_id(usuario_id)
            
            if not usuario or not usuario.get('es_activo', False):
                logger.warning(f"Usuario {usuario_id} no existe o está inactivo")
                return None
            
            # Generar nuevo token con Flask-JWT-Extended
            nuevo_token = self.generar_token(usuario)
            logger.info(f"Token renovado para usuario {usuario_id}")
            
            return nuevo_token
            
        except Exception as e:
            logger.error(f"Error al renovar token: {str(e)}")
            return None
    
    def logout_usuario(self, usuario_id: int) -> Dict[str, Any]:
        """
        Procesar logout del usuario
        Los push tokens se mantienen activos para notificaciones en segundo plano
        
        Args:
            usuario_id: ID del usuario
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Los push tokens NO se desactivan en logout para permitir 
            # notificaciones en segundo plano. Solo se reasignan cuando 
            # otro usuario hace login en el mismo dispositivo.
            
            # Aquí podrías agregar lógica adicional de logout como:
            # - Blacklist del JWT token
            # - Logging de la sesión cerrada
            # - Etc.
            
            logger.info(f"Logout procesado para usuario {usuario_id} (push tokens mantenidos activos)")
            return {
                'success': True,
                'message': 'Logout exitoso'
            }
            
        except Exception as e:
            logger.error(f"Error en logout para usuario {usuario_id}: {str(e)}")
            return {
                'success': False,
                'error': 'LOGOUT_ERROR',
                'message': 'Error al procesar logout'
            }
    
    # === MÉTODOS DE PASSWORD RESET ===
    
    def solicitar_reset_password(self, email: str) -> Dict[str, Any]:
        """
        Solicitar reset de contraseña (versión externa - sin JWT)
        
        Args:
            email: Email del usuario
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Verificar que el usuario existe
            usuario = self.usuario_dao.obtener_por_email(email)
            if not usuario:
                # Por seguridad, no revelamos si el email existe o no
                return {
                    'success': True,
                    'message': 'Si el email existe, recibirás instrucciones para restablecer tu contraseña'
                }
            
            # Verificar que el usuario esté activo
            if not usuario.get('es_activo', False):
                return {
                    'success': False,
                    'error': 'USER_INACTIVE',
                    'message': 'Usuario inactivo'
                }
            
            # Generar código de verificación
            codigo = self.email_service.generar_codigo()
            
            # Guardar código en BD con expiración de 2 minutos (para debug) - usando UTC
            expiracion = datetime.utcnow() + timedelta(minutes=2)
            resultado_bd = self.auth_dao.guardar_codigo_reset(
                usuario_id=usuario['id_usuario'],
                codigo=codigo,
                expiracion=expiracion
            )
            
            if not resultado_bd:
                return {
                    'success': False,
                    'error': 'DB_ERROR',
                    'message': 'Error al guardar código de verificación'
                }
            
            # Enviar email con código
            resultado_email = self.email_service.enviar_codigo_reset(
                email=email,
                codigo=codigo,
                nombre=usuario.get('nombre', '')
            )
            
            if resultado_email['success']:
                logger.info(f"Código de reset enviado para usuario {email}")
                return {
                    'success': True,
                    'message': 'Código de verificación enviado a tu email',
                    'debug_info': resultado_email if resultado_email.get('debug') else None
                }
            else:
                return {
                    'success': False,
                    'error': 'EMAIL_ERROR',
                    'message': 'Error al enviar email de verificación'
                }
                
        except Exception as e:
            logger.error(f"Error en solicitar_reset_password para {email}: {str(e)}")
            return {
                'success': False,
                'error': 'INTERNAL_ERROR',
                'message': 'Error interno del servidor'
            }
    
    def verificar_codigo_reset(self, email: str, codigo: str) -> Dict[str, Any]:
        """
        Verificar código de reset de contraseña
        
        Args:
            email: Email del usuario
            codigo: Código de 6 dígitos
            
        Returns:
            Dict con resultado de la verificación
        """
        try:
            # Obtener usuario
            usuario = self.usuario_dao.obtener_por_email(email)
            if not usuario:
                return {
                    'success': False,
                    'error': 'USER_NOT_FOUND',
                    'message': 'Usuario no encontrado'
                }
            
            # Verificar código
            resultado = self.auth_dao.verificar_codigo_reset(
                usuario_id=usuario['id_usuario'],
                codigo=codigo
            )
            
            if resultado['valido']:
                logger.info(f"Código de reset verificado para usuario {email}")
                return {
                    'success': True,
                    'message': 'Código verificado correctamente',
                    'usuario_id': usuario['id_usuario']
                }
            else:
                return {
                    'success': False,
                    'error': 'INVALID_CODE',
                    'message': resultado.get('mensaje', 'Código inválido o expirado')
                }
                
        except Exception as e:
            logger.error(f"Error en verificar_codigo_reset para {email}: {str(e)}")
            return {
                'success': False,
                'error': 'INTERNAL_ERROR',
                'message': 'Error interno del servidor'
            }
    
    def restablecer_password(self, email: str, codigo: str, nueva_password: str) -> Dict[str, Any]:
        """
        Restablecer contraseña con código de verificación (versión externa)
        
        Args:
            email: Email del usuario
            codigo: Código de verificación
            nueva_password: Nueva contraseña
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Verificar código primero
            verificacion = self.verificar_codigo_reset(email, codigo)
            if not verificacion['success']:
                return verificacion
            
            # Hashear nueva password
            nuevo_password_hash = generate_password_hash(nueva_password)
            
            # Actualizar password en BD
            resultado = self.usuario_dao.actualizar_password(
                verificacion['usuario_id'],
                nuevo_password_hash
            )
            
            if resultado:
                # Invalidar código usado
                self.auth_dao.invalidar_codigo_reset(verificacion['usuario_id'])
                
                logger.info(f"Password restablecida para usuario {email}")
                return {
                    'success': True,
                    'message': 'Contraseña restablecida exitosamente'
                }
            else:
                return {
                    'success': False,
                    'error': 'UPDATE_ERROR',
                    'message': 'Error al actualizar contraseña'
                }
                
        except Exception as e:
            logger.error(f"Error en restablecer_password para {email}: {str(e)}")
            return {
                'success': False,
                'error': 'INTERNAL_ERROR',
                'message': 'Error interno del servidor'
            }
    
    def solicitar_reset_password_interno(self, usuario_admin_id: int, email_usuario: str) -> Dict[str, Any]:
        """
        Solicitar reset de contraseña desde panel admin (versión interna - con JWT)
        
        Args:
            usuario_admin_id: ID del administrador que solicita el reset
            email_usuario: Email del usuario al que se le reseteará la password
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Verificar que el admin existe y es realmente admin
            admin = self.usuario_dao.obtener_por_id(usuario_admin_id)
            if not admin or not self._es_administrador(admin):
                return {
                    'success': False,
                    'error': 'PERMISSION_DENIED',
                    'message': 'Sin permisos de administrador'
                }
            
            # Verificar que el usuario objetivo existe
            usuario = self.usuario_dao.obtener_por_email(email_usuario)
            if not usuario:
                return {
                    'success': False,
                    'error': 'USER_NOT_FOUND',
                    'message': 'Usuario no encontrado'
                }
            
            # Generar código
            codigo = self.email_service.generar_codigo()
            
            # Guardar código con expiración de 2 minutos (para debug) - usando UTC
            expiracion = datetime.utcnow() + timedelta(minutes=2)
            resultado_bd = self.auth_dao.guardar_codigo_reset(
                usuario_id=usuario['id_usuario'],
                codigo=codigo,
                expiracion=expiracion
            )
            
            if not resultado_bd:
                return {
                    'success': False,
                    'error': 'DB_ERROR',
                    'message': 'Error al guardar código'
                }
            
            # Enviar email
            resultado_email = self.email_service.enviar_codigo_reset(
                email=email_usuario,
                codigo=codigo,
                nombre=usuario.get('nombre', '')
            )
            
            if resultado_email['success']:
                logger.info(f"Reset interno solicitado por admin {usuario_admin_id} para usuario {email_usuario}")
                return {
                    'success': True,
                    'message': f'Código de reset enviado a {email_usuario}',
                    'debug_info': resultado_email if resultado_email.get('debug') else None
                }
            else:
                return {
                    'success': False,
                    'error': 'EMAIL_ERROR',
                    'message': 'Error al enviar email'
                }
                
        except Exception as e:
            logger.error(f"Error en solicitar_reset_password_interno: {str(e)}")
            return {
                'success': False,
                'error': 'INTERNAL_ERROR',
                'message': 'Error interno del servidor'
            }

    def solicitar_validacion_correo(self, email: str) -> Dict[str, Any]:
        """
        Solicitar validación de correo electrónico enviando un código al email

        Args:
            email: Correo electrónico del usuario

        Returns:
            Dict con el resultado de la operación
        """
        try:
            # Verificar si el correo ya está registrado
            if not self.usuario_dao.obtener_por_email(email):
                return {
                    'success': False,
                    'error': 'EMAIL_REGISTERED',
                    'message': 'El correo no está registrado'
                }

            # Generar código de validación
            codigo = self.email_service.generar_codigo()

            # Guardar código en la base de datos (el DAO maneja la timezone)
            resultado_bd = self.auth_dao.guardar_codigo_validacion(email, codigo, None)

            if not resultado_bd:
                return {
                    'success': False,
                    'error': 'DB_ERROR',
                    'message': 'Error al guardar el código de validación'
                }

            # Enviar email con el código
            enviado = self.email_service._enviar_email(
                to_email=email,
                subject="Validación de correo electrónico",
                body=f"""
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #2c3e50;">Validación de correo electrónico</h2>
                        <p>Tu código de validación es:</p>
                        <div style="text-align: center; margin: 30px 0;">
                            <span style="font-size: 32px; font-weight: bold; color: #e74c3c; letter-spacing: 5px;">
                                {codigo}
                            </span>
                        </div>
                        <p><strong>Este código expira en 10 minutos.</strong></p>
                    </div>
                </body>
                </html>
                """
            )

            if enviado.get('success'):
                logger.info(f"Código de validación enviado a {email}")
                return {
                    'success': True,
                    'message': 'Código de validación enviado a tu correo electrónico'
                }
            else:
                return {
                    'success': False,
                    'error': 'EMAIL_ERROR',
                    'message': 'No se pudo enviar el código de validación'
                }

        except Exception as e:
            logger.error(f"Error al solicitar validación de correo para {email}: {str(e)}")
            return {
                'success': False,
                'error': 'INTERNAL_ERROR',
                'message': f'Error interno al procesar la solicitud {e}'
            }

    def verificar_codigo_validacion(self, email: str, codigo: str) -> Dict[str, Any]:
        """
        Verificar el código de validación enviado al correo electrónico
        Args:
            email: Correo electrónico del empleado
            codigo: Código de validación recibido
        Returns:
            Resultado de la verificación
        """
        try:
            valido = self.auth_dao.verificar_codigo_validacion(email, codigo)

            if valido:
                logger.info(f"Código de validación correcto para {email}")
                return {
                    'success': True,
                    'message': 'Código de validación verificado correctamente'
                }
            else:
                logger.warning(f"Código de validación incorrecto para {email}")
                return {
                    'success': False,
                    'error': 'INVALID_CODE',
                    'message': 'El código de validación es incorrecto o ha expirado'
                }

        except Exception as e:
            logger.error(f"Error al verificar código de validación para {email}: {str(e)}")
            return {
                'success': False,
                'error': 'INTERNAL_ERROR',
                'message': 'Error interno al procesar la verificación'
            }
    
    def _verificar_password(self, usuario: Dict[str, Any], password: str) -> bool:
        """
        Verificar password del usuario
        
        Args:
            usuario: Datos del usuario
            password: Password en texto plano
            
        Returns:
            True si el password es correcto, False en caso contrario
        """
        try:
            password_hash = usuario.get('hash_password', '')
            
            if password_hash:
                return check_password_hash(password_hash, password)
            else:
                # Fallback temporal para pruebas
                return password in ['test123', 'admin', '123456']
            
        except Exception as e:
            logger.error(f"Error al verificar password: {str(e)}")
            return False
    
    def _es_administrador(self, usuario: Dict[str, Any]) -> bool:
        """
        Determinar si un usuario es administrador basado en rol_id = 1
        
        Args:
            usuario: Datos del usuario con roles
            
        Returns:
            True si es administrador, False si no
        """
        roles = usuario.get('roles', [])
        return any(rol.get('id_rol') == 1 for rol in roles)
    
    def preparar_respuesta_usuario(self, usuario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preparar respuesta completa del usuario para el endpoint de login
        
        Args:
            usuario: Datos del usuario
            
        Returns:
            Dict con datos del usuario para la respuesta
        """
        es_admin = self._es_administrador(usuario)
        
        # Obtener sucursales según el tipo de usuario
        sucursales = None
        if es_admin:
            # Admin ve todas las sucursales activas
            from src.dao.catalogos.sucursal_dao import SucursalDAO
            sucursal_dao = SucursalDAO()
            sucursales = sucursal_dao.obtener_activas()
        elif not usuario.get('es_cliente', False):
            # Empleado ve solo sus sucursales asignadas
            sucursales_asignadas = usuario.get('sucursales', [])
            if sucursales_asignadas:
                # Ya tenemos las sucursales con todos los datos desde el DAO
                sucursales = sucursales_asignadas
        # Cliente: sucursales = None (por defecto)
        
        return {
            'id': usuario['id_usuario'],
            'email': usuario['email'],
            'nombre': usuario['nombre'],
            'apellido': usuario['apellido'],
            'telefono': usuario.get('telefono', ''),
            'es_admin': es_admin,
            'es_cliente': usuario.get('es_cliente', False),
            'acepta_marketing': usuario.get('acepta_marketing', False),
            'tipo_acceso': usuario.get('tipo_acceso', ''),
            'mostrar_empresas': es_admin,
            'roles': usuario.get('roles', []),
            'modulos': usuario.get('modulos', []),
            'sucursales': sucursales
        }