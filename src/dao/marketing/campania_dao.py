"""
CampaniaDAO - Data Access Object para marketing.Campania y CampaniaUsuario
Gestión de campañas promocionales, validación de cupones y métricas CRM
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from pytz import timezone

from sqlalchemy import and_, func, case, distinct, desc
from sqlalchemy.sql import text
from src.core.db.session_manager import get_db_session
from src.models.marketing.campania_model import Campania
from src.models.marketing.campania_usuario_model import CampaniaUsuario
from src.models.auth.usuario import Usuario
from src.models import Pedido, Pago
from src.models.operaciones.reserva_model import Reserva

logger = logging.getLogger(__name__)

# Timezone de México para validación de vigencia
MEXICO_TZ = timezone('America/Mexico_City')


class CampaniaDAO:
    """
    Data Access Object para Campaña y CampaniaUsuario.
    Incluye validación completa de cupones.
    """
    
    # =========================================================================
    # CRUD CAMPANIA
    # =========================================================================
    
    @staticmethod
    def crear_campania(
        usuario_crea_id: int,
        nombre_campania: str,
        porcentaje_desc: Decimal,
        codigo: str = None,
        estatus: int = 1
    ) -> dict:
        """
        Crear nueva campaña de marketing.
        
        Args:
            usuario_crea_id: ID del usuario que crea la campaña
            nombre_campania: Nombre descriptivo
            porcentaje_desc: Porcentaje de descuento (ej: 10.00 = 10%)
            codigo: Código de cupón único (opcional)
            estatus: 0=Inactiva, 1=Activa (default)
        
        Returns:
            Dict con datos de la campaña creada
        """
        with get_db_session() as session:
            try:
                # Validar código único si se proporciona
                if codigo:
                    existe = session.query(Campania).filter(
                        Campania.codigo == codigo.upper()
                    ).first()
                    if existe:
                        raise ValueError(f"El código de cupón '{codigo}' ya existe")
                
                campania = Campania(
                    usuario_crea_id=usuario_crea_id,
                    nombre_campania=nombre_campania,
                    porcentaje_desc=porcentaje_desc,
                    codigo=codigo.upper() if codigo else None,
                    estatus=estatus
                )
                
                session.add(campania)
                session.flush()
                
                logger.info(f"Campaña creada: ID {campania.id_campania}, código={codigo}")
                return campania.to_dict()
                
            except ValueError:
                raise
            except Exception as e:
                logger.error(f"Error al crear campaña: {str(e)}")
                raise ValueError(f"Error al crear campaña: {str(e)}")
    
    
    @staticmethod
    def obtener_campania(campania_id: int) -> dict:
        """Obtener campaña por ID"""
        with get_db_session() as session:
            campania = session.query(Campania).filter(
                Campania.id_campania == campania_id
            ).first()
            
            if not campania:
                return None
            
            return campania.to_dict()
    
    
    @staticmethod
    def obtener_campania_por_codigo(codigo: str) -> dict:
        """Obtener campaña por código de cupón"""
        with get_db_session() as session:
            campania = session.query(Campania).filter(
                Campania.codigo == codigo.upper()
            ).first()
            
            if not campania:
                return None
            
            return campania.to_dict()
    
    
    @staticmethod
    def listar_campanias(estatus: int = None, limit: int = 50, offset: int = 0) -> dict:
        """
        Listar campañas con filtros opcionales.
        
        Args:
            estatus: Filtrar por estatus (0=Inactiva, 1=Activa)
            limit: Máximo de resultados
            offset: Desplazamiento
        
        Returns:
            Dict con lista de campañas y total
        """
        with get_db_session() as session:
            query = session.query(Campania)
            
            if estatus is not None:
                query = query.filter(Campania.estatus == estatus)
            
            total = query.count()
            campanias = query.order_by(Campania.created_at.desc()).limit(limit).offset(offset).all()
            
            return {
                'campanias': [c.to_dict() for c in campanias],
                'total': total
            }
    
    
    @staticmethod
    def listar_campanias_activas() -> list:
        """
        Listar solo campañas activas con contadores de cupones.
        
        Returns:
            Lista de campañas activas con total_cupones y total_cupones_usados
        """
        with get_db_session() as session:
            try:
                # Subquery para contar cupones totales y usados por campaña
                cupones_stats = session.query(
                    CampaniaUsuario.campania_id,
                    func.count(CampaniaUsuario.id_campania_usuario).label('total_cupones'),
                    func.sum(case((CampaniaUsuario.estatus == 1, 1), else_=0)).label('total_cupones_usados')
                ).group_by(CampaniaUsuario.campania_id).subquery()
                
                # Query principal: campañas activas con stats
                resultados = session.query(
                    Campania,
                    func.coalesce(cupones_stats.c.total_cupones, 0).label('total_cupones'),
                    func.coalesce(cupones_stats.c.total_cupones_usados, 0).label('total_cupones_usados')
                ).outerjoin(
                    cupones_stats, Campania.id_campania == cupones_stats.c.campania_id
                ).filter(
                    Campania.estatus == 1  # Solo activas
                ).order_by(
                    Campania.created_at.desc()
                ).all()
                
                campanias = []
                for campania, total_cupones, total_cupones_usados in resultados:
                    campania_dict = campania.to_dict()
                    campania_dict['total_cupones'] = total_cupones or 0
                    campania_dict['total_cupones_usados'] = total_cupones_usados or 0
                    campanias.append(campania_dict)
                
                logger.info(f"Listando {len(campanias)} campañas activas")
                return campanias
                
            except Exception as e:
                logger.error(f"Error listando campañas activas: {str(e)}")
                raise
    
    
    @staticmethod
    def cambiar_estatus_campania(campania_id: int, nuevo_estatus: int) -> dict:
        """Activar/Desactivar campaña"""
        with get_db_session() as session:
            campania = session.query(Campania).filter(
                Campania.id_campania == campania_id
            ).first()
            
            if not campania:
                raise ValueError(f"Campaña {campania_id} no existe")
            
            campania.estatus = nuevo_estatus
            session.commit()
            
            logger.info(f"Campaña {campania_id} cambió estatus a {nuevo_estatus}")
            return campania.to_dict()
    
    
    # =========================================================================
    # CRUD CAMPANIA_USUARIO (Asignación de cupones)
    # =========================================================================
    
    @staticmethod
    def asignar_cupon_usuario(
        cliente_id: int,
        campania_id: int,
        fecha_vigencia: datetime = None
    ) -> dict:
        """
        Asignar cupón de campaña a un usuario/cliente.
        
        Args:
            cliente_id: ID del cliente
            campania_id: ID de la campaña
            fecha_vigencia: Fecha límite de uso del cupón
        
        Returns:
            Dict con datos de la asignación
        """
        with get_db_session() as session:
            try:
                # Verificar que la campaña existe y está activa
                campania = session.query(Campania).filter(
                    Campania.id_campania == campania_id
                ).first()
                
                if not campania:
                    raise ValueError(f"Campaña {campania_id} no existe")
                
                if campania.estatus != 1:
                    raise ValueError(f"Campaña {campania_id} no está activa")
                
                # Verificar si ya tiene asignado este cupón (no usado)
                existe = session.query(CampaniaUsuario).filter(
                    and_(
                        CampaniaUsuario.cliente_id == cliente_id,
                        CampaniaUsuario.campania_id == campania_id,
                        CampaniaUsuario.estatus == 0  # No usado
                    )
                ).first()
                
                if existe:
                    raise ValueError(f"El cliente ya tiene asignado este cupón")
                
                asignacion = CampaniaUsuario(
                    cliente_id=cliente_id,
                    campania_id=campania_id,
                    fecha_vigencia=fecha_vigencia,
                    estatus=0  # No usado
                )
                
                session.add(asignacion)
                session.flush()
                
                logger.info(f"Cupón asignado: Cliente {cliente_id}, Campaña {campania_id}")
                return asignacion.to_dict()
                
            except ValueError:
                raise
            except Exception as e:
                logger.error(f"Error al asignar cupón: {str(e)}")
                raise ValueError(f"Error al asignar cupón: {str(e)}")
    
    
    @staticmethod
    def listar_cupones_usuario(cliente_id: int, solo_disponibles: bool = True) -> list:
        """
        Listar cupones asignados a un usuario.
        
        Args:
            cliente_id: ID del cliente
            solo_disponibles: Si True, solo cupones no usados y vigentes
        
        Returns:
            Lista de cupones con info de campaña
        """
        with get_db_session() as session:
            query = session.query(CampaniaUsuario, Campania).join(
                Campania, CampaniaUsuario.campania_id == Campania.id_campania
            ).filter(
                CampaniaUsuario.cliente_id == cliente_id
            )
            
            if solo_disponibles:
                ahora_mx = datetime.now(MEXICO_TZ)
                query = query.filter(
                    and_(
                        CampaniaUsuario.estatus == 0,  # No usado
                        Campania.estatus == 1  # Campaña activa
                    )
                )
            
            resultados = query.order_by(CampaniaUsuario.created_at.desc()).all()
            
            cupones = []
            ahora_mx = datetime.now(MEXICO_TZ)
            
            for asignacion, campania in resultados:
                cupon_dict = asignacion.to_dict()
                cupon_dict['campania'] = campania.to_dict()
                
                # Verificar vigencia
                if asignacion.fecha_vigencia:
                    fecha_vig = asignacion.fecha_vigencia
                    if fecha_vig.tzinfo is None:
                        fecha_vig = MEXICO_TZ.localize(fecha_vig)
                    cupon_dict['vigente'] = fecha_vig >= ahora_mx
                else:
                    cupon_dict['vigente'] = True  # Sin fecha = siempre vigente
                
                # Filtrar por vigencia si solo_disponibles
                if solo_disponibles and not cupon_dict['vigente']:
                    continue
                
                cupones.append(cupon_dict)
            
            return cupones
    
    
    @staticmethod
    def marcar_cupon_usado(campania_usuario_id: int) -> dict:
        """
        Marcar cupón como usado (estatus 0 → 1).
        
        Args:
            campania_usuario_id: ID de la asignación CampaniaUsuario
        
        Returns:
            Dict actualizado
        """
        with get_db_session() as session:
            asignacion = session.query(CampaniaUsuario).filter(
                CampaniaUsuario.id_campania_usuario == campania_usuario_id
            ).first()
            
            if not asignacion:
                raise ValueError(f"Asignación {campania_usuario_id} no existe")
            
            if asignacion.estatus != 0:
                raise ValueError("El cupón ya fue usado")
            
            asignacion.estatus = 1  # Usado
            session.commit()
            
            logger.info(f"Cupón {campania_usuario_id} marcado como usado")
            return asignacion.to_dict()
    
    
    # =========================================================================
    # VALIDACIÓN DE CUPÓN (Para uso en Pago)
    # =========================================================================
    
    @staticmethod
    def validar_cupon(codigo: str, cliente_id: int) -> dict:
        """
        Validar si un cupón es válido para un cliente.
        
        Validaciones:
            1. Campaña existe (por código)
            2. Campaña activa (estatus = 1)
            3. CampaniaUsuario existe (cliente_id + campania_id)
            4. CampaniaUsuario.estatus = 0 (no usado)
            5. CampaniaUsuario.fecha_vigencia >= NOW() (timezone México)
        
        Args:
            codigo: Código del cupón
            cliente_id: ID del cliente que quiere usar el cupón
        
        Returns:
            Dict con:
                - valido: bool
                - error: str (si no es válido)
                - campania: dict (info de la campaña)
                - campania_usuario_id: int (para marcar como usado)
                - porcentaje_desc: Decimal (para calcular descuento)
        """
        with get_db_session() as session:
            try:
                # 1. Buscar campaña por código
                campania = session.query(Campania).filter(
                    Campania.codigo == codigo.upper()
                ).first()
                
                if not campania:
                    return {
                        'valido': False,
                        'error': f"Código de cupón '{codigo}' no existe"
                    }
                
                # 2. Verificar campaña activa
                if campania.estatus != 1:
                    return {
                        'valido': False,
                        'error': "La campaña no está activa"
                    }
                
                # 3. Buscar asignación del cliente
                asignacion = session.query(CampaniaUsuario).filter(
                    and_(
                        CampaniaUsuario.cliente_id == cliente_id,
                        CampaniaUsuario.campania_id == campania.id_campania
                    )
                ).first()
                
                if not asignacion:
                    return {
                        'valido': False,
                        'error': "Este cupón no está asignado a tu cuenta"
                    }
                
                # 4. Verificar no usado
                if asignacion.estatus != 0:
                    return {
                        'valido': False,
                        'error': "Este cupón ya fue utilizado"
                    }
                
                # 5. Verificar vigencia (timezone México)
                if asignacion.fecha_vigencia:
                    ahora_mx = datetime.now(MEXICO_TZ)
                    fecha_vig = asignacion.fecha_vigencia
                    
                    # Si la fecha no tiene timezone, asumir México
                    if fecha_vig.tzinfo is None:
                        fecha_vig = MEXICO_TZ.localize(fecha_vig)
                    
                    if fecha_vig < ahora_mx:
                        return {
                            'valido': False,
                            'error': f"El cupón expiró el {fecha_vig.strftime('%Y-%m-%d %H:%M')}"
                        }
                
                # ✅ Cupón válido
                logger.info(f"Cupón '{codigo}' validado para cliente {cliente_id}")
                
                return {
                    'valido': True,
                    'campania': campania.to_dict(),
                    'campania_usuario_id': asignacion.id_campania_usuario,
                    'campania_id': campania.id_campania,
                    'porcentaje_desc': Decimal(str(campania.porcentaje_desc))
                }
                
            except Exception as e:
                logger.error(f"Error validando cupón: {str(e)}")
                return {
                    'valido': False,
                    'error': f"Error al validar cupón: {str(e)}"
                }
    
    
    # =========================================================================
    # MÉTRICAS CRM - Segmentación de Clientes
    # =========================================================================
    
    @staticmethod
    def obtener_clientes_vip(top_n: int = 20) -> list:
        """
        Obtener TOP clientes por gasto total (VIP / Alto Consumo).
        
        Args:
            top_n: Número de clientes TOP a retornar
        
        Returns:
            Lista de clientes con métricas de gasto
        """
        with get_db_session() as session:
            try:
                # Query: Usuarios con sus pagos totales
                resultados = session.query(
                    Usuario.id_usuario,
                    Usuario.nombre,
                    Usuario.apellido,
                    Usuario.email,
                    Usuario.telefono,
                    func.count(distinct(Pedido.id_pedido)).label('total_pedidos'),
                    func.coalesce(func.sum(Pago.monto), 0).label('gasto_total'),
                    func.coalesce(func.sum(Pago.propina), 0).label('propinas_total'),
                    func.coalesce(func.avg(Pago.monto), 0).label('ticket_promedio')
                ).join(
                    Pedido, Usuario.id_usuario == Pedido.cliente_id
                ).join(
                    Pago, Pedido.id_pedido == Pago.pedido_id
                ).filter(
                    Usuario.es_activo == True,
                    Pago.estatus == 2  # Pago completado
                ).group_by(
                    Usuario.id_usuario,
                    Usuario.nombre,
                    Usuario.apellido,
                    Usuario.email,
                    Usuario.telefono
                ).order_by(
                    desc('gasto_total')
                ).limit(top_n).all()
                
                clientes = []
                for r in resultados:
                    clientes.append({
                        'id_usuario': r.id_usuario,
                        'nombre': r.nombre,
                        'apellido': r.apellido,
                        'nombre_completo': f"{r.nombre} {r.apellido}".strip(),
                        'email': r.email,
                        'telefono': r.telefono,
                        'total_pedidos': r.total_pedidos,
                        'gasto_total': float(r.gasto_total) if r.gasto_total else 0,
                        'propinas_total': float(r.propinas_total) if r.propinas_total else 0,
                        'ticket_promedio': float(r.ticket_promedio) if r.ticket_promedio else 0,
                        'segmento': 'VIP'
                    })
                
                logger.info(f"Métrica VIP: {len(clientes)} clientes obtenidos")
                return clientes
                
            except Exception as e:
                logger.error(f"Error obteniendo clientes VIP: {str(e)}")
                raise
    
    
    @staticmethod
    def obtener_clientes_frecuentes(top_n: int = 20) -> list:
        """
        Obtener clientes con mayor número de visitas (pedidos + reservas).
        
        Args:
            top_n: Número de clientes TOP a retornar
        
        Returns:
            Lista de clientes con métricas de frecuencia
        """
        with get_db_session() as session:
            try:
                # Subquery para contar pedidos
                pedidos_count = session.query(
                    Pedido.cliente_id,
                    func.count(Pedido.id_pedido).label('total_pedidos'),
                    func.min(Pedido.created_at).label('primera_visita'),
                    func.max(Pedido.created_at).label('ultima_visita')
                ).filter(
                    Pedido.cliente_id.isnot(None)
                ).group_by(Pedido.cliente_id).subquery()
                
                # Subquery para contar reservas
                reservas_count = session.query(
                    Reserva.cliente_id,
                    func.count(Reserva.id_reserva).label('total_reservas')
                ).filter(
                    Reserva.cliente_id.isnot(None)
                ).group_by(Reserva.cliente_id).subquery()
                
                # Query principal - usar INNER JOIN con pedidos para garantizar que tienen pedidos
                resultados = session.query(
                    Usuario.id_usuario,
                    Usuario.nombre,
                    Usuario.apellido,
                    Usuario.email,
                    Usuario.telefono,
                    pedidos_count.c.total_pedidos,
                    func.coalesce(reservas_count.c.total_reservas, 0).label('total_reservas'),
                    pedidos_count.c.primera_visita,
                    pedidos_count.c.ultima_visita
                ).join(
                    pedidos_count, Usuario.id_usuario == pedidos_count.c.cliente_id
                ).outerjoin(
                    reservas_count, Usuario.id_usuario == reservas_count.c.cliente_id
                ).filter(
                    Usuario.es_activo == True
                ).order_by(
                    desc(pedidos_count.c.total_pedidos + func.coalesce(reservas_count.c.total_reservas, 0))
                ).limit(top_n).all()
                
                clientes = []
                for r in resultados:
                    total_interacciones = (r.total_pedidos or 0) + (r.total_reservas or 0)
                    clientes.append({
                        'id_usuario': r.id_usuario,
                        'nombre': r.nombre,
                        'apellido': r.apellido,
                        'nombre_completo': f"{r.nombre} {r.apellido}".strip(),
                        'email': r.email,
                        'telefono': r.telefono,
                        'total_pedidos': r.total_pedidos or 0,
                        'total_reservas': r.total_reservas or 0,
                        'total_interacciones': total_interacciones,
                        'primera_visita': r.primera_visita.isoformat() if r.primera_visita else None,
                        'ultima_visita': r.ultima_visita.isoformat() if r.ultima_visita else None,
                        'segmento': 'FRECUENTE'
                    })
                
                logger.info(f"Métrica Frecuentes: {len(clientes)} clientes obtenidos")
                return clientes
                
            except Exception as e:
                logger.error(f"Error obteniendo clientes frecuentes: {str(e)}")
                raise
    
    
    @staticmethod
    def obtener_clientes_inactivos(dias_sin_comprar: int = 30) -> list:
        """
        Obtener clientes que no han comprado en X días.
        
        Args:
            dias_sin_comprar: Número de días sin actividad
        
        Returns:
            Lista de clientes inactivos con historial
        """
        with get_db_session() as session:
            try:
                fecha_corte = datetime.utcnow() - timedelta(days=dias_sin_comprar)
                
                # Subquery: último pedido de cada cliente
                ultimo_pedido = session.query(
                    Pedido.cliente_id,
                    func.max(Pedido.created_at).label('ultimo_pedido'),
                    func.count(Pedido.id_pedido).label('historico_pedidos')
                ).filter(
                    Pedido.cliente_id.isnot(None)
                ).group_by(Pedido.cliente_id).subquery()
                
                # Subquery: gasto histórico
                gasto_hist = session.query(
                    Pedido.cliente_id,
                    func.coalesce(func.sum(Pago.monto), 0).label('gasto_historico')
                ).join(
                    Pago, Pedido.id_pedido == Pago.pedido_id
                ).filter(
                    Pedido.cliente_id.isnot(None)
                ).group_by(Pedido.cliente_id).subquery()
                
                # Query principal: clientes cuyo último pedido fue antes de fecha_corte
                resultados = session.query(
                    Usuario.id_usuario,
                    Usuario.nombre,
                    Usuario.apellido,
                    Usuario.email,
                    Usuario.telefono,
                    ultimo_pedido.c.ultimo_pedido,
                    ultimo_pedido.c.historico_pedidos,
                    func.coalesce(gasto_hist.c.gasto_historico, 0).label('gasto_historico')
                ).join(
                    ultimo_pedido, Usuario.id_usuario == ultimo_pedido.c.cliente_id
                ).outerjoin(
                    gasto_hist, Usuario.id_usuario == gasto_hist.c.cliente_id
                ).filter(
                    Usuario.es_activo == True,
                    ultimo_pedido.c.ultimo_pedido < fecha_corte
                ).order_by(
                    ultimo_pedido.c.ultimo_pedido.asc()  # Más antiguos primero
                ).all()
                
                clientes = []
                ahora = datetime.utcnow()
                for r in resultados:
                    dias_inactivo = (ahora - r.ultimo_pedido).days if r.ultimo_pedido else 0
                    
                    # Determinar nivel de riesgo
                    if dias_inactivo >= 90:
                        nivel_riesgo = 'PERDIDO'
                    elif dias_inactivo >= 60:
                        nivel_riesgo = 'INACTIVO'
                    else:
                        nivel_riesgo = 'EN_RIESGO'
                    
                    clientes.append({
                        'id_usuario': r.id_usuario,
                        'nombre': r.nombre,
                        'apellido': r.apellido,
                        'nombre_completo': f"{r.nombre} {r.apellido}".strip(),
                        'email': r.email,
                        'telefono': r.telefono,
                        'ultimo_pedido': r.ultimo_pedido.isoformat() if r.ultimo_pedido else None,
                        'dias_sin_comprar': dias_inactivo,
                        'historico_pedidos': r.historico_pedidos or 0,
                        'gasto_historico': float(r.gasto_historico) if r.gasto_historico else 0,
                        'nivel_riesgo': nivel_riesgo,
                        'segmento': 'INACTIVO'
                    })
                
                logger.info(f"Métrica Inactivos ({dias_sin_comprar} días): {len(clientes)} clientes")
                return clientes
                
            except Exception as e:
                logger.error(f"Error obteniendo clientes inactivos: {str(e)}")
                raise
    
    
    @staticmethod
    def obtener_clientes_nuevos(dias_registro: int = 30) -> list:
        """
        Obtener clientes registrados recientemente o con pocos pedidos.
        
        Args:
            dias_registro: Días desde el registro para considerar "nuevo"
        
        Returns:
            Lista de clientes nuevos
        """
        with get_db_session() as session:
            try:
                fecha_corte = datetime.utcnow() - timedelta(days=dias_registro)
                
                # Subquery: conteo de pedidos por cliente
                pedidos_count = session.query(
                    Pedido.cliente_id,
                    func.count(Pedido.id_pedido).label('total_pedidos'),
                    func.coalesce(func.sum(Pago.monto), 0).label('gasto_total')
                ).outerjoin(
                    Pago, Pedido.id_pedido == Pago.pedido_id
                ).filter(
                    Pedido.cliente_id.isnot(None)
                ).group_by(Pedido.cliente_id).subquery()
                
                # Query: usuarios nuevos (por fecha registro O pocos pedidos)
                resultados = session.query(
                    Usuario.id_usuario,
                    Usuario.nombre,
                    Usuario.apellido,
                    Usuario.email,
                    Usuario.telefono,
                    Usuario.created_at,
                    func.coalesce(pedidos_count.c.total_pedidos, 0).label('total_pedidos'),
                    func.coalesce(pedidos_count.c.gasto_total, 0).label('gasto_total')
                ).outerjoin(
                    pedidos_count, Usuario.id_usuario == pedidos_count.c.cliente_id
                ).filter(
                    Usuario.es_activo == True,
                    # Registrados recientemente O con pocos pedidos
                    ((Usuario.created_at >= fecha_corte) | 
                     (func.coalesce(pedidos_count.c.total_pedidos, 0) <= 2))
                ).order_by(
                    Usuario.created_at.desc()
                ).all()
                
                clientes = []
                ahora = datetime.utcnow()
                for r in resultados:
                    dias_desde_registro = (ahora - r.created_at).days if r.created_at else 0
                    
                    # Determinar etapa
                    if r.total_pedidos == 0:
                        etapa = 'SIN_PEDIDOS'
                    elif r.total_pedidos == 1:
                        etapa = 'PRIMERA_COMPRA'
                    else:
                        etapa = 'EN_ADOPCION'
                    
                    clientes.append({
                        'id_usuario': r.id_usuario,
                        'nombre': r.nombre,
                        'apellido': r.apellido,
                        'nombre_completo': f"{r.nombre} {r.apellido}".strip(),
                        'email': r.email,
                        'telefono': r.telefono,
                        'fecha_registro': r.created_at.isoformat() if r.created_at else None,
                        'dias_desde_registro': dias_desde_registro,
                        'total_pedidos': r.total_pedidos or 0,
                        'gasto_total': float(r.gasto_total) if r.gasto_total else 0,
                        'etapa': etapa,
                        'segmento': 'NUEVO'
                    })
                
                logger.info(f"Métrica Nuevos ({dias_registro} días): {len(clientes)} clientes")
                return clientes
                
            except Exception as e:
                logger.error(f"Error obteniendo clientes nuevos: {str(e)}")
                raise
    
    
    @staticmethod
    def obtener_clientes_por_canal() -> list:
        """
        Segmentar clientes por canal preferido (Mesa/Takeaway/Delivery).
        
        tipo_pedido en BD:
            1 = En Mesa
            2 = Takeaway
            3 = Delivery
        
        Returns:
            Lista de clientes con su canal preferido
        """
        with get_db_session() as session:
            try:
                # Subquery: conteo por tipo de pedido
                tipo_pedido_count = session.query(
                    Pedido.cliente_id,
                    func.sum(case((Pedido.tipo_pedido == 1, 1), else_=0)).label('pedidos_mesa'),
                    func.sum(case((Pedido.tipo_pedido == 2, 1), else_=0)).label('pedidos_takeaway'),
                    func.sum(case((Pedido.tipo_pedido == 3, 1), else_=0)).label('pedidos_delivery'),
                    func.count(Pedido.id_pedido).label('total_pedidos')
                ).filter(
                    Pedido.cliente_id.isnot(None)
                ).group_by(Pedido.cliente_id).subquery()
                
                # Subquery: conteo de reservas
                reservas_count = session.query(
                    Reserva.cliente_id,
                    func.count(Reserva.id_reserva).label('total_reservas')
                ).filter(
                    Reserva.cliente_id.isnot(None)
                ).group_by(Reserva.cliente_id).subquery()
                
                # Query principal - usar INNER JOIN para garantizar que tienen pedidos
                resultados = session.query(
                    Usuario.id_usuario,
                    Usuario.nombre,
                    Usuario.apellido,
                    Usuario.email,
                    Usuario.telefono,
                    tipo_pedido_count.c.pedidos_mesa,
                    tipo_pedido_count.c.pedidos_takeaway,
                    tipo_pedido_count.c.pedidos_delivery,
                    tipo_pedido_count.c.total_pedidos,
                    func.coalesce(reservas_count.c.total_reservas, 0).label('total_reservas')
                ).join(
                    tipo_pedido_count, Usuario.id_usuario == tipo_pedido_count.c.cliente_id
                ).outerjoin(
                    reservas_count, Usuario.id_usuario == reservas_count.c.cliente_id
                ).filter(
                    Usuario.es_activo == True
                ).order_by(
                    desc(tipo_pedido_count.c.total_pedidos)
                ).all()
                
                clientes = []
                for r in resultados:
                    # Determinar canal preferido
                    mesa = r.pedidos_mesa or 0
                    takeaway = r.pedidos_takeaway or 0
                    delivery = r.pedidos_delivery or 0
                    reservas = r.total_reservas or 0
                    
                    # Lógica de preferencia
                    if reservas > 0 and reservas >= max(takeaway, delivery):
                        canal_preferido = 'RESERVA_PREFERIDO'
                    elif delivery > mesa and delivery > takeaway:
                        canal_preferido = 'DELIVERY_PREFERIDO'
                    elif takeaway > mesa:
                        canal_preferido = 'TAKEAWAY_PREFERIDO'
                    elif mesa > 0:
                        canal_preferido = 'MESA_PREFERIDO'
                    else:
                        canal_preferido = 'MIXTO'
                    
                    clientes.append({
                        'id_usuario': r.id_usuario,
                        'nombre': r.nombre,
                        'apellido': r.apellido,
                        'nombre_completo': f"{r.nombre} {r.apellido}".strip(),
                        'email': r.email,
                        'telefono': r.telefono,
                        'pedidos_mesa': mesa,
                        'pedidos_takeaway': takeaway,
                        'pedidos_delivery': delivery,
                        'total_reservas': reservas,
                        'total_pedidos': r.total_pedidos or 0,
                        'canal_preferido': canal_preferido,
                        'segmento': 'POR_CANAL'
                    })
                
                logger.info(f"Métrica Por Canal: {len(clientes)} clientes")
                return clientes
                
            except Exception as e:
                logger.error(f"Error obteniendo clientes por canal: {str(e)}")
                raise
    
    
    @staticmethod
    def asignar_cupones_masivo(
        cliente_ids: list,
        campania_id: int,
        fecha_vigencia: datetime = None
    ) -> dict:
        """
        Asignar cupón a múltiples clientes (para generar campaña desde métrica).
        
        Args:
            cliente_ids: Lista de IDs de clientes
            campania_id: ID de la campaña
            fecha_vigencia: Fecha límite de uso
        
        Returns:
            Dict con resumen de asignaciones
        """
        with get_db_session() as session:
            try:
                # Verificar campaña existe y está activa
                campania = session.query(Campania).filter(
                    Campania.id_campania == campania_id
                ).first()
                
                if not campania:
                    raise ValueError(f"Campaña {campania_id} no existe")
                
                if campania.estatus != 1:
                    raise ValueError(f"Campaña {campania_id} no está activa")
                
                asignados = 0
                ya_asignados = 0
                errores = []
                
                for cliente_id in cliente_ids:
                    try:
                        # Verificar si ya tiene este cupón
                        existe = session.query(CampaniaUsuario).filter(
                            and_(
                                CampaniaUsuario.cliente_id == cliente_id,
                                CampaniaUsuario.campania_id == campania_id,
                                CampaniaUsuario.estatus == 0
                            )
                        ).first()
                        
                        if existe:
                            ya_asignados += 1
                            continue
                        
                        # Crear asignación
                        asignacion = CampaniaUsuario(
                            cliente_id=cliente_id,
                            campania_id=campania_id,
                            fecha_vigencia=fecha_vigencia,
                            estatus=0
                        )
                        session.add(asignacion)
                        asignados += 1
                        
                    except Exception as e:
                        errores.append(f"Cliente {cliente_id}: {str(e)}")
                
                session.commit()
                
                logger.info(f"Asignación masiva: {asignados} nuevos, {ya_asignados} ya tenían, {len(errores)} errores")
                
                return {
                    'campania_id': campania_id,
                    'total_clientes': len(cliente_ids),
                    'asignados': asignados,
                    'ya_asignados': ya_asignados,
                    'errores': len(errores),
                    'detalle_errores': errores[:10] if errores else []  # Max 10 errores
                }
                
            except ValueError:
                raise
            except Exception as e:
                logger.error(f"Error en asignación masiva: {str(e)}")
                raise
    
    
    # =========================================================================
    # VERIFICACIÓN DE CAMPAÑAS VENCIDAS (Para Push Notifications)
    # =========================================================================
    
    @staticmethod
    def obtener_cupones_vencidos_no_marcados() -> list:
        """
        Obtener cupones vencidos que aún tienen estatus 0 (NoUsado).
        
        Criterios:
            - CampaniaUsuario.estatus = 0 (no usado)
            - CampaniaUsuario.fecha_vigencia < NOW() (ya venció)
        
        Returns:
            Lista de cupones vencidos con info de campaña y cliente
        """
        with get_db_session() as session:
            try:
                ahora_mx = datetime.now(MEXICO_TZ)
                
                # Query: cupones no usados con fecha_vigencia pasada
                resultados = session.query(
                    CampaniaUsuario,
                    Campania,
                    Usuario
                ).join(
                    Campania, CampaniaUsuario.campania_id == Campania.id_campania
                ).join(
                    Usuario, CampaniaUsuario.cliente_id == Usuario.id_usuario
                ).filter(
                    CampaniaUsuario.estatus == 0,  # No usado
                    CampaniaUsuario.fecha_vigencia.isnot(None),  # Tiene fecha de vigencia
                    CampaniaUsuario.fecha_vigencia < ahora_mx  # Ya venció
                ).all()
                
                cupones_vencidos = []
                for asignacion, campania, usuario in resultados:
                    cupones_vencidos.append({
                        'id_campania_usuario': asignacion.id_campania_usuario,
                        'cliente_id': asignacion.cliente_id,
                        'cliente_nombre': f"{usuario.nombre} {usuario.apellido}".strip(),
                        'cliente_email': usuario.email,
                        'campania_id': campania.id_campania,
                        'campania_nombre': campania.nombre_campania,
                        'campania_codigo': campania.codigo,
                        'fecha_vigencia': asignacion.fecha_vigencia.isoformat() if asignacion.fecha_vigencia else None,
                        'dias_vencido': (ahora_mx - asignacion.fecha_vigencia.replace(tzinfo=MEXICO_TZ)).days if asignacion.fecha_vigencia else 0
                    })
                
                logger.info(f"Encontrados {len(cupones_vencidos)} cupones vencidos no marcados")
                return cupones_vencidos
                
            except Exception as e:
                logger.error(f"Error obteniendo cupones vencidos: {str(e)}")
                raise
    
    
    @staticmethod
    def marcar_cupones_vencidos() -> dict:
        """
        Marcar cupones vencidos con estatus 2 (Vencido).
        
        Actualiza:
            - CampaniaUsuario.estatus = 2 donde fecha_vigencia < NOW() y estatus = 0
        
        Returns:
            Dict con resumen de actualización
        """
        with get_db_session() as session:
            try:
                ahora_mx = datetime.now(MEXICO_TZ)
                
                # Obtener cupones a marcar (para logging)
                cupones_vencidos = session.query(CampaniaUsuario).filter(
                    CampaniaUsuario.estatus == 0,
                    CampaniaUsuario.fecha_vigencia.isnot(None),
                    CampaniaUsuario.fecha_vigencia < ahora_mx
                ).all()
                
                total_vencidos = len(cupones_vencidos)
                
                if total_vencidos == 0:
                    logger.info("No hay cupones vencidos para marcar")
                    return {
                        'cupones_actualizados': 0,
                        'campanias_afectadas': []
                    }
                
                # Obtener campañas afectadas antes de actualizar
                campanias_ids = list(set([c.campania_id for c in cupones_vencidos]))
                
                # Actualizar estatus a 2 (Vencido)
                for cupon in cupones_vencidos:
                    cupon.estatus = 2
                
                session.commit()
                
                logger.info(f"Marcados {total_vencidos} cupones como vencidos (estatus=2)")
                
                return {
                    'cupones_actualizados': total_vencidos,
                    'campanias_afectadas': campanias_ids
                }
                
            except Exception as e:
                logger.error(f"Error marcando cupones vencidos: {str(e)}")
                raise
    
    
    @staticmethod
    def verificar_campanias_sin_cupones_activos() -> list:
        """
        Verificar campañas activas que ya no tienen cupones disponibles.
        
        Una campaña debería desactivarse si:
            - Todos sus cupones están usados (estatus=1) o vencidos (estatus=2)
            - No quedan cupones con estatus=0 y fecha_vigencia >= NOW()
        
        Returns:
            Lista de campañas que deberían desactivarse
        """
        with get_db_session() as session:
            try:
                ahora_mx = datetime.now(MEXICO_TZ)
                
                # Subquery: contar cupones disponibles por campaña
                # Disponible = estatus=0 AND (fecha_vigencia IS NULL OR fecha_vigencia >= NOW)
                cupones_disponibles = session.query(
                    CampaniaUsuario.campania_id,
                    func.count(CampaniaUsuario.id_campania_usuario).label('total_disponibles')
                ).filter(
                    CampaniaUsuario.estatus == 0,
                    ((CampaniaUsuario.fecha_vigencia.is_(None)) | 
                     (CampaniaUsuario.fecha_vigencia >= ahora_mx))
                ).group_by(CampaniaUsuario.campania_id).subquery()
                
                # Campañas activas sin cupones disponibles
                campanias_para_desactivar = session.query(
                    Campania
                ).outerjoin(
                    cupones_disponibles, Campania.id_campania == cupones_disponibles.c.campania_id
                ).filter(
                    Campania.estatus == 1,  # Activa
                    ((cupones_disponibles.c.total_disponibles.is_(None)) | 
                     (cupones_disponibles.c.total_disponibles == 0))
                ).all()
                
                resultado = []
                for campania in campanias_para_desactivar:
                    # Contar cupones totales, usados y vencidos
                    stats = session.query(
                        func.count(CampaniaUsuario.id_campania_usuario).label('total'),
                        func.sum(case((CampaniaUsuario.estatus == 1, 1), else_=0)).label('usados'),
                        func.sum(case((CampaniaUsuario.estatus == 2, 1), else_=0)).label('vencidos')
                    ).filter(
                        CampaniaUsuario.campania_id == campania.id_campania
                    ).first()
                    
                    resultado.append({
                        'campania_id': campania.id_campania,
                        'nombre_campania': campania.nombre_campania,
                        'codigo': campania.codigo,
                        'total_cupones': stats.total or 0,
                        'cupones_usados': stats.usados or 0,
                        'cupones_vencidos': stats.vencidos or 0
                    })
                
                logger.info(f"Encontradas {len(resultado)} campañas sin cupones activos")
                return resultado
                
            except Exception as e:
                logger.error(f"Error verificando campañas sin cupones: {str(e)}")
                raise
    
    
    @staticmethod
    def desactivar_campanias_sin_cupones() -> dict:
        """
        Desactivar campañas que ya no tienen cupones disponibles.
        
        Returns:
            Dict con resumen de desactivación
        """
        with get_db_session() as session:
            try:
                ahora_mx = datetime.now(MEXICO_TZ)
                
                # Subquery: contar cupones disponibles por campaña
                cupones_disponibles = session.query(
                    CampaniaUsuario.campania_id,
                    func.count(CampaniaUsuario.id_campania_usuario).label('total_disponibles')
                ).filter(
                    CampaniaUsuario.estatus == 0,
                    ((CampaniaUsuario.fecha_vigencia.is_(None)) | 
                     (CampaniaUsuario.fecha_vigencia >= ahora_mx))
                ).group_by(CampaniaUsuario.campania_id).subquery()
                
                # Campañas activas sin cupones disponibles
                campanias = session.query(Campania).outerjoin(
                    cupones_disponibles, Campania.id_campania == cupones_disponibles.c.campania_id
                ).filter(
                    Campania.estatus == 1,
                    ((cupones_disponibles.c.total_disponibles.is_(None)) | 
                     (cupones_disponibles.c.total_disponibles == 0))
                ).all()
                
                if not campanias:
                    logger.info("No hay campañas para desactivar")
                    return {
                        'campanias_desactivadas': 0,
                        'detalle': []
                    }
                
                desactivadas = []
                for campania in campanias:
                    campania.estatus = 0  # Desactivar
                    desactivadas.append({
                        'campania_id': campania.id_campania,
                        'nombre_campania': campania.nombre_campania,
                        'codigo': campania.codigo
                    })
                
                session.commit()
                
                logger.info(f"Desactivadas {len(desactivadas)} campañas sin cupones activos")
                
                return {
                    'campanias_desactivadas': len(desactivadas),
                    'detalle': desactivadas
                }
                
            except Exception as e:
                logger.error(f"Error desactivando campañas: {str(e)}")
                raise
