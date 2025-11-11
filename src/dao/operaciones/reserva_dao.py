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

logger = logging.getLogger(__name__)


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
        
        Args:
            cliente_id: ID del cliente que reserva
            recepcionista_id: ID del recepcionista que confirma (desde PWA)
            inicio: Fecha/hora inicio reserva
            fin_estimado: Fecha/hora fin estimado
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
        cliente_id: int = None,
        estatus: int = None,
        fecha_desde: datetime = None,
        fecha_hasta: datetime = None
    ) -> list:
        """
        Listar reservas con filtros opcionales.
        
        Args:
            cliente_id: Filtrar por cliente
            estatus: Filtrar por estatus
            fecha_desde: Filtrar desde fecha
            fecha_hasta: Filtrar hasta fecha
            
        Returns:
            Lista de dicts de reservas
        """
        schema = ReservaResponseSchema()
        with get_db_session() as session:
            query = session.query(Reserva)
            
            if cliente_id:
                query = query.filter(Reserva.cliente_id == cliente_id)
            
            if estatus:
                query = query.filter(Reserva.estatus == estatus)
            
            if fecha_desde:
                query = query.filter(Reserva.inicio >= fecha_desde)
            
            if fecha_hasta:
                query = query.filter(Reserva.inicio <= fecha_hasta)
            
            reservas = query.order_by(Reserva.inicio.asc()).all()
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
        
        Args:
            reserva_id: ID de la reserva
            
        Returns:
            Dict actualizado o None
        """
        return ReservaDAO.actualizar_estatus_reserva(
            reserva_id,
            3,  # Completada
            "Reserva completada"
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
    def verificar_no_shows() -> int:
        """
        Job de limpieza: Marcar como NoShow reservas programadas
        donde se pasó el tiempo de tolerancia.
        
        Returns:
            Cantidad de reservas marcadas como NoShow
        """
        with get_db_session() as session:
            ahora = datetime.now()
            
            # Obtener config default de tolerancia (15 min)
            # TODO: Leer desde config.ConfigSucursal
            tolerancia_default = 15
            
            # Buscar reservas programadas donde ya pasó inicio + tolerancia
            reservas_programadas = session.query(Reserva).filter(
                Reserva.estatus == 1  # Solo programadas
            ).all()
            
            count = 0
            for reserva in reservas_programadas:
                tolerancia = reserva.tolerancia_min or tolerancia_default
                # Si pasó inicio + tolerancia
                from datetime import timedelta
                limite = reserva.inicio + timedelta(minutes=tolerancia)
                
                if ahora > limite:
                    reserva.estatus = 4  # NoShow
                    reserva.updated_at = ahora
                    reserva.notas = (reserva.notas or "") + f" | NoShow automático (tolerancia {tolerancia} min)"
                    count += 1
            
            if count > 0:
                session.commit()
                logger.info(f"Job: {count} reservas marcadas como NoShow automáticamente")
            
            return count
    
    
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
