"""
DashboardService - Lógica de negocio para métricas del Dashboard
Consolidación de datos para gráficas y KPIs
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
import pytz

from src.core.db.session_manager import get_db_session
from src.models.pagos.pago_model import Pago
from src.models.operaciones.pedido_model import Pedido
from src.models.operaciones.pedido_item_model import PedidoItem
from src.models.operaciones.reserva_model import Reserva
from src.models.servicio.calificacion_model import Calificacion
from src.models.inventario.existencia_model import Existencia
from src.models.inventario.insumo_model import Insumo
from src.models.catalogos.producto_model import Producto
from src.models.catalogos.combo_model import Combo
from src.models import Sucursal
from src.dao.inventario.lote_dao import LoteDAO
from sqlalchemy import func, and_, or_, case, extract, cast, Date, literal_column

logger = logging.getLogger(__name__)

# Zona horaria de México
TZ_MEXICO = pytz.timezone('America/Mexico_City')


class DashboardService:
    """Servicio para métricas del Dashboard"""
    
    # =========================================================================
    # 1. VENTAS/PAGOS
    # =========================================================================
    
    @staticmethod
    def obtener_ventas_periodo(sucursal_id: int, fecha_desde: datetime, fecha_hasta: datetime, 
                                agrupar_por: str = 'dia') -> dict:
        """
        Obtiene ventas agrupadas por día, semana o mes.
        
        Args:
            sucursal_id: ID de la sucursal
            fecha_desde: Fecha inicio
            fecha_hasta: Fecha fin
            agrupar_por: 'dia', 'semana', 'mes'
        """
        try:
            with get_db_session() as session:
                # Filtro base
                filtros = [
                    Pago.sucursal_id == sucursal_id,
                    Pago.estatus == 2,  # Solo pagados
                    Pago.created_at >= fecha_desde,
                    Pago.created_at <= fecha_hasta
                ]
                
                # Determinar agrupación - SQL Server compatible
                if agrupar_por == 'dia':
                    # SQL Server: CONVERT(DATE, created_at)
                    grupo = cast(Pago.created_at, Date)
                elif agrupar_por == 'semana':
                    # SQL Server: DATEPART(YEAR, created_at) * 100 + DATEPART(WEEK, created_at)
                    grupo = func.datepart(literal_column("'YEAR'"), Pago.created_at) * 100 + func.datepart(literal_column("'WEEK'"), Pago.created_at)
                else:  # mes
                    # SQL Server: FORMAT(created_at, 'yyyy-MM')
                    grupo = func.format(Pago.created_at, 'yyyy-MM')
                
                resultados = session.query(
                    grupo.label('periodo'),
                    func.count(Pago.id_pago).label('cantidad'),
                    func.sum(Pago.monto).label('total'),
                    func.sum(Pago.propina).label('propinas')
                ).filter(
                    and_(*filtros)
                ).group_by(grupo).order_by(grupo).all()
                
                data = [
                    {
                        'periodo': str(r.periodo),
                        'cantidad': r.cantidad,
                        'total': float(r.total or 0),
                        'propinas': float(r.propinas or 0)
                    }
                    for r in resultados
                ]
                
                # Totales
                total_ventas = sum(d['total'] for d in data)
                total_propinas = sum(d['propinas'] for d in data)
                total_transacciones = sum(d['cantidad'] for d in data)
                
                return {
                    'success': True,
                    'data': data,
                    'resumen': {
                        'total_ventas': total_ventas,
                        'total_propinas': total_propinas,
                        'total_transacciones': total_transacciones,
                        'ticket_promedio': total_ventas / total_transacciones if total_transacciones > 0 else 0
                    }
                }
                
        except Exception as e:
            logger.error(f"Error en obtener_ventas_periodo: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def obtener_ventas_por_sucursal(fecha_desde: datetime, fecha_hasta: datetime) -> dict:
        """Obtiene ventas totales por sucursal"""
        try:
            with get_db_session() as session:
                resultados = session.query(
                    Pago.sucursal_id,
                    Sucursal.nombre.label('sucursal_nombre'),
                    func.count(Pago.id_pago).label('cantidad'),
                    func.sum(Pago.monto).label('total')
                ).join(
                    Sucursal, Pago.sucursal_id == Sucursal.id_sucursal
                ).filter(
                    and_(
                        Pago.estatus == 2,
                        Pago.created_at >= fecha_desde,
                        Pago.created_at <= fecha_hasta
                    )
                ).group_by(Pago.sucursal_id, Sucursal.nombre).all()
                
                data = [
                    {
                        'sucursal_id': r.sucursal_id,
                        'sucursal_nombre': r.sucursal_nombre,
                        'cantidad': r.cantidad,
                        'total': float(r.total or 0)
                    }
                    for r in resultados
                ]
                
                return {'success': True, 'data': data}
                
        except Exception as e:
            logger.error(f"Error en obtener_ventas_por_sucursal: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def obtener_ventas_por_metodo_pago(sucursal_id: int, fecha_desde: datetime, fecha_hasta: datetime) -> dict:
        """Obtiene distribución de ventas por método de pago"""
        try:
            with get_db_session() as session:
                resultados = session.query(
                    Pago.metodo_pago,
                    func.count(Pago.id_pago).label('cantidad'),
                    func.sum(Pago.monto).label('total')
                ).filter(
                    and_(
                        Pago.sucursal_id == sucursal_id,
                        Pago.estatus == 2,
                        Pago.created_at >= fecha_desde,
                        Pago.created_at <= fecha_hasta
                    )
                ).group_by(Pago.metodo_pago).all()
                
                # Mapeo de métodos de pago
                metodos_map = {
                    1: 'Efectivo',
                    2: 'Tarjeta Débito',
                    3: 'Tarjeta Crédito',
                    4: 'Transferencia',
                    5: 'Otro'
                }
                
                data = [
                    {
                        'metodo_pago': r.metodo_pago,
                        'metodo_nombre': metodos_map.get(r.metodo_pago, 'Desconocido'),
                        'cantidad': r.cantidad,
                        'total': float(r.total or 0)
                    }
                    for r in resultados
                ]
                
                return {'success': True, 'data': data}
                
        except Exception as e:
            logger.error(f"Error en obtener_ventas_por_metodo_pago: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # =========================================================================
    # 2. PEDIDOS
    # =========================================================================
    
    @staticmethod
    def obtener_pedidos_por_estado(sucursal_id: int, fecha_desde: datetime, fecha_hasta: datetime) -> dict:
        """Obtiene distribución de pedidos por estado"""
        try:
            with get_db_session() as session:
                resultados = session.query(
                    Pedido.estado_pedido,
                    func.count(Pedido.id_pedido).label('cantidad')
                ).filter(
                    and_(
                        Pedido.sucursal_id == sucursal_id,
                        Pedido.created_at >= fecha_desde,
                        Pedido.created_at <= fecha_hasta
                    )
                ).group_by(Pedido.estado_pedido).all()
                
                estados_map = {
                    0: 'Iniciado',
                    3: 'Completo',
                    4: 'Cancelado',
                    5: 'Pagado'
                }
                
                data = [
                    {
                        'estado': r.estado_pedido,
                        'estado_nombre': estados_map.get(r.estado_pedido, 'Desconocido'),
                        'cantidad': r.cantidad
                    }
                    for r in resultados
                ]
                
                return {'success': True, 'data': data}
                
        except Exception as e:
            logger.error(f"Error en obtener_pedidos_por_estado: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def obtener_pedidos_por_tipo(sucursal_id: int, fecha_desde: datetime, fecha_hasta: datetime) -> dict:
        """Obtiene distribución Dine-in vs Takeaway"""
        try:
            with get_db_session() as session:
                resultados = session.query(
                    Pedido.tipo_pedido,
                    func.count(Pedido.id_pedido).label('cantidad')
                ).filter(
                    and_(
                        Pedido.sucursal_id == sucursal_id,
                        Pedido.created_at >= fecha_desde,
                        Pedido.created_at <= fecha_hasta
                    )
                ).group_by(Pedido.tipo_pedido).all()
                
                tipos_map = {1: 'Dine-in', 2: 'Takeaway'}
                
                data = [
                    {
                        'tipo': r.tipo_pedido,
                        'tipo_nombre': tipos_map.get(r.tipo_pedido, 'Desconocido'),
                        'cantidad': r.cantidad
                    }
                    for r in resultados
                ]
                
                return {'success': True, 'data': data}
                
        except Exception as e:
            logger.error(f"Error en obtener_pedidos_por_tipo: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def obtener_pedidos_por_hora(sucursal_id: int, fecha_desde: datetime, fecha_hasta: datetime) -> dict:
        """Obtiene distribución de pedidos por hora del día"""
        try:
            with get_db_session() as session:
                resultados = session.query(
                    extract('hour', Pedido.created_at).label('hora'),
                    func.count(Pedido.id_pedido).label('cantidad')
                ).filter(
                    and_(
                        Pedido.sucursal_id == sucursal_id,
                        Pedido.created_at >= fecha_desde,
                        Pedido.created_at <= fecha_hasta
                    )
                ).group_by(extract('hour', Pedido.created_at)).order_by('hora').all()
                
                data = [
                    {
                        'hora': int(r.hora),
                        'hora_display': f"{int(r.hora):02d}:00",
                        'cantidad': r.cantidad
                    }
                    for r in resultados
                ]
                
                return {'success': True, 'data': data}
                
        except Exception as e:
            logger.error(f"Error en obtener_pedidos_por_hora: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def obtener_productos_mas_vendidos(sucursal_id: int, fecha_desde: datetime, 
                                        fecha_hasta: datetime, top_n: int = 10) -> dict:
        """Obtiene los productos más vendidos"""
        try:
            with get_db_session() as session:
                resultados = session.query(
                    PedidoItem.producto_id,
                    Producto.nombre.label('producto_nombre'),
                    func.sum(PedidoItem.cantidad).label('cantidad_total'),
                    func.count(PedidoItem.id_pedido_item).label('veces_pedido')
                ).join(
                    Producto, PedidoItem.producto_id == Producto.id_producto
                ).join(
                    Pedido, PedidoItem.pedido_id == Pedido.id_pedido
                ).filter(
                    and_(
                        Pedido.sucursal_id == sucursal_id,
                        Pedido.created_at >= fecha_desde,
                        Pedido.created_at <= fecha_hasta,
                        PedidoItem.producto_id.isnot(None),
                        Pedido.estado_pedido.in_([3, 5])  # Completo o Pagado
                    )
                ).group_by(
                    PedidoItem.producto_id, Producto.nombre
                ).order_by(
                    func.sum(PedidoItem.cantidad).desc()
                ).limit(top_n).all()
                
                data = [
                    {
                        'producto_id': r.producto_id,
                        'producto_nombre': r.producto_nombre,
                        'cantidad_total': int(r.cantidad_total),
                        'veces_pedido': r.veces_pedido
                    }
                    for r in resultados
                ]
                
                return {'success': True, 'data': data}
                
        except Exception as e:
            logger.error(f"Error en obtener_productos_mas_vendidos: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def obtener_combos_mas_vendidos(sucursal_id: int, fecha_desde: datetime, 
                                     fecha_hasta: datetime, top_n: int = 10) -> dict:
        """Obtiene los combos más vendidos"""
        try:
            with get_db_session() as session:
                resultados = session.query(
                    PedidoItem.combo_id,
                    Combo.nombre.label('combo_nombre'),
                    func.sum(PedidoItem.cantidad).label('cantidad_total'),
                    func.count(PedidoItem.id_pedido_item).label('veces_pedido')
                ).join(
                    Combo, PedidoItem.combo_id == Combo.id_combo
                ).join(
                    Pedido, PedidoItem.pedido_id == Pedido.id_pedido
                ).filter(
                    and_(
                        Pedido.sucursal_id == sucursal_id,
                        Pedido.created_at >= fecha_desde,
                        Pedido.created_at <= fecha_hasta,
                        PedidoItem.combo_id.isnot(None),
                        Pedido.estado_pedido.in_([3, 5])
                    )
                ).group_by(
                    PedidoItem.combo_id, Combo.nombre
                ).order_by(
                    func.sum(PedidoItem.cantidad).desc()
                ).limit(top_n).all()
                
                data = [
                    {
                        'combo_id': r.combo_id,
                        'combo_nombre': r.combo_nombre,
                        'cantidad_total': int(r.cantidad_total),
                        'veces_pedido': r.veces_pedido
                    }
                    for r in resultados
                ]
                
                return {'success': True, 'data': data}
                
        except Exception as e:
            logger.error(f"Error en obtener_combos_mas_vendidos: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # =========================================================================
    # 3. RESERVAS
    # =========================================================================
    
    @staticmethod
    def obtener_reservas_por_estado(sucursal_id: int, fecha_desde: datetime, fecha_hasta: datetime) -> dict:
        """Obtiene distribución de reservas por estado"""
        try:
            with get_db_session() as session:
                from src.models.operaciones.hold_mesa_model import HoldMesa
                from src.models.catalogos.mesa_model import Mesa
                from src.models.catalogos.area_model import Area
                
                # Join para filtrar por sucursal
                resultados = session.query(
                    Reserva.estatus,
                    func.count(Reserva.id_reserva).label('cantidad')
                ).join(
                    HoldMesa, Reserva.hold_id == HoldMesa.id_hold_mesa
                ).join(
                    Mesa, HoldMesa.mesa_id == Mesa.id_mesa
                ).join(
                    Area, Mesa.area_id == Area.id_area
                ).filter(
                    and_(
                        Area.sucursal_id == sucursal_id,
                        Reserva.inicio >= fecha_desde,
                        Reserva.inicio <= fecha_hasta
                    )
                ).group_by(Reserva.estatus).all()
                
                estados_map = {
                    1: 'Programada',
                    2: 'En Curso',
                    3: 'Completada',
                    4: 'No Show',
                    5: 'Cancelada'
                }
                
                data = [
                    {
                        'estado': r.estatus,
                        'estado_nombre': estados_map.get(r.estatus, 'Desconocido'),
                        'cantidad': r.cantidad
                    }
                    for r in resultados
                ]
                
                return {'success': True, 'data': data}
                
        except Exception as e:
            logger.error(f"Error en obtener_reservas_por_estado: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def obtener_tasa_noshow(sucursal_id: int, fecha_desde: datetime, fecha_hasta: datetime) -> dict:
        """Calcula la tasa de No-Show"""
        try:
            with get_db_session() as session:
                from src.models.operaciones.hold_mesa_model import HoldMesa
                from src.models.catalogos.mesa_model import Mesa
                from src.models.catalogos.area_model import Area
                
                # Total de reservas
                total = session.query(func.count(Reserva.id_reserva)).join(
                    HoldMesa, Reserva.hold_id == HoldMesa.id_hold_mesa
                ).join(
                    Mesa, HoldMesa.mesa_id == Mesa.id_mesa
                ).join(
                    Area, Mesa.area_id == Area.id_area
                ).filter(
                    and_(
                        Area.sucursal_id == sucursal_id,
                        Reserva.inicio >= fecha_desde,
                        Reserva.inicio <= fecha_hasta,
                        Reserva.estatus.in_([2, 3, 4])  # Solo finalizadas (no programadas ni canceladas)
                    )
                ).scalar() or 0
                
                # No-shows
                noshows = session.query(func.count(Reserva.id_reserva)).join(
                    HoldMesa, Reserva.hold_id == HoldMesa.id_hold_mesa
                ).join(
                    Mesa, HoldMesa.mesa_id == Mesa.id_mesa
                ).join(
                    Area, Mesa.area_id == Area.id_area
                ).filter(
                    and_(
                        Area.sucursal_id == sucursal_id,
                        Reserva.inicio >= fecha_desde,
                        Reserva.inicio <= fecha_hasta,
                        Reserva.estatus == 4
                    )
                ).scalar() or 0
                
                tasa = (noshows / total * 100) if total > 0 else 0
                
                return {
                    'success': True,
                    'data': {
                        'total_reservas': total,
                        'noshows': noshows,
                        'tasa_noshow': round(tasa, 2)
                    }
                }
                
        except Exception as e:
            logger.error(f"Error en obtener_tasa_noshow: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # =========================================================================
    # 4. INVENTARIO
    # =========================================================================
    
    @staticmethod
    def obtener_insumos_bajo_stock(sucursal_id: int) -> dict:
        """Obtiene insumos con stock bajo el mínimo"""
        try:
            with get_db_session() as session:
                resultados = session.query(
                    Existencia.insumo_id,
                    Insumo.nombre.label('insumo_nombre'),
                    Existencia.cantidad,
                    Insumo.minimo_stock,
                    (Insumo.minimo_stock - Existencia.cantidad).label('faltante')
                ).join(
                    Insumo, Existencia.insumo_id == Insumo.id_insumo
                ).filter(
                    and_(
                        Existencia.sucursal_id == sucursal_id,
                        Existencia.cantidad < Insumo.minimo_stock,
                        Insumo.es_activo == True
                    )
                ).order_by(
                    (Insumo.minimo_stock - Existencia.cantidad).desc()
                ).all()
                
                data = [
                    {
                        'insumo_id': r.insumo_id,
                        'insumo_nombre': r.insumo_nombre,
                        'cantidad_actual': float(r.cantidad),
                        'minimo_stock': float(r.minimo_stock),
                        'faltante': float(r.faltante)
                    }
                    for r in resultados
                ]
                
                return {
                    'success': True,
                    'data': data,
                    'total': len(data)
                }
                
        except Exception as e:
            logger.error(f"Error en obtener_insumos_bajo_stock: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def obtener_lotes_proximos_vencer(sucursal_id: int, dias: int = 30) -> dict:
        """Obtiene lotes próximos a vencer"""
        try:
            lotes = LoteDAO.obtener_lotes_proximos_a_vencer(sucursal_id, dias)
            
            # Contar por urgencia
            criticos = len([l for l in lotes if l.get('dias_para_vencer', 999) <= 7])
            altos = len([l for l in lotes if 7 < l.get('dias_para_vencer', 999) <= 14])
            medios = len([l for l in lotes if l.get('dias_para_vencer', 999) > 14])
            
            return {
                'success': True,
                'data': lotes,
                'resumen': {
                    'total': len(lotes),
                    'criticos': criticos,
                    'altos': altos,
                    'medios': medios
                }
            }
            
        except Exception as e:
            logger.error(f"Error en obtener_lotes_proximos_vencer: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def obtener_lotes_vencidos(sucursal_id: int) -> dict:
        """Obtiene lotes vencidos"""
        try:
            lotes = LoteDAO.obtener_lotes_vencidos(sucursal_id)
            
            # Calcular pérdida total
            perdida_total = sum(l.get('costo_total_perdida', 0) for l in lotes)
            
            return {
                'success': True,
                'data': lotes,
                'resumen': {
                    'total': len(lotes),
                    'perdida_total': perdida_total
                }
            }
            
        except Exception as e:
            logger.error(f"Error en obtener_lotes_vencidos: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # =========================================================================
    # 5. CALIFICACIONES
    # =========================================================================
    
    @staticmethod
    def obtener_promedio_calificaciones(sucursal_id: int, fecha_desde: datetime, fecha_hasta: datetime) -> dict:
        """Obtiene promedio general de calificaciones"""
        try:
            with get_db_session() as session:
                resultado = session.query(
                    func.avg(Calificacion.calificacion).label('promedio'),
                    func.count(Calificacion.id_calificacion).label('total'),
                    func.min(Calificacion.calificacion).label('minima'),
                    func.max(Calificacion.calificacion).label('maxima')
                ).join(
                    Pedido, Calificacion.pedido_id == Pedido.id_pedido
                ).filter(
                    and_(
                        Pedido.sucursal_id == sucursal_id,
                        Calificacion.created_at >= fecha_desde,
                        Calificacion.created_at <= fecha_hasta
                    )
                ).first()
                
                return {
                    'success': True,
                    'data': {
                        'promedio': round(float(resultado.promedio or 0), 2),
                        'total_calificaciones': resultado.total or 0,
                        'calificacion_minima': resultado.minima or 0,
                        'calificacion_maxima': resultado.maxima or 0
                    }
                }
                
        except Exception as e:
            logger.error(f"Error en obtener_promedio_calificaciones: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def obtener_top_empleados(sucursal_id: int, fecha_desde: datetime, 
                               fecha_hasta: datetime, top_n: int = 10) -> dict:
        """Obtiene top empleados por calificación"""
        try:
            with get_db_session() as session:
                from src.models.auth.usuario import Usuario
                
                resultados = session.query(
                    Calificacion.empleado_id,
                    Usuario.nombre.label('empleado_nombre'),
                    Usuario.apellido.label('empleado_apellido'),
                    func.avg(Calificacion.calificacion).label('promedio'),
                    func.count(Calificacion.id_calificacion).label('total')
                ).join(
                    Usuario, Calificacion.empleado_id == Usuario.id_usuario
                ).join(
                    Pedido, Calificacion.pedido_id == Pedido.id_pedido
                ).filter(
                    and_(
                        Pedido.sucursal_id == sucursal_id,
                        Calificacion.created_at >= fecha_desde,
                        Calificacion.created_at <= fecha_hasta
                    )
                ).group_by(
                    Calificacion.empleado_id, Usuario.nombre, Usuario.apellido
                ).order_by(
                    func.avg(Calificacion.calificacion).desc()
                ).limit(top_n).all()
                
                data = [
                    {
                        'empleado_id': r.empleado_id,
                        'empleado_nombre': f"{r.empleado_nombre} {r.empleado_apellido}",
                        'promedio': round(float(r.promedio), 2),
                        'total_calificaciones': r.total
                    }
                    for r in resultados
                ]
                
                return {'success': True, 'data': data}
                
        except Exception as e:
            logger.error(f"Error en obtener_top_empleados: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # =========================================================================
    # 6. KPIs PRINCIPALES (Dashboard Home)
    # =========================================================================
    
    @staticmethod
    def obtener_kpis_principales(sucursal_id: int) -> dict:
        """Obtiene los KPIs principales para el dashboard home"""
        try:
            ahora = datetime.now(TZ_MEXICO).replace(tzinfo=None)
            inicio_dia = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
            fin_dia = ahora.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            with get_db_session() as session:
                # 1. Ventas de hoy
                ventas_hoy = session.query(
                    func.sum(Pago.monto).label('total'),
                    func.count(Pago.id_pago).label('cantidad')
                ).filter(
                    and_(
                        Pago.sucursal_id == sucursal_id,
                        Pago.estatus == 2,
                        Pago.created_at >= inicio_dia,
                        Pago.created_at <= fin_dia
                    )
                ).first()
                
                # 2. Pedidos activos (estado 0 y 3)
                pedidos_activos = session.query(
                    func.count(Pedido.id_pedido)
                ).filter(
                    and_(
                        Pedido.sucursal_id == sucursal_id,
                        Pedido.estado_pedido.in_([0, 3])
                    )
                ).scalar() or 0
                
                # 3. Reservas de hoy
                from src.models.operaciones.hold_mesa_model import HoldMesa
                from src.models.catalogos.mesa_model import Mesa
                from src.models.catalogos.area_model import Area
                
                reservas_hoy = session.query(
                    func.count(Reserva.id_reserva)
                ).join(
                    HoldMesa, Reserva.hold_id == HoldMesa.id_hold_mesa
                ).join(
                    Mesa, HoldMesa.mesa_id == Mesa.id_mesa
                ).join(
                    Area, Mesa.area_id == Area.id_area
                ).filter(
                    and_(
                        Area.sucursal_id == sucursal_id,
                        Reserva.inicio >= inicio_dia,
                        Reserva.inicio <= fin_dia,
                        Reserva.estatus.in_([1, 2])  # Programadas o En Curso
                    )
                ).scalar() or 0
                
                # 4. Insumos bajo stock
                insumos_bajo = session.query(
                    func.count(Existencia.id_existencia)
                ).join(
                    Insumo, Existencia.insumo_id == Insumo.id_insumo
                ).filter(
                    and_(
                        Existencia.sucursal_id == sucursal_id,
                        Existencia.cantidad < Insumo.minimo_stock,
                        Insumo.es_activo == True
                    )
                ).scalar() or 0
                
                # 5. Lotes por vencer (próximos 7 días)
                lotes_proximos = LoteDAO.obtener_lotes_proximos_a_vencer(sucursal_id, 7)
                
                # 6. Calificación promedio del mes
                inicio_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                calif_promedio = session.query(
                    func.avg(Calificacion.calificacion)
                ).join(
                    Pedido, Calificacion.pedido_id == Pedido.id_pedido
                ).filter(
                    and_(
                        Pedido.sucursal_id == sucursal_id,
                        Calificacion.created_at >= inicio_mes
                    )
                ).scalar() or 0
                
                return {
                    'success': True,
                    'data': {
                        'ventas_hoy': {
                            'total': float(ventas_hoy.total or 0),
                            'transacciones': ventas_hoy.cantidad or 0
                        },
                        'pedidos_activos': pedidos_activos,
                        'reservas_hoy': reservas_hoy,
                        'insumos_bajo_stock': insumos_bajo,
                        'lotes_por_vencer': len(lotes_proximos),
                        'calificacion_promedio': round(float(calif_promedio), 2),
                        'fecha_consulta': ahora.isoformat()
                    }
                }
                
        except Exception as e:
            logger.error(f"Error en obtener_kpis_principales: {str(e)}")
            return {'success': False, 'error': str(e)}
