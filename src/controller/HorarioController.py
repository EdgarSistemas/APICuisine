"""
HorarioController - Endpoints para gestión de horarios (ADMIN)
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.rrhh.horario_service import HorarioService
import logging

logger = logging.getLogger(__name__)

horario_bp = Blueprint('horarios', __name__, url_prefix='/api/horarios')


@horario_bp.route('', methods=['POST'])
@jwt_required()
def crear_horario():
    """
    Crear horario con sus detalles
    ---
    tags:
      - Horarios
    summary: Crear un nuevo horario con sus detalles
    description: Permite crear un horario con múltiples detalles de días y turnos
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - sucursal_id
            - clave
            - nombre
          properties:
            sucursal_id:
              type: integer
              example: 1
            clave:
              type: string
              example: "TURNO_MANANA"
            nombre:
              type: string
              example: "Turno Matutino"
            descripcion:
              type: string
              example: "9AM-5PM"
            detalles:
              type: array
              items:
                type: object
                properties:
                  dia_semana:
                    type: integer
                    example: 1
                  hora_inicio:
                    type: string
                    example: "09:00"
                  hora_fin:
                    type: string
                    example: "17:00"
                  turno_idx:
                    type: integer
                    example: 1
                  tolerancia_min:
                    type: integer
                    example: 10
    responses:
      201:
        description: Horario creado exitosamente
      400:
        description: Error en los datos enviados
      403:
        description: Acceso denegado
      500:
        description: Error interno del servidor
    """
    try:
        # current_user = get_jwt_identity()
        # user_role = current_user.get('rol') if isinstance(current_user, dict) else None
        
        # if user_role not in ['Administrador', 'Gerente']:
        #     return jsonify({
        #         "success": False,
        #         "error": "Acceso denegado. Se requiere rol ADMIN o GERENTE"
        #     }), 403
        
        data = request.get_json()
        resultado = HorarioService.crear_horario(data)
        
        if not resultado['success']:
            return jsonify(resultado), 400
        
        return jsonify(resultado), 201
        
    except Exception as e:
        logger.error(f"Error en crear_horario: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@horario_bp.route('/id/<int:id_horario>', methods=['GET'])
@jwt_required()
def obtener_horario(id_horario):
    """
    Obtener horario por ID con sus detalles completos
    ---
    tags:
      - Horarios
    summary: Obtener un horario específico con detalles
    description: Retorna el horario con su encabezado y todos sus detalles de días/turnos
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id_horario
        required: true
        type: integer
        description: ID del horario
    responses:
      200:
        description: Horario encontrado con detalles
      404:
        description: Horario no encontrado
      500:
        description: Error interno del servidor
    """
    try:
        resultado = HorarioService.obtener_horario(id_horario)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 404
        
    except Exception as e:
        logger.error(f"Error en obtener_horario: {str(e)}")
        return jsonify({
            "success": False,
            "error": "SERVER_ERROR",
            "message": str(e)
        }), 500

@horario_bp.route('usuarios_asignados/<int:id_horario>', methods=['GET'])
@jwt_required()
def obtener_horario_usuarios_asignados(id_horario):
    """
    Obtener total de usuarios asignados a un horario específico
    ---
    tags:
      - Horarios
    summary: Obtener total de usuarios asignados a un horario
    description: Retorna el conteo de usuarios que tienen asignado el horario especificado
    parameters:
      - in: path
        name: id_horario
        required: true
        type: integer
        description: ID del horario
    responses:
      200:
        description: Conteo de usuarios asignados
      404:
        description: Horario no encontrado
      500:
        description: Error interno del servidor
    """
    try:
        resultado = HorarioService.obtener_usuarios_asignados(id_horario)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 404
        
    except Exception as e:
        logger.error(f"Error en obtener_horario_usuarios_asignados: {str(e)}")
        return jsonify({
            "success": False,
            "error": "SERVER_ERROR",
            "message": str(e)
        }), 500

@horario_bp.route('/<int:sucursal_id>', methods=['GET'])
@jwt_required()
def listar_horarios(sucursal_id):
    """
    Listar horarios de una sucursal
    ---
    tags:
      - Horarios
    summary: Listar horarios por sucursal
    description: Retorna una lista de horarios activos de una sucursal específica, con count de usuarios asignados
    parameters:
      - in: path
        name: sucursal_id
        type: integer
        required: true
        description: ID de la sucursal
    responses:
      200:
        description: Lista de horarios con usuarios asignados
        schema:
          type: object
          properties:
            success:
              type: boolean
            horarios:
              type: array
              items:
                type: object
                properties:
                  id_horario:
                    type: integer
                  sucursal_id:
                    type: integer
                  clave:
                    type: string
                  nombre:
                    type: string
                  descripcion:
                    type: string
                  usuarios_asignados:
                    type: integer
                    description: Total de usuarios con este horario asignado
                  es_activo:
                    type: boolean
            count:
              type: integer
      500:
        description: Error interno del servidor
    """
    try:
        resultado = HorarioService.listar_horarios_con_usuarios(sucursal_id)
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Error en listar_horarios: {str(e)}")
        return jsonify({
            "success": False,
            "error": "SERVER_ERROR",
            "message": str(e)
        }), 500


@horario_bp.route('/id/<int:id_horario>', methods=['PUT'])
@jwt_required()
def actualizar_horario(id_horario):
    """
    Actualizar información del horario
    ---
    tags:
      - Horarios
    summary: Actualizar un horario existente
    description: Permite actualizar la información básica del horario (no los detalles)
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id_horario
        required: true
        type: integer
        description: ID del horario a actualizar
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            clave:
              type: string
              example: "TURNO_MANANA_2"
            nombre:
              type: string
              example: "Turno Matutino Modificado"
            descripcion:
              type: string
              example: "Nueva descripción"
    responses:
      200:
        description: Horario actualizado exitosamente
      400:
        description: Error en los datos enviados
      403:
        description: Acceso denegado
      500:
        description: Error interno del servidor
    """
    try:
        # current_user = get_jwt_identity()
        # user_role = current_user.get('rol') if isinstance(current_user, dict) else None
        
        # if user_role not in ['ADMIN', 'GERENTE']:
        #     return jsonify({
        #         "success": False,
        #         "error": "Acceso denegado. Se requiere rol ADMIN o GERENTE"
        #     }), 403
        
        data = request.get_json()
        resultado = HorarioService.actualizar_horario(id_horario, data)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            # Determinar código de estado según el error
            error_msg = resultado.get('error', '').lower()
            if 'no encontrado' in error_msg or 'no existe' in error_msg:
                status = 404
            else:
                status = 400
            return jsonify(resultado), status
        
    except Exception as e:
        logger.error(f"Error en actualizar_horario: {str(e)}")
        return jsonify({
            "success": False,
            "error": "SERVER_ERROR",
            "message": str(e)
        }), 500


@horario_bp.route('/id/<int:id_horario>', methods=['DELETE'])
@jwt_required()
def desactivar_horario(id_horario):
    """
    Desactivar horario (soft delete)
    ---
    tags:
      - Horarios
    summary: Desactivar un horario
    description: Marca el horario como inactivo sin eliminarlo de la base de datos
    security:
      - Bearer: []
    parameters:
      - in: path
        name: id_horario
        required: true
        type: integer
        description: ID del horario a desactivar
    responses:
      200:
        description: Horario desactivado exitosamente
      400:
        description: Error al desactivar el horario
      404:
        description: Horario no encontrado
      500:
        description: Error interno del servidor
    """
    try:
        resultado = HorarioService.desactivar_horario(id_horario)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            error_msg = resultado.get('error', '').lower()
            if 'no encontrado' in error_msg or 'no existe' in error_msg:
                status = 404
            else:
                status = 400
            return jsonify(resultado), status
        
    except Exception as e:
        logger.error(f"Error en desactivar_horario: {str(e)}")
        return jsonify({
            "success": False,
            "error": "SERVER_ERROR",
            "message": str(e)
        }), 500


@horario_bp.route('/usuario/<int:usuario_id>', methods=['GET'])
@jwt_required()
def obtener_horario_usuario(usuario_id):
    """
    Obtener horario activo de un usuario con detalles completos
    ---
    tags:
      - Horarios
    summary: Obtener horario asignado a un usuario
    description: Retorna el horario activo del usuario con todos sus detalles (días, horas, tolerancia)
    security:
      - Bearer: []
    parameters:
      - in: path
        name: usuario_id
        required: true
        type: integer
        description: ID del usuario
    responses:
      200:
        description: Horario del usuario encontrado
      404:
        description: Usuario no tiene horario asignado
      500:
        description: Error interno del servidor
    """
    try:
        resultado = HorarioService.obtener_horario_usuario(usuario_id)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 404
        
    except Exception as e:
        logger.error(f"Error en obtener_horario_usuario: {str(e)}")
        return jsonify({
            "success": False,
            "error": "SERVER_ERROR",
            "message": str(e)
        }), 500


@horario_bp.route('/turno-codigo', methods=['POST'])
@jwt_required()
def obtener_codigo_turno():
    """
    Obtener código de turno para un horario y fecha específicos
    ---
    tags:
      - Horarios
    summary: Obtener código de turno/asistencia
    description: Retorna el código generado para check-in de un horario en una fecha específica
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - horario_id
            - fecha
          properties:
            horario_id:
              type: integer
              example: 3
              description: ID del horario
            fecha:
              type: string
              example: "2025-11-12"
              description: Fecha en formato YYYY-MM-DD
    responses:
      200:
        description: Código de turno encontrado
      400:
        description: Parámetros faltantes o formato inválido
      404:
        description: No existe código para ese horario y fecha
      500:
        description: Error interno del servidor
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No se recibieron datos"
            }), 400
        
        horario_id = data.get('horario_id')
        fecha = data.get('fecha')
        
        if not horario_id:
            return jsonify({
                "success": False,
                "error": "El campo horario_id es requerido"
            }), 400
        
        if not fecha:
            return jsonify({
                "success": False,
                "error": "El campo fecha es requerido (formato: YYYY-MM-DD)"
            }), 400
        
        resultado = HorarioService.obtener_codigo_turno(horario_id, fecha)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            error_msg = resultado.get('error', '').lower()
            if 'no se encontró' in error_msg or 'no existe' in error_msg:
                status = 404
            elif 'formato' in error_msg or 'inválido' in error_msg:
                status = 400
            else:
                status = 400
            return jsonify(resultado), status
        
    except Exception as e:
        logger.error(f"Error en obtener_codigo_turno: {str(e)}")
        return jsonify({
            "success": False,
            "error": "SERVER_ERROR",
            "message": str(e)
        }), 500


@horario_bp.route('/asignar', methods=['POST'])
@jwt_required()
def asignar_horario_usuario():
    """
    Asignar horario a un usuario
    ---
    tags:
      - Horarios
    summary: Asignar horario a empleado
    description: Asigna un horario existente a un usuario. Desactiva asignaciones previas automáticamente.
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - usuario_id
            - horario_id
            - fecha_inicio
          properties:
            usuario_id:
              type: integer
              example: 15
              description: ID del usuario (empleado)
            horario_id:
              type: integer
              example: 2
              description: ID del horario a asignar
            fecha_inicio:
              type: string
              example: "2025-11-12"
              description: Fecha de inicio de vigencia (YYYY-MM-DD)
            fecha_fin:
              type: string
              example: "2025-12-31"
              description: Fecha de fin de vigencia (opcional, null = indefinido)
    responses:
      201:
        description: Horario asignado exitosamente
        schema:
          type: object
          properties:
            success:
              type: boolean
            asignacion:
              type: object
              properties:
                id_usuario_horario:
                  type: integer
                usuario_id:
                  type: integer
                horario_id:
                  type: integer
                fecha_inicio:
                  type: string
                fecha_fin:
                  type: string
            message:
              type: string
      400:
        description: Datos inválidos o fechas incorrectas
      404:
        description: Horario no encontrado o inactivo
      500:
        description: Error interno del servidor
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No se recibieron datos"
            }), 400
        
        # Validar campos requeridos
        usuario_id = data.get('usuario_id')
        horario_id = data.get('horario_id')
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin')  # Opcional
        
        if not usuario_id:
            return jsonify({
                "success": False,
                "error": "El campo usuario_id es requerido"
            }), 400
        
        if not horario_id:
            return jsonify({
                "success": False,
                "error": "El campo horario_id es requerido"
            }), 400
        
        if not fecha_inicio:
            return jsonify({
                "success": False,
                "error": "El campo fecha_inicio es requerido"
            }), 400
        
        resultado = HorarioService.asignar_horario_a_usuario(
            usuario_id=usuario_id,
            horario_id=horario_id,
            fecha_inicio_str=fecha_inicio,
            fecha_fin_str=fecha_fin
        )
        
        if resultado['success']:
            return jsonify(resultado), 201
        else:
            error_msg = resultado.get('error', '').lower()
            if 'no encontrado' in error_msg or 'no está activo' in error_msg:
                status = 404
            else:
                status = 400
            return jsonify(resultado), status
        
    except Exception as e:
        logger.error(f"Error en asignar_horario_usuario: {str(e)}")
        return jsonify({
            "success": False,
            "error": "SERVER_ERROR",
            "message": str(e)
        }), 500


@horario_bp.route('/generar-codigos', methods=['POST'])
def generar_codigos():
    """
    Generar códigos de turno para el día especificado
    ---
    tags:
      - Horarios
    summary: Generar códigos de asistencia diarios
    description: |
      Genera códigos de turno de 6 caracteres para todos los HorarioDetalles que 
      coincidan con el día de la semana especificado. Si no se especifica fecha, 
      genera para el día actual. Este endpoint está diseñado para ser llamado 
      automáticamente por Azure Functions cada día.
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: false
        schema:
          type: object
          properties:
            fecha:
              type: string
              example: "2025-11-13"
              description: Fecha para generar códigos (YYYY-MM-DD). Si no se envía, usa hoy.
            expira_horas:
              type: integer
              example: 2
              description: Horas de validez del código desde hora_inicio del turno. Default 2.
    responses:
      200:
        description: Códigos generados exitosamente
        schema:
          type: object
          properties:
            fecha:
              type: string
            dia_semana:
              type: integer
            codigos_generados:
              type: array
              items:
                type: object
                properties:
                  id_turno_clave:
                    type: integer
                  horario_id:
                    type: integer
                  horario_detalle_id:
                    type: integer
                  codigo:
                    type: string
                  fecha:
                    type: string
                  hora_inicio:
                    type: string
                  hora_fin:
                    type: string
                  expira_en:
                    type: string
                  ya_existia:
                    type: boolean
            codigos_existentes:
              type: array
              description: Códigos que ya existían para esta fecha
            total_codigos:
              type: integer
      400:
        description: Formato de fecha inválido
      500:
        description: Error al generar códigos
    """
    try:
        data = request.get_json() or {}
        
        fecha = data.get('fecha')
        expira_horas = data.get('expira_horas', 2)
        
        resultado, status = HorarioService.generar_codigos_turno(fecha, expira_horas)
        return jsonify(resultado), status
        
    except Exception as e:
        logger.error(f"Error en generar_codigos: {str(e)}")
        return jsonify({
            "error": "SERVER_ERROR",
            "message": str(e)
        }), 500
