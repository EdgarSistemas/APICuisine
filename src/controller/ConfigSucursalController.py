"""
ConfigSucursalController - Endpoints REST para gestión de Configuraciones por Sucursal
Solo ADMIN puede crear/actualizar/eliminar configuraciones
Cualquier usuario autenticado puede consultar
"""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from src.services.config.config_sucursal_service import ConfigSucursalService
from src.schemas.config_sucursal_schema import ConfigSucursalCreateSchema, ConfigSucursalUpdateSchema

logger = logging.getLogger(__name__)

# Blueprint para configuraciones
bp = Blueprint('config_sucursal', __name__, url_prefix='/api/config')


# ============================================================================
# POST /api/config - Crear o Actualizar Configuración (Upsert)
# ============================================================================
@bp.route('', methods=['POST'])
@jwt_required()
def crear_o_actualizar_config():
    """
    Crear o actualizar configuración (upsert)
    Solo ADMIN
    ---
    tags:
      - Configuración
    security:
      - Bearer: []
    parameters:
      - in: body
        name: config
        required: true
        schema:
          type: object
          required:
            - sucursal_id
            - clave
          properties:
            sucursal_id:
              type: integer
              example: 1
            clave:
              type: string
              example: "tolerancia_noshow"
            valor_string:
              type: string
              example: "15"
    responses:
      200:
        description: Configuración creada/actualizada
      400:
        description: Datos inválidos
      403:
        description: Solo ADMIN
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar schema
        schema = ConfigSucursalCreateSchema()
        try:
            datos_validados = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': e.messages
            }), 400
        
        resultado = ConfigSucursalService.crear_o_actualizar_config(
            usuario_id=usuario_id,
            sucursal_id=datos_validados['sucursal_id'],
            clave=datos_validados['clave'],
            valor_string=datos_validados.get('valor_string')
        )
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            status = 403 if 'admin' in resultado.get('error', '').lower() else 400
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error en crear_o_actualizar_config: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# GET /api/config?sucursal_id=1&clave=tolerancia_noshow - Obtener Config
# ============================================================================
@bp.route('', methods=['GET'])
@jwt_required()
def obtener_config():
    """
    Obtener configuración por sucursal y clave
    ---
    tags:
      - Configuración
    security:
      - Bearer: []
    parameters:
      - in: query
        name: sucursal_id
        type: integer
        required: true
      - in: query
        name: clave
        type: string
        required: true
    responses:
      200:
        description: Configuración encontrada
      404:
        description: Configuración no encontrada
    """
    try:
        sucursal_id = request.args.get('sucursal_id', type=int)
        clave = request.args.get('clave', type=str)
        
        if not sucursal_id or not clave:
            return jsonify({
                'success': False,
                'error': 'MISSING_PARAMS',
                'message': 'Debe proporcionar sucursal_id y clave'
            }), 400
        
        resultado = ConfigSucursalService.obtener_config(sucursal_id, clave)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 404
            
    except Exception as e:
        logger.error(f"Error en obtener_config: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# GET /api/config/sucursal/<id> - Listar Configs por Sucursal
# ============================================================================
@bp.route('/sucursal/<int:sucursal_id>', methods=['GET'])
@jwt_required()
def listar_configs_sucursal(sucursal_id):
    """
    Listar todas las configuraciones de una sucursal
    ---
    tags:
      - Configuración
    security:
      - Bearer: []
    parameters:
      - in: path
        name: sucursal_id
        type: integer
        required: true
    responses:
      200:
        description: Lista de configuraciones
    """
    try:
        resultado = ConfigSucursalService.listar_configs(sucursal_id)
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en listar_configs_sucursal: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# DELETE /api/config - Eliminar Configuración
# ============================================================================
@bp.route('', methods=['DELETE'])
@jwt_required()
def eliminar_config():
    """
    Eliminar configuración
    Solo ADMIN
    ---
    tags:
      - Configuración
    security:
      - Bearer: []
    parameters:
      - in: query
        name: sucursal_id
        type: integer
        required: true
      - in: query
        name: clave
        type: string
        required: true
    responses:
      200:
        description: Configuración eliminada
      403:
        description: Solo ADMIN
      404:
        description: Configuración no encontrada
    """
    try:
        usuario_id = get_jwt_identity()
        sucursal_id = request.args.get('sucursal_id', type=int)
        clave = request.args.get('clave', type=str)
        
        if not sucursal_id or not clave:
            return jsonify({
                'success': False,
                'error': 'MISSING_PARAMS',
                'message': 'Debe proporcionar sucursal_id y clave'
            }), 400
        
        resultado = ConfigSucursalService.eliminar_config(usuario_id, sucursal_id, clave)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            status = 403 if 'admin' in resultado.get('error', '').lower() else 404
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error en eliminar_config: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500
