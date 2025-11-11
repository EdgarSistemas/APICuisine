"""
PedidoController - Centro de operaciones
Endpoints: POST, GET, GET/{id}, PUT, DELETE (soft)
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

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
    Crear pedido (Admin o Mesero/Recepción de su sucursal)
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json()
        
        # Validación 1: sucursal_id requerido
        sucursal_id = data.get('sucursal_id')
        if not sucursal_id:
            return {'success': False, 'error': 'sucursal_id requerido'}, 400
        
        # Validación 2: sucursal existe
        if not validar_sucursal_existe(sucursal_id):
            return {'success': False, 'error': 'Sucursal no existe'}, 400
        
        # Validación 3: usuario tiene acceso
        if not validar_acceso_sucursal(usuario_id, sucursal_id):
            return {'success': False, 'error': 'FORBIDDEN'}, 403
        
        # Crear pedido
        pedido = Pedido(
            sucursal_id=sucursal_id,
            folio=data.get('folio'),
            tipo_pedido=data.get('tipo_pedido', 1),
            canal=data.get('canal', 1),
            mesa_id=data.get('mesa_id'),
            inicia_usuario_id=usuario_id,
            estado_pedido=data.get('estado_pedido', 1),
            notas=data.get('notas')
        )
        
        from src.core.db.session_manager import get_db_session
        with get_db_session() as session:
            session.add(pedido)
            session.commit()
            logger.info(f"Pedido {pedido.id_pedido} creado por usuario {usuario_id}")
        
        return {
            'success': True,
            'data': pedido.to_dict(),
            'message': 'Pedido creado'
        }, 201
        
    except Exception as e:
        logger.error(f"Error creando pedido: {str(e)}")
        return {'success': False, 'error': 'Error interno'}, 500


# ============================================================================
# GET /api/pedidos - Listar Pedidos
# ============================================================================
@bp.route('', methods=['GET'])
@jwt_required()
def obtener_pedidos():
    """
    Listar pedidos (Admin ve todas sucursales, Empleado ve su sucursal)
    """
    try:
        usuario_id = get_jwt_identity()
        
        from src.core.db.session_manager import get_db_session
        with get_db_session() as session:
            query = session.query(Pedido)
            
            # Aplicar filtro multi-tenant
            query = agregar_filtro_sucursal(query, Pedido, usuario_id)
            
            pedidos = query.order_by(Pedido.created_at.desc()).all()
            
            return {
                'success': True,
                'data': [p.to_dict() for p in pedidos],
                'total': len(pedidos)
            }, 200
            
    except Exception as e:
        logger.error(f"Error listando pedidos: {str(e)}")
        return {'success': False, 'error': 'Error interno'}, 500


# ============================================================================
# GET /api/pedidos/{id} - Obtener Pedido por ID
# ============================================================================
@bp.route('/<int:pedido_id>', methods=['GET'])
@jwt_required()
def obtener_pedido(pedido_id):
    """
    Obtener pedido específico (validar acceso a sucursal)
    """
    try:
        usuario_id = get_jwt_identity()
        
        from src.core.db.session_manager import get_db_session
        with get_db_session() as session:
            pedido = session.query(Pedido).get(pedido_id)
            
            if not pedido:
                return {'success': False, 'error': 'Pedido no existe'}, 404
            
            # Validar acceso
            if not validar_pertenencia_sucursal(usuario_id, pedido):
                return {'success': False, 'error': 'FORBIDDEN'}, 403
            
            return {
                'success': True,
                'data': pedido.to_dict()
            }, 200
            
    except Exception as e:
        logger.error(f"Error obteniendo pedido {pedido_id}: {str(e)}")
        return {'success': False, 'error': 'Error interno'}, 500


# ============================================================================
# PUT /api/pedidos/{id} - Actualizar Pedido
# ============================================================================
@bp.route('/<int:pedido_id>', methods=['PUT'])
@jwt_required()
def actualizar_pedido(pedido_id):
    """
    Actualizar pedido (Mesero/Cocina solo su sucursal)
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json()
        
        from src.core.db.session_manager import get_db_session
        with get_db_session() as session:
            pedido = session.query(Pedido).get(pedido_id)
            
            if not pedido:
                return {'success': False, 'error': 'Pedido no existe'}, 404
            
            # Validar acceso
            if not validar_pertenencia_sucursal(usuario_id, pedido):
                return {'success': False, 'error': 'FORBIDDEN'}, 403
            
            # Actualizar campos permitidos
            if 'estado_pedido' in data:
                pedido.estado_pedido = data['estado_pedido']
            if 'notas' in data:
                pedido.notas = data['notas']
            
            session.commit()
            logger.info(f"Pedido {pedido_id} actualizado por usuario {usuario_id}")
            
            return {
                'success': True,
                'data': pedido.to_dict(),
                'message': 'Pedido actualizado'
            }, 200
            
    except Exception as e:
        logger.error(f"Error actualizando pedido {pedido_id}: {str(e)}")
        return {'success': False, 'error': 'Error interno'}, 500


# ============================================================================
# DELETE /api/pedidos/{id} - Eliminar Pedido (Soft)
# ============================================================================
@bp.route('/<int:pedido_id>', methods=['DELETE'])
@jwt_required()
def eliminar_pedido(pedido_id):
    """
    Eliminar pedido - SOLO ADMIN (soft delete: cambiar estado a cancelado)
    """
    try:
        usuario_id = get_jwt_identity()
        
        # Validar que es admin
        if not es_admin(usuario_id):
            return {'success': False, 'error': 'FORBIDDEN'}, 403
        
        from src.core.db.session_manager import get_db_session
        with get_db_session() as session:
            pedido = session.query(Pedido).get(pedido_id)
            
            if not pedido:
                return {'success': False, 'error': 'Pedido no existe'}, 404
            
            # Soft delete: cambiar estado a cancelado
            pedido.estado_pedido = 4  # 4 = Cancelado
            session.commit()
            logger.info(f"Pedido {pedido_id} cancelado por admin {usuario_id}")
            
            return {
                'success': True,
                'message': 'Pedido cancelado'
            }, 200
            
    except Exception as e:
        logger.error(f"Error eliminando pedido {pedido_id}: {str(e)}")
        return {'success': False, 'error': 'Error interno'}, 500
