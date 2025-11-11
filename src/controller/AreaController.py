"""
AreaController - Endpoints REST para gestión de Áreas
Arquitectura n-capas: Controller → Service → DAO → Database
Con documentación Swagger completa para todos los endpoints
"""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.services.area.area_service import AreaService

logger = logging.getLogger(__name__)

# Blueprint para areas
bp = Blueprint('areas', __name__, url_prefix='/api/areas')


# ============================================================================
# POST /api/areas - Crear Área
# ============================================================================
@bp.route('', methods=['POST'])
@jwt_required()
def crear_area():
    """
    Crear nueva área
    ---
    tags:
      - Areas
    security:
      - Bearer: []
    parameters:
      - in: body
        name: area
        required: true
        schema:
          type: object
          properties:
            sucursal_id:
              type: integer
              example: 1
            nombre:
              type: string
              example: "Salón Principal"
            descripcion:
              type: string
              example: "Área principal con vista al jardín"
    responses:
      201:
        description: Área creada exitosamente
      400:
        description: Datos inválidos
      403:
        description: Solo administradores pueden crear áreas
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json()
        
        sucursal_id = data.get('sucursal_id')
        nombre = data.get('nombre')
        descripcion = data.get('descripcion')
        
        if not sucursal_id or not nombre:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': 'sucursal_id y nombre son requeridos'
            }), 400
        
        resultado = AreaService.crear_area(usuario_id, sucursal_id, nombre, descripcion)
        
        if resultado['success']:
            logger.info(f"Área '{nombre}' creada por usuario {usuario_id}")
            return jsonify(resultado), 201
        else:
            # Determinar status code según el error
            status = 403 if 'admin' in resultado.get('error', '').lower() else 400
            return jsonify(resultado), status
        
    except Exception as e:
        logger.error(f"Error creando área: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500


# ============================================================================
# GET /api/areas - Listar Áreas
# ============================================================================
@bp.route('', methods=['GET'])
@jwt_required()
def listar_areas():
    """
    Listar áreas con filtros opcionales
    ---
    tags:
      - Areas
    security:
      - Bearer: []
    parameters:
      - in: query
        name: sucursal_id
        type: integer
        description: Filtrar por sucursal (requerido para empleados)
      - in: query
        name: solo_activas
        type: boolean
        description: Solo mostrar áreas activas (default true)
      - in: query
        name: busqueda
        type: string
        description: Buscar por nombre o descripción
    responses:
      200:
        description: Lista de áreas
      400:
        description: Parámetros inválidos
    """
    try:
        usuario_id = int(get_jwt_identity())
        sucursal_id = request.args.get('sucursal_id', type=int)
        solo_activas = request.args.get('solo_activas', 'true').lower() == 'true'
        busqueda = request.args.get('busqueda', '').strip()
        
        # Validar parámetros
        if not sucursal_id:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': 'sucursal_id es requerido'
            }), 400
        
        # Obtener áreas
        resultado = AreaService.obtener_areas(usuario_id, sucursal_id=sucursal_id)
        
        if resultado['success']:
            areas = resultado.get('data', [])
            
            # Filtrar por búsqueda si se proporciona
            if busqueda:
                areas = [a for a in areas if busqueda.lower() in a.get('nombre', '').lower() or 
                         busqueda.lower() in a.get('descripcion', '').lower()]
            
            # Filtrar por estado activo si se solicita
            if solo_activas:
                areas = [a for a in areas if a.get('es_activa', True)]
            
            return jsonify({
                'success': True,
                'data': areas,
                'total': len(areas),
                'filtros': {
                    'sucursal_id': sucursal_id,
                    'solo_activas': solo_activas,
                    'busqueda': busqueda if busqueda else None
                }
            }), 200
        else:
            status = 403 if 'acceso' in resultado.get('error', '').lower() else 400
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error listando áreas: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500


# ============================================================================
# GET /api/areas/{id} - Obtener Área por ID
# ============================================================================
@bp.route('/<int:id_area>', methods=['GET'])
@jwt_required()
def obtener_area(id_area):
    """
    Obtener área por ID
    ---
    tags:
      - Areas
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id_area
        required: true
        type: integer
    responses:
      200:
        description: Área encontrada
      404:
        description: Área no encontrada
      403:
        description: Sin acceso a esta área
    """
    try:
        usuario_id = get_jwt_identity()
        resultado = AreaService.obtener_area(usuario_id, id_area)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            # Determinar status code
            error_msg = resultado.get('error', '').lower()
            if 'no existe' in error_msg:
                status = 404
            elif 'acceso' in error_msg:
                status = 403
            else:
                status = 400
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error obteniendo área {id_area}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500


# ============================================================================
# PUT /api/areas/{id} - Actualizar Área
# ============================================================================
@bp.route('/<int:id_area>', methods=['PUT'])
@jwt_required()
def actualizar_area(id_area):
    """
    Actualizar área
    ---
    tags:
      - Areas
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id_area
        required: true
        type: integer
      - in: body
        name: area
        required: true
        schema:
          type: object
          properties:
            nombre:
              type: string
              example: "Salón Principal Renovado"
            descripcion:
              type: string
              example: "Nueva descripción del área"
    responses:
      200:
        description: Área actualizada exitosamente
      404:
        description: Área no encontrada
      400:
        description: Datos inválidos
      403:
        description: Solo administradores pueden actualizar
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json()
        
        nombre = data.get('nombre')
        descripcion = data.get('descripcion')
        
        resultado = AreaService.actualizar_area(usuario_id, id_area, nombre, descripcion)
        
        if resultado['success']:
            logger.info(f"Área {id_area} actualizada por usuario {usuario_id}")
            return jsonify(resultado), 200
        else:
            # Determinar status code
            error_msg = resultado.get('error', '').lower()
            if 'admin' in error_msg:
                status = 403
            elif 'no existe' in error_msg:
                status = 404
            else:
                status = 400
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error actualizando área {id_area}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500


# ============================================================================
# DELETE /api/areas/{id} - Eliminar Área (Soft Delete)
# ============================================================================
@bp.route('/<int:id_area>', methods=['DELETE'])
@jwt_required()
def eliminar_area(id_area):
    """
    Eliminar área (eliminación lógica)
    ---
    tags:
      - Areas
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id_area
        required: true
        type: integer
    responses:
      200:
        description: Área eliminada exitosamente
      404:
        description: Área no encontrada
      403:
        description: Solo administradores pueden eliminar
    """
    try:
        usuario_id = get_jwt_identity()
        resultado = AreaService.eliminar_area(usuario_id, id_area)
        
        if resultado['success']:
            logger.info(f"Área {id_area} eliminada por usuario {usuario_id}")
            return jsonify(resultado), 200
        else:
            # Determinar status code
            error_msg = resultado.get('error', '').lower()
            if 'admin' in error_msg:
                status = 403
            elif 'no existe' in error_msg:
                status = 404
            else:
                status = 400
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error eliminando área {id_area}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500


# ============================================================================
# PATCH /api/areas/{id}/activar - Activar/Desactivar Área
# ============================================================================
# @bp.route('/<int:id_area>/activar', methods=['PATCH'])
# @jwt_required()
# def cambiar_estado_area(id_area):
#     """
#     Activar/Desactivar área
#     ---
#     tags:
#       - Areas
#     security:
#       - Bearer: []
#     parameters:
#       - in: path
#         name: id_area
#         required: true
#         type: integer
#       - in: body
#         name: activacion
#         required: true
#         schema:
#           type: object
#           properties:
#             activar:
#               type: boolean
#               example: true
#     responses:
#       200:
#         description: Estado del área cambiado exitosamente
#       404:
#         description: Área no encontrada
#       403:
#         description: Solo administradores pueden cambiar estado
#     """
#     try:
#         usuario_id = get_jwt_identity()
#         data = request.get_json()
        
#         if data is None or 'activar' not in data:
#             return jsonify({
#                 'success': False,
#                 'error': 'VALIDATION_ERROR',
#                 'message': 'Se requiere el campo "activar" (boolean)'
#             }), 400
        
#         activar = data.get('activar')
        
#         # Actualizar con es_activa
#         resultado = AreaService.actualizar_area(usuario_id, id_area, es_activa=activar)
        
#         if resultado['success']:
#             accion = "activada" if activar else "desactivada"
#             logger.info(f"Área {id_area} {accion} por usuario {usuario_id}")
#             return jsonify({
#                 'success': True,
#                 'message': f'Área {accion} exitosamente',
#                 'data': resultado.get('data')
#             }), 200
#         else:
#             # Determinar status code
#             error_msg = resultado.get('error', '').lower()
#             if 'admin' in error_msg:
#                 status = 403
#             elif 'no existe' in error_msg:
#                 status = 404
#             else:
#                 status = 400
#             return jsonify(resultado), status
            
#     except Exception as e:
#         logger.error(f"Error cambiando estado de área {id_area}: {str(e)}")
#         return jsonify({
#             'success': False,
#             'error': 'INTERNAL_ERROR',
#             'message': 'Error interno del servidor'
#         }), 500
