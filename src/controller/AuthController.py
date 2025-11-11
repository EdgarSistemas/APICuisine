"""Endpoint de autenticación"""

import logging
from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from werkzeug.security import generate_password_hash

# Flask-JWT-Extended imports
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from src.services.auth.auth_service import AuthService
from src.core.auth.jwt_helpers import get_current_user, get_current_user_id, get_current_user_email
from src.schemas.auth_schema import (
    LoginSchema, TokenSchema, CambiarPasswordSchema, 
    ErrorSchema, SuccessSchema
)

logger = logging.getLogger(__name__)

# Blueprint para autenticaciÃ³n
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Instanciar esquemas
login_schema = LoginSchema()
token_schema = TokenSchema()
cambiar_password_schema = CambiarPasswordSchema()
error_schema = ErrorSchema()
success_schema = SuccessSchema()

# Instanciar servicio
auth_service = AuthService()


@auth_bp.route('/hash-password', methods=['POST'])
def hash_password():
    """
    Hashear password para desarrollo
    ---
    tags:
      - Autenticación
    parameters:
      - in: body
        name: password_data
        required: true
        schema:
          type: object
          properties:
            password:
              type: string
              example: "admin123"
    responses:
      200:
        description: Password hasheado exitosamente
      400:
        description: Password requerido
    """
    try:
        from werkzeug.security import generate_password_hash
        
        datos = request.get_json()
        if not datos or not datos.get('password'):
            return jsonify({
                'success': False,
                'error': 'MISSING_PASSWORD',
                'message': 'Se requiere el campo password'
            }), 400
        
        password = datos['password']
        hashed = generate_password_hash(password)
        
        return jsonify({
            'success': True,
            'original_password': password,
            'hashed_password': hashed,
            'message': 'Password hasheado exitosamente'
        }), 200
        
    except Exception as e:
        logger.error(f"Error al hashear password: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'HASH_ERROR',
            'message': f'Error al hashear password: {str(e)}'
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login de usuario
    ---
    tags:
      - Autenticación
    parameters:
      - in: body
        name: credentials
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              example: "admin@test.com"
            password:
              type: string
              example: "admin123"
            push_token:
              type: string
              description: "Token FCM del dispositivo (opcional)"
              example: "fcm_token_ejemplo_123456"
            plataforma:
              type: string
              description: "Plataforma del dispositivo (opcional)"
              enum: ["android", "web"]
              example: "android"
    responses:
      200:
        description: Login exitoso
      400:
        description: Credenciales inválidas
    """
    try:
        # Validar datos de entrada
        datos_login = login_schema.load(request.get_json())
        
        # Autenticar usuario
        usuario = auth_service.autenticar_usuario(
            datos_login['email'], 
            datos_login['password'],
            datos_login.get('push_token'),
            datos_login.get('plataforma')
        )
        
        if not usuario:
            return jsonify(error_schema.dump({
                'error': 'INVALID_CREDENTIALS',
                'message': 'Email o password incorrecto'
            })), 401
        
        # Generar token
        token = auth_service.generar_token(usuario)
        
        # Preparar respuesta
        respuesta = {
            'access_token': token,
            'token_type': 'Bearer',
            'expires_in': auth_service.token_expiration * 3600,
            'user': auth_service.preparar_respuesta_usuario(usuario)
        }
        
        logger.info(f"Login exitoso para usuario {datos_login['email']}")
        return jsonify(token_schema.dump(respuesta)), 200
        
    except ValidationError as e:
        logger.warning(f"Datos de login invÃ¡lidos: {e.messages}")
        return jsonify(error_schema.dump({
            'error': 'VALIDATION_ERROR',
            'message': 'Datos invÃ¡lidos',
            'details': e.messages
        })), 400
        
    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        return jsonify(error_schema.dump({
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        })), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required()
def refresh_token():
    """
    Renovar token JWT
    ---
    tags:
      - Autenticación
    security:
      - Bearer: []
    responses:
      200:
        description: Token renovado exitosamente
      401:
        description: Token inválido o expirado
    """
    try:
        # El usuario ya estÃ¡ validado por @jwt_required
        current_user = get_current_user()
        
        # Obtener token actual del header
        auth_header = request.headers.get('Authorization')
        token_actual = auth_header.split(' ')[1]
        
        # Renovar token usando el servicio
        nuevo_token = auth_service.renovar_token(token_actual)
        
        if not nuevo_token:
            return jsonify(error_schema.dump({
                'error': 'REFRESH_ERROR',
                'message': 'No se pudo renovar el token'
            })), 401
        
        # Preparar respuesta
        respuesta = {
            'access_token': nuevo_token,
            'token_type': 'Bearer',
            'expires_in': auth_service.token_expiration * 3600,
            'user_id': current_user['user_id'],
            'email': current_user['email']
        }
        
        logger.info(f"Token renovado para usuario {current_user['email']}")
        return jsonify(token_schema.dump(respuesta)), 200
        
    except Exception as e:
        logger.error(f"Error al renovar token: {str(e)}")
        return jsonify(error_schema.dump({
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        })), 500


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """
    Cambiar contraseña del usuario
    ---
    tags:
      - Autenticación
    security:
      - Bearer: []
    parameters:
      - in: body
        name: password_data
        required: true
        schema:
          type: object
          properties:
            current_password:
              type: string
              example: "currentPass123"
            new_password:
              type: string
              example: "newPass456"
    responses:
      200:
        description: Contraseña cambiada exitosamente
      400:
        description: Datos inválidos
      401:
        description: Contraseña actual incorrecta
    """
    try:
        # Validar datos de entrada
        datos = cambiar_password_schema.load(request.get_json())
        
        # Obtener usuario actual del token (ya validado por @jwt_required)
        current_user = get_current_user()
        usuario_id = current_user['user_id']
        
        # Cambiar password usando el servicio
        resultado = auth_service.cambiar_password(
            usuario_id,
            datos['password_actual'],
            datos['password_nuevo']
        )
        
        if not resultado['success']:
            # Determinar el cÃ³digo de estado basado en el error
            status_code = 400 if resultado['error'] == 'INVALID_PASSWORD' else 500
            return jsonify(error_schema.dump(resultado)), status_code
        
        logger.info(f"Password cambiado para usuario {current_user['email']} (ID: {usuario_id})")
        return jsonify(success_schema.dump(resultado)), 200
        
    except ValidationError as e:
        logger.warning(f"Datos invÃ¡lidos para cambio de password: {e.messages}")
        return jsonify(error_schema.dump({
            'error': 'VALIDATION_ERROR',
            'message': 'Datos invÃ¡lidos',
            'details': e.messages
        })), 400
        
    except Exception as e:
        logger.error(f"Error al cambiar password: {str(e)}")
        return jsonify(error_schema.dump({
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        })), 500


@auth_bp.route('/verify', methods=['GET'])
@jwt_required()
def verify_token():
    """
    Verificar token JWT
    ---
    tags:
      - Autenticación
    security:
      - Bearer: []
    responses:
      200:
        description: Token válido
      401:
        description: Token inválido
    """
    try:
        # El token ya estÃ¡ validado por el decorador @jwt_required
        current_user = get_current_user()
        
        # Retornar informaciÃ³n bÃ¡sica del usuario (desde el token, sin consultas adicionales)
        from datetime import datetime
        return jsonify({
            'valid': True,
            'user_id': current_user['user_id'],
            'email': current_user['email'],
            'nombre': current_user.get('nombre', ''),
            'roles': current_user.get('roles', []),
            'expires_at': current_user['exp'],
            'verified_at': datetime.utcnow().isoformat() + "Z"
        }), 200
        
    except Exception as e:
        logger.error(f"Error al verificar token: {str(e)}")
        return jsonify(error_schema.dump({
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        })), 500


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Obtener perfil del usuario
    ---
    tags:
      - Autenticación
    security:
      - Bearer: []
    responses:
      200:
        description: Datos del perfil
      401:
        description: No autorizado
    """
    try:
        # El usuario ya estÃ¡ validado por @jwt_required
        current_user = get_current_user()
        
        # Obtener perfil completo del usuario
        perfil = auth_service.obtener_perfil_usuario(current_user['user_id'])
        
        if not perfil:
            return jsonify({
                'error': 'USER_NOT_FOUND',
                'message': 'Usuario no encontrado'
            }), 404
        
        logger.info(f"Perfil consultado por usuario: {current_user['email']}")
        
        return jsonify({
            'success': True,
            'message': f'Perfil de {current_user["email"]}',
            'user': perfil,
            'authenticated_as': current_user['email'],
            'token_roles': current_user.get('roles', [])
        }), 200
        
    except Exception as e:
        logger.error(f"Error al obtener perfil: {str(e)}")
        return jsonify(error_schema.dump({
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        })), 500


@auth_bp.route('/cambiar-password', methods=['POST'])
@jwt_required()
def cambiar_password():
    """
    Cambiar contraseña (usuario autenticado)
    ---
    tags:
      - Autenticación
    security:
      - Bearer: []
    summary: Cambiar contraseña del usuario autenticado
    description: |
      Permite al usuario autenticado cambiar su contraseña proporcionando
      la contraseña actual y la nueva contraseña.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - password_actual
            - nueva_password
            - confirmar_password
          properties:
            password_actual:
              type: string
              example: "passwordActual123"
              description: Contraseña actual del usuario
            nueva_password:
              type: string
              minLength: 8
              example: "nuevaPassword123"
              description: Nueva contraseña (mínimo 8 caracteres, letras y números)
            confirmar_password:
              type: string
              example: "nuevaPassword123"
              description: Confirmación de la nueva contraseña
    responses:
      200:
        description: Contraseña cambiada exitosamente
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Contraseña actualizada exitosamente"
      400:
        description: Error de validación o contraseña actual incorrecta
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: "Contraseña actual incorrecta"
            error:
              type: string
              example: "CURRENT_PASSWORD_INCORRECT"
            errors:
              type: object
              description: Errores específicos de validación
      401:
        description: No autorizado
        schema:
          $ref: '#/definitions/ErrorResponse'
      500:
        description: Error interno del servidor
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    try:
        from src.schemas.password_reset_schema import CambiarPasswordSchema
        from src.dao.auth.usuario_dao import UsuarioDAO
        
        current_user = get_current_user()
        user_id = current_user['user_id']
        
        # Validar datos de entrada
        cambiar_password_schema = CambiarPasswordSchema()
        datos = cambiar_password_schema.load(request.json)
        
        # Usar DAO para cambiar contraseña
        usuario_dao = UsuarioDAO()
        resultado = usuario_dao.cambiar_password_con_actual(
            user_id=user_id,
            password_actual=datos['password_actual'],
            nueva_password=datos['nueva_password']
        )
        
        # Determinar código de estado
        if resultado['success']:
            status_code = 200
            logger.info(f"Contraseña cambiada por usuario {current_user['email']}")
        elif resultado.get('error') == 'CURRENT_PASSWORD_INCORRECT':
            status_code = 400
            logger.warning(f"Intento de cambio con contraseña incorrecta: {current_user['email']}")
        else:
            status_code = 500
            logger.error(f"Error al cambiar contraseña: {resultado}")
        
        return jsonify(resultado), status_code
        
    except ValidationError as e:
        logger.warning(f"Error de validación en cambiar_password: {e.messages}")
        return jsonify({
            'success': False,
            'message': 'Error de validación',
            'errors': e.messages
        }), 400
    except Exception as e:
        logger.error(f"Error no controlado en cambiar_password: {str(e)}")
        return jsonify(error_schema.dump({
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        })), 500


# === ENDPOINTS DE PASSWORD RESET ===

@auth_bp.route('/password-reset/solicitar', methods=['POST'])
def solicitar_password_reset():
    """
    Solicitar reset de contraseña (versión externa sin JWT)
    ---
    tags:
      - Autenticación
    parameters:
      - in: body
        name: reset_data
        required: true
        schema:
          type: object
          required:
            - email
          properties:
            email:
              type: string
              format: email
              example: "usuario@ejemplo.com"
              description: "Email del usuario"
    responses:
      200:
        description: Solicitud procesada exitosamente
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Código de verificación enviado a tu email"
            debug_info:
              type: object
              description: "Solo visible en modo debug"
      400:
        description: Error de validación
        schema:
          $ref: '#/definitions/Error'
      500:
        description: Error interno del servidor
        schema:
          $ref: '#/definitions/Error'
    """
    try:
        data = request.get_json()
        
        # Validación básica
        if not data or 'email' not in data:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': 'Email es requerido'
            }), 400
        
        email = data['email'].strip().lower()
        
        # Solicitar reset
        resultado = auth_service.solicitar_reset_password(email)
        
        if resultado['success']:
            logger.info(f"Solicitud de reset procesada para: {email}")
            status_code = 200
        else:
            logger.warning(f"Error en solicitud de reset para {email}: {resultado.get('error')}")
            status_code = 400
        
        return jsonify(resultado), status_code
        
    except Exception as e:
        logger.error(f"Error no controlado en solicitar_password_reset: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500


@auth_bp.route('/password-reset/verificar', methods=['POST'])
def verificar_codigo_reset():
    """
    Verificar código de reset de contraseña
    ---
    tags:
      - Autenticación
    parameters:
      - in: body
        name: verify_data
        required: true
        schema:
          type: object
          required:
            - email
            - codigo
          properties:
            email:
              type: string
              format: email
              example: "usuario@ejemplo.com"
            codigo:
              type: string
              example: "123456"
              description: "Código de 6 dígitos recibido por email"
    responses:
      200:
        description: Código verificado correctamente
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Código verificado correctamente"
      400:
        description: Código inválido o expirado
        schema:
          $ref: '#/definitions/Error'
      500:
        description: Error interno del servidor
        schema:
          $ref: '#/definitions/Error'
    """
    try:
        data = request.get_json()
        
        # Validación básica
        if not data or 'email' not in data or 'codigo' not in data:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': 'Email y código son requeridos'
            }), 400
        
        email = data['email'].strip().lower()
        codigo = data['codigo'].strip()
        
        # Verificar código
        resultado = auth_service.verificar_codigo_reset(email, codigo)
        
        if resultado['success']:
            logger.info(f"Código verificado para: {email}")
            status_code = 200
        else:
            logger.warning(f"Error en verificación de código para {email}: {resultado.get('error')}")
            status_code = 400
        
        return jsonify(resultado), status_code
        
    except Exception as e:
        logger.error(f"Error no controlado en verificar_codigo_reset: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500


@auth_bp.route('/password-reset/restablecer', methods=['POST'])
def restablecer_password():
    """
    Restablecer contraseña con código de verificación (versión externa)
    ---
    tags:
      - Autenticación
    parameters:
      - in: body
        name: reset_data
        required: true
        schema:
          type: object
          required:
            - email
            - codigo
            - nueva_password
          properties:
            email:
              type: string
              format: email
              example: "usuario@ejemplo.com"
            codigo:
              type: string
              example: "123456"
              description: "Código de verificación"
            nueva_password:
              type: string
              example: "NuevaPassword123!"
              description: "Nueva contraseña"
    responses:
      200:
        description: Contraseña restablecida exitosamente
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Contraseña restablecida exitosamente"
      400:
        description: Error en validación o código inválido
        schema:
          $ref: '#/definitions/Error'
      500:
        description: Error interno del servidor
        schema:
          $ref: '#/definitions/Error'
    """
    try:
        data = request.get_json()
        
        # Validación básica
        required_fields = ['email', 'codigo', 'nueva_password']
        for field in required_fields:
            if not data or field not in data:
                return jsonify({
                    'success': False,
                    'error': 'VALIDATION_ERROR',
                    'message': f'{field} es requerido'
                }), 400
        
        email = data['email'].strip().lower()
        codigo = data['codigo'].strip()
        nueva_password = data['nueva_password']
        
        # Validación de password
        if len(nueva_password) < 6:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': 'La contraseña debe tener al menos 6 caracteres'
            }), 400
        
        # Restablecer password
        resultado = auth_service.restablecer_password(email, codigo, nueva_password)
        
        if resultado['success']:
            logger.info(f"Password restablecida para: {email}")
            status_code = 200
        else:
            logger.warning(f"Error al restablecer password para {email}: {resultado.get('error')}")
            status_code = 400
        
        return jsonify(resultado), status_code
        
    except Exception as e:
        logger.error(f"Error no controlado en restablecer_password: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500


@auth_bp.route('/password-reset/solicitar-admin', methods=['POST'])
@jwt_required()
def solicitar_password_reset_admin():
    """
    Solicitar reset de contraseña desde panel admin (versión interna con JWT)
    ---
    tags:
      - Autenticación
    security:
      - Bearer: []
    parameters:
      - in: body
        name: admin_reset_data
        required: true
        schema:
          type: object
          required:
            - email_usuario
          properties:
            email_usuario:
              type: string
              format: email
              example: "usuario@ejemplo.com"
              description: "Email del usuario al que se le reseteará la contraseña"
    responses:
      200:
        description: Solicitud procesada exitosamente
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Código de reset enviado a usuario@ejemplo.com"
      400:
        description: Error de validación o permisos
        schema:
          $ref: '#/definitions/Error'
      401:
        description: Token JWT inválido
        schema:
          $ref: '#/definitions/Error'
      500:
        description: Error interno del servidor
        schema:
          $ref: '#/definitions/Error'
    """
    try:
        data = request.get_json()
        
        # Validación básica
        if not data or 'email_usuario' not in data:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': 'email_usuario es requerido'
            }), 400
        
        # Obtener ID del administrador actual
        current_user_id = get_current_user_id()
        
        email_usuario = data['email_usuario'].strip().lower()
        
        # Solicitar reset como admin
        resultado = auth_service.solicitar_reset_password_interno(current_user_id, email_usuario)
        
        if resultado['success']:
            logger.info(f"Reset admin solicitado por usuario {current_user_id} para {email_usuario}")
            status_code = 200
        else:
            if resultado.get('error') == 'PERMISSION_DENIED':
                status_code = 403
            else:
                status_code = 400
            logger.warning(f"Error en reset admin: {resultado.get('error')}")
        
        return jsonify(resultado), status_code
        
    except Exception as e:
        logger.error(f"Error no controlado en solicitar_password_reset_admin: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500


# === ENDPOINTS DE VALIDACIÓN DE CORREO ===

@auth_bp.route('/email-validation/solicitar', methods=['POST'])
def solicitar_validacion_correo():
    """
    Solicitar validación de correo electrónico para empleados
    ---
    tags:
      - Autenticación
    parameters:
      - in: body
        name: email_data
        required: true
        schema:
          type: object
          required:
            - email
          properties:
            email:
              type: string
              format: email
              example: "empleado@ejemplo.com"
              description: "Correo electrónico del empleado"
    responses:
      200:
        description: Código de validación enviado exitosamente
      400:
        description: Error de validación
      500:
        description: Error interno del servidor
    """
    try:
        data = request.get_json()

        # Validación básica
        if not data or 'email' not in data:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': 'Email es requerido'
            }), 400

        email = data['email'].strip().lower()

        # Solicitar validación
        resultado = auth_service.solicitar_validacion_correo(email)

        if resultado['success']:
            logger.info(f"Solicitud de validación procesada para: {email}")
            status_code = 200
        else:
            logger.warning(f"Error en solicitud de validación para {email}: {resultado.get('error')}")
            status_code = 400

        return jsonify(resultado), status_code

    except Exception as e:
        logger.error(f"Error no controlado en solicitar_validacion_correo: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500


@auth_bp.route('/email-validation/verificar', methods=['POST'])
def verificar_codigo_validacion():
    """
    Verificar código de validación de correo electrónico
    ---
    tags:
      - Autenticación
    parameters:
      - in: body
        name: verify_data
        required: true
        schema:
          type: object
          required:
            - email
            - codigo
          properties:
            email:
              type: string
              format: email
              example: "empleado@ejemplo.com"
            codigo:
              type: string
              example: "123456"
              description: "Código de validación recibido por email"
    responses:
      200:
        description: Código verificado correctamente
      400:
        description: Código inválido o expirado
      500:
        description: Error interno del servidor
    """
    try:
        data = request.get_json()

        # Validación básica
        if not data or 'email' not in data or 'codigo' not in data:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': 'Email y código son requeridos'
            }), 400

        email = data['email'].strip().lower()
        codigo = data['codigo'].strip()

        # Verificar código
        resultado = auth_service.verificar_codigo_validacion(email, codigo)

        if resultado['success']:
            logger.info(f"Código verificado para: {email}")
            status_code = 200
        else:
            logger.warning(f"Error en verificación de código para {email}: {resultado.get('error')}")
            status_code = 400

        return jsonify(resultado), status_code

    except Exception as e:
        logger.error(f"Error no controlado en verificar_codigo_validacion: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500

