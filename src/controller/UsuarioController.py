"""Endpoint de usuarios"""

import logging
from flask import Blueprint, request, jsonify
from marshmallow import ValidationError

# Flask-JWT-Extended imports
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from src.services.usuario.usuario_service import UsuarioService
from src.core.auth.jwt_helpers import get_current_user, get_current_user_id, get_current_user_email
from src.schemas.usuario_schema import (
    UsuarioEmpleadoCreateSchema, UsuarioClienteCreateSchema, UsuarioUpdateSchema,
    ErrorSchema, SuccessSchema
)

logger = logging.getLogger(__name__)

# Blueprint para usuarios
usuario_bp = Blueprint('usuarios', __name__, url_prefix='/api/usuarios')

# Instanciar esquemas
empleado_create_schema = UsuarioEmpleadoCreateSchema()
cliente_create_schema = UsuarioClienteCreateSchema()
usuario_update_schema = UsuarioUpdateSchema()
error_schema = ErrorSchema()
success_schema = SuccessSchema()

# Instanciar servicio
usuario_service = UsuarioService()


@usuario_bp.route('/empleado', methods=['POST'])
@jwt_required()
def crear_empleado():
    """
    Crear nuevo usuario empleado
    ---
    tags:
      - Usuarios
    security:
      - Bearer: []
    parameters:
      - in: body
        name: empleado
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
            password:
              type: string
            nombre:
              type: string
            apellido:
              type: string
            telefono:
              type: string
            rol_id:
              type: integer
            sucursal_id:
              type: integer
    responses:
      201:
        description: Empleado creado exitosamente
      400:
        description: Datos inválidos
    """
    try:
        # Validar datos de entrada
        datos_empleado = empleado_create_schema.load(request.get_json())

        # Crear empleado
        empleado = usuario_service.crear_empleado(datos_empleado)

        return jsonify({
            'success': True,
            'message': 'Empleado creado exitosamente',
            'data': empleado
        }), 201

    except ValidationError as e:
        logger.warning(f"Datos inválidos para crear empleado: {e.messages}")
        return jsonify({
            'success': False,
            'error': 'VALIDATION_ERROR',
            'message': 'Datos inválidos',
            'details': e.messages
        }), 400

    except Exception as e:
        logger.error(f"Error al crear empleado: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500


@usuario_bp.route('/cliente', methods=['POST'])
def crear_cliente():
    """
    Crear nuevo usuario cliente (sin JWT requerido)
    ---
    tags:
      - Usuarios
    parameters:
      - in: body
        name: cliente
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
            password:
              type: string
            nombre:
              type: string
            apellido:
              type: string
            telefono:
              type: string
            acepta_marketing:
              type: boolean
    responses:
      201:
        description: Cliente creado exitosamente
      400:
        description: Datos inválidos
    """
    try:
        # Validar datos de entrada
        datos_cliente = cliente_create_schema.load(request.get_json())

        # Crear cliente
        cliente = usuario_service.crear_cliente(datos_cliente)

        return jsonify({
            'success': True,
            'message': 'Cliente creado exitosamente',
            'data': cliente
        }), 201

    except ValidationError as e:
        logger.warning(f"Datos inválidos para crear cliente: {e.messages}")
        return jsonify({
            'success': False,
            'error': 'VALIDATION_ERROR',
            'message': 'Datos inválidos',
            'details': e.messages
        }), 400

    except Exception as e:
        logger.error(f"Error al crear cliente: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500


@usuario_bp.route('', methods=['GET'])
@jwt_required()
def listar_usuarios():
    """
    Listar usuarios
    ---
    tags:
      - Usuarios
    security:
      - Bearer: []
    responses:
      200:
        description: Lista de usuarios
      401:
        description: No autorizado
    """
    try:
        # Obtener usuarios sin paginación
        usuarios = usuario_service.listar_usuarios()

        return jsonify({
            'success': True,
            'data': usuarios
        }), 200

    except Exception as e:
        logger.error(f"Error al listar usuarios: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500


@usuario_bp.route('/<int:usuario_id>', methods=['GET'])
@jwt_required()
def obtener_usuario(usuario_id):
    """
    Obtener usuario por ID
    ---
    tags:
      - Usuarios
    security:
      - Bearer: []
    parameters:
      - in: path
        name: usuario_id
        type: integer
        required: true
        description: ID del usuario
    responses:
      200:
        description: Datos del usuario
      404:
        description: Usuario no encontrado
    """
    try:
        # Obtener usuario
        usuario = usuario_service.obtener_usuario_por_id(usuario_id)

        if usuario:
            return jsonify({
                'success': True,
                'data': usuario
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'USER_NOT_FOUND',
                'message': 'Usuario no encontrado'
            }), 404

    except Exception as e:
        logger.error(f"Error al obtener usuario: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500


@usuario_bp.route('/<int:usuario_id>', methods=['PUT'])
@jwt_required()
def actualizar_usuario(usuario_id):
    """
    Actualizar usuario
    ---
    tags:
      - Usuarios
    security:
      - Bearer: []
    parameters:
      - in: path
        name: usuario_id
        type: integer
        required: true
      - in: body
        name: usuario_data
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
            nombre:
              type: string
            apellido:
              type: string
    responses:
      200:
        description: Usuario actualizado exitosamente
      404:
        description: Usuario no encontrado
    """
    try:
        # Validar datos de entrada
        datos_usuario = usuario_update_schema.load(request.get_json())

        # Actualizar usuario
        usuario = usuario_service.actualizar_usuario(usuario_id, datos_usuario)

        return jsonify({
            'success': True,
            'message': 'Usuario actualizado exitosamente',
            'data': usuario
        }), 200

    except ValidationError as e:
        logger.warning(
            f"Datos invÃ¡lidos para actualizar usuario: {e.messages}")
        return jsonify({
            'success': False,
            'error': 'VALIDATION_ERROR',
            'message': 'Datos invÃ¡lidos',
            'details': e.messages
        }), 400

    except Exception as e:
        logger.error(f"Error al actualizar usuario: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500


@usuario_bp.route('/<int:usuario_id>', methods=['DELETE'])
@jwt_required()
def eliminar_usuario(usuario_id):
    """
    Eliminar usuario (eliminación lógica)
    ---
    tags:
      - Usuarios
    security:
      - Bearer: []
    parameters:
      - in: path
        name: usuario_id
        type: integer
        required: true
        description: ID del usuario a eliminar
    responses:
      200:
        description: Usuario eliminado exitosamente
      404:
        description: Usuario no encontrado
    """
    try:
        # Eliminar usuario
        eliminado = usuario_service.eliminar_usuario(usuario_id)

        if eliminado:
            return jsonify({
                'success': True,
                'message': 'Usuario eliminado exitosamente'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'USER_NOT_FOUND',
                'message': 'Usuario no encontrado'
            }), 404

    except Exception as e:
        logger.error(f"Error al eliminar usuario: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500


@usuario_bp.route('/<int:usuario_id>/activate', methods=['POST'])
@jwt_required()
def activar_usuario(usuario_id):
    """
    Activar usuario
    ---
    tags:
      - Usuarios
    security:
      - Bearer: []
    parameters:
      - in: path
        name: usuario_id
        type: integer
        required: true
        description: ID del usuario a activar
    responses:
      200:
        description: Usuario activado exitosamente
      404:
        description: Usuario no encontrado
    """
    try:
        # Activar usuario
        usuario = usuario_service.activar_desactivar_usuario(usuario_id, True)

        return jsonify({
            'success': True,
            'message': 'Usuario activado exitosamente',
            'data': usuario
        }), 200

    except Exception as e:
        logger.error(f"Error al activar usuario: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500


@usuario_bp.route('/meseros', methods=['GET'])
@jwt_required()
def listar_meseros():
    """
    GET /api/usuarios/meseros?sucursal_id=X
    Listar todos los meseros (rol_id=5) de una sucursal.
    
    Query params:
        - sucursal_id: ID de la sucursal (requerido)
    
    Returns:
        200 OK - Lista de meseros
        400 Bad Request - sucursal_id requerido
        403 Forbidden - Sin acceso
    """
    try:
        usuario_id = get_jwt_identity()
        sucursal_id = request.args.get('sucursal_id', type=int)
        
        # Validar que sucursal_id sea provided
        if not sucursal_id:
            return jsonify({
                "success": False,
                "error": "Parámetro 'sucursal_id' requerido"
            }), 400
        
        # VALIDACIÓN: Si no es ADMIN, verificar acceso a sucursal
        from src.core.utils.multitenant import es_admin, validar_pertenencia_sucursal
        if not es_admin(usuario_id):
            if not validar_pertenencia_sucursal(usuario_id, sucursal_id):
                logger.warning(f"Usuario {usuario_id} intentó listar meseros sin acceso a sucursal {sucursal_id}")
                return jsonify({
                    "success": False,
                    "error": "No tiene acceso a esta sucursal"
                }), 403
        
        # Obtener meseros
        from src.dao.seguridad.usuario_dao import UsuarioDAO
        meseros = UsuarioDAO.obtener_meseros_por_sucursal(sucursal_id)
        meseros_dicts = [m.to_dict() for m in meseros]
        
        logger.info(f"Usuario {usuario_id} listó {len(meseros_dicts)} meseros de sucursal {sucursal_id}")
        return jsonify({
            "success": True,
            "data": meseros_dicts,
            "total": len(meseros_dicts)
        }), 200
        
    except Exception as e:
        logger.error(f"Error en GET /api/usuarios/meseros: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Error al listar meseros: {str(e)}"
        }), 500
