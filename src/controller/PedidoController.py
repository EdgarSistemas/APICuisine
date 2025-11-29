"""
PedidoController - API Endpoints para Gestión de Pedidos

Sistema de Estados (0-5):
  Pedido:
    0 = Iniciado (pedido recién creado)
    3 = Completo (usuario cierra el pedido)
    4 = Cancelado
    5 = Pagado

  PedidoItem:
    1 = EnCocina (item creado, inventario consumido)
    2 = Listo (preparado por cocina)
    3 = Completo (cerrado)
    4 = Cancelado
    5 = Pagado

Flujo:
  Pedido:     0 (crear) → 3 (cerrar) → 5 (pagar via PagoController)
  PedidoItem: 1 (crear+inventario) → 2 (cocina) → 3 (cerrar) → 5 (pagar)
  
  Takeaway: Cuando cocina marca todos items como Listo (2), auto-paga a 5

Endpoints (solo acciones de pedidos):
  POST   /api/pedidos                - Crear pedido Dine-in (estado=0, items=1)
  POST   /api/pedidos/para-llevar    - Crear pedido Takeaway
  GET    /api/pedidos/{id}           - Obtener pedido completo
  POST   /api/pedidos/{id}/items     - Agregar item (va directo a EnCocina, consume inventario)
  PATCH  /api/pedidos/{id}/completar - Cerrar pedido (0→3, items 2→3)
  PATCH  /api/pedidos/{id}/cancelar  - Cancelar pedido (0→4)
  POST   /api/pedidos/listar         - Listar pedidos
  GET    /api/pedidos/activos        - Pedidos activos

NOTA: 
  - Marcar items como Listo (1→2) está en CocinaController
  - Pagar pedido (3→5) está en PagoController:
      POST /api/pagos               - Crear pago
      POST /api/pagos/{id}/marcar-pagado - Confirmar pago y transicionar pedido a 5
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
    PedidoListSchema
)

logger = logging.getLogger(__name__)
bp = Blueprint('pedidos', __name__, url_prefix='/api/pedidos')


# ============================================================================
# POST /api/pedidos - Crear Pedido Dine-in
# ============================================================================
@bp.route('', methods=['POST'])
@jwt_required()
def crear_pedido_dine_in():
    """
    Crear pedido Dine-in (con mesa y reserva)
    ---
    tags:
      - Pedidos
    summary: Crear Pedido Dine-in
    description: |
      Crea pedido para cliente en restaurante.
      - Pedido se crea en estado 0 (Iniciado)
      - Items se crean en estado 1 (EnCocina) y CONSUMEN INVENTARIO inmediatamente
      - Requiere reserva activa (estatus 1 o 2)
      - mesa_id se obtiene automáticamente de la reserva
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
              example: 1
            cliente_id:
              type: integer
              example: 123
            canal:
              type: integer
              description: "1=PWA, 2=Móvil, 3=Presencial"
              example: 2
            reserva_id:
              type: integer
              example: 456
            notas:
              type: string
              example: "Sin picante"
            items:
              type: array
              items:
                type: object
                properties:
                  producto_id:
                    type: integer
                  combo_id:
                    type: integer
                  cantidad:
                    type: integer
                    example: 2
                  notas:
                    type: string
    responses:
      201:
        description: Pedido creado (estado=0, items en EnCocina=1)
      400:
        description: Error de validación
    """
    try:
        usuario_id = get_jwt_identity()
        
        schema = PedidoCreateSchema()
        try:
            datos = schema.load(request.get_json())
        except ValidationError as e:
            return jsonify({"error": "Validación fallida", "detalles": e.messages}), 400
        
        if datos.get('tipo_pedido') != 1:
            return jsonify({"error": "Este endpoint es para Dine-in (tipo_pedido=1)"}), 400
        
        pedido = PedidoService.crear_pedido_dine_in(
            sucursal_id=datos['sucursal_id'],
            cliente_id=datos['cliente_id'],
            canal=datos['canal'],
            reserva_id=datos['reserva_id'],
            inicia_usuario_id=usuario_id,
            items=datos['items'],
            notas=datos.get('notas')
        )
        
        logger.info(f"Pedido Dine-in {pedido['id_pedido']} creado, items en EnCocina")
        
        # Verificar si hubo errores de consumo
        advertencias = pedido.pop('advertencias_consumo', None)
        
        response = {
            "mensaje": "Pedido creado - items en cocina",
            "pedido": PedidoResponseSchema().dump(pedido)
        }
        
        if advertencias:
            response["advertencias_consumo"] = advertencias
            response["mensaje"] = "Pedido creado - ALGUNOS ITEMS NO CONSUMIERON INVENTARIO"
            logger.warning(f"Pedido {pedido['id_pedido']} con errores de consumo: {advertencias}")
        else:
            response["mensaje"] = "Pedido creado - items en cocina, inventario consumido"
        
        return jsonify(response), 201
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error crear pedido: {str(e)}")
        return jsonify({"error": "Error interno", "detalles": str(e)}), 500


# ============================================================================
# POST /api/pedidos/para-llevar - Crear Pedido Takeaway
# ============================================================================
@bp.route('/para-llevar', methods=['POST'])
@jwt_required()
def crear_pedido_takeaway():
    """
    Crear pedido Takeaway (para llevar)
    ---
    tags:
      - Pedidos
    summary: Crear Pedido Takeaway
    description: |
      Crea pedido para llevar (sin mesa).
      - Crea reserva interna automáticamente (estatus=5)
      - Pedido se crea en estado 0 (Iniciado)
      - Items se crean en estado 1 (EnCocina) y CONSUMEN INVENTARIO
      - Cuando cocina marca todos items como Listo (2), SE AUTO-PAGA a 5
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
            cliente_id:
              type: integer
              description: REQUERIDO para Takeaway
            canal:
              type: integer
            notas:
              type: string
            items:
              type: array
              items:
                type: object
    responses:
      201:
        description: Pedido Takeaway creado
      400:
        description: cliente_id faltante o error validación
    """
    try:
        usuario_id = get_jwt_identity()
        
        payload = request.get_json()
        payload['tipo_pedido'] = 2  # Forzar Takeaway
        
        schema = PedidoCreateSchema()
        try:
            datos = schema.load(payload)
        except ValidationError as e:
            return jsonify({"error": "Validación fallida", "detalles": e.messages}), 400
        
        if not datos.get('cliente_id'):
            return jsonify({"error": "cliente_id es OBLIGATORIO para Takeaway"}), 400
        
        pedido = PedidoService.crear_pedido_takeaway(
            sucursal_id=datos['sucursal_id'],
            cliente_id=datos['cliente_id'],
            canal=datos['canal'],
            inicia_usuario_id=usuario_id,
            items=datos['items'],
            notas=datos.get('notas')
        )
        
        logger.info(f"Pedido Takeaway {pedido['id_pedido']} creado")
        
        return jsonify({
            "mensaje": "Pedido Takeaway creado - auto-pago cuando cocina termine",
            "pedido": PedidoResponseSchema().dump(pedido),
            "reserva_interna_id": pedido.get('reserva_interna_id')
        }), 201
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error crear takeaway: {str(e)}")
        return jsonify({"error": "Error interno", "detalles": str(e)}), 500


# ============================================================================
# GET /api/pedidos/{id} - Obtener Pedido
# ============================================================================
@bp.route('/<int:pedido_id>', methods=['GET'])
@jwt_required()
def obtener_pedido(pedido_id):
    """
    Obtener pedido completo con items e histórico
    ---
    tags:
      - Pedidos
    summary: Obtener Pedido
    parameters:
      - in: path
        name: pedido_id
        type: integer
        required: true
    responses:
      200:
        description: Pedido encontrado
      404:
        description: Pedido no existe
    """
    try:
        pedido = PedidoService.obtener_pedido(pedido_id)
        return jsonify({"pedido": PedidoResponseSchema().dump(pedido)}), 200
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error obtener pedido: {str(e)}")
        return jsonify({"error": "Error interno"}), 500


# ============================================================================
# POST /api/pedidos/{id}/items - Agregar Item
# ============================================================================
@bp.route('/<int:pedido_id>/items', methods=['POST'])
@jwt_required()
def agregar_item(pedido_id):
    """
    Agregar item a pedido (CONSUME INVENTARIO)
    ---
    tags:
      - Pedidos
    summary: Agregar Item a Pedido
    description: |
      Agrega producto o combo al pedido.
      - Item se crea directamente en estado 1 (EnCocina)
      - CONSUME INVENTARIO inmediatamente (FIFO por lotes)
      - Pedido debe estar en estado 0 (Iniciado) o 3 (Completo)
    parameters:
      - in: path
        name: pedido_id
        type: integer
        required: true
      - in: body
        name: body
        schema:
          type: object
          required:
            - cantidad
          properties:
            producto_id:
              type: integer
              description: XOR con combo_id
            combo_id:
              type: integer
              description: XOR con producto_id
            cantidad:
              type: integer
              example: 2
            notas:
              type: string
    responses:
      201:
        description: Item agregado, inventario consumido
      400:
        description: Error validación o stock insuficiente
    """
    try:
        payload = request.get_json()
        
        if not payload.get('producto_id') and not payload.get('combo_id'):
            return jsonify({"error": "Debe proporcionar producto_id o combo_id"}), 400
        if payload.get('producto_id') and payload.get('combo_id'):
            return jsonify({"error": "Solo uno: producto_id o combo_id"}), 400
        
        item = PedidoService.agregar_item(
            pedido_id=pedido_id,
            producto_id=payload.get('producto_id'),
            combo_id=payload.get('combo_id'),
            cantidad=payload.get('cantidad', 1),
            notas=payload.get('notas')
        )
        
        # Verificar si el consumo de inventario fue exitoso
        consumo_exitoso = item.get('consumo_exitoso', False)
        inventario_consumido = item.get('inventario_consumido')
        
        if not consumo_exitoso:
            error_msg = item.get('error_consumo', 'No se pudo consumir inventario')
            logger.warning(f"Item {item.get('id_pedido_item')} creado pero inventario NO consumido: {error_msg}")
            return jsonify({
                "mensaje": "Item creado pero SIN consumo de inventario",
                "advertencia": error_msg,
                "item": item
            }), 201
        
        if not inventario_consumido:
            logger.warning(f"Item {item.get('id_pedido_item')} creado - producto sin receta configurada")
            return jsonify({
                "mensaje": "Item creado - PRODUCTO SIN RECETA",
                "advertencia": "El producto/combo no tiene receta configurada. No se consumió inventario.",
                "item": item
            }), 201
        
        logger.info(f"Item agregado a pedido {pedido_id}, inventario consumido: {len(inventario_consumido)} insumos")
        
        return jsonify({
            "mensaje": "Item agregado - en cocina, inventario consumido",
            "insumos_consumidos": len(inventario_consumido),
            "item": item
        }), 201
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error agregar item: {str(e)}")
        return jsonify({"error": "Error interno", "detalles": str(e)}), 500


# ============================================================================
# PATCH /api/pedidos/{id}/completar - Cerrar Pedido
# ============================================================================
@bp.route('/<int:pedido_id>/completar', methods=['PATCH'])
@jwt_required()
def completar_pedido(pedido_id):
    """
    Cerrar pedido (0→3)
    ---
    tags:
      - Pedidos
    summary: Completar/Cerrar Pedido
    description: |
      Usuario cierra el pedido.
      - Pedido: 0 (Iniciado) → 3 (Completo)
      - Items: 2 (Listo) → 3 (Completo)
      - Requiere que todos los items estén en Listo (2) o superior
    parameters:
      - in: path
        name: pedido_id
        type: integer
        required: true
    responses:
      200:
        description: Pedido completado
      400:
        description: Items no listos
    """
    try:
        usuario_id = get_jwt_identity()
        resultado = PedidoService.completar_pedido(pedido_id, usuario_id)
        
        logger.info(f"Pedido {pedido_id} completado (0→3)")
        
        return jsonify({
            "mensaje": "Pedido cerrado exitosamente",
            "pedido": PedidoResponseSchema().dump(resultado)
        }), 200
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error completar: {str(e)}")
        return jsonify({"error": "Error interno"}), 500


# ============================================================================
# PATCH /api/pedidos/{id}/cancelar - Cancelar Pedido
# ============================================================================
@bp.route('/<int:pedido_id>/cancelar', methods=['PATCH'])
@jwt_required()
def cancelar_pedido(pedido_id):
    """
    Cancelar pedido (0→4)
    ---
    tags:
      - Pedidos
    summary: Cancelar Pedido
    description: |
      Cancela pedido y todos sus items.
      - Pedido: 0 (Iniciado) → 4 (Cancelado)
      - Items: (todos) → 4 (Cancelado)
      - NOTA: Si items ya consumieron inventario, NO se revierte
    parameters:
      - in: path
        name: pedido_id
        type: integer
        required: true
      - in: body
        name: body
        schema:
          type: object
          properties:
            comentario:
              type: string
    responses:
      200:
        description: Pedido cancelado
      400:
        description: No se puede cancelar
    """
    try:
        usuario_id = get_jwt_identity()
        payload = request.get_json() or {}
        
        resultado = PedidoService.cancelar_pedido(
            pedido_id, usuario_id, payload.get('comentario')
        )
        
        logger.info(f"Pedido {pedido_id} cancelado (0→4)")
        
        return jsonify({
            "mensaje": "Pedido cancelado",
            "pedido": PedidoResponseSchema().dump(resultado)
        }), 200
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error cancelar: {str(e)}")
        return jsonify({"error": "Error interno"}), 500


# ============================================================================
# POST /api/pedidos/listar - Listar Pedidos
# ============================================================================
@bp.route('/listar', methods=['POST'])
@jwt_required()
def listar_pedidos():
    """
    Listar pedidos de sucursal
    ---
    tags:
      - Pedidos
    summary: Listar Pedidos
    description: |
      Lista pedidos con filtros opcionales.
      Todos los parámetros son opcionales.
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            sucursal_id:
              type: integer
              description: ID de sucursal (opcional, si no se envía usa las del usuario)
            estado:
              type: integer
              description: "0=Iniciado, 3=Completo, 4=Cancelado, 5=Pagado (opcional)"
            fecha_desde:
              type: string
              description: "YYYY-MM-DD (opcional)"
            fecha_hasta:
              type: string
              description: "YYYY-MM-DD (opcional)"
            tipo_pedido:
              type: integer
              description: "1=Dine-in, 2=Takeaway (opcional)"
            cliente_id:
              type: integer
              description: "ID del cliente para filtrar pedidos (opcional)"
    responses:
      200:
        description: Lista de pedidos
    """
    try:
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario') if isinstance(current_user, dict) else current_user
        
        # Obtener parámetros del body
        payload = request.get_json() or {}
        sucursal_id = payload.get('sucursal_id')
        estado = payload.get('estado')
        fecha_desde = payload.get('fecha_desde')
        fecha_hasta = payload.get('fecha_hasta')
        tipo_pedido = payload.get('tipo_pedido')
        cliente_id = payload.get('cliente_id')
        
        # Si no se especifica sucursal, usar las del usuario
        if sucursal_id:
            from src.core.utils.multitenant import validar_acceso_sucursal
            if not validar_acceso_sucursal(usuario_id, sucursal_id):
                return jsonify({"error": "Sin acceso a esta sucursal"}), 403
        else:
            from src.core.utils.multitenant import obtener_sucursales_usuario
            sucursales_usuario = obtener_sucursales_usuario(usuario_id)
            if not sucursales_usuario:
                return jsonify({"error": "Usuario sin sucursal asignada"}), 403
            sucursal_id = sucursales_usuario[0]  # Usar primera sucursal por defecto
        
        # Parsear fechas si vienen
        try:
            fecha_desde = datetime.fromisoformat(fecha_desde) if fecha_desde else None
            fecha_hasta = datetime.fromisoformat(fecha_hasta) if fecha_hasta else None
        except ValueError:
            return jsonify({"error": "Formato fecha inválido (YYYY-MM-DD)"}), 400
        
        pedidos, total = PedidoDAO.listar_pedidos_por_sucursal(
            sucursal_id=sucursal_id,
            estado=estado,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            tipo_pedido=tipo_pedido,
            cliente_id=cliente_id
        )
        
        return jsonify({
            "pedidos": PedidoListSchema(many=True).dump(pedidos),
            "total": total,
            "filtros_aplicados": {
                "sucursal_id": sucursal_id,
                "estado": estado,
                "fecha_desde": fecha_desde.isoformat() if fecha_desde else None,
                "fecha_hasta": fecha_hasta.isoformat() if fecha_hasta else None,
                "tipo_pedido": tipo_pedido,
                "cliente_id": cliente_id
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error listar: {str(e)}")
        return jsonify({"error": "Error interno", "detalle": str(e)}), 500


# ============================================================================
# GET /api/pedidos/activos - Pedidos Activos
# ============================================================================
@bp.route('/activos', methods=['GET'])
@jwt_required()
def pedidos_activos():
    """
    Pedidos activos de sucursal
    ---
    tags:
      - Pedidos
    summary: Pedidos Activos
    description: Pedidos en estado 0 (Iniciado) y 3 (Completo)
    parameters:
      - in: query
        name: sucursal_id
        type: integer
        required: true
    responses:
      200:
        description: Pedidos agrupados por estado
    """
    try:
        sucursal_id = request.args.get('sucursal_id', type=int)
        if not sucursal_id:
            return jsonify({"error": "sucursal_id requerido"}), 400
        
        resultado = PedidoService.obtener_pedidos_activos(sucursal_id)
        return jsonify(resultado), 200
    
    except Exception as e:
        logger.error(f"Error pedidos activos: {str(e)}")
        return jsonify({"error": "Error interno"}), 500
