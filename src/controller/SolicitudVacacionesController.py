"""
SolicitudVacacionesController - Endpoints para solicitudes de vacaciones
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from flasgger import swag_from
from src.services.rrhh.solicitud_vacaciones_service import SolicitudVacacionesService
from src.core.auth.jwt_helpers import get_current_user_id, get_current_user_roles
import logging

logger = logging.getLogger(__name__)

solicitud_vacaciones_bp = Blueprint('solicitud_vacaciones', __name__, url_prefix='/api/vacaciones')


@solicitud_vacaciones_bp.route('', methods=['POST'])
@jwt_required()
def crear_solicitud():
    """
    Crear solicitud de vacaciones
    ---
    tags:
      - Vacaciones
    summary: Crear solicitud de vacaciones (Empleado)
    description: |
      Permite al empleado solicitar días de vacaciones.
      La solicitud queda en estatus PENDIENTE hasta que el gerente la apruebe o rechace.
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
            type: object
            required:
              - fecha_inicio
              - fecha_fin
            properties:
              fecha_inicio:
                type: string
                format: date
                example: "2025-02-01"
              fecha_fin:
                type: string
                format: date
                example: "2025-02-15"
              motivo:
                type: string
                maxLength: 300
                description: Motivo opcional de la solicitud
            example:
              fecha_inicio: "2025-02-01"
              fecha_fin: "2025-02-15"
              motivo: "Vacaciones familiares"
    responses:
      201:
        description: Solicitud creada exitosamente
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: true
                solicitud:
                  type: object
                  properties:
                    id_solicitud:
                      type: integer
                    horario_usuario_id:
                      type: integer
                    fecha_inicio:
                      type: string
                      format: date
                      example: "2025-02-01"
                    fecha_fin:
                      type: string
                      format: date
                      example: "2025-02-15"
                    motivo:
                      type: string
                      nullable: true
                    estatus:
                      type: integer
                      example: 1
                      description: 1=Pendiente, 2=Aprobada, 3=Rechazada
                    estatus_display:
                      type: string
                      example: "Pendiente"
                    revisado_por:
                      type: integer
                      nullable: true
                      description: ID del gerente que revisó
                    fecha_revision:
                      type: string
                      format: date-time
                      nullable: true
                    created_at:
                      type: string
                      example: "2025-01-22 14:30:00"
                    updated_at:
                      type: string
                      format: date-time
                      nullable: true
      400:
        description: Error de validación
      500:
        description: Error interno del servidor
    """
    try:
        current_user_id = get_current_user_id()
        
        # Usar silent=True para evitar error 415 si Content-Type no es application/json
        data = request.get_json(silent=True) or {}
        
        resultado = SolicitudVacacionesService.crear_solicitud(
            usuario_id=current_user_id,
            data=data
        )
        
        if not resultado['success']:
            return jsonify(resultado), 400
        
        return jsonify(resultado), 201
        
    except Exception as e:
        logger.error(f"Error en crear_solicitud: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@solicitud_vacaciones_bp.route('/mis-solicitudes', methods=['GET'])
@jwt_required()
def listar_mis_solicitudes():
    """
    Listar mis solicitudes de vacaciones
    ---
    tags:
      - Vacaciones
    summary: Ver mis solicitudes (Empleado)
    description: Lista todas las solicitudes del empleado autenticado
    security:
      - Bearer: []
    parameters:
      - name: estatus
        in: query
        required: false
        schema:
          type: integer
          enum: [1, 2, 3]
          description: "1=Pendiente, 2=Aprobada, 3=Rechazada"
    responses:
      200:
        description: Lista de solicitudes
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                solicitudes:
                  type: array
                  items:
                    type: object
                count:
                  type: integer
      500:
        description: Error interno
    """
    try:
        current_user_id = get_current_user_id()
        
        estatus = request.args.get('estatus', type=int)
        
        resultado = SolicitudVacacionesService.listar_solicitudes_usuario(
            usuario_id=current_user_id,
            estatus=estatus
        )
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en listar_mis_solicitudes: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@solicitud_vacaciones_bp.route('/sucursal/<int:sucursal_id>', methods=['GET'])
@jwt_required()
def listar_solicitudes_sucursal(sucursal_id):
    """
    Listar solicitudes de una sucursal
    ---
    tags:
      - Vacaciones
    summary: Ver solicitudes de sucursal (Gerente/Admin)
    description: Lista todas las solicitudes de vacaciones de una sucursal específica
    security:
      - Bearer: []
    parameters:
      - name: sucursal_id
        in: path
        required: true
        schema:
          type: integer
      - name: estatus
        in: query
        required: false
        schema:
          type: integer
          enum: [1, 2, 3]
    responses:
      200:
        description: Lista de solicitudes
      403:
        description: Acceso denegado
      500:
        description: Error interno
    """
    try:
        # Endpoint requiere autenticación - ya está validado por @jwt_required()
        # Por ahora abierto a cualquier usuario autenticado
        
        estatus = request.args.get('estatus', type=int)
        
        resultado = SolicitudVacacionesService.listar_solicitudes_sucursal(
            sucursal_id=sucursal_id,
            estatus=estatus
        )
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en listar_solicitudes_sucursal: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@solicitud_vacaciones_bp.route('/<int:id_solicitud>', methods=['GET'])
@jwt_required()
def obtener_solicitud(id_solicitud):
    """
    Obtener solicitud por ID
    ---
    tags:
      - Vacaciones
    summary: Ver detalle de solicitud
    description: Obtiene los detalles de una solicitud específica
    security:
      - Bearer: []
    parameters:
      - name: id_solicitud
        in: path
        required: true
        schema:
          type: integer
    responses:
      200:
        description: Solicitud encontrada
      403:
        description: No autorizado
      404:
        description: Solicitud no encontrada
      500:
        description: Error interno
    """
    try:
        resultado = SolicitudVacacionesService.obtener_solicitud(id_solicitud)
        
        if not resultado['success']:
            return jsonify(resultado), 404
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en obtener_solicitud: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@solicitud_vacaciones_bp.route('/<int:id_solicitud>/aprobar', methods=['POST'])
@jwt_required()
def aprobar_solicitud(id_solicitud):
    """
    Aprobar solicitud de vacaciones
    ---
    tags:
      - Vacaciones
    summary: Aprobar solicitud (Gerente/Admin)
    description: Cambia el estatus de la solicitud a APROBADA (estatus=2)
    security:
      - Bearer: []
    parameters:
      - name: id_solicitud
        in: path
        required: true
        schema:
          type: integer
    requestBody:
      required: false
      content:
        application/json:
          schema:
            type: object
            properties:
              notas_gerente:
                type: string
                maxLength: 300
                nullable: true
    responses:
      200:
        description: Solicitud aprobada
      400:
        description: Error en la operación
      403:
        description: Acceso denegado
      500:
        description: Error interno
    """
    try:
        from src.core.auth.jwt_helpers import get_current_user_id
        
        current_user_id = get_current_user_id()
        
        # Usar silent=True para evitar error 415 si Content-Type no es application/json
        data = request.get_json(silent=True) or {}
        
        resultado = SolicitudVacacionesService.aprobar_solicitud(
            id_solicitud=id_solicitud,
            gerente_id=current_user_id,
            data=data
        )
        
        if not resultado['success']:
            return jsonify(resultado), 400
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en aprobar_solicitud: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@solicitud_vacaciones_bp.route('/<int:id_solicitud>/rechazar', methods=['POST'])
@jwt_required()
def rechazar_solicitud(id_solicitud):
    """
    Rechazar solicitud de vacaciones
    ---
    tags:
      - Vacaciones
    summary: Rechazar solicitud (Gerente/Admin)
    description: Cambia el estatus de la solicitud a RECHAZADA (estatus=3). Permite guardar notas del gerente.
    security:
      - Bearer: []
    parameters:
      - name: id_solicitud
        in: path
        required: true
        schema:
          type: integer
    requestBody:
      required: false
      content:
        application/json:
          schema:
            type: object
            properties:
              notas_gerente:
                type: string
                maxLength: 300
                nullable: true
                description: "Motivo del rechazo"
          example:
            notas_gerente: "No hay cobertura disponible en esas fechas"
    responses:
      200:
        description: Solicitud rechazada exitosamente
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: true
                solicitud:
                  type: object
      400:
        description: Error en la operación
      403:
        description: Acceso denegado
      500:
        description: Error interno
    """
    try:
        from src.core.auth.jwt_helpers import get_current_user_id
        
        current_user_id = get_current_user_id()
        
        # Usar silent=True para evitar error 415 si Content-Type no es application/json
        data = request.get_json(silent=True) or {}
        
        resultado = SolicitudVacacionesService.rechazar_solicitud(
            id_solicitud=id_solicitud,
            gerente_id=current_user_id,
            data=data
        )
        
        if not resultado['success']:
            return jsonify(resultado), 400
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en rechazar_solicitud: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@solicitud_vacaciones_bp.route('/pendientes/count', methods=['GET'])
@jwt_required()
def contar_pendientes():
    """
    Contar solicitudes pendientes
    ---
    tags:
      - Vacaciones
    summary: Contar pendientes (Gerente/Admin)
    description: Cuenta cuántas solicitudes están en estatus PENDIENTE (estatus=1)
    security:
      - Bearer: []
    parameters:
      - name: sucursal_id
        in: query
        required: false
        schema:
          type: integer
          description: Filtrar por sucursal
    responses:
      200:
        description: Cantidad de pendientes
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                count:
                  type: integer
      403:
        description: Acceso denegado
      500:
        description: Error interno
    """
    try:
        # Endpoint requiere autenticación - ya está validado por @jwt_required()
        # Por ahora abierto a cualquier usuario autenticado
        
        sucursal_id = request.args.get('sucursal_id', type=int)
        
        resultado = SolicitudVacacionesService.contar_pendientes(sucursal_id)
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en contar_pendientes: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
