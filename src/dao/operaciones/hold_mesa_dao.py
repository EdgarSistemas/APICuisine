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
import pytz

logger = logging.getLogger(__name__)

# Zona horaria de México
TZ_MEXICO = pytz.timezone('America/Mexico_City')


class HoldMesaDAO:
    """Data Access Object para HoldMesa"""
    
    @staticmethod
    def crear_hold(
        mesa_id: int,
        actor_tipo: int,
        actor_usuario_id: int,
        inicio: datetime,
        fin_estimado: datetime,
        ttl_minutes: int = 3,
        notas: str = None,
        horas: int = None
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
            # Obtener hora actual en zona de México (SIN timezone para SQL Server)
            ahora_mexico = datetime.now(TZ_MEXICO).replace(tzinfo=None)
            
            # Calcular expires_at en zona de México
            expires_at = ahora_mexico + timedelta(minutes=ttl_minutes)
            
            hold = HoldMesa(
                mesa_id=mesa_id,
                actor_tipo=actor_tipo,
                actor_usuario_id=actor_usuario_id,
                inicio=inicio,
                fin_estimado=fin_estimado,
                expires_at=expires_at,
                estatus=1,  # Activo
                notas=notas,
                horas=horas
            )
            session.add(hold)
            session.commit()
            
            print(f"\n[CREAR HOLD] ✓ ID={hold.id_hold_mesa}, Mesa={mesa_id}, Estatus={hold.estatus}, Expira={expires_at}")
            logger.info(
                f"[HOLD] Creado: ID={hold.id_hold_mesa}, Mesa={mesa_id}, "
                f"Expira en {ttl_minutes}min a {expires_at} (zona México)"
            )
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
        
        ⚡ IMPORTANTE: Suma 10 minutos de limpieza automáticamente a fin_estimado
        para evitar que se sobrepongan reservas.
        
        Verifica:
        - No hay holds activos que se traslapen
        - No hay reservas programadas/en_curso que se traslapen
        - Incluye 10 minutos de limpieza después de cada reserva/hold
        
        NOTA: Todas las fechas están en zona de México.
        
        Args:
            mesa_id: ID de la mesa
            inicio: Fecha/hora inicio deseada
            fin_estimado: Fecha/hora fin estimado (se agregan 10 min de limpieza)
            
        Returns:
            True si está disponible, False si hay conflicto
        """
        from datetime import timedelta
        
        with get_db_session() as session:
            # Obtener hora actual en zona de México
            ahora_mexico = datetime.now(TZ_MEXICO).replace(tzinfo=None)
            
            # ⚡ AGREGAR 10 MINUTOS DE LIMPIEZA AL RANGO SOLICITADO
            fin_con_limpieza = fin_estimado + timedelta(minutes=10)
            
            print(f"\n[VERIFICAR_DISPONIBLE] Comprobando disponibilidad")
            print(f"  Mesa {mesa_id}")
            print(f"  Rango original: {inicio} - {fin_estimado}")
            print(f"  Rango con limpieza: {inicio} - {fin_con_limpieza}")
            print(f"  Ahora (México): {ahora_mexico}")
            
            # Verificar holds activos (estatus=1) que no hayan expirado
            # ⚡ IMPORTANTE: VALIDA SOLO QUE NO HAYA OTRO HOLD ACTIVO
            # NO importa si tiene reserva o no - un hold activo bloquea
            # TAMBIÉN CONSIDERAR 10 MINUTOS DE LIMPIEZA EN LOS HOLDS EXISTENTES
            
            holds_activos = session.query(HoldMesa).filter(
                and_(
                    HoldMesa.mesa_id == mesa_id,
                    HoldMesa.estatus == 1,  # Activo (sin importar si tiene reserva)
                    HoldMesa.expires_at > ahora_mexico,  # No expirado (zona México)
                )
            ).all()
            
            # Procesar en Python para evitar problemas con SQL Server
            for hold in holds_activos:
                hold_fin_con_limpieza = hold.fin_estimado + timedelta(minutes=10)
                
                # Verificar si hay traslape
                if (
                    # Traslape: nuevo inicio está dentro de hold existente (+ 10 min limpieza)
                    (hold.inicio <= inicio < hold_fin_con_limpieza) or
                    # Traslape: nuevo fin está dentro de hold existente (+ 10 min limpieza)
                    (hold.inicio < fin_con_limpieza <= hold_fin_con_limpieza) or
                    # Traslape: nuevo rango contiene completamente el hold existente (+ 10 min limpieza)
                    (inicio <= hold.inicio and hold_fin_con_limpieza <= fin_con_limpieza) or
                    # Traslape: hold contiene completamente el nuevo rango
                    (hold.inicio <= inicio and fin_con_limpieza <= hold_fin_con_limpieza)
                ):
                    print(f"  ⚠️  Conflicto: Hold activo encontrado (ID={hold.id_hold_mesa})")
                    print(f"     Hold ocupa: {hold.inicio} - {hold_fin_con_limpieza} (con limpieza)")
                    logger.warning(f"Mesa {mesa_id} tiene hold activo en rango {inicio} - {fin_con_limpieza}")
                    return False
            
            print(f"  ✓ Mesa disponible")
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
        print(f"\n[⚠️ CANCELAR_HOLD] ID={hold_id}")
        schema = HoldMesaResponseSchema()
        with get_db_session() as session:
            hold = session.query(HoldMesa).filter(
                HoldMesa.id_hold_mesa == hold_id
            ).first()
            
            if not hold:
                return None
            
            print(f"[⚠️ CANCELAR_HOLD] Estatus anterior: {hold.estatus}")
            hold.estatus = 4  # Cancelado
            # Usar zona de México para updated_at
            hold.updated_at = datetime.now(TZ_MEXICO).replace(tzinfo=None)
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
        print(f"\n[⚠️ CONFIRMAR_HOLD] ID={hold_id}")
        schema = HoldMesaResponseSchema()
        with get_db_session() as session:
            hold = session.query(HoldMesa).filter(
                HoldMesa.id_hold_mesa == hold_id
            ).first()
            
            if not hold:
                return None
            
            print(f"[⚠️ CONFIRMAR_HOLD] Estatus anterior: {hold.estatus}")
            hold.estatus = 2  # Confirmado
            # Usar zona de México para updated_at
            hold.updated_at = datetime.now(TZ_MEXICO).replace(tzinfo=None)
            session.commit()
            logger.info(f"Hold {hold_id} confirmado (convertido a reserva)")
            return schema.dump(hold)
    
    
    @staticmethod
    def listar_holds_activos(mesa_id: int = None) -> list:
        """
        Listar holds activos (estatus=1) que no hayan expirado.
        
        NOTA: Todas las fechas están en zona de México.
        
        Args:
            mesa_id: Filtrar por mesa (opcional)
            
        Returns:
            Lista de dicts de holds activos
        """
        schema = HoldMesaResponseSchema()
        with get_db_session() as session:
            # Obtener hora actual en zona de México
            ahora_mexico = datetime.now(TZ_MEXICO).replace(tzinfo=None)
            
            query = session.query(HoldMesa).filter(
                and_(
                    HoldMesa.estatus == 1,
                    HoldMesa.expires_at > ahora_mexico  # No expirado (zona México)
                )
            )
            
            if mesa_id:
                query = query.filter(HoldMesa.mesa_id == mesa_id)
            
            holds = query.order_by(HoldMesa.created_at.desc()).all()
            print(f"\n[LISTAR HOLDS] Encontrados {len(holds)} holds activos en BD (ahora={ahora_mexico})")
            for h in holds:
                print(f"  - Hold ID={h.id_hold_mesa}, Estatus={h.estatus}, Expira={h.expires_at}")
            return [schema.dump(h) for h in holds]
    
    
    @staticmethod
    def cambiar_estatus(hold_id: int, estatus: int) -> bool:
        """
        Cambiar estatus de un hold.
        
        Args:
            hold_id: ID del hold
            estatus: Nuevo estatus (1=Activo, 2=Confirmado, 3=Expirado, 4=Cancelado)
            
        Returns:
            True si se actualizó, False si no existe
        """
        with get_db_session() as session:
            ahora_mexico = datetime.now(TZ_MEXICO).replace(tzinfo=None)
            
            # Obtener el hold primero para actualizarlo correctamente
            hold = session.query(HoldMesa).filter(
                HoldMesa.id_hold_mesa == hold_id
            ).first()
            
            if not hold:
                logger.warning(f"Hold {hold_id} no existe para cambiar estatus")
                return False
            
            # Cambiar estatus y updated_at
            estatus_anterior = hold.estatus
            hold.estatus = estatus
            hold.updated_at = ahora_mexico
            session.commit()
            
            logger.info(f"Hold {hold_id} estatus cambiado: {estatus_anterior} → {estatus}")
            return True
    
    
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
    
    
    @staticmethod
    def limpiar_holds_expirados_manual() -> dict:
        """
        Ejecuta expiración de holds INCOMPLETOS de forma síncrona.
        Útil para debugging, testing y limpieza manual.
        
        Solo procesa holds con estatus=1 (incompletos).
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            with get_db_session() as session:
                ahora_mexico = datetime.now(TZ_MEXICO).replace(tzinfo=None)
                
                # SOLO holds INCOMPLETOS (estatus=1)
                holds_incompletos = session.query(HoldMesa).filter(
                    HoldMesa.estatus == 1
                ).all()
                
                ids_a_expirar = []
                for hold in holds_incompletos:
                    if hold.expires_at <= ahora_mexico:
                        ids_a_expirar.append(hold.id_hold_mesa)
                
                if ids_a_expirar:
                    result = session.query(HoldMesa).filter(
                        HoldMesa.id_hold_mesa.in_(ids_a_expirar)
                    ).update(
                        {
                            'estatus': 3,
                            'updated_at': ahora_mexico
                        },
                        synchronize_session=False
                    )
                    session.commit()
                    
                    return {
                        "success": True,
                        "message": f"Se expiraron {result} holds incompletos",
                        "cantidad_expirados": result
                    }
                else:
                    return {
                        "success": True,
                        "message": "No hay holds incompletos para expirar",
                        "cantidad_expirados": 0
                    }
                    
        except Exception as e:
            logger.error(f"Error al limpiar holds expirados: {str(e)}")
            return {
                "success": False,
                "message": f"Error al expirar holds: {str(e)}",
                "cantidad_expirados": 0
            }
