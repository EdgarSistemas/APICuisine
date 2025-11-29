"""
DashboardController - Endpoints REST para Dashboard y Métricas
Consolidación de datos para gráficas y KPIs del sistema
"""

import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import pytz

from src.services.dashboard.dashboard_service import DashboardService
from src.core.utils.multitenant import obtener_sucursales_usuario, validar_acceso_sucursal

logger = logging.getLogger(__name__)

# Blueprint para dashboard
bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

# Zona horaria de México
TZ_MEXICO = pytz.timezone('America/Mexico_City')


def parse_fechas(data: dict) -> tuple:
    """Helper para parsear fechas del request (formato yyyy-mm-dd)"""
    ahora = datetime.now(TZ_MEXICO).replace(tzinfo=None)
    
    # Por defecto: últimos 30 días
    fecha_desde = data.get('fecha_desde')
    fecha_hasta = data.get('fecha_hasta')
    
    if fecha_desde:
        if isinstance(fecha_desde, str):
            # Soportar formato yyyy-mm-dd
            if 'T' in fecha_desde:
                fecha_desde = datetime.fromisoformat(fecha_desde.replace('Z', ''))
            else:
                fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d')
    else:
        fecha_desde = ahora - timedelta(days=30)
    
    if fecha_hasta:
        if isinstance(fecha_hasta, str):
            # Soportar formato yyyy-mm-dd
            if 'T' in fecha_hasta:
                fecha_hasta = datetime.fromisoformat(fecha_hasta.replace('Z', ''))
            else:
                fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d')
                # Ajustar al final del día
                fecha_hasta = fecha_hasta.replace(hour=23, minute=59, second=59)
    else:
        fecha_hasta = ahora
    
    return fecha_desde, fecha_hasta


# ============================================================================
# 1. VENTAS/PAGOS
# ============================================================================

@bp.route('/ventas/periodo', methods=['POST'])
@jwt_required()
def ventas_periodo():
    """
    Ventas agrupadas por período
    ---
    tags:
      - Dashboard - Ventas
    security:
      - Bearer: []
    summary: Gráfica 1 - Ventas por Período
    description: |
      Obtiene las ventas agrupadas por día, semana o mes.
      Ideal para gráficas de línea o área que muestran tendencias de ventas.
      Incluye total de ventas, propinas y cantidad de transacciones por período.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            sucursal_id:
              type: integer
              description: ID de sucursal. Si no se envía, usa la del usuario.
              example: 1
            fecha_desde:
              type: string
              format: date
              description: Fecha inicial en formato yyyy-mm-dd. Default - 30 días atrás.
              example: "2025-01-01"
            fecha_hasta:
              type: string
              format: date
              description: Fecha final en formato yyyy-mm-dd. Default - hoy.
              example: "2025-01-31"
            agrupar_por:
              type: string
              enum: [dia, semana, mes]
              description: Cómo agrupar los resultados.
              default: dia
              example: "dia"
    responses:
      200:
        description: Datos de ventas por período
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                type: object
                properties:
                  periodo:
                    type: string
                    example: "2025-01-15"
                  cantidad:
                    type: integer
                    example: 25
                  total:
                    type: number
                    example: 12500.00
                  propinas:
                    type: number
                    example: 850.00
            resumen:
              type: object
              properties:
                total_ventas:
                  type: number
                total_propinas:
                  type: number
                total_transacciones:
                  type: integer
                ticket_promedio:
                  type: number
      401:
        description: Token no válido o expirado
      403:
        description: Sin acceso a la sucursal
    """
    try:
        current_user = get_jwt_identity()
        data = request.get_json() or {}
        
        sucursal_id = data.get('sucursal_id')
        if not sucursal_id:
            sucursales = obtener_sucursales_usuario(current_user)
            if sucursales:
                sucursal_id = sucursales[0]
        
        if not validar_acceso_sucursal(current_user, sucursal_id):
            return jsonify({'error': 'Sin acceso a esta sucursal'}), 403
        
        fecha_desde, fecha_hasta = parse_fechas(data)
        agrupar_por = data.get('agrupar_por', 'dia')
        
        resultado = DashboardService.obtener_ventas_periodo(
            sucursal_id, fecha_desde, fecha_hasta, agrupar_por
        )
        
        return jsonify(resultado), 200 if resultado['success'] else 500
        
    except Exception as e:
        logger.error(f"Error en ventas_periodo: {str(e)}")
        return jsonify({'error': str(e)}), 500


@bp.route('/ventas/sucursales', methods=['POST'])
@jwt_required()
def ventas_por_sucursal():
    """
    Ventas totales por sucursal
    ---
    tags:
      - Dashboard - Ventas
    security:
      - Bearer: []
    summary: Gráfica 2 - Ventas por Sucursal
    description: |
      Comparativa de ventas entre todas las sucursales.
      Útil para gráficas de barras comparativas entre sucursales.
      Solo administradores pueden ver todas las sucursales.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            fecha_desde:
              type: string
              format: date
              description: Fecha inicial en formato yyyy-mm-dd. Default - 30 días atrás.
              example: "2025-01-01"
            fecha_hasta:
              type: string
              format: date
              description: Fecha final en formato yyyy-mm-dd. Default - hoy.
              example: "2025-01-31"
    responses:
      200:
        description: Datos de ventas por sucursal
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                type: object
                properties:
                  sucursal_id:
                    type: integer
                    example: 1
                  sucursal_nombre:
                    type: string
                    example: "Sucursal Centro"
                  cantidad:
                    type: integer
                    example: 150
                  total:
                    type: number
                    example: 75000.00
      401:
        description: Token no válido o expirado
    """
    try:
        data = request.get_json() or {}
        fecha_desde, fecha_hasta = parse_fechas(data)
        
        resultado = DashboardService.obtener_ventas_por_sucursal(fecha_desde, fecha_hasta)
        
        return jsonify(resultado), 200 if resultado['success'] else 500
        
    except Exception as e:
        logger.error(f"Error en ventas_por_sucursal: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# 2. PEDIDOS
# ============================================================================

@bp.route('/pedidos/estados', methods=['POST'])
@jwt_required()
def pedidos_por_estado():
    """
    Distribución de pedidos por estado
    ---
    tags:
      - Dashboard - Pedidos
    security:
      - Bearer: []
    summary: Gráfica 5 - Pedidos por Estado
    description: |
      Muestra cuántos pedidos hay en cada estado (Iniciado, Completo, Cancelado, Pagado).
      Ideal para gráficas de pastel o dona.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            sucursal_id:
              type: integer
              description: ID de sucursal. Si no se envía, usa la del usuario.
              example: 1
            fecha_desde:
              type: string
              format: date
              description: Fecha inicial en formato yyyy-mm-dd. Default - 30 días atrás.
              example: "2025-01-01"
            fecha_hasta:
              type: string
              format: date
              description: Fecha final en formato yyyy-mm-dd. Default - hoy.
              example: "2025-01-31"
    responses:
      200:
        description: Datos de pedidos por estado
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                type: object
                properties:
                  estado:
                    type: integer
                    example: 3
                  estado_nombre:
                    type: string
                    example: "Completo"
                  cantidad:
                    type: integer
                    example: 85
      401:
        description: Token no válido o expirado
    """
    try:
        current_user = get_jwt_identity()
        data = request.get_json() or {}
        
        sucursal_id = data.get('sucursal_id')
        if not sucursal_id:
            sucursales = obtener_sucursales_usuario(current_user)
            if sucursales:
                sucursal_id = sucursales[0]
        
        fecha_desde, fecha_hasta = parse_fechas(data)
        
        resultado = DashboardService.obtener_pedidos_por_estado(
            sucursal_id, fecha_desde, fecha_hasta
        )
        
        return jsonify(resultado), 200 if resultado['success'] else 500
        
    except Exception as e:
        logger.error(f"Error en pedidos_por_estado: {str(e)}")
        return jsonify({'error': str(e)}), 500


@bp.route('/pedidos/tipos', methods=['POST'])
@jwt_required()
def pedidos_por_tipo():
    """
    Dine-in vs Takeaway
    ---
    tags:
      - Dashboard - Pedidos
    security:
      - Bearer: []
    summary: Gráfica 6 - Dine-in vs Takeaway
    description: |
      Compara pedidos para comer aquí (Dine-in) vs para llevar (Takeaway).
      Útil para gráficas de barras o pastel.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            sucursal_id:
              type: integer
              description: ID de sucursal. Si no se envía, usa la del usuario.
              example: 1
            fecha_desde:
              type: string
              format: date
              description: Fecha inicial en formato yyyy-mm-dd. Default - 30 días atrás.
              example: "2025-01-01"
            fecha_hasta:
              type: string
              format: date
              description: Fecha final en formato yyyy-mm-dd. Default - hoy.
              example: "2025-01-31"
    responses:
      200:
        description: Datos de tipos de pedido
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                type: object
                properties:
                  tipo:
                    type: integer
                    example: 1
                  tipo_nombre:
                    type: string
                    example: "Dine-in"
                  cantidad:
                    type: integer
                    example: 200
      401:
        description: Token no válido o expirado
    """
    try:
        current_user = get_jwt_identity()
        data = request.get_json() or {}
        
        sucursal_id = data.get('sucursal_id')
        if not sucursal_id:
            sucursales = obtener_sucursales_usuario(current_user)
            if sucursales:
                sucursal_id = sucursales[0]
        
        fecha_desde, fecha_hasta = parse_fechas(data)
        
        resultado = DashboardService.obtener_pedidos_por_tipo(
            sucursal_id, fecha_desde, fecha_hasta
        )
        
        return jsonify(resultado), 200 if resultado['success'] else 500
        
    except Exception as e:
        logger.error(f"Error en pedidos_por_tipo: {str(e)}")
        return jsonify({'error': str(e)}), 500


@bp.route('/pedidos/horas', methods=['POST'])
@jwt_required()
def pedidos_por_hora():
    """
    Pedidos por hora del día
    ---
    tags:
      - Dashboard - Pedidos
    security:
      - Bearer: []
    summary: Gráfica 7 - Pedidos por Hora
    description: |
      Muestra en qué horas del día hay más pedidos.
      Para identificar horas pico. Ideal para gráfica de barras por hora.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            sucursal_id:
              type: integer
              description: ID de sucursal. Si no se envía, usa la del usuario.
              example: 1
            fecha_desde:
              type: string
              format: date
              description: Fecha inicial en formato yyyy-mm-dd. Default - 30 días atrás.
              example: "2025-01-01"
            fecha_hasta:
              type: string
              format: date
              description: Fecha final en formato yyyy-mm-dd. Default - hoy.
              example: "2025-01-31"
    responses:
      200:
        description: Datos de pedidos por hora
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                type: object
                properties:
                  hora:
                    type: integer
                    example: 13
                  hora_display:
                    type: string
                    example: "13:00"
                  cantidad:
                    type: integer
                    example: 60
      401:
        description: Token no válido o expirado
    """
    try:
        current_user = get_jwt_identity()
        data = request.get_json() or {}
        
        sucursal_id = data.get('sucursal_id')
        if not sucursal_id:
            sucursales = obtener_sucursales_usuario(current_user)
            if sucursales:
                sucursal_id = sucursales[0]
        
        fecha_desde, fecha_hasta = parse_fechas(data)
        
        resultado = DashboardService.obtener_pedidos_por_hora(
            sucursal_id, fecha_desde, fecha_hasta
        )
        
        return jsonify(resultado), 200 if resultado['success'] else 500
        
    except Exception as e:
        logger.error(f"Error en pedidos_por_hora: {str(e)}")
        return jsonify({'error': str(e)}), 500


@bp.route('/pedidos/top-productos', methods=['POST'])
@jwt_required()
def top_productos():
    """
    Productos más vendidos
    ---
    tags:
      - Dashboard - Pedidos
    security:
      - Bearer: []
    summary: Gráfica 8 - Top Productos
    description: |
      Los productos más vendidos.
      Ideal para gráfica de barras horizontales tipo ranking.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            sucursal_id:
              type: integer
              description: ID de sucursal. Si no se envía, usa la del usuario.
              example: 1
            fecha_desde:
              type: string
              format: date
              description: Fecha inicial en formato yyyy-mm-dd. Default - 30 días atrás.
              example: "2025-01-01"
            fecha_hasta:
              type: string
              format: date
              description: Fecha final en formato yyyy-mm-dd. Default - hoy.
              example: "2025-01-31"
            top_n:
              type: integer
              description: Cantidad de productos a mostrar. Default 10.
              default: 10
              example: 10
    responses:
      200:
        description: Top productos
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                type: object
                properties:
                  producto_id:
                    type: integer
                    example: 15
                  producto_nombre:
                    type: string
                    example: "Hamburguesa Clásica"
                  cantidad_total:
                    type: integer
                    example: 250
                  veces_pedido:
                    type: integer
                    example: 200
      401:
        description: Token no válido o expirado
    """
    try:
        current_user = get_jwt_identity()
        data = request.get_json() or {}
        
        sucursal_id = data.get('sucursal_id')
        if not sucursal_id:
            sucursales = obtener_sucursales_usuario(current_user)
            if sucursales:
                sucursal_id = sucursales[0]
        
        fecha_desde, fecha_hasta = parse_fechas(data)
        top_n = data.get('top_n', 10)
        
        resultado = DashboardService.obtener_productos_mas_vendidos(
            sucursal_id, fecha_desde, fecha_hasta, top_n
        )
        
        return jsonify(resultado), 200 if resultado['success'] else 500
        
    except Exception as e:
        logger.error(f"Error en top_productos: {str(e)}")
        return jsonify({'error': str(e)}), 500


@bp.route('/pedidos/top-combos', methods=['POST'])
@jwt_required()
def top_combos():
    """
    Combos más vendidos
    ---
    tags:
      - Dashboard - Pedidos
    security:
      - Bearer: []
    summary: Gráfica 9 - Top Combos
    description: |
      Los combos más vendidos.
      Igual que top productos pero para combos.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            sucursal_id:
              type: integer
              description: ID de sucursal. Si no se envía, usa la del usuario.
              example: 1
            fecha_desde:
              type: string
              format: date
              description: Fecha inicial en formato yyyy-mm-dd. Default - 30 días atrás.
              example: "2025-01-01"
            fecha_hasta:
              type: string
              format: date
              description: Fecha final en formato yyyy-mm-dd. Default - hoy.
              example: "2025-01-31"
            top_n:
              type: integer
              description: Cantidad de combos a mostrar. Default 10.
              default: 10
              example: 10
    responses:
      200:
        description: Top combos
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                type: object
                properties:
                  combo_id:
                    type: integer
                    example: 3
                  combo_nombre:
                    type: string
                    example: "Combo Familiar"
                  cantidad_total:
                    type: integer
                    example: 85
                  veces_pedido:
                    type: integer
                    example: 85
      401:
        description: Token no válido o expirado
    """
    try:
        current_user = get_jwt_identity()
        data = request.get_json() or {}
        
        sucursal_id = data.get('sucursal_id')
        if not sucursal_id:
            sucursales = obtener_sucursales_usuario(current_user)
            if sucursales:
                sucursal_id = sucursales[0]
        
        fecha_desde, fecha_hasta = parse_fechas(data)
        top_n = data.get('top_n', 10)
        
        resultado = DashboardService.obtener_combos_mas_vendidos(
            sucursal_id, fecha_desde, fecha_hasta, top_n
        )
        
        return jsonify(resultado), 200 if resultado['success'] else 500
        
    except Exception as e:
        logger.error(f"Error en top_combos: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# 3. RESERVAS
# ============================================================================

@bp.route('/reservas/estados', methods=['POST'])
@jwt_required()
def reservas_por_estado():
    """
    Distribución de reservas por estado
    ---
    tags:
      - Dashboard - Reservas
    security:
      - Bearer: []
    summary: Gráfica 10 - Reservas por Estado
    description: |
      Distribución de reservas por estado (Programada, En Curso, Completada, No Show, Cancelada).
      Ideal para gráficas de pastel o dona.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            sucursal_id:
              type: integer
              description: ID de sucursal. Si no se envía, usa la del usuario.
              example: 1
            fecha_desde:
              type: string
              format: date
              description: Fecha inicial en formato yyyy-mm-dd. Default - 30 días atrás.
              example: "2025-01-01"
            fecha_hasta:
              type: string
              format: date
              description: Fecha final en formato yyyy-mm-dd. Default - hoy.
              example: "2025-01-31"
    responses:
      200:
        description: Datos de reservas por estado
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                type: object
                properties:
                  estado:
                    type: integer
                    example: 3
                  estado_nombre:
                    type: string
                    example: "Completada"
                  cantidad:
                    type: integer
                    example: 180
      401:
        description: Token no válido o expirado
    """
    try:
        current_user = get_jwt_identity()
        data = request.get_json() or {}
        
        sucursal_id = data.get('sucursal_id')
        if not sucursal_id:
            sucursales = obtener_sucursales_usuario(current_user)
            if sucursales:
                sucursal_id = sucursales[0]
        
        fecha_desde, fecha_hasta = parse_fechas(data)
        
        resultado = DashboardService.obtener_reservas_por_estado(
            sucursal_id, fecha_desde, fecha_hasta
        )
        
        return jsonify(resultado), 200 if resultado['success'] else 500
        
    except Exception as e:
        logger.error(f"Error en reservas_por_estado: {str(e)}")
        return jsonify({'error': str(e)}), 500


@bp.route('/reservas/tasa-noshow', methods=['POST'])
@jwt_required()
def tasa_noshow():
    """
    Tasa de No-Show
    ---
    tags:
      - Dashboard - Reservas
    security:
      - Bearer: []
    summary: Gráfica 12 - Tasa de No-Show
    description: |
      Calcula el porcentaje de clientes que hicieron reserva pero no llegaron.
      Importante para medir pérdida de oportunidad.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            sucursal_id:
              type: integer
              description: ID de sucursal. Si no se envía, usa la del usuario.
              example: 1
            fecha_desde:
              type: string
              format: date
              description: Fecha inicial en formato yyyy-mm-dd. Default - 30 días atrás.
              example: "2025-01-01"
            fecha_hasta:
              type: string
              format: date
              description: Fecha final en formato yyyy-mm-dd. Default - hoy.
              example: "2025-01-31"
    responses:
      200:
        description: Tasa de No-Show
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: object
              properties:
                total_reservas:
                  type: integer
                  example: 197
                noshows:
                  type: integer
                  example: 12
                tasa_noshow:
                  type: number
                  example: 6.09
      401:
        description: Token no válido o expirado
    """
    try:
        current_user = get_jwt_identity()
        data = request.get_json() or {}
        
        sucursal_id = data.get('sucursal_id')
        if not sucursal_id:
            sucursales = obtener_sucursales_usuario(current_user)
            if sucursales:
                sucursal_id = sucursales[0]
        
        fecha_desde, fecha_hasta = parse_fechas(data)
        
        resultado = DashboardService.obtener_tasa_noshow(
            sucursal_id, fecha_desde, fecha_hasta
        )
        
        return jsonify(resultado), 200 if resultado['success'] else 500
        
    except Exception as e:
        logger.error(f"Error en tasa_noshow: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# 4. INVENTARIO
# ============================================================================

@bp.route('/inventario/bajo-stock', methods=['POST'])
@jwt_required()
def insumos_bajo_stock():
    """
    Insumos bajo stock mínimo
    ---
    tags:
      - Dashboard - Inventario
    security:
      - Bearer: []
    summary: Gráfica 18 - Insumos Bajo Stock
    description: |
      Lista de insumos que están por debajo del stock mínimo configurado.
      Alertas de reabastecimiento.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            sucursal_id:
              type: integer
              description: ID de sucursal. Si no se envía, usa la del usuario.
              example: 1
    responses:
      200:
        description: Insumos bajo stock
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                type: object
                properties:
                  insumo_id:
                    type: integer
                    example: 5
                  insumo_nombre:
                    type: string
                    example: "Carne de Res"
                  cantidad_actual:
                    type: number
                    example: 8.5
                  minimo_stock:
                    type: number
                    example: 15.0
                  faltante:
                    type: number
                    example: 6.5
            total:
              type: integer
              example: 2
      401:
        description: Token no válido o expirado
    """
    try:
        current_user = get_jwt_identity()
        data = request.get_json() or {}
        
        sucursal_id = data.get('sucursal_id')
        if not sucursal_id:
            sucursales = obtener_sucursales_usuario(current_user)
            if sucursales:
                sucursal_id = sucursales[0]
        
        resultado = DashboardService.obtener_insumos_bajo_stock(sucursal_id)
        
        return jsonify(resultado), 200 if resultado['success'] else 500
        
    except Exception as e:
        logger.error(f"Error en insumos_bajo_stock: {str(e)}")
        return jsonify({'error': str(e)}), 500


@bp.route('/inventario/lotes-por-vencer', methods=['POST'])
@jwt_required()
def lotes_por_vencer():
    """
    Lotes próximos a vencer
    ---
    tags:
      - Dashboard - Inventario
    security:
      - Bearer: []
    summary: Gráfica 19 - Lotes por Vencer
    description: |
      Lista de lotes que vencen próximamente con niveles de urgencia:
      - Crítico: <= 7 días
      - Alto: <= 14 días
      - Medio: > 14 días
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            sucursal_id:
              type: integer
              description: ID de sucursal. Si no se envía, usa la del usuario.
              example: 1
            dias:
              type: integer
              description: Días de anticipación para buscar lotes. Default 30.
              default: 30
              example: 30
    responses:
      200:
        description: Lotes por vencer
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                type: object
                properties:
                  lote_id:
                    type: integer
                    example: 45
                  insumo_nombre:
                    type: string
                    example: "Queso Oaxaca"
                  lote:
                    type: string
                    example: "L2025-001"
                  fecha_caducidad:
                    type: string
                    example: "2025-01-20"
                  dias_para_vencer:
                    type: integer
                    example: 5
                  cantidad_disponible:
                    type: number
                    example: 15.5
                  urgencia:
                    type: string
                    example: "critico"
            resumen:
              type: object
              properties:
                total:
                  type: integer
                  example: 8
                criticos:
                  type: integer
                  example: 2
                altos:
                  type: integer
                  example: 3
                medios:
                  type: integer
                  example: 3
      401:
        description: Token no válido o expirado
    """
    try:
        current_user = get_jwt_identity()
        data = request.get_json() or {}
        
        sucursal_id = data.get('sucursal_id')
        if not sucursal_id:
            sucursales = obtener_sucursales_usuario(current_user)
            if sucursales:
                sucursal_id = sucursales[0]
        
        dias = data.get('dias', 30)
        
        resultado = DashboardService.obtener_lotes_proximos_vencer(sucursal_id, dias)
        
        return jsonify(resultado), 200 if resultado['success'] else 500
        
    except Exception as e:
        logger.error(f"Error en lotes_por_vencer: {str(e)}")
        return jsonify({'error': str(e)}), 500


@bp.route('/inventario/lotes-vencidos', methods=['POST'])
@jwt_required()
def lotes_vencidos():
    """
    Lotes vencidos
    ---
    tags:
      - Dashboard - Inventario
    security:
      - Bearer: []
    summary: Gráfica 20 - Lotes Vencidos
    description: |
      Lista de lotes que YA vencieron y siguen en inventario.
      Muestra el cálculo de pérdida económica total.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            sucursal_id:
              type: integer
              description: ID de sucursal. Si no se envía, usa la del usuario.
              example: 1
    responses:
      200:
        description: Lotes vencidos
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                type: object
                properties:
                  lote_id:
                    type: integer
                    example: 32
                  insumo_nombre:
                    type: string
                    example: "Leche Entera"
                  lote:
                    type: string
                    example: "L2024-089"
                  fecha_caducidad:
                    type: string
                    example: "2025-01-10"
                  cantidad_disponible:
                    type: number
                    example: 5.0
                  costo_total_perdida:
                    type: number
                    example: 175.00
            resumen:
              type: object
              properties:
                total:
                  type: integer
                  example: 1
                perdida_total:
                  type: number
                  example: 175.00
      401:
        description: Token no válido o expirado
    """
    try:
        current_user = get_jwt_identity()
        data = request.get_json() or {}
        
        sucursal_id = data.get('sucursal_id')
        if not sucursal_id:
            sucursales = obtener_sucursales_usuario(current_user)
            if sucursales:
                sucursal_id = sucursales[0]
        
        resultado = DashboardService.obtener_lotes_vencidos(sucursal_id)
        
        return jsonify(resultado), 200 if resultado['success'] else 500
        
    except Exception as e:
        logger.error(f"Error en lotes_vencidos: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# 5. CALIFICACIONES
# ============================================================================

@bp.route('/calificaciones/promedio', methods=['POST'])
@jwt_required()
def promedio_calificaciones():
    """
    Promedio general de calificaciones
    ---
    tags:
      - Dashboard - Calificaciones
    security:
      - Bearer: []
    summary: Gráfica 22 - Promedio Calificaciones
    description: |
      Promedio general de calificaciones del servicio.
      Muestra también la mínima y máxima recibida.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            sucursal_id:
              type: integer
              description: ID de sucursal. Si no se envía, usa la del usuario.
              example: 1
            fecha_desde:
              type: string
              format: date
              description: Fecha inicial en formato yyyy-mm-dd. Default - 30 días atrás.
              example: "2025-01-01"
            fecha_hasta:
              type: string
              format: date
              description: Fecha final en formato yyyy-mm-dd. Default - hoy.
              example: "2025-01-31"
    responses:
      200:
        description: Promedio de calificaciones
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: object
              properties:
                promedio:
                  type: number
                  example: 4.35
                total_calificaciones:
                  type: integer
                  example: 245
                calificacion_minima:
                  type: integer
                  example: 1
                calificacion_maxima:
                  type: integer
                  example: 5
      401:
        description: Token no válido o expirado
    """
    try:
        current_user = get_jwt_identity()
        data = request.get_json() or {}
        
        sucursal_id = data.get('sucursal_id')
        if not sucursal_id:
            sucursales = obtener_sucursales_usuario(current_user)
            if sucursales:
                sucursal_id = sucursales[0]
        
        fecha_desde, fecha_hasta = parse_fechas(data)
        
        resultado = DashboardService.obtener_promedio_calificaciones(
            sucursal_id, fecha_desde, fecha_hasta
        )
        
        return jsonify(resultado), 200 if resultado['success'] else 500
        
    except Exception as e:
        logger.error(f"Error en promedio_calificaciones: {str(e)}")
        return jsonify({'error': str(e)}), 500


@bp.route('/calificaciones/top-empleados', methods=['POST'])
@jwt_required()
def top_empleados():
    """
    Top empleados por calificación
    ---
    tags:
      - Dashboard - Calificaciones
    security:
      - Bearer: []
    summary: Gráfica 23 - Top Empleados
    description: |
      Ranking de empleados mejor calificados por los clientes.
      Para reconocimiento y gamificación.
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            sucursal_id:
              type: integer
              description: ID de sucursal. Si no se envía, usa la del usuario.
              example: 1
            fecha_desde:
              type: string
              format: date
              description: Fecha inicial en formato yyyy-mm-dd. Default - 30 días atrás.
              example: "2025-01-01"
            fecha_hasta:
              type: string
              format: date
              description: Fecha final en formato yyyy-mm-dd. Default - hoy.
              example: "2025-01-31"
            top_n:
              type: integer
              description: Cantidad de empleados a mostrar. Default 10.
              default: 10
              example: 10
    responses:
      200:
        description: Top empleados
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                type: object
                properties:
                  empleado_id:
                    type: integer
                    example: 15
                  empleado_nombre:
                    type: string
                    example: "María García"
                  promedio:
                    type: number
                    example: 4.85
                  total_calificaciones:
                    type: integer
                    example: 45
      401:
        description: Token no válido o expirado
    """
    try:
        current_user = get_jwt_identity()
        data = request.get_json() or {}
        
        sucursal_id = data.get('sucursal_id')
        if not sucursal_id:
            sucursales = obtener_sucursales_usuario(current_user)
            if sucursales:
                sucursal_id = sucursales[0]
        
        fecha_desde, fecha_hasta = parse_fechas(data)
        top_n = data.get('top_n', 10)
        
        resultado = DashboardService.obtener_top_empleados(
            sucursal_id, fecha_desde, fecha_hasta, top_n
        )
        
        return jsonify(resultado), 200 if resultado['success'] else 500
        
    except Exception as e:
        logger.error(f"Error en top_empleados: {str(e)}")
        return jsonify({'error': str(e)}), 500
