"""
HoldMesaDAO - Data Access Object para operaciones.HoldMesa
Gestión de holds temporales de mesas durante proceso de reserva
"""

from datetime import datetime, timedelta
from sqlalchemy import and_, or_
from src.models.operaciones.hold_mesa_model import HoldMesa
from src.core.db.session_manager import get_db_session
from src.schemas.reserva_schema import HoldMesaResponseSchema
import logging

logger = logging.getLogger(__name__)


class HoldMesaDAO:
    """Data Access Object para HoldMesa"""
    
    @staticmethod
    def crear_hold(
        mesa_id: int,
        actor_tipo: int,
        actor_usuario_id: int,
        inicio: datetime,
        fin_estimado: datetime,
        ttl_minutes: int = 5,
        notas: str = None
    ) -> dict:
        """
        Crear nuevo hold de mesa.
        
        Args:
            mesa_id: ID de la mesa a reservar
            actor_tipo: 1=Cliente, 2=Recepcionista
            actor_usuario_id: ID del usuario que genera hold
            inicio: Fecha/hora inicio deseada
            fin_estimado: Fecha/hora fin estimado
            ttl_minutes: Minutos antes de expirar (default 5)
            notas: Notas adicionales
            
        Returns:
            Dict serializado del hold
        """
        schema = HoldMesaResponseSchema()
        with get_db_session() as session:
            # Calcular expires_at
            expires_at = datetime.now() + timedelta(minutes=ttl_minutes)
            
            hold = HoldMesa(
                mesa_id=mesa_id,
                actor_tipo=actor_tipo,
                actor_usuario_id=actor_usuario_id,
                inicio=inicio,
                fin_estimado=fin_estimado,
                expires_at=expires_at,
                estatus=1,  # Activo
                notas=notas
            )
            session.add(hold)
            session.commit()
            logger.info(f"Hold creado: ID {hold.id_hold_mesa} para mesa {mesa_id}, expira en {ttl_minutes} min")
            return schema.dump(hold)
    
    
    @staticmethod
    def obtener_hold_por_id(hold_id: int) -> dict:
        """
        Obtener hold por ID.
        
        Args:
            hold_id: ID del hold
            
        Returns:
            Dict del hold o None
        """
        schema = HoldMesaResponseSchema()
        with get_db_session() as session:
            hold = session.query(HoldMesa).filter(
                HoldMesa.id_hold_mesa == hold_id
            ).first()
            return schema.dump(hold) if hold else None
    
    
    @staticmethod
    def verificar_mesa_disponible(mesa_id: int, inicio: datetime, fin_estimado: datetime) -> bool:
        """
        Verificar si una mesa está disponible en el rango de fechas.
        Verifica:
        - No hay holds activos que se traslapen
        - No hay reservas programadas/en_curso que se traslapen
        
        Args:
            mesa_id: ID de la mesa
            inicio: Fecha/hora inicio deseada
            fin_estimado: Fecha/hora fin estimado
            
        Returns:
            True si está disponible, False si hay conflicto
        """
        with get_db_session() as session:
            ahora = datetime.now()
            
            # Verificar holds activos (estatus=1) que no hayan expirado
            holds_activos = session.query(HoldMesa).filter(
                and_(
                    HoldMesa.mesa_id == mesa_id,
                    HoldMesa.estatus == 1,  # Activo
                    HoldMesa.expires_at > ahora,  # No expirado
                    or_(
                        # Traslape: nuevo inicio está dentro de hold existente
                        and_(HoldMesa.inicio <= inicio, HoldMesa.fin_estimado > inicio),
                        # Traslape: nuevo fin está dentro de hold existente
                        and_(HoldMesa.inicio < fin_estimado, HoldMesa.fin_estimado >= fin_estimado),
                        # Traslape: nuevo rango contiene completamente el hold existente
                        and_(HoldMesa.inicio >= inicio, HoldMesa.fin_estimado <= fin_estimado)
                    )
                )
            ).first()
            
            if holds_activos:
                logger.warning(f"Mesa {mesa_id} tiene hold activo en rango {inicio} - {fin_estimado}")
                return False
            
            # IMPORTANTE: También verificar reservas confirmadas
            # Importamos aquí para evitar circular import
            from src.models.operaciones.reserva_model import Reserva
            
            reservas_activas = session.query(Reserva).filter(
                # Filtrar por mesa_id una vez que agregues relación
                # Por ahora filtramos por estatus
                and_(
                    Reserva.estatus.in_([1, 2]),  # Programada o EnCurso
                    or_(
                        and_(Reserva.inicio <= inicio, Reserva.fin_estimado > inicio),
                        and_(Reserva.inicio < fin_estimado, Reserva.fin_estimado >= fin_estimado),
                        and_(Reserva.inicio >= inicio, Reserva.fin_estimado <= fin_estimado)
                    )
                )
            ).first()
            
            if reservas_activas:
                logger.warning(f"Mesa {mesa_id} tiene reserva activa en rango {inicio} - {fin_estimado}")
                return False
            
            return True
    
    
    @staticmethod
    def cancelar_hold(hold_id: int) -> dict:
        """
        Cancelar hold (cambiar estatus a 4).
        
        Args:
            hold_id: ID del hold
            
        Returns:
            Dict actualizado o None
        """
        schema = HoldMesaResponseSchema()
        with get_db_session() as session:
            hold = session.query(HoldMesa).filter(
                HoldMesa.id_hold_mesa == hold_id
            ).first()
            
            if not hold:
                return None
            
            hold.estatus = 4  # Cancelado
            hold.updated_at = datetime.now()
            session.commit()
            logger.info(f"Hold {hold_id} cancelado")
            return schema.dump(hold)
    
    
    @staticmethod
    def confirmar_hold(hold_id: int) -> dict:
        """
        Confirmar hold (cambiar estatus a 2 - Confirmado).
        Se usa cuando se crea reserva desde hold.
        
        Args:
            hold_id: ID del hold
            
        Returns:
            Dict actualizado o None
        """
        schema = HoldMesaResponseSchema()
        with get_db_session() as session:
            hold = session.query(HoldMesa).filter(
                HoldMesa.id_hold_mesa == hold_id
            ).first()
            
            if not hold:
                return None
            
            hold.estatus = 2  # Confirmado
            hold.updated_at = datetime.now()
            session.commit()
            logger.info(f"Hold {hold_id} confirmado (convertido a reserva)")
            return schema.dump(hold)
    
    
    @staticmethod
    def expirar_holds_vencidos() -> int:
        """
        Job de limpieza: Marcar como expirados todos los holds activos
        cuyo expires_at haya pasado.
        
        Returns:
            Cantidad de holds expirados
        """
        with get_db_session() as session:
            ahora = datetime.now()
            
            result = session.query(HoldMesa).filter(
                and_(
                    HoldMesa.estatus == 1,  # Solo activos
                    HoldMesa.expires_at <= ahora  # Ya expiró
                )
            ).update(
                {
                    'estatus': 3,  # Expirado
                    'updated_at': ahora
                },
                synchronize_session=False
            )
            
            session.commit()
            
            if result > 0:
                logger.info(f"Job: {result} holds expirados automáticamente")
            
            return result
    
    
    @staticmethod
    def listar_holds_activos(mesa_id: int = None) -> list:
        """
        Listar holds activos (estatus=1) que no hayan expirado.
        
        Args:
            mesa_id: Filtrar por mesa (opcional)
            
        Returns:
            Lista de dicts de holds activos
        """
        schema = HoldMesaResponseSchema()
        with get_db_session() as session:
            ahora = datetime.now()
            query = session.query(HoldMesa).filter(
                and_(
                    HoldMesa.estatus == 1,
                    HoldMesa.expires_at > ahora
                )
            )
            
            if mesa_id:
                query = query.filter(HoldMesa.mesa_id == mesa_id)
            
            holds = query.order_by(HoldMesa.created_at.desc()).all()
            return [schema.dump(h) for h in holds]
    
    
    @staticmethod
    def hold_existe(hold_id: int) -> bool:
        """
        Verificar si un hold existe.
        
        Args:
            hold_id: ID del hold
            
        Returns:
            True si existe
        """
        with get_db_session() as session:
            existe = session.query(HoldMesa).filter(
                HoldMesa.id_hold_mesa == hold_id
            ).first()
            return existe is not None
