"""
MesaController - Endpoints REST para gestión de Mesas
Arquitectura n-capas: Controller → Service → DAO → Database
Con documentación Swagger completa para todos los endpoints
"""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.services.catalogos.mesa_service import MesaService

logger = logging.getLogger(__name__)

# Blueprint para mesas
bp = Blueprint('mesas', __name__, url_prefix='/api/mesas')


# ============================================================================
# POST /api/mesas - Crear Mesa
# ============================================================================
@bp.route('', methods=['POST'])
@jwt_required()
def crear_mesa():
    """
    Crear nueva mesa
    ---
    tags:
      - Mesas
    security:
      - Bearer: []
    parameters:
      - in: body
        name: mesa
        required: true
        schema:
          type: object
          required:
            - area_id
            - capacidad
          properties:
            area_id:
              type: integer
              example: 1
              description: "ID del área donde se creará la mesa"
            capacidad:
              type: integer
              example: 4
              description: "Capacidad de personas"
          description: "El código de mesa se genera automáticamente con formato MES-YYYYMMDDHHMMSS"
    responses:
      201:
        description: Mesa creada exitosamente con código generado automáticamente
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: object
              properties:
                codigo_mesa:
                  type: string
                  example: "MES-20251106074844"
            message:
              type: string
      400:
        description: Datos inválidos
      403:
        description: Solo administradores pueden crear mesas
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json()
        
        area_id = data.get('area_id')
        capacidad = data.get('capacidad')
        
        if not area_id or capacidad is None:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': 'area_id y capacidad son requeridos'
            }), 400
        
        resultado = MesaService.crear_mesa(usuario_id, area_id, capacidad)
        
        if resultado['success']:
            codigo_generado = resultado['data']['codigo_mesa']
            logger.info(f"Mesa '{codigo_generado}' creada por usuario {usuario_id}")
            return jsonify(resultado), 201
        else:
            status = 403 if 'admin' in resultado.get('error', '').lower() else 400
            return jsonify(resultado), status
        
    except Exception as e:
        logger.error(f"Error creando mesa: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500


# ============================================================================
# GET /api/mesas - Listar Mesas
# ============================================================================
@bp.route('', methods=['GET'])
@jwt_required()
def listar_mesas():
    """
    Listar mesas con filtros opcionales
    ---
    tags:
      - Mesas
    security:
      - Bearer: []
    parameters:
      - in: query
        name: area_id
        type: integer
        description: Filtrar por área
      - in: query
        name: sucursal_id
        type: integer
        description: Filtrar por sucursal
      - in: query
        name: solo_activas
        type: boolean
        description: Solo mostrar mesas activas (default true)
      - in: query
        name: busqueda
        type: string
        description: Buscar por código de mesa
    responses:
      200:
        description: Lista de mesas
      400:
        description: Parámetros inválidos
    """
    try:
        usuario_id = int(get_jwt_identity())
        area_id = request.args.get('area_id', type=int)
        sucursal_id = request.args.get('sucursal_id', type=int)
        solo_activas = request.args.get('solo_activas', 'true').lower() == 'true'
        busqueda = request.args.get('busqueda', '').strip()
        
        # Obtener mesas
        resultado = MesaService.obtener_mesas(usuario_id, area_id=area_id, sucursal_id=sucursal_id)
        
        if resultado['success']:
            mesas = resultado.get('data', [])
            
            # Filtrar por búsqueda si se proporciona
            if busqueda:
                mesas = [m for m in mesas if busqueda.lower() in m.get('codigo_mesa', '').lower()]
            
            # Filtrar por estado activo si se solicita
            if solo_activas:
                mesas = [m for m in mesas if m.get('es_activa', True)]
            
            return jsonify({
                'success': True,
                'data': mesas,
                'total': len(mesas),
                'filtros': {
                    'area_id': area_id,
                    'sucursal_id': sucursal_id,
                    'solo_activas': solo_activas,
                    'busqueda': busqueda if busqueda else None
                }
            }), 200
        else:
            status = 403 if 'acceso' in resultado.get('error', '').lower() else 400
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error listando mesas: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500


# ============================================================================
# GET /api/mesas/{id} - Obtener Mesa por ID
# ============================================================================
@bp.route('/<int:id_mesa>', methods=['GET'])
@jwt_required()
def obtener_mesa(id_mesa):
    """
    Obtener mesa por ID
    ---
    tags:
      - Mesas
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id_mesa
        required: true
        type: integer
    responses:
      200:
        description: Mesa encontrada
      404:
        description: Mesa no encontrada
      403:
        description: Sin acceso a esta mesa
    """
    try:
        usuario_id = get_jwt_identity()
        resultado = MesaService.obtener_mesa(usuario_id, id_mesa)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            error_msg = resultado.get('error', '').lower()
            if 'no existe' in error_msg:
                status = 404
            elif 'acceso' in error_msg:
                status = 403
            else:
                status = 400
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error obteniendo mesa {id_mesa}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500


# ============================================================================
# PUT /api/mesas/{id} - Actualizar Mesa
# ============================================================================
@bp.route('/<int:id_mesa>', methods=['PUT'])
@jwt_required()
def actualizar_mesa(id_mesa):
    """
    Actualizar mesa
    ---
    tags:
      - Mesas
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id_mesa
        required: true
        type: integer
        description: "ID de la mesa a actualizar"
      - in: body
        name: mesa
        required: true
        schema:
          type: object
          properties:
            capacidad:
              type: integer
              example: 6
              description: "Nueva capacidad de personas"
          description: "El código de mesa NO se puede modificar"
    responses:
      200:
        description: Mesa actualizada exitosamente
      404:
        description: Mesa no encontrada
      400:
        description: Datos inválidos
      403:
        description: Solo administradores pueden actualizar
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json()
        
        capacidad = data.get('capacidad')
        
        resultado = MesaService.actualizar_mesa(usuario_id, id_mesa, capacidad)
        
        if resultado['success']:
            logger.info(f"Mesa {id_mesa} actualizada por usuario {usuario_id}")
            return jsonify(resultado), 200
        else:
            error_msg = resultado.get('error', '').lower()
            if 'admin' in error_msg:
                status = 403
            elif 'no existe' in error_msg:
                status = 404
            else:
                status = 400
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error actualizando mesa {id_mesa}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500


# ============================================================================
# DELETE /api/mesas/{id} - Eliminar Mesa (Soft Delete)
# ============================================================================
@bp.route('/<int:id_mesa>', methods=['DELETE'])
@jwt_required()
def eliminar_mesa(id_mesa):
    """
    Eliminar mesa (eliminación lógica)
    ---
    tags:
      - Mesas
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id_mesa
        required: true
        type: integer
    responses:
      200:
        description: Mesa eliminada exitosamente
      404:
        description: Mesa no encontrada
      403:
        description: Solo administradores pueden eliminar
    """
    try:
        usuario_id = get_jwt_identity()
        resultado = MesaService.eliminar_mesa(usuario_id, id_mesa)
        
        if resultado['success']:
            logger.info(f"Mesa {id_mesa} eliminada por usuario {usuario_id}")
            return jsonify(resultado), 200
        else:
            error_msg = resultado.get('error', '').lower()
            if 'admin' in error_msg:
                status = 403
            elif 'no existe' in error_msg:
                status = 404
            else:
                status = 400
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error eliminando mesa {id_mesa}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500
