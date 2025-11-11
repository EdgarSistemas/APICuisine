"""
CompraController - Gestión de compras
Endpoints: POST crear con detalles, GET listar por sucursal, GET/:id con detalles completos
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
import logging

from src.services.inventario.compra_service import CompraService
from src.schemas.compra_schema import CompraCreateSchema, CompraUpdateSchema

logger = logging.getLogger(__name__)
bp = Blueprint('compras', __name__, url_prefix='/api/compras')


# ============================================================================
# POST /api/compras - Crear Compra con Detalles
# ============================================================================
@bp.route('', methods=['POST'])
@jwt_required()
def crear_compra():
    """
    Crear nueva compra con detalles
    Solo ADMIN (id_rol=1) o COMPRAS (id_rol=8)
    ---
    tags:
      - Compras
    security:
      - Bearer: []
    parameters:
      - in: body
        name: compra
        required: true
        schema:
          type: object
          properties:
            sucursal_id:
              type: integer
              example: 1
            proveedor_id:
              type: integer
              example: 1
            detalles:
              type: array
              items:
                type: object
                properties:
                  insumo_id:
                    type: integer
                  cant_presentacion:
                    type: number
                    example: 5
                  costo_unit_present:
                    type: number
                    example: 150.50
                  presentacion:
                    type: string
                    example: "costal"
    responses:
      201:
        description: Compra creada exitosamente
      400:
        description: Datos inválidos
      403:
        description: Solo ADMIN o COMPRAS
    """
    try:
        usuario_id = get_jwt_identity()
        data = request.get_json()
        
        # Validar schema
        schema = CompraCreateSchema()
        try:
            datos_validados = schema.load(data)
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': e.messages
            }), 400
        
        resultado = CompraService.crear_compra(
            usuario_id=usuario_id,
            sucursal_id=datos_validados['sucursal_id'],
            proveedor_id=datos_validados['proveedor_id'],
            detalles=datos_validados['detalles']
        )
        
        if resultado['success']:
            return jsonify(resultado), 201
        else:
            status = 403 if 'admin' in resultado.get('error', '').lower() or 'compras' in resultado.get('error', '').lower() else 400
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error en crear_compra: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# GET /api/compras - Listar Compras por Sucursal
# ============================================================================
@bp.route('/<int:sucursal_id>', methods=['GET'])
@jwt_required()
def listar_compras(sucursal_id):
    """
    Listar compras de una sucursal
    ---
    tags:
      - Compras
    security:
      - Bearer: []
    parameters:
      - in: path
        name: sucursal_id
        type: integer
        required: true
    responses:
      200:
        description: Lista de compras
      400:
        description: Falta sucursal_id
    """
    try:        
        resultado = CompraService.listar_compras_por_sucursal(sucursal_id)
        return jsonify(resultado), 200
            
    except Exception as e:
        logger.error(f"Error en listar_compras: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# GET /api/compras/{id} - Obtener Compra por ID con Datos Completos
# ============================================================================
@bp.route('/id/<int:compra_id>', methods=['GET'])
@jwt_required()
def obtener_compra(compra_id):
    """
    Obtener compra con datos completos: proveedor, sucursal, usuario, detalles con insumo y unidad de medida
    ---
    tags:
      - Compras
    security:
      - Bearer: []
    parameters:
      - in: path
        name: compra_id
        type: integer
        required: true
    responses:
      200:
        description: Compra encontrada con datos completos
      404:
        description: Compra no existe
    """
    try:
        resultado = CompraService.obtener_compra(compra_id)
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 404
            
    except Exception as e:
        logger.error(f"Error en obtener_compra: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# ============================================================================
# PATCH /api/compras/{id}/cancelar - Cancelar Compra
# ============================================================================
@bp.route('/id/<int:compra_id>/cancelar', methods=['PATCH'])
@jwt_required()
def cancelar_compra(compra_id):
    """
    Cancelar una compra (estatus=3)
    Solo ADMIN (id_rol=1) o COMPRAS (id_rol=8)
    No se puede cancelar si ya tiene recepción asociada
    ---
    tags:
      - Compras
    security:
      - Bearer: []
    parameters:
      - in: path
        name: compra_id
        type: integer
        required: true
    responses:
      200:
        description: Compra cancelada exitosamente
      400:
        description: Error de validación (ya cancelada o tiene recepción)
      403:
        description: Solo ADMIN o COMPRAS pueden cancelar
      404:
        description: Compra no existe
    """
    try:
        usuario_id = get_jwt_identity()
        
        resultado = CompraService.cancelar_compra(
            usuario_id=usuario_id,
            compra_id=compra_id
        )
        
        if resultado['success']:
            return jsonify(resultado), 200
        else:
            # Determinar código de estado según el error
            error_msg = resultado.get('error', '').lower()
            if 'admin' in error_msg or 'compras' in error_msg or 'permisos' in error_msg:
                status = 403
            elif 'no existe' in error_msg:
                status = 404
            else:
                status = 400
            
            return jsonify(resultado), status
            
    except Exception as e:
        logger.error(f"Error en cancelar_compra: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500

