"""
ReservaDAO - Data Access Object para operaciones.Reserva
Gestión de reservaciones confirmadas de mesas
"""

from datetime import datetime
from sqlalchemy import and_, or_
from src.models.operaciones.reserva_model import Reserva
from src.models.operaciones.hold_mesa_model import HoldMesa
from src.core.db.session_manager import get_db_session
from src.schemas.reserva_schema import ReservaResponseSchema
import logging
import pytz

logger = logging.getLogger(__name__)

# Zona horaria de México
TZ_MEXICO = pytz.timezone('America/Mexico_City')


class ReservaDAO:
    """Data Access Object para Reserva"""
    
    @staticmethod
    def verificar_reserva_disponible(mesa_id: int, inicio: datetime, fin_estimado: datetime) -> dict:
        """
        Verificar si hay traslape con otras RESERVAS activas (confirmadas).
        
        ⚡ IMPORTANTE: 
        - SOLO valida Reservas, NO Holds
        - Suma 10 minutos de limpieza automáticamente
        - CALCULA EN PYTHON (no en SQL Server) para evitar errores de tipo datetime2
        
        Args:
            mesa_id: ID de la mesa
            inicio: Fecha/hora inicio deseada
            fin_estimado: Fecha/hora fin estimado
            
        Returns:
            Dict con estructura:
            {
                "disponible": bool,
                "proxima_disponibilidad": datetime o None,  # Cuándo queda disponible si hay conflicto
                "razon": str  # Detalles del conflicto si existe
            }
        """
        from datetime import timedelta
        
        with get_db_session() as session:
            # AGREGAR 10 MINUTOS DE LIMPIEZA AL RANGO SOLICITADO (en Python, no en SQL)
            fin_con_limpieza = fin_estimado + timedelta(minutes=10)
            
            print(f"\n[VERIFICAR_RESERVA_DISPONIBLE] Comprobando disponibilidad")
            print(f"  Mesa {mesa_id}")
            print(f"  Rango original: {inicio} - {fin_estimado}")
            print(f"  Rango con limpieza: {inicio} - {fin_con_limpieza}")
            
            # OBTENER TODAS LAS RESERVAS ACTIVAS PARA ESTA MESA
            # Usamos HoldMesa como intermediario porque Reserva no tiene mesa_id directo
            # Reserva.hold_id -> HoldMesa.mesa_id
            try:
                reservas_activas = session.query(Reserva).join(
                    HoldMesa, Reserva.hold_id == HoldMesa.id_hold_mesa
                ).filter(
                    HoldMesa.mesa_id == mesa_id,
                    Reserva.estatus.in_([1, 2])  # Programada o EnCurso
                ).all()
            except Exception as e:
                logger.error(f"Error al consultar reservas activas para mesa {mesa_id}: {e}")
                print(f"  ERROR en consulta: {e}")
                raise
            
            print(f"  Encontradas {len(reservas_activas)} reservas activas en mesa {mesa_id}")
            
            # VERIFICAR TRASLAPES EN PYTHON (NO en SQL)
            proxima_disponibilidad = None
            reserva_conflictiva = None
            
            for reserva in reservas_activas:
                # Rango de la reserva existente (con 10 min de limpieza) - CALCULADO EN PYTHON
                reserva_fin_con_limpieza = reserva.fin_estimado + timedelta(minutes=10)
                
                # Lógica de solapamiento (en Python):
                # Dos rangos se solapan si:
                # inicio_nuevo <= fin_existente_limpio AND fin_nuevo_limpio >= inicio_existente
                if inicio <= reserva_fin_con_limpieza and fin_con_limpieza >= reserva.inicio:
                    print(f"  ⚠️  TRASLAPE DETECTADO: Reserva {reserva.id_reserva}")
                    print(f"     Rango existente: {reserva.inicio} - {reserva_fin_con_limpieza} (con 10 min limpieza)")
                    print(f"     Rango solicitado: {inicio} - {fin_con_limpieza}")
                    logger.warning(f"Mesa {mesa_id} tiene traslape con Reserva {reserva.id_reserva} en rango {inicio} - {fin_con_limpieza}")
                    
                    # Guardar la hora más temprana cuando queda disponible
                    if proxima_disponibilidad is None or reserva_fin_con_limpieza < proxima_disponibilidad:
                        proxima_disponibilidad = reserva_fin_con_limpieza
                        reserva_conflictiva = reserva
            
            if proxima_disponibilidad and reserva_conflictiva:
                # Mesa disponible DESPUÉS de la limpieza (fin + 10 min)
                mesa_disponible_desde = proxima_disponibilidad
                
                # Reserva nueva debe terminar ANTES de: inicio_conflictiva - 10 min (para tu limpieza)
                reserva_debe_terminar_antes = reserva_conflictiva.inicio - timedelta(minutes=10)
                
                print(f"  ✗ No disponible")
                print(f"     Mesa disponible desde: {mesa_disponible_desde.strftime('%H:%M')}")
                print(f"     Reserva debe terminar antes: {reserva_debe_terminar_antes.strftime('%H:%M')}")
                
                return {
                    "disponible": False,
                    "mesa_disponible_desde": mesa_disponible_desde,
                    "reserva_debe_terminar_antes": reserva_debe_terminar_antes,
                    "razon": f"Conflicto con reserva existente"
                }
            
            print(f"  ✓ Disponible - No hay traslapes")
            return {
                "disponible": True,
                "mesa_disponible_desde": None,
                "reserva_debe_terminar_antes": None,
                "razon": None
            }
    
    @staticmethod
    def crear_reserva(
        cliente_id: int,
        recepcionista_id: int,
        inicio: datetime,
        fin_estimado: datetime,
        tolerancia_min: int = None,
        notas: str = None,
        hold_id: int = None,
        mesa_id: int = None
    ) -> dict:
        """
        Crear nueva reserva confirmada.
        
        VALIDACIÓN: Verifica que no haya traslape con otras reservas activas.
        
        Las fechas (inicio, fin_estimado) llegan como naive datetime (sin timezone).
        Se asume que están en zona de México y se convierten si es necesario.
        
        Args:
            cliente_id: ID del cliente que reserva
            recepcionista_id: ID del recepcionista que confirma (desde PWA)
            inicio: Fecha/hora inicio reserva (naive datetime, asumida zona México)
            fin_estimado: Fecha/hora fin estimado (naive datetime, asumida zona México)
            tolerancia_min: Minutos de tolerancia para NoShow (NULL = usar config)
            notas: Notas adicionales
            hold_id: ID del hold si se origina desde hold
            mesa_id: ID de la mesa (opcional, se obtiene del hold si no se proporciona)
            
        Returns:
            Dict serializado de la reserva, o None si hay error
        """
        schema = ReservaResponseSchema()
        
        with get_db_session() as session:
            # PASO 1: Convertir fechas naive a zona de México si es necesario
            # Las fechas llegan sin timezone, se asume que están en zona de México
            if inicio.tzinfo is None:
                inicio = TZ_MEXICO.localize(inicio).replace(tzinfo=None)
            if fin_estimado.tzinfo is None:
                fin_estimado = TZ_MEXICO.localize(fin_estimado).replace(tzinfo=None)
            
            logger.info(f"[CREAR_RESERVA] Fechas convertidas a zona México: {inicio} - {fin_estimado}")
            
            # PASO 2: Obtener mesa_id del hold si no se proporcionó
            if not mesa_id and hold_id:
                hold = session.query(HoldMesa).filter(HoldMesa.id_hold_mesa == hold_id).first()
                if hold:
                    mesa_id = hold.mesa_id
                    logger.info(f"Mesa obtenida desde Hold {hold_id}: mesa_id={mesa_id}")
            
            # PASO 2B: Validar que mesa existe (si tenemos mesa_id)
            if mesa_id:
                from src.models.catalogos.mesa_model import Mesa
                mesa_existe = session.query(Mesa).filter(Mesa.id_mesa == mesa_id).first()
                if not mesa_existe:
                    logger.error(f"Mesa {mesa_id} no existe en BD")
                    raise ValueError(f"Mesa {mesa_id} no existe en el sistema")
            
            # PASO 3: VALIDACIÓN - Verificar que no hay traslape con otras reservas activas
            if mesa_id:
                resultado_disponibilidad = ReservaDAO.verificar_reserva_disponible(mesa_id, inicio, fin_estimado)
                if not resultado_disponibilidad["disponible"]:
                    logger.warning(f"No se puede crear reserva: traslape detectado en mesa {mesa_id} para {inicio} - {fin_estimado}")
                    
                    # Obtener los horarios disponibles
                    mesa_disponible_desde = resultado_disponibilidad.get("mesa_disponible_desde")
                    reserva_debe_terminar_antes = resultado_disponibilidad.get("reserva_debe_terminar_antes")
                    
                    if mesa_disponible_desde and reserva_debe_terminar_antes:
                        error = ValueError(f"Mesa no disponible en ese horario")
                        # Adjuntar datos de disponibilidad a la excepción
                        error.mesa_disponible_desde = mesa_disponible_desde
                        error.reserva_debe_terminar_antes = reserva_debe_terminar_antes
                        raise error
                    else:
                        raise ValueError(resultado_disponibilidad.get("razon", "Mesa no disponible en ese horario"))
            else:
                logger.warning(f"Reserva creada sin mesa_id (hold_id={hold_id}), no se validó traslape")
            
            # PASO 4: Crear la reserva
            reserva = Reserva(
                cliente_id=cliente_id,
                recepcionista_id=recepcionista_id,
                inicio=inicio,
                fin_estimado=fin_estimado,
                estatus=1,  # Programada
                tolerancia_min=tolerancia_min,
                notas=notas,
                hold_id=hold_id
            )
            session.add(reserva)
            session.commit()
            logger.info(f"Reserva creada: ID {reserva.id_reserva} para cliente {cliente_id}, inicio {inicio}")
            return schema.dump(reserva)
    
    @staticmethod
    def obtener_reserva_por_id(reserva_id: int) -> dict:
        """
        Obtener reserva por ID.
        
        Args:
            reserva_id: ID de la reserva
            
        Returns:
            Dict de la reserva o None
        """
        schema = ReservaResponseSchema()
        with get_db_session() as session:
            reserva = session.query(Reserva).filter(
                Reserva.id_reserva == reserva_id
            ).first()
            return schema.dump(reserva) if reserva else None
       
    @staticmethod
    def listar_reservas(
        sucursal_id: int = None,
        cliente_id: int = None,
        estatus: int = None,
        fecha_desde: datetime = None,
        fecha_hasta: datetime = None
    ) -> list:
        """
        Listar reservas con filtros opcionales.
        
        Filtros sobre fechas:
        - fecha_desde + fecha_hasta: retorna reservas que se solapan con el rango (inicio <= fecha_hasta AND fin_estimado >= fecha_desde)
        - solo fecha_desde: retorna reservas que NO han terminado antes (fin_estimado >= fecha_desde)
        - solo fecha_hasta: retorna reservas que NO comienzan después (inicio <= fecha_hasta)
        
        Para filtrar por sucursal_id, se hace JOIN: Reserva -> HoldMesa -> Mesa -> Area -> sucursal_id
        
        Args:
            sucursal_id: Filtrar por sucursal (a través de hold_id -> mesa -> area -> sucursal)
            cliente_id: Filtrar por cliente
            estatus: Filtrar por estatus
            fecha_desde: Inicio del rango de fechas (opcional)
            fecha_hasta: Fin del rango de fechas (opcional)
            
        Returns:
            Lista de dicts de reservas
        """
        from src.models.operaciones.hold_mesa_model import HoldMesa
        from src.models.catalogos.mesa_model import Mesa
        from src.models.catalogos.area_model import Area
        
        schema = ReservaResponseSchema()
        with get_db_session() as session:
            query = session.query(Reserva)
            
            # Si busca por sucursal, hacer JOIN con HoldMesa, Mesa y Area
            if sucursal_id:
                query = query.join(
                    HoldMesa, Reserva.hold_id == HoldMesa.id_hold_mesa
                ).join(
                    Mesa, HoldMesa.mesa_id == Mesa.id_mesa
                ).join(
                    Area, Mesa.area_id == Area.id_area
                ).filter(
                    Area.sucursal_id == sucursal_id
                )
            
            if cliente_id:
                query = query.filter(Reserva.cliente_id == cliente_id)
            
            if estatus:
                query = query.filter(Reserva.estatus == estatus)
            
            # Filtrar por rango de fechas: reservas que se solapan con el período consultado
            # Una reserva se solapa si: inicio < fecha_hasta AND fin_estimado > fecha_desde
            if fecha_desde and fecha_hasta:
                query = query.filter(
                    Reserva.inicio <= fecha_hasta,
                    Reserva.fin_estimado >= fecha_desde
                )
            elif fecha_desde:
                # Si solo hay fecha_desde, mostrar reservas que NO han terminado antes
                query = query.filter(Reserva.fin_estimado >= fecha_desde)
            elif fecha_hasta:
                # Si solo hay fecha_hasta, mostrar reservas que NO comienzan después
                query = query.filter(Reserva.inicio <= fecha_hasta)
            
            reservas = query.order_by(Reserva.inicio.asc()).all()
            return [schema.dump(r) for r in reservas]
    
    @staticmethod
    def listar_reservas_por_mesero(usuario_id: int) -> list:
        """
        Listar reservas asignadas a un mesero (a través de AsignacionMesa).
        Ordenadas por estatus (de menor a mayor).
        
        Args:
            usuario_id: ID del mesero (usuario)
            
        Returns:
            Lista de dicts de reservas ordenadas por estatus
        """
        from src.models.operaciones.asignacion_mesa_model import AsignacionMesa
        from src.models.operaciones.hold_mesa_model import HoldMesa
        from src.models.catalogos.mesa_model import Mesa
        
        schema = ReservaResponseSchema()
        with get_db_session() as session:
            # JOIN Reserva -> HoldMesa -> Mesa -> AsignacionMesa (usuario_id)
            query = session.query(Reserva).join(
                HoldMesa, Reserva.hold_id == HoldMesa.id_hold_mesa
            ).join(
                Mesa, HoldMesa.mesa_id == Mesa.id_mesa
            ).join(
                AsignacionMesa, Mesa.id_mesa == AsignacionMesa.mesa_id
            ).filter(
                AsignacionMesa.usuario_id == usuario_id,
                AsignacionMesa.es_activa == True  # Solo asignaciones activas
            ).order_by(Reserva.estatus.asc())
            
            reservas = query.all()
            return [schema.dump(r) for r in reservas]
    
    @staticmethod
    def actualizar_estatus_reserva(reserva_id: int, estatus: int, notas: str = None) -> dict:
        """
        Actualizar estatus de reserva.
        
        Args:
            reserva_id: ID de la reserva
            estatus: Nuevo estatus (1=Programada, 2=EnCurso, 3=Completada, 4=NoShow, 5=Cancelada)
            notas: Notas adicionales (opcional)
            
        Returns:
            Dict actualizado o None
        """
        schema = ReservaResponseSchema()
        with get_db_session() as session:
            reserva = session.query(Reserva).filter(
                Reserva.id_reserva == reserva_id
            ).first()
            
            if not reserva:
                return None
            
            reserva.estatus = estatus
            reserva.updated_at = datetime.now()
            
            if notas:
                # Agregar notas a las existentes
                if reserva.notas:
                    reserva.notas += f" | {notas}"
                else:
                    reserva.notas = notas
            
            session.commit()
            logger.info(f"Reserva {reserva_id} actualizada a estatus {estatus}")
            return schema.dump(reserva)
    
    @staticmethod
    def cancelar_reserva(reserva_id: int, motivo: str = None) -> dict:
        """
        Cancelar reserva (estatus=5).
        
        ACCIÓN PRINCIPAL:
        - Marca la reserva como Cancelada (estatus=5)
        
        ACCIÓN SECUNDARIA (siempre que sea posible):
        - Marca la mesa asociada como "Disponible" (estatus=1)
        - Se obtiene la mesa a través del Hold asociado a la reserva
        
        Args:
            reserva_id: ID de la reserva
            motivo: Motivo de cancelación
            
        Returns:
            Dict con reserva actualizada o None
        """
        from src.dao.catalogos.mesa_estatus_dao import MesaEstatusDAO
        from src.models.operaciones.hold_mesa_model import HoldMesa
        
        schema = ReservaResponseSchema()
        with get_db_session() as session:
            # Obtener reserva
            reserva = session.query(Reserva).filter(
                Reserva.id_reserva == reserva_id
            ).first()
            
            if not reserva:
                return None
            
            # Si tiene hold, obtener la mesa y actualizarla a "Disponible"
            if reserva.hold_id:
                hold = session.query(HoldMesa).filter(
                    HoldMesa.id_hold_mesa == reserva.hold_id
                ).first()
                
                if hold:
                    mesa_id = hold.mesa_id
                    # Cambiar mesa a "Disponible" (estatus=1)
                    MesaEstatusDAO.actualizar_estatus_mesa(
                        mesa_id,
                        1,  # Disponible
                        None,
                        f"Mesa disponible - Reserva cancelada {reserva_id}: {motivo if motivo else 'Sin motivo'}"
                    )
                    logger.info(f"Mesa {mesa_id} marcada como disponible tras cancelar reserva {reserva_id}")
            else:
                logger.warning(f"Reserva {reserva_id} cancelada pero sin hold asociado - mesa no actualizada")
            
            # Actualizar estatus de reserva a cancelada
            reserva.estatus = 5
            reserva.updated_at = datetime.now()
            if motivo:
                if reserva.notas:
                    reserva.notas += f" | Cancelada: {motivo}"
                else:
                    reserva.notas = f"Cancelada: {motivo}"
            session.commit()
            
            logger.info(f"Reserva {reserva_id} cancelada - estatus cambiado a 5 (Cancelada)")
            return schema.dump(reserva)
    
    @staticmethod
    def iniciar_reserva(reserva_id: int) -> dict:
        """
        Iniciar reserva (estatus=2 - EnCurso).
        Cliente llegó y está ocupando mesa.
        
        ACCIÓN PRINCIPAL:
        - Marca la reserva como EnCurso (estatus=2)
        
        ACCIÓN SECUNDARIA (siempre que sea posible):
        - Marca la mesa asociada como "Ocupada" (estatus=2)
        - Se obtiene la mesa a través del Hold asociado a la reserva
        
        Args:
            reserva_id: ID de la reserva
            
        Returns:
            Dict con reserva actualizada o None
        """
        from src.dao.catalogos.mesa_estatus_dao import MesaEstatusDAO
        from src.models.operaciones.hold_mesa_model import HoldMesa
        
        schema = ReservaResponseSchema()
        with get_db_session() as session:
            # Obtener reserva
            reserva = session.query(Reserva).filter(
                Reserva.id_reserva == reserva_id
            ).first()
            
            if not reserva:
                return None
            
            # Si tiene hold, obtener la mesa y actualizarla a "Ocupada"
            if reserva.hold_id:
                hold = session.query(HoldMesa).filter(
                    HoldMesa.id_hold_mesa == reserva.hold_id
                ).first()
                
                if hold:
                    mesa_id = hold.mesa_id
                    # Cambiar mesa a "Ocupada" (estatus=2)
                    MesaEstatusDAO.actualizar_estatus_mesa(
                        mesa_id,
                        2,  # Ocupada
                        None,
                        f"Mesa ocupada - Reserva iniciada {reserva_id}"
                    )
                    logger.info(f"Mesa {mesa_id} marcada como ocupada para reserva {reserva_id}")
            else:
                logger.warning(f"Reserva {reserva_id} iniciada pero sin hold asociado - mesa no actualizada")
            
            # Actualizar estatus de reserva a en curso
            reserva.estatus = 2
            reserva.updated_at = datetime.now()
            session.commit()
            
            logger.info(f"Reserva {reserva_id} iniciada - estatus cambiado a 2 (EnCurso)")
            return schema.dump(reserva)

    @staticmethod
    def completar_reserva(reserva_id: int) -> dict:
        """
        Completar reserva (estatus=3 - Completada).
        Cliente terminó y se fue.
        
        ACCIÓN PRINCIPAL:
        - Marca la reserva como Completada (estatus=3)
        
        ACCIÓN SECUNDARIA (siempre que sea posible):
        - Marca la mesa asociada como "En Limpieza" (estatus=3)
        - Se obtiene la mesa a través del Hold asociado a la reserva
        - Si no hay Hold, solo se completa la reserva (sin cambio de mesa)
        
        Args:
            reserva_id: ID de la reserva
            
        Returns:
            Dict con reserva actualizada o None
        """
        from src.dao.catalogos.mesa_estatus_dao import MesaEstatusDAO
        from src.models.operaciones.hold_mesa_model import HoldMesa
        
        schema = ReservaResponseSchema()
        with get_db_session() as session:
            # Obtener reserva
            reserva = session.query(Reserva).filter(
                Reserva.id_reserva == reserva_id
            ).first()
            
            if not reserva:
                return None
            
            # Si tiene hold, obtener la mesa y actualizarla a "En Limpieza"
            if reserva.hold_id:
                hold = session.query(HoldMesa).filter(
                    HoldMesa.id_hold_mesa == reserva.hold_id
                ).first()
                
                if hold:
                    mesa_id = hold.mesa_id
                    # Cambiar mesa a "En Limpieza" (estatus=3)
                    MesaEstatusDAO.actualizar_estatus_mesa(
                        mesa_id,
                        3,  # En Limpieza
                        None,
                        f"Mesa en limpieza después de completar reserva {reserva_id}"
                    )
                    logger.info(f"Mesa {mesa_id} marcada en limpieza después de completar reserva {reserva_id}")
            else:
                logger.warning(f"Reserva {reserva_id} completada pero sin hold asociado - mesa no actualizada")
            
            # Actualizar estatus de reserva a completada
            reserva.estatus = 3
            reserva.updated_at = datetime.now()
            session.commit()
            
            logger.info(f"Reserva {reserva_id} completada - estatus cambiado a 3 (Completada)")
            return schema.dump(reserva)
  
    @staticmethod
    def marcar_no_show(reserva_id: int) -> dict:
        """
        Marcar reserva como NoShow (estatus=4).
        Cliente no llegó en tiempo de tolerancia.
        
        ACCIÓN PRINCIPAL:
        - Marca la reserva como NoShow (estatus=4)
        
        ACCIÓN SECUNDARIA (siempre que sea posible):
        - Marca la mesa asociada como "Disponible" (estatus=1)
        - Se obtiene la mesa a través del Hold asociado a la reserva
        
        Args:
            reserva_id: ID de la reserva
            
        Returns:
            Dict con reserva actualizada o None
        """
        from src.dao.catalogos.mesa_estatus_dao import MesaEstatusDAO
        from src.models.operaciones.hold_mesa_model import HoldMesa
        
        schema = ReservaResponseSchema()
        with get_db_session() as session:
            # Obtener reserva
            reserva = session.query(Reserva).filter(
                Reserva.id_reserva == reserva_id
            ).first()
            
            if not reserva:
                return None
            
            # Si tiene hold, obtener la mesa y actualizarla a "Disponible"
            if reserva.hold_id:
                hold = session.query(HoldMesa).filter(
                    HoldMesa.id_hold_mesa == reserva.hold_id
                ).first()
                
                if hold:
                    mesa_id = hold.mesa_id
                    # Cambiar mesa a "Disponible" (estatus=1)
                    MesaEstatusDAO.actualizar_estatus_mesa(
                        mesa_id,
                        1,  # Disponible
                        None,
                        f"Mesa disponible - Reserva NoShow {reserva_id}"
                    )
                    logger.info(f"Mesa {mesa_id} marcada como disponible tras NoShow en reserva {reserva_id}")
            else:
                logger.warning(f"Reserva {reserva_id} marcada NoShow pero sin hold asociado - mesa no actualizada")
            
            # Actualizar estatus de reserva a no show
            reserva.estatus = 4
            reserva.updated_at = datetime.now()
            if reserva.notas:
                reserva.notas += " | Cliente no se presentó"
            else:
                reserva.notas = "Cliente no se presentó"
            session.commit()
            
            logger.info(f"Reserva {reserva_id} marcada NoShow - estatus cambiado a 4")
            return schema.dump(reserva)
    
    @staticmethod
    def reserva_existe(reserva_id: int) -> bool:
        """
        Verificar si una reserva existe.
        
        Args:
            reserva_id: ID de la reserva
            
        Returns:
            True si existe
        """
        with get_db_session() as session:
            existe = session.query(Reserva).filter(
                Reserva.id_reserva == reserva_id
            ).first()
            return existe is not None
    
    @staticmethod
    def verificar_no_shows() -> int:
        """
        Job: Marca automáticamente como NoShow reservas programadas donde pasó la tolerancia.
        
        LÓGICA:
        - Busca reservas con estatus=1 (Programada)
        - Verifica si ahora > (inicio + tolerancia_min)
        - Cambia estatus a 4 (NoShow) automáticamente
        - LIBERA LA MESA: la devuelve a Disponible (estatus=1)
        
        IMPORTANTE: 
        - Se ejecuta desde Azure Function Timer (NO desde scheduler local)
        - NO hay ejecución automática local
        - Solo consumido por POST /api/jobs/verificar-no-shows
        - Usa timezone MÉXICO para todas las comparaciones
        
        Returns:
            int: Cantidad de reservas marcadas como NoShow
        """
        from src.dao.catalogos.mesa_estatus_dao import MesaEstatusDAO
        
        with get_db_session() as session:
            from datetime import timedelta
            ahora_mexico = datetime.now(TZ_MEXICO).replace(tzinfo=None)
            tolerancia_default = 15
            
            # Buscar reservas programadas (estatus=1)
            reservas_programadas = session.query(Reserva).filter(
                Reserva.estatus == 1  # Solo programadas
            ).all()
            
            count = 0
            for reserva in reservas_programadas:
                tolerancia = reserva.tolerancia_min or tolerancia_default
                
                # Convertir inicio a datetime si es string y aplicar timezone
                inicio_reserva = reserva.inicio
                if isinstance(inicio_reserva, str):
                    inicio_reserva = datetime.fromisoformat(inicio_reserva.replace('Z', '+00:00'))
                    if inicio_reserva.tzinfo:
                        inicio_reserva = inicio_reserva.astimezone(TZ_MEXICO).replace(tzinfo=None)
                
                # Calcular límite de tolerancia con timezone México
                limite = inicio_reserva + timedelta(minutes=tolerancia)
                
                # Si pasó el deadline de tolerancia, marcar como NoShow (comparación con timezone México)
                if ahora_mexico > limite:
                    reserva.estatus = 4  # NoShow
                    reserva.updated_at = ahora_mexico
                    reserva.notas = (reserva.notas or "") + f" | NoShow automático (por job - tolerancia {tolerancia} min)"
                    count += 1
                    
                    # LIBERAR LA MESA: devolverla a Disponible si tiene hold
                    if reserva.hold_id:
                        hold = session.query(HoldMesa).filter(
                            HoldMesa.id_hold_mesa == reserva.hold_id
                        ).first()
                        
                        if hold:
                            mesa_id = hold.mesa_id
                            # Cambiar mesa a "Disponible" (estatus=1)
                            MesaEstatusDAO.actualizar_estatus_mesa(
                                mesa_id,
                                1,  # Disponible
                                None,
                                f"Mesa disponible - Reserva marcada NoShow por tolerancia expirada"
                            )
                            logger.info(f"Job verificar_no_shows: Mesa {mesa_id} liberada después de NoShow en reserva {reserva.id_reserva}")
            
            if count > 0:
                session.commit()
                logger.info(f"Job verificar_no_shows: {count} reservas marcadas como NoShow (timezone México)")
            
            return count
