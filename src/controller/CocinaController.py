"""
CocinaController - API Endpoints para Vista de Cocina

Sistema de Estados de Items (estatus_detalle):
    1 = EnCocina (item creado, inventario ya consumido, pendiente preparar)
    2 = Listo (preparación completada)
    3 = Completo (cerrado)
    4 = Cancelado
    5 = Pagado

Flujo Items: 1 (crear) → 2 (cocina marca listo) → 3 (cerrar) → 5 (pagar)

Takeaway: Cuando cocina marca TODOS los items como Listo (2), 
          el pedido e items se AUTO-PAGAN a 5

Endpoints (solo acciones de cocina):
  GET  /api/cocina/pendientes     - Items pendientes de preparar (estatus=1)
  PUT  /api/cocina/item/{id}/listo - Marcar item como listo (1→2, auto-pay si takeaway)
  GET  /api/cocina/pedidos        - Pedidos con items en cocina (agrupados)
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import logging

from src.core.db.session_manager import get_db_session
from src.models.operaciones.pedido_model import Pedido
from src.models.operaciones.pedido_item_model import PedidoItem
from src.models.catalogos.producto_model import Producto
from src.models.catalogos.combo_model import Combo
from src.services.operaciones.pedido_service import PedidoService
from src.dao.operaciones.pedido_item_dao import PedidoItemDAO
from src.core.utils.multitenant import validar_acceso_sucursal, obtener_sucursales_usuario
from sqlalchemy import and_, distinct

logger = logging.getLogger(__name__)
bp = Blueprint('cocina', __name__, url_prefix='/api/cocina')

# Constantes de estado
ESTADO_INICIADO = 0
ESTADO_PAGADO = 5

ESTATUS_ITEM_EN_COCINA = 1
ESTATUS_ITEM_LISTO = 2
ESTATUS_ITEM_CANCELADO = 4


# ============================================================================
# POST /api/cocina/pendientes - Items pendientes de preparar
# ============================================================================
@bp.route('/pendientes', methods=['POST'])
@jwt_required()
def obtener_items_pendientes():
    """
    Items pendientes de preparar en cocina
    ---
    tags:
      - Cocina
    summary: Items Pendientes en Cocina
    description: |
      Lista items en estado 1 (EnCocina) de pedidos activos.
      Ordenados FIFO (primero en llegar, primero en salir).
      
      Los items ya tienen inventario consumido, solo falta prepararlos.
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            sucursal_id:
              type: integer
              description: ID de sucursal (opcional, si no se envía usa las del usuario)
    responses:
      200:
        description: Lista de items pendientes
        schema:
          type: object
          properties:
            items:
              type: array
              items:
                type: object
                properties:
                  id_pedido_item:
                    type: integer
                  pedido_id:
                    type: integer
                  folio_pedido:
                    type: string
                  tipo_pedido:
                    type: integer
                    description: "1=Dine-in, 2=Takeaway"
                  tipo_pedido_display:
                    type: string
                  producto_nombre:
                    type: string
                  cantidad:
                    type: integer
                  notas:
                    type: string
                  tiempo_en_cocina:
                    type: string
            total:
              type: integer
    """
    try:
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario') if isinstance(current_user, dict) else current_user
        
        # Obtener parámetros del body
        payload = request.get_json() or {}
        sucursal_id_filtro = payload.get('sucursal_id')
        
        # Si se especifica sucursal_id, usarlo; si no, usar las del usuario
        if sucursal_id_filtro:
            # Validar acceso a la sucursal
            if not validar_acceso_sucursal(usuario_id, sucursal_id_filtro):
                return jsonify({"error": "Sin acceso a esta sucursal"}), 403
            sucursales = [sucursal_id_filtro]
        else:
            sucursales = obtener_sucursales_usuario(usuario_id)
            if not sucursales:
                return jsonify({"error": "Usuario sin sucursal asignada"}), 403
        
        with get_db_session() as session:
            # Items en cocina (estatus=1) de pedidos activos (estado=0)
            query = session.query(
                PedidoItem, Pedido
            ).join(
                Pedido, PedidoItem.pedido_id == Pedido.id_pedido
            ).filter(
                and_(
                    PedidoItem.estatus_detalle == ESTATUS_ITEM_EN_COCINA,
                    Pedido.sucursal_id.in_(sucursales),
                    Pedido.estado_pedido == ESTADO_INICIADO
                )
            ).order_by(
                PedidoItem.created_at.asc()  # FIFO
            )
            
            resultados = query.all()
            ahora = datetime.utcnow()
            items = []
            
            for item, pedido in resultados:
                # Calcular tiempo en cocina
                tiempo_en_cocina = None
                if item.created_at:
                    delta = ahora - item.created_at
                    minutos = int(delta.total_seconds() / 60)
                    if minutos < 60:
                        tiempo_en_cocina = f"{minutos} min"
                    else:
                        horas = minutos // 60
                        mins = minutos % 60
                        tiempo_en_cocina = f"{horas}h {mins}m"
                
                # Obtener nombre
                producto_nombre = None
                if item.producto_id:
                    producto = session.query(Producto).filter(
                        Producto.id_producto == item.producto_id
                    ).first()
                    producto_nombre = producto.nombre if producto else f"Producto {item.producto_id}"
                elif item.combo_id:
                    combo = session.query(Combo).filter(
                        Combo.id_combo == item.combo_id
                    ).first()
                    producto_nombre = combo.nombre if combo else f"Combo {item.combo_id}"
                
                items.append({
                    'id_pedido_item': item.id_pedido_item,
                    'pedido_id': item.pedido_id,
                    'folio_pedido': pedido.folio,
                    'tipo_pedido': pedido.tipo_pedido,
                    'tipo_pedido_display': 'Dine-in' if pedido.tipo_pedido == 1 else 'Para llevar',
                    'mesa_id': pedido.mesa_id,
                    'producto_id': item.producto_id,
                    'combo_id': item.combo_id,
                    'producto_nombre': producto_nombre,
                    'cantidad': item.cantidad,
                    'notas': item.notas,
                    'estatus_detalle': item.estatus_detalle,
                    'created_at': item.created_at.isoformat() if item.created_at else None,
                    'tiempo_en_cocina': tiempo_en_cocina
                })
            
            return jsonify({
                "items": items,
                "total": len(items)
            }), 200
            
    except Exception as e:
        logger.error(f"Error obteniendo items pendientes: {str(e)}", exc_info=True)
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


# ============================================================================
# PUT /api/cocina/item/{id}/listo - Marcar item como listo
# ============================================================================
@bp.route('/item/<int:item_id>/listo', methods=['PUT'])
@jwt_required()
def marcar_item_listo(item_id):
    """
    Marcar item como listo (1→2)
    ---
    tags:
      - Cocina
    summary: Marcar Item como Listo
    description: |
      Cocina marca item como preparado: estatus 1 (EnCocina) → 2 (Listo).
      
      **TAKEAWAY AUTO-PAY:**
      Si el pedido es Takeaway (tipo_pedido=2) y TODOS los items 
      quedan en estado Listo (2), el pedido e items se AUTO-PAGAN a 5.
    parameters:
      - in: path
        name: item_id
        type: integer
        required: true
        description: ID del item a marcar como listo
    responses:
      200:
        description: Item marcado como listo
        schema:
          type: object
          properties:
            message:
              type: string
            item:
              type: object
            pedido_auto_pagado:
              type: boolean
              description: "True si pedido Takeaway se auto-pagó"
      400:
        description: Item no está en cocina
      404:
        description: Item no encontrado
    """
    try:
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario') if isinstance(current_user, dict) else current_user
        
        with get_db_session() as session:
            # Obtener item
            item = session.query(PedidoItem).filter(
                PedidoItem.id_pedido_item == item_id
            ).first()
            
            if not item:
                return jsonify({"error": f"Item {item_id} no encontrado"}), 404
            
            # Obtener pedido
            pedido = session.query(Pedido).filter(
                Pedido.id_pedido == item.pedido_id
            ).first()
            
            if not pedido:
                return jsonify({"error": "Pedido no encontrado"}), 404
            
            # Validar acceso
            if not validar_acceso_sucursal(usuario_id, pedido.sucursal_id):
                return jsonify({"error": "Sin acceso a esta sucursal"}), 403
            
            # Validar estado actual
            if item.estatus_detalle != ESTATUS_ITEM_EN_COCINA:
                estatus_map = {0: 'Iniciado', 1: 'EnCocina', 2: 'Listo', 3: 'Completo', 4: 'Cancelado', 5: 'Pagado'}
                return jsonify({
                    "error": f"Item no está en cocina. Estado actual: {estatus_map.get(item.estatus_detalle, 'Desconocido')}"
                }), 400
        
        # Marcar como listo usando Service (maneja auto-pay de takeaway)
        try:
            item_actualizado = PedidoService.marcar_item_listo(item_id, usuario_id)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        
        # Verificar si hubo auto-pago
        pedido_auto_pagado = item_actualizado.get('pedido_auto_pagado', False)
        
        mensaje = "Item marcado como listo"
        if pedido_auto_pagado:
            mensaje = "Item listo - Pedido Takeaway AUTO-PAGADO (todos items listos)"
        
        logger.info(f"Item {item_id} marcado listo por usuario {usuario_id}, auto_pagado={pedido_auto_pagado}")
        
        return jsonify({
            "message": mensaje,
            "item": item_actualizado,
            "pedido_auto_pagado": pedido_auto_pagado
        }), 200
        
    except Exception as e:
        logger.error(f"Error marcando item listo: {str(e)}", exc_info=True)
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


# ============================================================================
# POST /api/cocina/pedidos - Pedidos con items en cocina
# ============================================================================
@bp.route('/pedidos', methods=['POST'])
@jwt_required()
def obtener_pedidos_en_cocina():
    """
    Pedidos con items en cocina (agrupados)
    ---
    tags:
      - Cocina
    summary: Pedidos en Cocina
    description: |
      Lista pedidos que tienen items en estado 1 (EnCocina),
      mostrando progreso de preparación.
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            sucursal_id:
              type: integer
              description: ID de sucursal (opcional, si no se envía usa las del usuario)
    responses:
      200:
        description: Pedidos con items en cocina
        schema:
          type: object
          properties:
            pedidos:
              type: array
              items:
                type: object
                properties:
                  id_pedido:
                    type: integer
                  folio:
                    type: string
                  tipo_pedido:
                    type: integer
                  tipo_pedido_display:
                    type: string
                  mesa_id:
                    type: integer
                  progreso:
                    type: string
                    description: "Ejemplo: 2/5 (items listos/total)"
                  items_en_cocina:
                    type: array
            total:
              type: integer
    """
    try:
        current_user = get_jwt_identity()
        usuario_id = current_user.get('id_usuario') if isinstance(current_user, dict) else current_user
        
        # Obtener parámetros del body
        payload = request.get_json() or {}
        sucursal_id_filtro = payload.get('sucursal_id')
        
        # Si se especifica sucursal_id, usarlo; si no, usar las del usuario
        if sucursal_id_filtro:
            # Validar acceso a la sucursal
            if not validar_acceso_sucursal(usuario_id, sucursal_id_filtro):
                return jsonify({"error": "Sin acceso a esta sucursal"}), 403
            sucursales = [sucursal_id_filtro]
        else:
            sucursales = obtener_sucursales_usuario(usuario_id)
            if not sucursales:
                return jsonify({"error": "Usuario sin sucursal asignada"}), 403
        
        with get_db_session() as session:
            # Obtener IDs de pedidos con items en cocina
            pedidos_ids = session.query(distinct(PedidoItem.pedido_id)).filter(
                PedidoItem.estatus_detalle == ESTATUS_ITEM_EN_COCINA
            ).all()
            
            pedidos_ids = [p[0] for p in pedidos_ids]
            
            if not pedidos_ids:
                return jsonify({"pedidos": [], "total": 0}), 200
            
            # Obtener pedidos
            pedidos = session.query(Pedido).filter(
                and_(
                    Pedido.id_pedido.in_(pedidos_ids),
                    Pedido.sucursal_id.in_(sucursales)
                )
            ).order_by(Pedido.created_at.asc()).all()
            
            resultado = []
            
            for pedido in pedidos:
                # Items en cocina de este pedido
                items_cocina = session.query(PedidoItem).filter(
                    and_(
                        PedidoItem.pedido_id == pedido.id_pedido,
                        PedidoItem.estatus_detalle == ESTATUS_ITEM_EN_COCINA
                    )
                ).all()
                
                # Todos los items para calcular progreso
                todos_items = session.query(PedidoItem).filter(
                    PedidoItem.pedido_id == pedido.id_pedido
                ).all()
                
                items_listos = sum(1 for i in todos_items if i.estatus_detalle >= ESTATUS_ITEM_LISTO and i.estatus_detalle != ESTATUS_ITEM_CANCELADO)
                items_activos = sum(1 for i in todos_items if i.estatus_detalle != ESTATUS_ITEM_CANCELADO)
                
                resultado.append({
                    'id_pedido': pedido.id_pedido,
                    'folio': pedido.folio,
                    'tipo_pedido': pedido.tipo_pedido,
                    'tipo_pedido_display': 'Dine-in' if pedido.tipo_pedido == 1 else 'Para llevar',
                    'mesa_id': pedido.mesa_id,
                    'estado_pedido': pedido.estado_pedido,
                    'created_at': pedido.created_at.isoformat() if pedido.created_at else None,
                    'progreso': f"{items_listos}/{items_activos}",
                    'items_en_cocina': [
                        {
                            'id_pedido_item': item.id_pedido_item,
                            'producto_id': item.producto_id,
                            'combo_id': item.combo_id,
                            'cantidad': item.cantidad,
                            'notas': item.notas,
                            'created_at': item.created_at.isoformat() if item.created_at else None
                        }
                        for item in items_cocina
                    ]
                })
            
            return jsonify({
                "pedidos": resultado,
                "total": len(resultado)
            }), 200
            
    except Exception as e:
        logger.error(f"Error obteniendo pedidos en cocina: {str(e)}", exc_info=True)
        return jsonify({"error": f"Error interno: {str(e)}"}), 500
