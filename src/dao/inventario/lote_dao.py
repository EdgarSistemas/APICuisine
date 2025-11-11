"""
LoteDAO - Data Access Object para inventario.Lote
"""

from src.models import Lote, RecepcionDetalle
from src.core.db.session_manager import get_db_session
from src.schemas.lote_schema import LoteResponseSchema
import logging

logger = logging.getLogger(__name__)


class LoteDAO:
    """Data Access Object para Lote"""
    
    @staticmethod
    def crear_lote(det_recepcion_id: int, lote: str = None, lote_proveedor: str = None,
                   cantidad_inicial: float = 0, costo_unitario: float = 0,
                   fecha_caducidad = None) -> dict:
        """
        Crear nuevo lote (generado automático desde RecepcionDetalle).
        
        Args:
            det_recepcion_id: ID del detalle de recepción
            lote: Número de lote interno
            lote_proveedor: Número de lote del proveedor
            cantidad_inicial: Cantidad inicial del lote
            costo_unitario: Costo unitario
            fecha_caducidad: Fecha de caducidad
            
        Returns:
            Dict serializado del lote
        """
        schema = LoteResponseSchema()
        with get_db_session() as session:
            lote_obj = Lote(
                det_recepcion_id=det_recepcion_id,
                lote=lote,
                lote_proveedor=lote_proveedor,
                cantidad_inicial=cantidad_inicial,
                cantidad_disponible=cantidad_inicial,  # Inicialmente todo disponible
                costo_unitario=costo_unitario,
                fecha_caducidad=fecha_caducidad,
                estado=1  # 1=Disponible
            )
            session.add(lote_obj)
            session.commit()
            logger.info(f"Lote creado: {lote} (ID: {lote_obj.id_lote})")
            return schema.dump(lote_obj)
    
    
    @staticmethod
    def obtener_lote_por_id(lote_id: int) -> dict:
        """
        Obtener lote por ID.
        
        Args:
            lote_id: ID del lote
            
        Returns:
            Dict del lote o None
        """
        schema = LoteResponseSchema()
        with get_db_session() as session:
            lote = session.query(Lote).filter(
                Lote.id_lote == lote_id
            ).first()
            return schema.dump(lote) if lote else None
    
    
    @staticmethod
    def obtener_lotes_por_insumo(insumo_id: int, solo_disponibles: bool = True) -> list:
        """
        Obtener lotes por insumo (desde RecepcionDetalle).
        
        Args:
            insumo_id: ID del insumo
            solo_disponibles: Si True, solo lotes con estado=1
            
        Returns:
            Lista de lotes
        """
        schema = LoteResponseSchema(many=True)
        with get_db_session() as session:
            query = session.query(Lote).join(
                RecepcionDetalle, Lote.det_recepcion_id == RecepcionDetalle.id_recepcion_det
            ).filter(RecepcionDetalle.insumo_id == insumo_id)
            
            if solo_disponibles:
                query = query.filter(Lote.estado == 1)
            
            lotes = query.order_by(Lote.fecha_caducidad).all()
            return schema.dump(lotes)
    
    
    @staticmethod
    def actualizar_cantidad_disponible(lote_id: int, nueva_cantidad: float) -> dict:
        """
        Actualizar cantidad disponible de un lote.
        Si llega a 0, cambiar estado a 2 (Agotado).
        
        Args:
            lote_id: ID del lote
            nueva_cantidad: Nueva cantidad disponible
            
        Returns:
            Dict del lote actualizado
        """
        schema = LoteResponseSchema()
        with get_db_session() as session:
            lote = session.query(Lote).filter(
                Lote.id_lote == lote_id
            ).first()
            
            if not lote:
                return None
            
            lote.cantidad_disponible = nueva_cantidad
            
            # Si cantidad llega a 0 o negativo, marcar como agotado
            if nueva_cantidad <= 0:
                lote.estado = 2  # Agotado
            
            session.commit()
            logger.info(f"Lote {lote_id} actualizado: cantidad_disponible={nueva_cantidad}")
            return schema.dump(lote)
    
    
    @staticmethod
    def cambiar_estado_lote(lote_id: int, nuevo_estado: int) -> dict:
        """
        Cambiar estado del lote.
        
        Args:
            lote_id: ID del lote
            nuevo_estado: 1=Disponible, 2=Agotado
            
        Returns:
            Dict del lote actualizado
        """
        schema = LoteResponseSchema()
        with get_db_session() as session:
            lote = session.query(Lote).filter(
                Lote.id_lote == lote_id
            ).first()
            
            if not lote:
                return None
            
            lote.estado = nuevo_estado
            session.commit()
            logger.info(f"Lote {lote_id} estado cambiado a {nuevo_estado}")
            return schema.dump(lote)
    
    
    @staticmethod
    def lote_existe(lote_id: int) -> bool:
        """
        Verificar si un lote existe.
        
        Args:
            lote_id: ID del lote
            
        Returns:
            True si existe
        """
        with get_db_session() as session:
            existe = session.query(Lote).filter(
                Lote.id_lote == lote_id
            ).first()
            return existe is not None
