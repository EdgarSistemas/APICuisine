"""
ReservaDAO - Data Access Object para operaciones.Reserva
Gestión de reservaciones confirmadas de mesas
"""

from datetime import datetime
from sqlalchemy import and_, or_
from src.models.operaciones.reserva_model import Reserva
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
    def crear_reserva(
        cliente_id: int,
        recepcionista_id: int,
        inicio: datetime,
        fin_estimado: datetime,
        tolerancia_min: int = None,
        notas: str = None,
        hold_id: int = None
    ) -> dict:
        """
        Crear nueva reserva confirmada.
        
        Las fechas (inicio, fin_estimado) llegan ya parseadas por Marshmallow
        en formato correcto de México (naive datetime en hora de México).
        
        Args:
            cliente_id: ID del cliente que reserva
            recepcionista_id: ID del recepcionista que confirma (desde PWA)
            inicio: Fecha/hora inicio reserva (naive datetime en TZ_MEXICO)
            fin_estimado: Fecha/hora fin estimado (naive datetime en TZ_MEXICO)
            tolerancia_min: Minutos de tolerancia para NoShow (NULL = usar config)
            notas: Notas adicionales
            hold_id: ID del hold si se origina desde hold
            
        Returns:
            Dict serializado de la reserva
        """
        schema = ReservaResponseSchema()
        
        with get_db_session() as session:
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
        - fecha_desde: reservas donde inicio >= fecha_desde
        - fecha_hasta: reservas donde fin_estimado <= fecha_hasta
        
        Para filtrar por sucursal_id, se hace JOIN con HoldMesa y Mesa
        
        Args:
            sucursal_id: Filtrar por sucursal (a través de hold_id -> mesa -> sucursal)
            cliente_id: Filtrar por cliente
            estatus: Filtrar por estatus
            fecha_desde: Filtrar desde fecha (aplica a 'inicio')
            fecha_hasta: Filtrar hasta fecha (aplica a 'fin_estimado')
            
        Returns:
            Lista de dicts de reservas
        """
        from src.models.operaciones.hold_mesa_model import HoldMesa
        from src.models.catalogos.mesa_model import Mesa
        
        schema = ReservaResponseSchema()
        with get_db_session() as session:
            query = session.query(Reserva)
            
            # Si busca por sucursal, hacer JOIN con HoldMesa y Mesa
            if sucursal_id:
                query = query.join(
                    HoldMesa, Reserva.hold_id == HoldMesa.id_hold_mesa
                ).join(
                    Mesa, HoldMesa.mesa_id == Mesa.id_mesa
                ).filter(
                    Mesa.sucursal_id == sucursal_id
                )
            
            if cliente_id:
                query = query.filter(Reserva.cliente_id == cliente_id)
            
            if estatus:
                query = query.filter(Reserva.estatus == estatus)
            
            # Filtrar por rango de fechas usando inicio y fin_estimado
            if fecha_desde:
                query = query.filter(Reserva.inicio >= fecha_desde)
            
            if fecha_hasta:
                query = query.filter(Reserva.fin_estimado <= fecha_hasta)
            
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
        
        Args:
            reserva_id: ID de la reserva
            motivo: Motivo de cancelación
            
        Returns:
            Dict actualizado o None
        """
        return ReservaDAO.actualizar_estatus_reserva(
            reserva_id,
            5,  # Cancelada
            f"Cancelada: {motivo}" if motivo else "Cancelada"
        )
    
    
    @staticmethod
    def iniciar_reserva(reserva_id: int) -> dict:
        """
        Iniciar reserva (estatus=2 - EnCurso).
        Cliente llegó y está ocupando mesa.
        
        Args:
            reserva_id: ID de la reserva
            
        Returns:
            Dict actualizado o None
        """
        return ReservaDAO.actualizar_estatus_reserva(
            reserva_id,
            2,  # EnCurso
            "Cliente llegó - Reserva iniciada"
        )
    
    
    @staticmethod
    def completar_reserva(reserva_id: int) -> dict:
        """
        Completar reserva (estatus=3 - Completada).
        Cliente terminó y se fue.
        
        ACCIÓN ADICIONAL:
        - Marca la mesa asociada a la reserva como "En Limpieza" (estatus=3)
        
        Args:
            reserva_id: ID de la reserva
            
        Returns:
            Dict actualizado o None
        """
        from src.dao.catalogos.mesa_estatus_dao import MesaEstatusDAO
        from src.models.operaciones.hold_mesa_model import HoldMesa
        from src.models.catalogos.mesa_model import Mesa
        
        with get_db_session() as session:
            # Obtener reserva y mesa asociada
            reserva = session.query(Reserva).filter(
                Reserva.id_reserva == reserva_id
            ).first()
            
            if not reserva or not reserva.hold_id:
                # No tiene hold asociado, solo actualizar estatus
                return ReservaDAO.actualizar_estatus_reserva(
                    reserva_id,
                    3,
                    "Reserva completada"
                )
            
            # Obtener mesa del hold
            hold = session.query(HoldMesa).filter(
                HoldMesa.id_hold_mesa == reserva.hold_id
            ).first()
            
            if hold:
                mesa_id = hold.mesa_id
                # Marcar mesa como "En Limpieza"
                MesaEstatusDAO.actualizar_estatus_mesa(
                    mesa_id,
                    3,  # En Limpieza
                    None,
                    f"Mesa en limpieza después de completar reserva {reserva_id}"
                )
                logger.info(f"Mesa {mesa_id} marcada en limpieza después de completar reserva {reserva_id}")
        
        # Actualizar estatus de reserva a completada
        return ReservaDAO.actualizar_estatus_reserva(
            reserva_id,
            3,  # Completada
            "Reserva completada - Mesa en limpieza"
        )
    
    
    @staticmethod
    def marcar_no_show(reserva_id: int) -> dict:
        """
        Marcar reserva como NoShow (estatus=4).
        Cliente no llegó en tiempo de tolerancia.
        
        Args:
            reserva_id: ID de la reserva
            
        Returns:
            Dict actualizado o None
        """
        return ReservaDAO.actualizar_estatus_reserva(
            reserva_id,
            4,  # NoShow
            "Cliente no se presentó"
        )
    
    
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
        
        IMPORTANTE: 
        - Se ejecuta desde Azure Function Timer (NO desde scheduler local)
        - NO hay ejecución automática local
        - Solo consumido por POST /api/jobs/verificar-no-shows
        - Usa timezone MÉXICO para todas las comparaciones
        
        Returns:
            int: Cantidad de reservas marcadas como NoShow
        """
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
            
            if count > 0:
                session.commit()
                logger.info(f"Job verificar_no_shows: {count} reservas marcadas como NoShow (timezone México)")
            
            return count
