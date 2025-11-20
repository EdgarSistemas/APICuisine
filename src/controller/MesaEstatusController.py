"""
MesaEstatusController - Endpoints REST para MesaEstatus
Gestión de estados de mesas (disponible, ocupada, en limpieza, etc)
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.dao.catalogos.mesa_estatus_dao import MesaEstatusDAO
import logging

logger = logging.getLogger(__name__)

# Blueprint
mesa_estatus_bp = Blueprint('mesa_estatus', __name__, url_prefix='/api/mesas-estatus')


@mesa_estatus_bp.route('/<int:mesa_id>', methods=['GET'])
@jwt_required()
def obtener_estatus_mesa(mesa_id):
    """
    Obtener estatus actual de una mesa.
    ---
    tags:
      - Mesas - Estados
    summary: "Obtener Estatus de Mesa"
    description: Retorna el estatus actual de una mesa específica (Disponible, Ocupada, En Limpieza, Fuera de Servicio).
    parameters:
      - in: path
        name: mesa_id
        type: integer
        required: true
        description: "ID de la mesa. Ej: 5"
    responses:
      200:
        description: "Estatus de la mesa obtenido exitosamente"
        schema:
          type: object
          properties:
            id_mesa_estatus:
              type: integer
              example: 1
            mesa_id:
              type: integer
              example: 5
            estatus:
              type: integer
              example: 1
              description: "1=Disponible, 2=Ocupada, 3=En Limpieza, 4=Fuera de Servicio"
            estatus_display:
              type: string
              example: "Disponible"
            cambio_por:
              type: integer
              nullable: true
              example: 3
            notas:
              type: string
              nullable: true
              example: "Limpieza completada"
            created_at:
              type: string
              format: date-time
            updated_at:
              type: string
              format: date-time
              nullable: true
      404:
        description: "Mesa no tiene estatus registrado"
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Mesa 5 no tiene estatus registrado"
      500:
        description: "Error interno del servidor"
    """
    try:
        estatus = MesaEstatusDAO.obtener_estatus_mesa(mesa_id)
        
        if not estatus:
            return jsonify({"error": f"Mesa {mesa_id} no tiene estatus registrado"}), 404
        
        # Agregar display
        estatus_map = {1: "Disponible", 2: "Ocupada", 3: "En Limpieza", 4: "Fuera de Servicio"}
        estatus['estatus_display'] = estatus_map.get(estatus['estatus'], 'Desconocido')
        
        return jsonify(estatus), 200
        
    except Exception as e:
        logger.error(f"Error en obtener_estatus_mesa: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@mesa_estatus_bp.route('/<int:mesa_id>/disponible', methods=['POST'])
@jwt_required()
def marcar_mesa_disponible(mesa_id):
    """
    Marcar mesa como disponible (termina limpieza).
    ---
    tags:
      - Mesas - Estados
    summary: "Marcar Mesa Disponible"
    description: Marca una mesa como disponible (estatus=1). Usado por el equipo de limpieza al terminar de limpiar una mesa. Solo usuarios con rol de Limpieza pueden usar este endpoint.
    parameters:
      - in: path
        name: mesa_id
        type: integer
        required: true
        description: "ID de la mesa a marcar disponible. Ej: 5"
    responses:
      200:
        description: "Mesa marcada como disponible exitosamente"
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Mesa marcada como disponible"
            estatus:
              type: object
              properties:
                id_mesa_estatus:
                  type: integer
                mesa_id:
                  type: integer
                estatus:
                  type: integer
                  example: 1
                estatus_display:
                  type: string
                  example: "Disponible"
                cambio_por:
                  type: integer
                  nullable: true
                notas:
                  type: string
                updated_at:
                  type: string
                  format: date-time
      500:
        description: "Error interno del servidor"
    """
    try:
        current_user = get_jwt_identity()
        
        # Marcar mesa disponible
        estatus = MesaEstatusDAO.marcar_mesa_disponible(mesa_id, current_user)
        
        # Agregar display
        estatus_map = {1: "Disponible", 2: "Ocupada", 3: "En Limpieza", 4: "Fuera de Servicio"}
        estatus['estatus_display'] = estatus_map.get(estatus['estatus'], 'Desconocido')
        
        logger.info(f"Usuario {current_user} marcó mesa {mesa_id} como disponible")
        
        return jsonify({
            "message": "Mesa marcada como disponible",
            "estatus": estatus
        }), 200
        
    except Exception as e:
        logger.error(f"Error en marcar_mesa_disponible: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@mesa_estatus_bp.route('/en-limpieza', methods=['GET'])
@jwt_required()
def listar_mesas_en_limpieza():
    """
    Listar todas las mesas que están en limpieza.
    ---
    tags:
      - Mesas - Estados
    summary: "Listar Mesas en Limpieza"
    description: Retorna todas las mesas que están actualmente en estado de limpieza (estatus=3). Útil para el equipo de limpieza saber qué mesas necesitan atención.
    parameters:
      - in: query
        name: sucursal_id
        type: integer
        required: false
        description: "Filtrar por sucursal (opcional). Ej: ?sucursal_id=1"
    responses:
      200:
        description: "Lista de mesas en limpieza obtenida exitosamente"
        schema:
          type: object
          properties:
            mesas:
              type: array
              items:
                type: object
                properties:
                  id_mesa_estatus:
                    type: integer
                  mesa_id:
                    type: integer
                  estatus:
                    type: integer
                    example: 3
                  estatus_display:
                    type: string
                    example: "En Limpieza"
                  cambio_por:
                    type: integer
                    nullable: true
                  notas:
                    type: string
                  updated_at:
                    type: string
                    format: date-time
            total:
              type: integer
              example: 3
      500:
        description: "Error interno del servidor"
    """
    try:
        sucursal_id = request.args.get('sucursal_id', type=int)
        mesas = MesaEstatusDAO.obtener_mesas_en_limpieza(sucursal_id)
        
        # Agregar display a cada mesa
        estatus_map = {1: "Disponible", 2: "Ocupada", 3: "En Limpieza", 4: "Fuera de Servicio"}
        for mesa in mesas:
            mesa['estatus_display'] = estatus_map.get(mesa['estatus'], 'Desconocido')
        
        return jsonify({
            "mesas": mesas,
            "total": len(mesas)
        }), 200
        
    except Exception as e:
        logger.error(f"Error en listar_mesas_en_limpieza: {str(e)}")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500
