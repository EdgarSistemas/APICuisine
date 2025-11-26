"""
CampaniaController - Gestión de Campañas, Cupones y CRM
Endpoints: 
- Campañas: CRUD de campañas de marketing
- Cupones: Asignación, listado y validación de cupones para clientes
- Métricas CRM: Segmentación de clientes para campañas inteligentes
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validates, ValidationError
from datetime import datetime
import logging

from src.services.marketing.campania_service import CampaniaService
from src.core.utils.multitenant import es_admin

logger = logging.getLogger(__name__)
bp = Blueprint('campanias', __name__, url_prefix='/api/campanias')


# ============================================================================
# SCHEMAS DE VALIDACIÓN
# ============================================================================

class CampaniaCreateSchema(Schema):
    """Schema para crear campaña"""
    nombre_campania = fields.Str(required=True)
    porcentaje_desc = fields.Float(required=True)
    codigo = fields.Str(required=False, allow_none=True)
    
    @validates('porcentaje_desc')
    def validate_porcentaje(self, value):
        if value <= 0 or value > 100:
            raise ValidationError("porcentaje_desc debe estar entre 0.01 y 100")


class AsignarCuponSchema(Schema):
    """Schema para asignar cupón a cliente"""
    cliente_id = fields.Int(required=True)
    campania_id = fields.Int(required=True)
    fecha_vigencia = fields.DateTime(required=False, allow_none=True)


class ValidarCuponSchema(Schema):
    """Schema para validar cupón"""
    codigo = fields.Str(required=True)
    cliente_id = fields.Int(required=True)


# ============================================================================
# ENDPOINTS DE CAMPAÑAS
# ============================================================================

@bp.route('', methods=['POST'])
@jwt_required()
def crear_campania():
    """
    Crear nueva campaña de marketing.
    ---
    tags:
      - CRM - Campañas
    summary: Crear campaña
    description: Crear nueva campaña promocional con código de cupón opcional. Solo administradores.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - nombre_campania
            - porcentaje_desc
          properties:
            nombre_campania:
              type: string
              description: "Nombre de la campaña. Ej: Promo Navidad 2025"
            porcentaje_desc:
              type: number
              description: "Porcentaje de descuento (1-100). Ej: 10 = 10%"
            codigo:
              type: string
              description: "Código único del cupón (opcional). Ej: NAVIDAD2025"
    responses:
      201:
        description: Campaña creada exitosamente
      400:
        description: Datos inválidos
      403:
        description: Sin permisos de administrador
    """
    try:
        current_user = get_jwt_identity()
        
        schema = CampaniaCreateSchema()
        data = schema.load(request.json)
        
        result = CampaniaService.crear_campania(
            usuario_id=current_user,
            nombre_campania=data['nombre_campania'],
            porcentaje_desc=data['porcentaje_desc'],
            codigo=data.get('codigo')
        )
        
        if not result['success']:
            return jsonify({"error": result['error']}), 400
        
        return jsonify({
            "message": "Campaña creada exitosamente",
            "campania": result['data']
        }), 201
        
    except ValidationError as e:
        return jsonify({"error": "Datos inválidos", "detalles": e.messages}), 400
    except Exception as e:
        logger.error(f"Error creando campaña: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@bp.route('', methods=['GET'])
@jwt_required()
def listar_campanias():
    """
    Listar campañas activas de marketing.
    ---
    tags:
      - CRM - Campañas
    summary: Listar campañas activas
    description: |
      Lista todas las campañas activas.
      Cada campaña incluye:
      - total_cupones: Cantidad de cupones asignados
      - total_cupones_usados: Cantidad de cupones ya utilizados
    responses:
      200:
        description: Lista de campañas activas
    """
    try:
        result = CampaniaService.listar_campanias_activas()
        
        if not result['success']:
            return jsonify({"error": result['error']}), 400
        
        return jsonify(result['data']), 200
        
    except Exception as e:
        logger.error(f"Error listando campañas: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@bp.route('/<int:campania_id>', methods=['GET'])
@jwt_required()
def obtener_campania(campania_id):
    """
    Obtener detalle de una campaña.
    ---
    tags:
      - CRM - Campañas
    summary: Obtener campaña
    parameters:
      - in: path
        name: campania_id
        type: integer
        required: true
    responses:
      200:
        description: Detalles de la campaña
      404:
        description: Campaña no encontrada
    """
    try:
        result = CampaniaService.obtener_campania(campania_id)
        
        if not result['success']:
            return jsonify({"error": result['error']}), 404
        
        return jsonify(result['data']), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo campaña: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@bp.route('/<int:campania_id>/activar', methods=['POST'])
@jwt_required()
def activar_campania(campania_id):
    """
    Activar campaña (estatus = 1).
    ---
    tags:
      - CRM - Campañas
    summary: Activar campaña
    parameters:
      - in: path
        name: campania_id
        type: integer
        required: true
    responses:
      200:
        description: Campaña activada
      403:
        description: Sin permisos
      404:
        description: Campaña no encontrada
    """
    try:
        current_user = get_jwt_identity()
        
        result = CampaniaService.activar_campania(campania_id)
        
        if not result['success']:
            return jsonify({"error": result['error']}), 404
        
        return jsonify({
            "message": "Campaña activada",
            "campania": result['data']
        }), 200
        
    except Exception as e:
        logger.error(f"Error activando campaña: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@bp.route('/<int:campania_id>/desactivar', methods=['POST'])
@jwt_required()
def desactivar_campania(campania_id):
    """
    Desactivar campaña (estatus = 0).
    ---
    tags:
      - CRM - Campañas
    summary: Desactivar campaña
    parameters:
      - in: path
        name: campania_id
        type: integer
        required: true
    responses:
      200:
        description: Campaña desactivada
      403:
        description: Sin permisos
      404:
        description: Campaña no encontrada
    """
    try:
        current_user = get_jwt_identity()
        
        result = CampaniaService.desactivar_campania(campania_id)
        
        if not result['success']:
            return jsonify({"error": result['error']}), 404
        
        return jsonify({
            "message": "Campaña desactivada",
            "campania": result['data']
        }), 200
        
    except Exception as e:
        logger.error(f"Error desactivando campaña: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


# ============================================================================
# ENDPOINTS DE CUPONES
# ============================================================================

@bp.route('/cupones/asignar', methods=['POST'])
@jwt_required()
def asignar_cupon():
    """
    Asignar cupón de campaña a un cliente.
    ---
    tags:
      - CRM - Cupones
    summary: Asignar cupón a cliente
    description: Asigna un cupón de campaña a un cliente específico. Solo administradores.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - cliente_id
            - campania_id
          properties:
            cliente_id:
              type: integer
              description: "ID del cliente"
            campania_id:
              type: integer
              description: "ID de la campaña"
            fecha_vigencia:
              type: string
              format: date-time
              description: "Fecha límite de uso del cupón (opcional)"
    responses:
      201:
        description: Cupón asignado exitosamente
      400:
        description: Error de validación
      403:
        description: Sin permisos
    """
    try:
        current_user = get_jwt_identity()
        
        schema = AsignarCuponSchema()
        data = schema.load(request.json)
        
        result = CampaniaService.asignar_cupon(
            cliente_id=data['cliente_id'],
            campania_id=data['campania_id'],
            fecha_vigencia=data.get('fecha_vigencia')
        )
        
        if not result['success']:
            return jsonify({"error": result['error']}), 400
        
        return jsonify({
            "message": "Cupón asignado exitosamente",
            "asignacion": result['data']
        }), 201
        
    except ValidationError as e:
        return jsonify({"error": "Datos inválidos", "detalles": e.messages}), 400
    except Exception as e:
        logger.error(f"Error asignando cupón: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@bp.route('/cupones/usuario/<int:cliente_id>', methods=['GET'])
@jwt_required()
def listar_cupones_usuario(cliente_id):
    """
    Listar cupones de un cliente.
    ---
    tags:
      - CRM - Cupones
    summary: Listar cupones de cliente
    description: Lista los cupones asignados a un cliente. El cliente puede ver sus propios cupones, admins pueden ver de cualquiera.
    parameters:
      - in: path
        name: cliente_id
        type: integer
        required: true
      - in: query
        name: solo_disponibles
        type: boolean
        default: true
        description: "Si true, solo cupones vigentes y no usados"
    responses:
      200:
        description: Lista de cupones del cliente
      403:
        description: Sin acceso a este cliente
    """
    try:
        current_user = get_jwt_identity()
        
        # El cliente puede ver sus propios cupones, admins pueden ver de cualquiera
        if current_user != cliente_id and not es_admin(current_user):
            return jsonify({"error": "No tienes acceso a los cupones de este cliente"}), 403
        
        solo_disponibles = request.args.get('solo_disponibles', 'true').lower() == 'true'
        
        result = CampaniaService.listar_cupones_cliente(
            cliente_id=cliente_id,
            solo_disponibles=solo_disponibles
        )
        
        if not result['success']:
            return jsonify({"error": result['error']}), 400
        
        return jsonify({
            "cupones": result['data'],
            "total": len(result['data'])
        }), 200
        
    except Exception as e:
        logger.error(f"Error listando cupones: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@bp.route('/cupones/mis-cupones', methods=['GET'])
@jwt_required()
def mis_cupones():
    """
    Listar mis cupones disponibles.
    ---
    tags:
      - CRM - Cupones
    summary: Mis cupones
    description: Lista los cupones disponibles del usuario autenticado.
    parameters:
      - in: query
        name: solo_disponibles
        type: boolean
        default: true
    responses:
      200:
        description: Lista de mis cupones
    """
    try:
        current_user = get_jwt_identity()
        
        solo_disponibles = request.args.get('solo_disponibles', 'true').lower() == 'true'
        
        result = CampaniaService.listar_cupones_cliente(
            cliente_id=current_user,
            solo_disponibles=solo_disponibles
        )
        
        if not result['success']:
            return jsonify({"error": result['error']}), 400
        
        return jsonify({
            "cupones": result['data'],
            "total": len(result['data'])
        }), 200
        
    except Exception as e:
        logger.error(f"Error listando mis cupones: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@bp.route('/cupones/validar', methods=['POST'])
@jwt_required()
def validar_cupon():
    """
    Validar cupón antes de aplicar en pago.
    ---
    tags:
      - CRM - Cupones
    summary: Validar cupón
    description: |
      Valida si un cupón es válido para un cliente.
      
      Validaciones:
      1. Código de cupón existe
      2. Campaña está activa
      3. Cupón asignado al cliente
      4. Cupón no usado previamente
      5. Cupón dentro de fecha de vigencia (timezone México)
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - codigo
            - cliente_id
          properties:
            codigo:
              type: string
              description: "Código del cupón. Ej: NAVIDAD2025"
            cliente_id:
              type: integer
              description: "ID del cliente que quiere usar el cupón"
    responses:
      200:
        description: Resultado de validación
        schema:
          type: object
          properties:
            valido:
              type: boolean
            error:
              type: string
            campania:
              type: object
            porcentaje_desc:
              type: number
    """
    try:
        schema = ValidarCuponSchema()
        data = schema.load(request.json)
        
        result = CampaniaService.validar_cupon(
            codigo=data['codigo'],
            cliente_id=data['cliente_id']
        )
        
        if not result['success']:
            return jsonify({"error": result['error']}), 400
        
        if result['valido']:
            return jsonify({
                "valido": True,
                "campania": result['data']['campania'],
                "porcentaje_desc": float(result['data']['porcentaje_desc']),
                "campania_usuario_id": result['data']['campania_usuario_id']
            }), 200
        else:
            return jsonify({
                "valido": False,
                "error": result.get('error', 'Cupón no válido')
            }), 200
        
    except ValidationError as e:
        return jsonify({"error": "Datos inválidos", "detalles": e.messages}), 400
    except Exception as e:
        logger.error(f"Error validando cupón: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


# ============================================================================
# MÉTRICAS CRM - Segmentación de Clientes
# ============================================================================

@bp.route('/metricas/clientes-vip', methods=['POST'])
@jwt_required()
def metrica_clientes_vip():
    """
    Obtener TOP clientes por gasto total (VIP).
    ---
    tags:
      - CRM - Métricas
    summary: Clientes VIP (Alto Consumo)
    description: |
      Obtiene los clientes que más han gastado (suma de pagos).
      Útil para programas de lealtad y trato preferencial.
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            top_n:
              type: integer
              default: 20
              description: "Número de clientes TOP a retornar"
    responses:
      200:
        description: Lista de clientes VIP
      403:
        description: Sin permisos de administrador
    """
    try:
        current_user = get_jwt_identity()
        
        payload = request.get_json() or {}
        top_n = payload.get('top_n', 20)
        
        result = CampaniaService.obtener_clientes_vip(top_n=top_n)
        
        if not result['success']:
            return jsonify({"error": result['error']}), 400
        
        return jsonify({
            "metrica": result['metrica'],
            "descripcion": result['descripcion'],
            "clientes": result['data'],
            "total": len(result['data'])
        }), 200
        
    except Exception as e:
        logger.error(f"Error en métrica clientes VIP: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@bp.route('/metricas/frecuentes', methods=['POST'])
@jwt_required()
def metrica_clientes_frecuentes():
    """
    Obtener clientes con mayor frecuencia de visitas.
    ---
    tags:
      - CRM - Métricas
    summary: Clientes Frecuentes
    description: |
      Obtiene los clientes con más pedidos y reservas.
      Útil para ofertas de fidelización.
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            top_n:
              type: integer
              default: 20
              description: "Número de clientes TOP a retornar"
    responses:
      200:
        description: Lista de clientes frecuentes
      403:
        description: Sin permisos de administrador
    """
    try:
        current_user = get_jwt_identity()
        
        payload = request.get_json() or {}
        top_n = payload.get('top_n', 20)
        
        result = CampaniaService.obtener_clientes_frecuentes(top_n=top_n)
        
        if not result['success']:
            return jsonify({"error": result['error']}), 400
        
        return jsonify({
            "metrica": result['metrica'],
            "descripcion": result['descripcion'],
            "clientes": result['data'],
            "total": len(result['data'])
        }), 200
        
    except Exception as e:
        logger.error(f"Error en métrica clientes frecuentes: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@bp.route('/metricas/inactivos', methods=['POST'])
@jwt_required()
def metrica_clientes_inactivos():
    """
    Obtener clientes inactivos (sin comprar en X días).
    ---
    tags:
      - CRM - Métricas
    summary: Clientes Inactivos
    description: |
      Obtiene clientes que no han comprado en cierto tiempo.
      Útil para campañas de reactivación ("Te extrañamos").
      
      Niveles de riesgo:
      - EN_RIESGO: 30-59 días sin comprar
      - INACTIVO: 60-89 días sin comprar
      - PERDIDO: 90+ días sin comprar
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            dias_sin_comprar:
              type: integer
              default: 30
              description: "Días mínimos sin actividad"
    responses:
      200:
        description: Lista de clientes inactivos
      403:
        description: Sin permisos de administrador
    """
    try:
        current_user = get_jwt_identity()
        
        payload = request.get_json() or {}
        dias_sin_comprar = payload.get('dias_sin_comprar', 30)
        
        result = CampaniaService.obtener_clientes_inactivos(dias_sin_comprar=dias_sin_comprar)
        
        if not result['success']:
            return jsonify({"error": result['error']}), 400
        
        return jsonify({
            "metrica": result['metrica'],
            "descripcion": result['descripcion'],
            "clientes": result['data'],
            "total": len(result['data'])
        }), 200
        
    except Exception as e:
        logger.error(f"Error en métrica clientes inactivos: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@bp.route('/metricas/nuevos', methods=['POST'])
@jwt_required()
def metrica_clientes_nuevos():
    """
    Obtener clientes nuevos (recién registrados o con pocos pedidos).
    ---
    tags:
      - CRM - Métricas
    summary: Clientes Nuevos
    description: |
      Obtiene clientes registrados recientemente o con pocos pedidos.
      Útil para campañas de bienvenida y primera compra.
      
      Etapas:
      - SIN_PEDIDOS: 0 pedidos (oportunidad primera conversión)
      - PRIMERA_COMPRA: 1 pedido (enviar encuesta satisfacción)
      - EN_ADOPCION: 2-3 pedidos (promociones fidelización)
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            dias_registro:
              type: integer
              default: 30
              description: "Días desde registro para considerar 'nuevo'"
    responses:
      200:
        description: Lista de clientes nuevos
      403:
        description: Sin permisos de administrador
    """
    try:
        current_user = get_jwt_identity()
        
        payload = request.get_json() or {}
        dias_registro = payload.get('dias_registro', 30)
        
        result = CampaniaService.obtener_clientes_nuevos(dias_registro=dias_registro)
        
        if not result['success']:
            return jsonify({"error": result['error']}), 400
        
        return jsonify({
            "metrica": result['metrica'],
            "descripcion": result['descripcion'],
            "clientes": result['data'],
            "total": len(result['data'])
        }), 200
        
    except Exception as e:
        logger.error(f"Error en métrica clientes nuevos: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@bp.route('/metricas/por-canal', methods=['POST'])
@jwt_required()
def metrica_clientes_por_canal():
    """
    Segmentar clientes por canal preferido.
    ---
    tags:
      - CRM - Métricas
    summary: Clientes por Canal
    description: |
      Segmenta clientes según su canal de consumo preferido.
      Útil para marketing dirigido por canal.
      
      Canales:
      - RESERVA_PREFERIDO: Prefieren hacer reserva
      - MESA_PREFERIDO: Consumen en restaurante
      - TAKEAWAY_PREFERIDO: Prefieren recoger
      - DELIVERY_PREFERIDO: Prefieren delivery
      - MIXTO: Sin preferencia clara
    responses:
      200:
        description: Lista de clientes segmentados por canal
      403:
        description: Sin permisos de administrador
    """
    try:
        current_user = get_jwt_identity()
        
        result = CampaniaService.obtener_clientes_por_canal()
        
        if not result['success']:
            return jsonify({"error": result['error']}), 400
        
        # Agrupar por canal para resumen
        resumen_canales = {}
        for cliente in result['data']:
            canal = cliente.get('canal_preferido', 'MIXTO')
            if canal not in resumen_canales:
                resumen_canales[canal] = 0
            resumen_canales[canal] += 1
        
        return jsonify({
            "metrica": result['metrica'],
            "descripcion": result['descripcion'],
            "clientes": result['data'],
            "total": len(result['data']),
            "resumen_canales": resumen_canales
        }), 200
        
    except Exception as e:
        logger.error(f"Error en métrica clientes por canal: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


# ============================================================================
# GENERAR CAMPAÑA DESDE MÉTRICA
# ============================================================================

@bp.route('/generar-desde-metrica', methods=['POST'])
@jwt_required()
def generar_campania_desde_metrica():
    """
    Crear campaña y asignar cupones a clientes de una métrica.
    ---
    tags:
      - CRM - Métricas
    summary: Generar Campaña desde Métrica
    description: |
      Flujo completo:
      1. Crea la campaña con el código especificado
      2. Asigna cupones a todos los clientes seleccionados
      
      Uso típico:
      1. Llamar endpoint de métrica (ej: /metricas/inactivos)
      2. Revisar clientes retornados
      3. Seleccionar IDs de clientes target
      4. Llamar este endpoint con la lista de IDs
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - nombre_campania
            - porcentaje_desc
            - codigo
            - cliente_ids
          properties:
            nombre_campania:
              type: string
              description: "Nombre de la campaña. Ej: Reactivación Noviembre"
            porcentaje_desc:
              type: number
              description: "Porcentaje de descuento (1-100)"
            codigo:
              type: string
              description: "Código del cupón. Ej: VUELVE15"
            cliente_ids:
              type: array
              items:
                type: integer
              description: "Lista de IDs de clientes a asignar"
            fecha_vigencia:
              type: string
              format: date-time
              description: "Fecha límite de uso (opcional)"
    responses:
      201:
        description: Campaña creada y cupones asignados
      400:
        description: Error de validación
      403:
        description: Sin permisos de administrador
    """
    try:
        current_user = get_jwt_identity()
        
        payload = request.get_json() or {}
        
        # Validaciones básicas
        nombre_campania = payload.get('nombre_campania')
        porcentaje_desc = payload.get('porcentaje_desc')
        codigo = payload.get('codigo')
        cliente_ids = payload.get('cliente_ids', [])
        fecha_vigencia_str = payload.get('fecha_vigencia')
        
        if not nombre_campania:
            return jsonify({"error": "nombre_campania es requerido"}), 400
        
        if not porcentaje_desc or porcentaje_desc <= 0 or porcentaje_desc > 100:
            return jsonify({"error": "porcentaje_desc debe estar entre 0.01 y 100"}), 400
        
        if not codigo:
            return jsonify({"error": "codigo es requerido"}), 400
        
        if not cliente_ids or len(cliente_ids) == 0:
            return jsonify({"error": "Debe seleccionar al menos un cliente"}), 400
        
        # Parsear fecha si viene
        fecha_vigencia = None
        if fecha_vigencia_str:
            try:
                fecha_vigencia = datetime.fromisoformat(fecha_vigencia_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({"error": "Formato de fecha_vigencia inválido (usar ISO 8601)"}), 400
        
        result = CampaniaService.generar_campania_desde_metrica(
            usuario_id=current_user,
            nombre_campania=nombre_campania,
            porcentaje_desc=porcentaje_desc,
            codigo=codigo,
            cliente_ids=cliente_ids,
            fecha_vigencia=fecha_vigencia
        )
        
        if not result['success']:
            return jsonify({"error": result['error']}), 400
        
        return jsonify({
            "message": "Campaña generada y cupones asignados exitosamente",
            "campania": result['data']['campania'],
            "asignaciones": result['data']['asignaciones']
        }), 201
        
    except Exception as e:
        logger.error(f"Error generando campaña desde métrica: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500
