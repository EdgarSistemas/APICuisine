"""
Controlador para logs de auditoría
"""

import logging
from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from flask_jwt_extended import jwt_required

from src.core.auth.jwt_helpers import get_current_user, admin_required
from src.services.auditoria.log_service import LogService, log_action
from src.schemas.auditoria_schema import (
    LogFiltrosSchema, EstadisticasSchema, LimpiarLogsSchema
)

logger = logging.getLogger(__name__)

# Crear blueprint
auditoria_bp = Blueprint('auditoria', __name__, url_prefix='/api/auditoria')

# Instanciar servicio
log_service = LogService()

@auditoria_bp.route('/logs', methods=['GET'])
@jwt_required()
@admin_required
def listar_logs():
    """
    Listar logs de auditoría con filtros opcionales (solo administradores)
    ---
    tags:
      - Auditoría
    summary: Listar logs de auditoría
    description: Obtiene logs de auditoría con filtros. Requiere permisos de administrador.
    parameters:
      - name: entidad
        in: query
        type: string
        required: false
        description: Filtrar por entidad (Usuario, Producto, etc.)
        example: "Usuario"
      - name: accion
        in: query
        type: string
        required: false
        description: Filtrar por acción (CREATE, UPDATE, DELETE, etc.)
        example: "LOGIN"
      - name: usuario_id
        in: query
        type: integer
        required: false
        description: Filtrar por ID de usuario
        example: 1
      - name: origen
        in: query
        type: string
        required: false
        description: Filtrar por origen
        enum: ['API', 'WEB', 'MOBILE', 'SYSTEM']
        example: "API"
      - name: fecha_desde
        in: query
        type: string
        required: false
        description: Fecha desde (formato ISO)
        example: "2025-10-26T00:00:00"
      - name: fecha_hasta
        in: query
        type: string
        required: false
        description: Fecha hasta (formato ISO)
        example: "2025-10-26T23:59:59"
    responses:
      200:
        description: Lista de logs obtenida exitosamente
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: array
              items:
                type: object
                properties:
                  id_log_accion:
                    type: integer
                    example: 1
                  origen:
                    type: string
                    example: "API"
                  entidad:
                    type: string
                    example: "Usuario"
                  entidad_id:
                    type: string
                    example: "123"
                  accion:
                    type: string
                    example: "LOGIN"
                  usuario_id:
                    type: integer
                    example: 1
                  detalle:
                    type: object
                    example: {"email": "user@example.com", "ip": "192.168.1.1"}
                  created_at:
                    type: string
                    example: "2025-10-26T20:30:00"
      400:
        description: Parámetros inválidos
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "VALIDATION_ERROR"
            message:
              type: string
              example: "Parámetros inválidos"
            details:
              type: object
      403:
        description: Sin permisos de administrador
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "ADMIN_REQUIRED"
            message:
              type: string
              example: "Se requieren permisos de administrador"
      500:
        description: Error interno del servidor
    """
    try:
        # Validar parámetros
        schema = LogFiltrosSchema()
        filtros = schema.load(request.args.to_dict())
        
        # Remover parámetros de paginación si existen
        filtros.pop('page', None)
        filtros.pop('per_page', None)
        
        # Limpiar filtros vacíos
        filtros = {k: v for k, v in filtros.items() if v is not None}
        
        # Obtener todos los logs sin paginación
        logs = log_service.obtener_todos_los_logs(filtros)
        
        # Log de la consulta
        usuario_actual = get_current_user()
        log_action('LogAccion', 'CONSULTA', 
                  detalle={'filtros': filtros},
                  usuario_id=usuario_actual['user_id'])
        
        return jsonify({
            'success': True,
            'data': logs
        })
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'VALIDATION_ERROR',
            'message': 'Parámetros inválidos',
            'details': e.messages
        }), 400
        
    except Exception as e:
        logger.error(f"Error al listar logs: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500

@auditoria_bp.route('/estadisticas', methods=['GET'])
@jwt_required()
@admin_required
def obtener_estadisticas():
    """
    Obtener estadísticas de logs de auditoría (solo administradores)
    ---
    tags:
      - Auditoría
    summary: Estadísticas de auditoría
    description: Obtiene estadísticas de actividad del sistema en un período determinado. Requiere permisos de administrador.
    parameters:
      - name: dias
        in: query
        type: integer
        required: false
        description: Período en días para las estadísticas (máximo 365)
        default: 30
        example: 7
    responses:
      200:
        description: Estadísticas obtenidas exitosamente
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                periodo_dias:
                  type: integer
                  example: 30
                total_logs:
                  type: integer
                  example: 1250
                por_entidad:
                  type: array
                  items:
                    type: object
                    properties:
                      entidad:
                        type: string
                        example: "Usuario"
                      count:
                        type: integer
                        example: 450
                por_accion:
                  type: array
                  items:
                    type: object
                    properties:
                      accion:
                        type: string
                        example: "LOGIN"
                      count:
                        type: integer
                        example: 320
                top_usuarios:
                  type: array
                  items:
                    type: object
                    properties:
                      usuario_id:
                        type: integer
                        example: 1
                      count:
                        type: integer
                        example: 125
      400:
        description: Parámetros inválidos
      403:
        description: Sin permisos de administrador
      500:
        description: Error interno del servidor
    """
    try:
        # Validar parámetros
        schema = EstadisticasSchema()
        datos = schema.load(request.args.to_dict())
        
        # Obtener estadísticas
        estadisticas = log_service.obtener_estadisticas(datos['dias'])
        
        # Log de la consulta
        usuario_actual = get_current_user()
        log_action('LogAccion', 'ESTADISTICAS', 
                  detalle={'periodo_dias': datos['dias']},
                  usuario_id=usuario_actual['user_id'])
        
        return jsonify({
            'success': True,
            'data': estadisticas
        })
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'VALIDATION_ERROR',
            'message': 'Parámetros inválidos',
            'details': e.messages
        }), 400
        
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500

@auditoria_bp.route('/limpiar', methods=['POST'])
@jwt_required()
@admin_required
def limpiar_logs():
    """
    Limpiar logs antiguos del sistema (solo administradores)
    ---
    tags:
      - Auditoría
    summary: Limpiar logs antiguos
    description: Elimina logs de auditoría más antiguos que el número de días especificado. Requiere permisos de administrador.
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - dias
          properties:
            dias:
              type: integer
              minimum: 30
              maximum: 3650
              description: Eliminar logs más antiguos que estos días (mínimo 30)
              example: 90
    responses:
      200:
        description: Logs limpiados exitosamente
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Se eliminaron 125 logs anteriores a 90 días"
            eliminados:
              type: integer
              example: 125
      400:
        description: Datos inválidos
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "VALIDATION_ERROR"
            message:
              type: string
              example: "Datos inválidos"
            details:
              type: object
      403:
        description: Sin permisos de administrador
      500:
        description: Error al limpiar logs
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "CLEANUP_ERROR"
            message:
              type: string
              example: "Error al limpiar logs"
    """
    try:
        # Validar datos
        schema = LimpiarLogsSchema()
        datos = schema.load(request.get_json() or {})
        
        # Limpiar logs
        resultado = log_service.limpiar_logs_antiguos(datos['dias'])
        
        # Log de la operación
        usuario_actual = get_current_user()
        log_action('LogAccion', 'LIMPIEZA', 
                  detalle={
                      'dias_antiguedad': datos['dias'],
                      'logs_eliminados': resultado.get('eliminados', 0)
                  },
                  usuario_id=usuario_actual['user_id'])
        
        if resultado['success']:
            return jsonify({
                'success': True,
                'message': resultado['message'],
                'eliminados': resultado['eliminados']
            })
        else:
            return jsonify({
                'success': False,
                'error': 'CLEANUP_ERROR',
                'message': 'Error al limpiar logs',
                'details': resultado.get('error')
            }), 500
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'VALIDATION_ERROR',
            'message': 'Datos inválidos',
            'details': e.messages
        }), 400
        
    except Exception as e:
        logger.error(f"Error al limpiar logs: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500

@auditoria_bp.route('/test', methods=['POST'])
@jwt_required()
@admin_required
def test_log():
    """
    Endpoint de prueba para generar un log manualmente (solo administradores)
    ---
    tags:
      - Auditoría
    summary: Generar log de prueba
    description: Crea un log de auditoría de prueba para verificar que el sistema funciona correctamente. Requiere permisos de administrador.
    parameters:
      - name: body
        in: body
        required: false
        schema:
          type: object
          properties:
            entidad:
              type: string
              description: Nombre de la entidad para el log de prueba
              default: "TestEntity"
              example: "TestEntity"
            accion:
              type: string
              description: Acción para el log de prueba
              default: "TEST"
              example: "TEST"
            entidad_id:
              type: string
              description: ID de la entidad (opcional)
              example: "123"
            detalle:
              type: object
              description: Detalles adicionales (opcional)
              example: {"prueba": true, "timestamp": "2025-10-26T20:30:00"}
    responses:
      200:
        description: Log de prueba generado exitosamente
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Log de prueba generado exitosamente"
      403:
        description: Sin permisos de administrador
      500:
        description: Error al generar log de prueba
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "LOG_ERROR"
            message:
              type: string
              example: "Error al generar log de prueba"
    """
    try:
        datos = request.get_json() or {}
        usuario_actual = get_current_user()
        
        # Generar log de prueba
        exito = log_action(
            entidad=datos.get('entidad', 'TestEntity'),
            accion=datos.get('accion', 'TEST'),
            entidad_id=datos.get('entidad_id'),
            detalle=datos.get('detalle', {'test': True, 'generado_por': 'endpoint_test'}),
            usuario_id=usuario_actual['user_id']
        )
        
        if exito:
            return jsonify({
                'success': True,
                'message': 'Log de prueba generado exitosamente'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'LOG_ERROR',
                'message': 'Error al generar log de prueba'
            }), 500
        
    except Exception as e:
        logger.error(f"Error en test de log: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'Error interno del servidor'
        }), 500