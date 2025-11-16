"""Endpoint de roles"""

import logging
from flask import Blueprint, request, jsonify
from marshmallow import ValidationError

# Flask-JWT-Extended imports
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from src.services.auth.rol_service import RolService
from src.core.auth.jwt_helpers import get_current_user, get_current_user_id, get_current_user_email
from src.schemas.auth_schema import (
    RolCreateSchema, RolUpdateSchema, RolResponseSchema,
    ErrorSchema, SuccessSchema
)

logger = logging.getLogger(__name__)

# Blueprint para roles
roles_bp = Blueprint('roles', __name__, url_prefix='/api/roles')

# Instanciar esquemas
rol_create_schema = RolCreateSchema()
rol_update_schema = RolUpdateSchema()
rol_response_schema = RolResponseSchema()
error_schema = ErrorSchema()
success_schema = SuccessSchema()

# Instanciar servicio
rol_service = RolService()


@roles_bp.route('', methods=['POST'])
@jwt_required()
def crear_rol():
    """
    Crear nuevo rol
    ---
    tags:
      - Roles
    security:
      - Bearer: []
    parameters:
      - in: body
        name: rol_data
        required: true
        schema:
          type: object
          properties:
            nombre:
              type: string
              example: "Administrador"
            descripcion:
              type: string
              example: "Rol con permisos administrativos"
            modulos:
              type: array
              items:
                type: integer
              example: [1, 2, 3]
    responses:
      201:
        description: Rol creado exitosamente
      400:
        description: Datos inválidos
    """
    try:
        # Validar datos de entrada
        datos_rol = rol_create_schema.load(request.get_json())
        
        # Crear rol
        resultado = rol_service.crear_rol(datos_rol)
        
        if resultado['success']:
            return jsonify(resultado), 201
        else:
            return jsonify(error_schema.dump(resultado)), 409
            
    except ValidationError as e:
        logger.warning(f"Datos invÃ¡lidos para crear rol: {e.messages}")
        return jsonify(error_schema.dump({
            'error': 'VALIDATION_ERROR',
            'message': 'Datos invÃ¡lidos',
            'details': e.messages
        })), 400
        
    except Exception as e:
        logger.error(f"Error al crear rol: {str(e)}")
        return jsonify(error_schema.dump({
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        })), 500


@roles_bp.route('', methods=['GET'])
@jwt_required()
def listar_roles():
    """
    Listar todos los roles
    ---
    tags:
      - Roles
    security:
      - Bearer: []
    responses:
      200:
        description: Lista de roles
      401:
        description: No autorizado
    """
    try:
        # Obtener búsqueda opcional
        search = request.args.get('search', '')
        
        # Listar roles
        resultado = rol_service.listar_roles(search=search)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            return jsonify(error_schema.dump(resultado)), 500
            
    except Exception as e:
        logger.error(f"Error al listar roles: {str(e)}")
        return jsonify(error_schema.dump({
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        })), 500


@roles_bp.route('/<int:id_rol>', methods=['GET'])
@jwt_required()
def obtener_rol(id_rol):
    """
    Obtener rol por ID
    ---
    tags:
      - Roles
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id_rol
        type: integer
        required: true
        description: ID del rol
    responses:
      200:
        description: Datos del rol
      404:
        description: Rol no encontrado
    """
    try:
        # Obtener rol
        resultado = rol_service.obtener_rol(id_rol)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            return jsonify(error_schema.dump(resultado)), 404
            
    except Exception as e:
        logger.error(f"Error al obtener rol: {str(e)}")
        return jsonify(error_schema.dump({
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        })), 500


@roles_bp.route('/<int:id_rol>', methods=['PUT'])
@jwt_required()
def actualizar_rol(id_rol):
    """
    Actualizar rol
    ---
    tags:
      - Roles
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id_rol
        type: integer
        required: true
      - in: body
        name: rol_data
        required: true
        schema:
          type: object
          properties:
            nombre:
              type: string
            descripcion:
              type: string
            modulos:
              type: array
              items:
                type: integer
    responses:
      200:
        description: Rol actualizado exitosamente
      404:
        description: Rol no encontrado
    """
    try:
        # Validar datos de entrada
        datos_rol = rol_update_schema.load(request.get_json())
        
        # Actualizar rol
        resultado = rol_service.actualizar_rol(id_rol, datos_rol)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            status_code = 404 if 'not found' in resultado.get('message', '').lower() else 409
            return jsonify(error_schema.dump(resultado)), status_code
            
    except ValidationError as e:
        logger.warning(f"Datos invÃ¡lidos para actualizar rol: {e.messages}")
        return jsonify(error_schema.dump({
            'error': 'VALIDATION_ERROR',
            'message': 'Datos invÃ¡lidos',
            'details': e.messages
        })), 400
        
    except Exception as e:
        logger.error(f"Error al actualizar rol: {str(e)}")
        return jsonify(error_schema.dump({
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        })), 500


@roles_bp.route('/<int:id_rol>/modulos', methods=['POST'])
@jwt_required()
def asignar_modulos(id_rol):
    """
    Asignar módulos a rol
    ---
    tags:
      - Roles
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id_rol
        type: integer
        required: true
        description: ID del rol
      - in: body
        name: modulos
        required: true
        schema:
          type: object
          properties:
            modulos:
              type: array
              items:
                type: integer
              example: [1, 2, 3]
    responses:
      200:
        description: Módulos asignados exitosamente
      404:
        description: Rol no encontrado
    """
    try:
        # Validar datos de entrada
        datos = request.get_json()
        if not datos or 'modulos_ids' not in datos:
            return jsonify(error_schema.dump({
                'error': 'VALIDATION_ERROR',
                'message': 'Se requiere el campo modulos_ids'
            })), 400
        
        modulos_ids = datos['modulos_ids']
        if not isinstance(modulos_ids, list):
            return jsonify(error_schema.dump({
                'error': 'VALIDATION_ERROR',
                'message': 'modulos_ids debe ser una lista'
            })), 400
        
        # Asignar mÃ³dulos
        resultado = rol_service.asignar_modulos(id_rol, modulos_ids)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            status_code = 404 if 'not found' in resultado.get('message', '').lower() else 400
            return jsonify(error_schema.dump(resultado)), status_code
            
    except Exception as e:
        logger.error(f"Error al asignar mÃ³dulos: {str(e)}")
        return jsonify(error_schema.dump({
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        })), 500


@roles_bp.route('/modulos', methods=['GET'])
@jwt_required()
def listar_modulos_activos():
    """
    Listar todos los módulos activos
    ---
    tags:
      - Roles
    summary: Obtener lista de módulos activos
    description: Retorna todos los módulos activos del sistema
    security:
      - Bearer: []
    responses:
      200:
        description: Lista de módulos activos
        schema:
          type: object
          properties:
            success:
              type: boolean
            modulos:
              type: array
              items:
                type: object
                properties:
                  id_modulo:
                    type: integer
                  nombre:
                    type: string
                  clave:
                    type: string
                  descripcion:
                    type: string
                  es_activo:
                    type: boolean
                  created_at:
                    type: string
                  updated_at:
                    type: string
            count:
              type: integer
      500:
        description: Error interno del servidor
    """
    try:
        resultado = rol_service.listar_modulos_activos()
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            return jsonify(error_schema.dump(resultado)), 500
        
    except Exception as e:
        logger.error(f"Error en listar_modulos_activos: {str(e)}")
        return jsonify(error_schema.dump({
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        })), 500
