"""
PedidoController - API Endpoints para Gestión de Pedidos
Endpoints:
  POST   /api/pedidos              - Crear pedido Dine-in
  POST   /api/pedidos/para-llevar  - Crear pedido Takeaway
  GET    /api/pedidos/{id}         - Obtener pedido completo
  POST   /api/pedidos/{id}/items   - Agregar item a pedido
  PATCH  /api/pedidos/{id}/estado  - Cambiar estado (confirmar, preparacion, listo, entregado)
  GET    /api/sucursales/{sid}/pedidos - Listar pedidos de sucursal

Estados: 1=Creado, 2=Confirmado, 3=EnPreparacion, 4=Listo, 5=Entregado, 6=Cancelado
Inventory consumed ONLY at estado=3 (EnPreparacion)
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime
import logging

from src.services.operaciones.pedido_service import PedidoService
from src.dao.operaciones.pedido_dao import PedidoDAO
from src.schemas.pedido_schema import (
    PedidoCreateSchema,
    PedidoResponseSchema,
    PedidoListSchema,
    PedidoItemSchema,
    PedidoCambiarEstadoSchema
)
from src.core.db.session_manager import get_db_session
from src.models.operaciones.pedido_model import Pedido

logger = logging.getLogger(__name__)
bp = Blueprint('pedidos', __name__, url_prefix='/api/pedidos')


# ============================================================================
# POST /api/pedidos - Crear Pedido Dine-in
# ============================================================================

@bp.route('', methods=['POST'])
@jwt_required()
def crear_pedido_dine_in():
    """
    Crea un nuevo pedido tipo Dine-in (con mesa y reserva activa)
    ---
    tags:
      - Pedidos
    summary: "Crear Pedido Dine-in"
    description: Crea un pedido para cliente que come en el restaurante (con mesa). Requiere reserva activa en estado 1 o 2.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - sucursal_id
            - reserva_id
            - items
          properties:
            sucursal_id:
              type: integer
              description: ID de sucursal
              example: 1
            cliente_id:
              type: integer
              description: ID del cliente (opcional)
              example: 123
            tipo_pedido:
              type: integer
              description: Tipo (1=Dine-in, 2=Takeaway)
              example: 1
            canal:
              type: integer
              description: Canal (1=PWA, 2=Móvil)
              example: 2
            reserva_id:
              type: integer
              description: ID de reserva activa
              example: 456
            notas:
              type: string
              description: Notas especiales
              example: "Sin picante"
            items:
              type: array
              required: true
              items:
                type: object
                required:
                  - cantidad
                properties:
                  producto_id:
                    type: integer
                    description: ID producto (XOR con combo_id)
                    example: 10
                  combo_id:
                    type: integer
                    description: ID combo (XOR con producto_id)
                    example: null
                  cantidad:
                    type: integer
                    description: Cantidad (1-100)
                    example: 2
                  notas:
                    type: string
                    example: "Extra queso"
    responses:
      201:
        description: Pedido creado exitosamente
        schema:
          type: object
          properties:
            mensaje:
              type: string
            pedido:
              type: object
      400:
        description: Validación fallida
      404:
        description: Reserva no existe
    x-code-samples:
      - lang: curl
        source: |
          curl -X POST http://localhost:5000/api/pedidos \\
            -H "Authorization: Bearer YOUR_TOKEN" \\
            -H "Content-Type: application/json" \\
            -d '{
              "sucursal_id": 1,
              "cliente_id": 123,
              "reserva_id": 456,
              "notas": "Sin picante",
              "items": [
                {"producto_id": 10, "cantidad": 2, "notas": "Extra queso"},
                {"combo_id": 5, "cantidad": 1}
              ]
            }'
    """
    try:
        usuario_id = get_jwt_identity()
        
        # Validar payload
        schema = PedidoCreateSchema()
        try:
            datos = schema.load(request.get_json())
        except ValidationError as e:
            return jsonify({"error": "Validación fallida", "detalles": e.messages}), 400
        
        # Validar tipo_pedido = 1 (Dine-in)
        if datos.get('tipo_pedido') != 1:
            return jsonify({"error": "Este endpoint es para pedidos Dine-in (tipo_pedido=1)"}), 400
        
        # Crear pedido
        pedido = PedidoService.crear_pedido_dine_in(
            sucursal_id=datos['sucursal_id'],
            cliente_id=datos['cliente_id'],
            canal=datos['canal'],
            reserva_id=datos['reserva_id'],
            inicia_usuario_id=usuario_id,
            items=datos['items'],
            notas=datos.get('notas')
        )
        
        response_schema = PedidoResponseSchema()
        
        logger.info(f"Pedido Dine-in {pedido['id_pedido']} creado por usuario {usuario_id}")
        
        return jsonify({
            "mensaje": "Pedido creado exitosamente",
            "pedido": response_schema.dump(pedido)
        }), 201
    
    except ValueError as e:
        logger.error(f"Error de validación: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error al crear pedido Dine-in: {str(e)}")
        return jsonify({"error": "Error interno", "detalles": str(e)}), 500


# ============================================================================
# POST /api/pedidos/para-llevar - Crear Pedido Takeaway
# ============================================================================

@bp.route('/para-llevar', methods=['POST'])
@jwt_required()
def crear_pedido_takeaway():
    """
    Crea un nuevo pedido tipo Takeaway (sin mesa, crea reserva interna)
    ---
    tags:
      - Pedidos
    summary: "Crear Pedido Takeaway"
    description: Crea un pedido para cliente que recoge en sucursal (para llevar). Crea automáticamente una reserva interna con estatus=5 (recepcionista_id=NULL).
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - sucursal_id
            - cliente_id
            - items
          properties:
            sucursal_id:
              type: integer
              example: 1
            cliente_id:
              type: integer
              description: ID cliente (REQUERIDO para Takeaway)
              example: 123
            canal:
              type: integer
              example: 2
            notas:
              type: string
              example: "Sin cebolla"
            items:
              type: array
              required: true
              items:
                type: object
                properties:
                  producto_id:
                    type: integer
                  combo_id:
                    type: integer
                  cantidad:
                    type: integer
    responses:
      201:
        description: Pedido Takeaway creado
        schema:
          type: object
          properties:
            mensaje:
              type: string
            pedido:
              type: object
            reserva_interna_id:
              type: integer
      400:
        description: Validación fallida o cliente_id faltante
    x-code-samples:
      - lang: curl
        source: |
          curl -X POST http://localhost:5000/api/pedidos/para-llevar \\
            -H "Authorization: Bearer YOUR_TOKEN" \\
            -H "Content-Type: application/json" \\
            -d '{
              "sucursal_id": 1,
              "cliente_id": 123,
              "notas": "Sin cebolla",
              "items": [
                {"producto_id": 10, "cantidad": 2}
              ]
            }'
    """
    try:
        usuario_id = get_jwt_identity()
        
        # Validar payload (tipo_pedido debe ser 2)
        payload = request.get_json()
        payload['tipo_pedido'] = 2  # Forzar Takeaway
        
        schema = PedidoCreateSchema()
        try:
            datos = schema.load(payload)
        except ValidationError as e:
            return jsonify({"error": "Validación fallida", "detalles": e.messages}), 400
        
        # Validar cliente_id OBLIGATORIO para takeaway
        if not datos.get('cliente_id'):
            return jsonify({"error": "cliente_id es OBLIGATORIO para pedidos Takeaway"}), 400
        
        # Crear pedido takeaway
        pedido = PedidoService.crear_pedido_takeaway(
            sucursal_id=datos['sucursal_id'],
            cliente_id=datos['cliente_id'],
            canal=datos['canal'],
            inicia_usuario_id=usuario_id,
            items=datos['items'],
            notas=datos.get('notas')
        )
        
        response_schema = PedidoResponseSchema()
        
        logger.info(f"Pedido Takeaway {pedido['id_pedido']} creado por usuario {usuario_id}")
        
        return jsonify({
            "mensaje": "Pedido Takeaway creado exitosamente",
            "pedido": response_schema.dump(pedido),
            "reserva_interna_id": pedido.get('reserva_interna_id')
        }), 201
    
    except ValueError as e:
        logger.error(f"Error de validación: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error al crear pedido Takeaway: {str(e)}")
        return jsonify({"error": "Error interno", "detalles": str(e)}), 500


# ============================================================================
# GET /api/pedidos/{id} - Obtener Pedido Completo
# ============================================================================

@bp.route('/<int:pedido_id>', methods=['GET'])
@jwt_required()
def obtener_pedido(pedido_id):
    """
    Obtiene los detalles completos de un pedido con items e histórico
    ---
    tags:
      - Pedidos
    summary: "Obtener Pedido"
    description: Retorna el pedido completo incluyendo todos los items, histórico de estados, y detalles de consumo de inventario.
    parameters:
      - in: path
        name: pedido_id
        type: integer
        required: true
        description: ID del pedido
        example: 25
    responses:
      200:
        description: Pedido encontrado
        schema:
          type: object
          properties:
            pedido:
              type: object
      404:
        description: Pedido no existe
    x-code-samples:
      - lang: curl
        source: |
          curl -X GET http://localhost:5000/api/pedidos/25 \\
            -H "Authorization: Bearer YOUR_TOKEN"
    """
    try:
        pedido = PedidoService.obtener_pedido(pedido_id)
        
        response_schema = PedidoResponseSchema()
        
        logger.info(f"Pedido {pedido_id} obtenido")
        
        return jsonify({
            "pedido": response_schema.dump(pedido)
        }), 200
    
    except ValueError as e:
        logger.error(f"Pedido no encontrado: {str(e)}")
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error al obtener pedido: {str(e)}")
        return jsonify({"error": "Error interno", "detalles": str(e)}), 500


# ============================================================================
# POST /api/pedidos/{id}/items - Agregar Item a Pedido
# ============================================================================

@bp.route('/<int:pedido_id>/items', methods=['POST'])
@jwt_required()
def agregar_item_a_pedido(pedido_id):
    """
    Agrega un item (producto o combo) a un pedido en estado Creado
    ---
    tags:
      - Pedidos - Items
    summary: "Agregar Item a Pedido"
    description: Agrega un producto o combo a un pedido mientras está en estado Creado (1). Máximo 100 unidades por item.
    parameters:
      - in: path
        name: pedido_id
        type: integer
        required: true
        example: 25
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - cantidad
          properties:
            producto_id:
              type: integer
              description: ID producto (XOR con combo_id)
              example: 10
            combo_id:
              type: integer
              description: ID combo (XOR con producto_id)
            cantidad:
              type: integer
              description: Cantidad (1-100)
              example: 2
            notas:
              type: string
              example: "Extra queso"
    responses:
      201:
        description: Item agregado exitosamente
        schema:
          type: object
          properties:
            mensaje:
              type: string
            item:
              type: object
      400:
        description: Validación fallida o XOR violation
      404:
        description: Pedido no existe
    x-code-samples:
      - lang: curl
        source: |
          curl -X POST http://localhost:5000/api/pedidos/25/items \\
            -H "Authorization: Bearer YOUR_TOKEN" \\
            -H "Content-Type: application/json" \\
            -d '{
              "producto_id": 10,
              "cantidad": 2,
              "notas": "Extra queso"
            }'
    """
    try:
        # Validar payload
        payload = request.get_json()
        
        if not payload.get('producto_id') and not payload.get('combo_id'):
            return jsonify({"error": "Debe proporcionar producto_id o combo_id"}), 400
        if payload.get('producto_id') and payload.get('combo_id'):
            return jsonify({"error": "No puede proporcionar ambos: producto_id y combo_id"}), 400
        
        # Agregar item
        item = PedidoService.agregar_item(
            pedido_id=pedido_id,
            producto_id=payload.get('producto_id'),
            combo_id=payload.get('combo_id'),
            cantidad=payload.get('cantidad', 1),
            notas=payload.get('notas')
        )
        
        logger.info(f"Item agregado a pedido {pedido_id}: {item}")
        
        return jsonify({
            "mensaje": "Item agregado exitosamente",
            "item": item
        }), 201
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error al agregar item: {str(e)}")
        return jsonify({"error": "Error interno", "detalles": str(e)}), 500


# ============================================================================
# PATCH /api/pedidos/{id}/estado - Cambiar Estado de Pedido
# ============================================================================

@bp.route('/<int:pedido_id>/estado', methods=['PATCH'])
@jwt_required()
def cambiar_estado_pedido(pedido_id):
    """
    Cambia el estado de un pedido (confirmación, a cocina, listo, entregado, cancelado)
    ---
    tags:
      - Pedidos - Estados
    summary: "Cambiar Estado de Pedido (⚠️ CRITICAL: Inventory Consumed at Estado 3)"
    description: |
      Cambia el estado del pedido. IMPORTANTE: El paso a estado 3 (EnPreparacion) DISPARA EL CONSUMO DE INVENTARIO.
      
      Transiciones válidas:
      - 1 → 2 (Creado → Confirmado)
      - 2 → 3 (Confirmado → EnPreparacion) ⚠️ **INVENTORY CONSUMED HERE**
      - 3 → 4 (EnPreparacion → Listo)
      - 4 → 5 (Listo → Entregado)
      - Cualquiera → 6 (Cancelado, solo si estado ≤ 2)
      
      **FLUJO DE CONSUMO DE INVENTARIO (Estado 2→3):**
      1. Para cada item Producto: obtiene receta → consume insumos por FIFO
      2. Para cada item Combo: resuelve Combo→Productos→Recetas→Insumos → consume FIFO
      3. Si falta stock: ROLLBACK completo (atómico)
      4. Si éxito: crea Movimientos de auditoría
    parameters:
      - in: path
        name: pedido_id
        type: integer
        required: true
        example: 25
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - estado_pedido
          properties:
            estado_pedido:
              type: integer
              description: Nuevo estado (2, 3, 4, 5, o 6)
              example: 2
            comentario:
              type: string
              description: Comentario opcional
              example: "Pedido confirmado por cliente"
    responses:
      200:
        description: Estado actualizado exitosamente
        schema:
          type: object
          properties:
            mensaje:
              type: string
            pedido:
              type: object
      400:
        description: Validación fallida o stock insuficiente
      404:
        description: Pedido no existe
    x-code-samples:
      - lang: curl
        source: |
          curl -X PATCH http://localhost:5000/api/pedidos/25/estado \\
            -H "Authorization: Bearer YOUR_TOKEN" \\
            -H "Content-Type: application/json" \\
            -d '{
              "estado_pedido": 2,
              "comentario": "Confirmado por cliente"
            }'
      - lang: curl
        source: |
          curl -X PATCH http://localhost:5000/api/pedidos/25/estado \\
            -H "Authorization: Bearer YOUR_TOKEN" \\
            -H "Content-Type: application/json" \\
            -d '{
              "estado_pedido": 3,
              "comentario": "Enviado a cocina (INVENTORY CONSUMED HERE)"
            }'
    """
    try:
        usuario_id = get_jwt_identity()
        
        # Validar payload
        schema = PedidoCambiarEstadoSchema()
        try:
            datos = schema.load(request.get_json())
        except ValidationError as e:
            return jsonify({"error": "Validación fallida", "detalles": e.messages}), 400
        
        nuevo_estado = datos['estado_pedido']
        comentario = datos.get('comentario')
        
        # Obtener pedido actual
        pedido = PedidoDAO.obtener_pedido_completo(pedido_id)
        if not pedido:
            return jsonify({"error": f"Pedido {pedido_id} no existe"}), 404
        
        estado_actual = pedido['estado_pedido']
        
        # Procesar según nuevo estado
        if nuevo_estado == 2:  # Confirmación
            resultado = PedidoService.confirmar_pedido(pedido_id, usuario_id)
        
        elif nuevo_estado == 3:  # A preparación (INVENTORY CONSUMPTION HAPPENS HERE)
            try:
                resultado = PedidoService.cambiar_a_preparacion(pedido_id, usuario_id)
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
        
        elif nuevo_estado == 4:  # Listo
            resultado = PedidoService.cambiar_a_listo(pedido_id, usuario_id)
        
        elif nuevo_estado == 5:  # Entregado
            resultado = PedidoService.entregar_pedido(pedido_id, usuario_id)
        
        elif nuevo_estado == 6:  # Cancelado
            try:
                resultado = PedidoService.cancelar_pedido(pedido_id, usuario_id, comentario)
            except ValueError as e:
                return jsonify({"error": str(e)}), 400
        
        else:
            return jsonify({"error": f"Estado {nuevo_estado} no válido"}), 400
        
        response_schema = PedidoResponseSchema()
        
        logger.info(f"Pedido {pedido_id}: estado {estado_actual} → {nuevo_estado} por usuario {usuario_id}")
        
        return jsonify({
            "mensaje": f"Pedido actualizado a estado {nuevo_estado}",
            "pedido": response_schema.dump(resultado)
        }), 200
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error al cambiar estado: {str(e)}")
        return jsonify({"error": "Error interno", "detalles": str(e)}), 500


# ============================================================================
# GET /api/sucursales/{sucursal_id}/pedidos - Listar Pedidos
# ============================================================================

@bp.route('', methods=['GET'])
@jwt_required()
def listar_pedidos():
    """
    Lista pedidos de una sucursal con filtros opcionales
    ---
    tags:
      - Pedidos
    summary: "Listar Pedidos"
    description: Retorna lista de pedidos con filtros opcionales por estado y rango de fechas.
    parameters:
      - in: query
        name: sucursal_id
        type: integer
        required: true
        description: ID de sucursal
        example: 1
      - in: query
        name: estado
        type: integer
        description: Filtrar por estado (1-6, opcional)
        example: 3
      - in: query
        name: fecha_desde
        type: string
        description: Filtrar desde fecha (ISO format YYYY-MM-DD, opcional)
        example: "2025-11-01"
      - in: query
        name: fecha_hasta
        type: string
        description: Filtrar hasta fecha (ISO format YYYY-MM-DD, opcional)
        example: "2025-11-23"
    responses:
      200:
        description: Lista de pedidos
        schema:
          type: object
          properties:
            pedidos:
              type: array
              items:
                type: object
            total:
              type: integer
      400:
        description: Parámetros inválidos
    x-code-samples:
      - lang: curl
        source: |
          curl -X GET "http://localhost:5000/api/pedidos?sucursal_id=1&estado=3" \\
            -H "Authorization: Bearer YOUR_TOKEN"
    """
    try:
        sucursal_id = request.args.get('sucursal_id', type=int)
        if not sucursal_id:
            return jsonify({"error": "sucursal_id es requerido"}), 400
        
        estado = request.args.get('estado', type=int, default=None)
        fecha_desde = request.args.get('fecha_desde')
        fecha_hasta = request.args.get('fecha_hasta')
        
        # Parsear fechas si vienen
        try:
            fecha_desde = datetime.fromisoformat(fecha_desde) if fecha_desde else None
            fecha_hasta = datetime.fromisoformat(fecha_hasta) if fecha_hasta else None
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido (use ISO format YYYY-MM-DD)"}), 400
        
        # Listar
        pedidos, total = PedidoDAO.listar_pedidos_por_sucursal(
            sucursal_id=sucursal_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            estado=estado
        )
        
        list_schema = PedidoListSchema(many=True)
        
        logger.info(f"Listado de {len(pedidos)} pedidos para sucursal {sucursal_id}")
        
        return jsonify({
            "pedidos": list_schema.dump(pedidos),
            "total": total
        }), 200
    
    except Exception as e:
        logger.error(f"Error al listar pedidos: {str(e)}")
        return jsonify({"error": "Error interno", "detalles": str(e)}), 500
