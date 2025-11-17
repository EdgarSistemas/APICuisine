"""
PedidoController - Gestión de Pedidos y Consumo de Inventario
Endpoints: POST (crear), POST (agregar item), POST (confirmar cocina - CRITICAL),
GET (listar), GET/{id} (obtener), PATCH (cambiar estatus items)
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
import logging

from src.services.operaciones.pedido_service import PedidoService
from src.services.operaciones.inventario_service import InventarioService
from src.schemas.pedido_schema import (
    PedidoCreateSchema,
    PedidoItemCreateSchema,
    PedidoConfirmarItemsSchema
)
from src.core.utils.multitenant import (
    es_admin, 
    validar_acceso_sucursal, 
    agregar_filtro_sucursal,
    validar_pertenencia_sucursal,
    validar_sucursal_existe
)
from src.models import Pedido

logger = logging.getLogger(__name__)
bp = Blueprint('pedidos', __name__, url_prefix='/api/pedidos')


# ============================================================================
# POST /api/pedidos - Crear Pedido
# ============================================================================
@bp.route('', methods=['POST'])
@jwt_required()
def crear_pedido():
    """
    Crear pedido ligado a una reserva.
    ---
    tags:
      - Pedidos
    summary: Crear nuevo pedido
    description: Crea un nuevo pedido vinculado a una reserva. Validaciones automáticas para reserva existente y sin duplicados.
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - reserva_id
              - sucursal_id
              - inicia_usuario_id
            properties:
              reserva_id:
                type: integer
                description: ID de la reserva
                example: 15
              sucursal_id:
                type: integer
                description: ID de la sucursal
                example: 1
              inicia_usuario_id:
                type: integer
                description: ID del usuario que inicia (cliente, mesero, etc)
                example: 5
              cliente_id:
                type: integer
                description: ID del cliente (opcional)
              tipo_pedido:
                type: integer
                description: 1=Dine-in, 2=Pickup, 3=Delivery (default 1)
                default: 1
              canal:
                type: integer
                description: 1=Mesero, 2=Sistema, 3=App (default 2)
                default: 2
              notas:
                type: string
                description: Notas del pedido
    responses:
      201:
        description: Pedido creado exitosamente
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                pedido:
                  type: object
      400:
        description: Validación fallida o error en datos
      403:
        description: Sin acceso a la sucursal
      404:
        description: Reserva no existe
      409:
        description: Pedido ya existe para esta reserva
    """
    try:
        # Validar schema
        schema = PedidoCreateSchema()
        data = schema.load(request.json)
        
        # Usuario autenticado
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario')
        
        # Verificar acceso a sucursal
        if not validar_acceso_sucursal(usuario_id, data['sucursal_id']):
            return jsonify({"error": "No tienes acceso a esta sucursal"}), 403
        
        # Usar servicio para crear pedido con validaciones
        result = PedidoService.crear_pedido(
            reserva_id=data['reserva_id'],
            sucursal_id=data['sucursal_id'],
            inicia_usuario_id=data['inicia_usuario_id']
        )
        
        if not result['success']:
            if 'no existe' in result.get('error', ''):
                return jsonify({"error": result['error']}), 404
            elif 'ya existe' in result.get('error', ''):
                return jsonify({"error": result['error']}), 409
            else:
                return jsonify({"error": result['error']}), 400
        
        return jsonify({
            "message": "Pedido creado exitosamente",
            "pedido": result['data']
        }), 201
        
    except ValidationError as e:
        logger.error(f"Error de validación en crear_pedido: {e.messages}")
        return jsonify({"error": "Datos inválidos", "detalles": e.messages}), 400
    except Exception as e:
        logger.error(f"Error en crear_pedido: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


# ============================================================================
# GET /api/pedidos - Listar Pedidos
# ============================================================================
@bp.route('', methods=['GET'])
@jwt_required()
def obtener_pedidos():
    """
    Listar pedidos con filtros opcionales.
    ---
    tags:
      - Pedidos
    summary: Obtener lista de pedidos
    description: Retorna lista de pedidos. Cocina ve solo items en cocina. Multi-tenant filtering automático.
    parameters:
      - in: query
        name: sucursal_id
        type: integer
        description: Filtrar por sucursal (opcional)
      - in: query
        name: estatus
        type: integer
        description: Filtrar por estatus (1=Abierto, 2=Enviado, 3=Entregado, 4=Cancelado)
    responses:
      200:
        description: Lista de pedidos
        content:
          application/json:
            schema:
              type: object
              properties:
                pedidos:
                  type: array
                  items:
                    type: object
                total:
                  type: integer
    """
    try:
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario')
        
        # TODO: Implementar lógica de rol para Cocina
        # Por ahora listar todos
        
        from src.core.db.session_manager import get_db_session
        with get_db_session() as session:
            query = session.query(Pedido)
            
            # Aplicar filtro multi-tenant
            query = agregar_filtro_sucursal(query, Pedido, usuario_id)
            
            # Filtros opcionales
            sucursal_id = request.args.get('sucursal_id', type=int)
            if sucursal_id:
                query = query.filter(Pedido.sucursal_id == sucursal_id)
            
            estatus = request.args.get('estatus', type=int)
            if estatus:
                query = query.filter(Pedido.estado_pedido == estatus)
            
            pedidos = query.order_by(Pedido.created_at.desc()).all()
            
            return jsonify({
                "pedidos": [p.to_dict() for p in pedidos],
                "total": len(pedidos)
            }), 200
            
    except Exception as e:
        logger.error(f"Error listando pedidos: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


# ============================================================================
# GET /api/pedidos/{pedido_id} - Obtener Pedido por ID
# ============================================================================
@bp.route('/<int:pedido_id>', methods=['GET'])
@jwt_required()
def obtener_pedido(pedido_id):
    """
    Obtener detalle completo de un pedido.
    ---
    tags:
      - Pedidos
    summary: Obtener detalle de pedido
    description: Retorna datos completos del pedido incluyendo items, con serialización completa.
    parameters:
      - in: path
        name: pedido_id
        type: integer
        required: true
        description: ID del pedido
    responses:
      200:
        description: Datos del pedido
        content:
          application/json:
            schema:
              type: object
      403:
        description: Sin acceso a esta sucursal
      404:
        description: Pedido no existe
    """
    try:
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario')
        
        result = PedidoService.obtener_pedido(pedido_id)
        
        if not result['success']:
            return jsonify({"error": result['error']}), 404
        
        # Validar acceso a sucursal
        sucursal_id = result['data'].get('sucursal_id')
        if not validar_acceso_sucursal(usuario_id, sucursal_id):
            return jsonify({"error": "No tienes acceso a esta sucursal"}), 403
        
        return jsonify(result['data']), 200
        
    except Exception as e:
        logger.error(f"Error en obtener_pedido {pedido_id}: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


# ============================================================================
# POST /api/pedidos/{pedido_id}/items - Agregar Item a Pedido
# ============================================================================
@bp.route('/<int:pedido_id>/items', methods=['POST'])
@jwt_required()
def agregar_item(pedido_id):
    """
    Agregar producto o combo al pedido.
    ---
    tags:
      - Pedidos - Items
    summary: Agregar item a pedido
    description: Permite agregar productos o combos a un pedido. Un item puede tener muchos productos antes de confirmar a cocina.
    parameters:
      - in: path
        name: pedido_id
        type: integer
        required: true
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - cantidad
            properties:
              producto_id:
                type: integer
                description: ID del producto (requerido si no hay combo_id)
              combo_id:
                type: integer
                description: ID del combo (requerido si no hay producto_id)
              cantidad:
                type: integer
                description: Cantidad (1-100)
                example: 2
              precio:
                type: number
                description: Precio unitario (opcional)
                example: 150.00
    responses:
      201:
        description: Item agregado exitosamente
      400:
        description: Validación fallida o producto/combo inválido
      404:
        description: Pedido no existe
    """
    try:
        schema = PedidoItemCreateSchema()
        data = schema.load(request.json)
        
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario')
        
        result = PedidoService.agregar_item(
            pedido_id=pedido_id,
            producto_id=data.get('producto_id'),
            combo_id=data.get('combo_id'),
            cantidad=data['cantidad'],
            precio=data.get('precio')
        )
        
        if not result['success']:
            if 'no existe' in result.get('error', ''):
                return jsonify({"error": result['error']}), 404
            else:
                return jsonify({"error": result['error']}), 400
        
        return jsonify({
            "message": "Item agregado exitosamente",
            "item": result['data']
        }), 201
        
    except ValidationError as e:
        logger.error(f"Error de validación en agregar_item: {e.messages}")
        return jsonify({"error": "Datos inválidos", "detalles": e.messages}), 400
    except Exception as e:
        logger.error(f"Error en agregar_item: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


# ============================================================================
# POST /api/pedidos/{pedido_id}/confirmar-items - CRITICAL: Enviar a Cocina
# ============================================================================
@bp.route('/<int:pedido_id>/confirmar-items', methods=['POST'])
@jwt_required()
def confirmar_items_a_cocina(pedido_id):
    """
    Confirmar items para enviar a cocina - *** TRIGGERS INVENTORY CONSUMPTION ***.
    ---
    tags:
      - Pedidos - Items
      - Inventario
    summary: Confirmar items y consumir inventario (CRITICAL)
    description: |
      **⚠️ CRITICAL OPERATION ⚠️**
      
      Confirma items para ir a cocina. ESTO DISPARA EL CONSUMO DE INVENTARIO.
      - Cambio de estatus items: 2 (Confirmado) → 3 (EnCocina)
      - ATOMIC: Todo o nada (all-or-nothing)
      - IRREVERSIBLE: Una vez consumido, NO hay rollback automático
      - FIFO: Usa lotes más próximos a vencer primero
      - Si falla inventario: Revierte estatus items automaticamente
      
    parameters:
      - in: path
        name: pedido_id
        type: integer
        required: true
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - item_ids
            properties:
              item_ids:
                type: array
                items:
                  type: integer
                description: IDs de items a confirmar (máx 50)
                example: [1, 2, 3]
    responses:
      200:
        description: Items confirmados e inventario consumido exitosamente
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                items_confirmados:
                  type: integer
                movimientos_inventario:
                  type: array
                  description: Movimientos de inventario realizados
      400:
        description: Validación fallida o inventario insuficiente
      403:
        description: Sin acceso a sucursal
      404:
        description: Pedido o items no existen
    """
    try:
        schema = PedidoConfirmarItemsSchema()
        data = schema.load(request.json)
        
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario')
        
        logger.info(f"INICIO: Confirmar items {data['item_ids']} de pedido {pedido_id}")
        
        # Obtener pedido para validar sucursal
        pedido_result = PedidoService.obtener_pedido(pedido_id)
        if not pedido_result['success']:
            return jsonify({"error": pedido_result['error']}), 404
        
        sucursal_id = pedido_result['data'].get('sucursal_id')
        if not validar_acceso_sucursal(usuario_id, sucursal_id):
            return jsonify({"error": "No tienes acceso a esta sucursal"}), 403
        
        # Confirmar items a cocina (TRIGGERS INVENTORY)
        result = PedidoService.confirmar_items_a_cocina(
            pedido_id=pedido_id,
            item_ids=data['item_ids'],
            usuario_id=usuario_id
        )
        
        if not result['success']:
            error_msg = result.get('error', '')
            
            # Inventario insuficiente
            if 'insuficiente' in error_msg.lower() or 'no hay' in error_msg.lower():
                logger.warning(f"INVENTORY FAILED: {error_msg}")
                return jsonify({
                    "error": "Inventario insuficiente",
                    "details": error_msg
                }), 400
            
            # Pedido/items no existen
            if 'no existe' in error_msg:
                return jsonify({"error": error_msg}), 404
            
            # Otro error
            logger.error(f"CONFIRMAR ITEMS ERROR: {error_msg}")
            return jsonify({"error": error_msg}), 400
        
        logger.info(f"SUCCESS: Items confirmados, inventario consumido. Movimientos: {len(result['data'].get('movimientos', []))}")
        
        return jsonify({
            "message": "Items confirmados y enviados a cocina",
            "items_confirmados": result['data'].get('items_confirmados', 0),
            "movimientos_inventario": result['data'].get('movimientos', [])
        }), 200
        
    except ValidationError as e:
        logger.error(f"Error de validación en confirmar_items_a_cocina: {e.messages}")
        return jsonify({"error": "Datos inválidos", "detalles": e.messages}), 400
    except Exception as e:
        logger.error(f"EXCEPTION en confirmar_items_a_cocina: {str(e)}", exc_info=True)
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


# ============================================================================
# PATCH /api/pedidos/{pedido_id}/items/{item_id}/listo - Marcar como Listo (Cocina)
# ============================================================================
@bp.route('/<int:pedido_id>/items/<int:item_id>/listo', methods=['PATCH'])
@jwt_required()
def marcar_item_listo(pedido_id, item_id):
    """
    Marcar item como listo (Cocina → Listo).
    ---
    tags:
      - Pedidos - Items
    summary: Marcar item como listo
    description: Transición de estatus 3 (EnCocina) → 4 (Listo). Típicamente llamado desde la estación de cocina.
    parameters:
      - in: path
        name: pedido_id
        type: integer
        required: true
      - in: path
        name: item_id
        type: integer
        required: true
    responses:
      200:
        description: Item marcado como listo
      400:
        description: Item no está en cocina
      404:
        description: Pedido o item no existe
    """
    try:
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario')
        
        result = PedidoService.marcar_listo(
            pedido_id=pedido_id,
            item_id=item_id
        )
        
        if not result['success']:
            if 'no existe' in result.get('error', ''):
                return jsonify({"error": result['error']}), 404
            else:
                return jsonify({"error": result['error']}), 400
        
        return jsonify({
            "message": "Item marcado como listo",
            "item": result['data']
        }), 200
        
    except Exception as e:
        logger.error(f"Error en marcar_item_listo: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


# ============================================================================
# PUT /api/pedidos/{pedido_id} - Actualizar Pedido (notas, etc)
# ============================================================================
@bp.route('/<int:pedido_id>', methods=['PUT'])
@jwt_required()
def actualizar_pedido(pedido_id):
    """
    Actualizar notas u otros campos del pedido.
    ---
    tags:
      - Pedidos
    summary: Actualizar pedido
    description: Permite actualizar campos como notas del pedido.
    parameters:
      - in: path
        name: pedido_id
        type: integer
        required: true
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              notas:
                type: string
                description: Notas del pedido
    responses:
      200:
        description: Pedido actualizado
      404:
        description: Pedido no existe
      403:
        description: Sin acceso a sucursal
    """
    try:
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario')
        data = request.get_json()
        
        from src.core.db.session_manager import get_db_session
        with get_db_session() as session:
            pedido = session.query(Pedido).get(pedido_id)
            
            if not pedido:
                return jsonify({"error": "Pedido no existe"}), 404
            
            # Validar acceso
            if not validar_acceso_sucursal(usuario_id, pedido.sucursal_id):
                return jsonify({"error": "No tienes acceso a esta sucursal"}), 403
            
            # Actualizar campos permitidos
            if 'notas' in data:
                pedido.notas = data['notas']
            
            session.commit()
            logger.info(f"Pedido {pedido_id} actualizado por usuario {usuario_id}")
            
            return jsonify({
                "message": "Pedido actualizado",
                "pedido": pedido.to_dict()
            }), 200
            
    except Exception as e:
        logger.error(f"Error actualizando pedido {pedido_id}: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


# ============================================================================
# DELETE /api/pedidos/{pedido_id} - Cancelar Pedido (Soft Delete)
# ============================================================================
@bp.route('/<int:pedido_id>', methods=['DELETE'])
@jwt_required()
def eliminar_pedido(pedido_id):
    """
    Cancelar pedido - SOLO ADMIN.
    ---
    tags:
      - Pedidos
    summary: Cancelar pedido
    description: Soft delete - cambia estatus a 4 (Cancelado). Solo administradores.
    parameters:
      - in: path
        name: pedido_id
        type: integer
        required: true
    responses:
      200:
        description: Pedido cancelado
      403:
        description: Sin permisos (solo admins)
      404:
        description: Pedido no existe
    """
    try:
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario')
        
        # Validar que es admin
        if not es_admin(usuario_id):
            return jsonify({"error": "Solo administradores pueden cancelar pedidos"}), 403
        
        from src.core.db.session_manager import get_db_session
        with get_db_session() as session:
            pedido = session.query(Pedido).get(pedido_id)
            
            if not pedido:
                return jsonify({"error": "Pedido no existe"}), 404
            
            # Soft delete: cambiar estado a cancelado
            pedido.estado_pedido = 4  # 4 = Cancelado
            session.commit()
            logger.info(f"Pedido {pedido_id} cancelado por admin {usuario_id}")
            
            return jsonify({
                "message": "Pedido cancelado exitosamente"
            }), 200
            
    except Exception as e:
        logger.error(f"Error cancelando pedido {pedido_id}: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500
