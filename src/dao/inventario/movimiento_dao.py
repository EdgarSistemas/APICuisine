"""
MovimientoDAO - Data Access Object para auditoría de movimientos
"""

from decimal import Decimal
from src.models import Movimiento
from src.core.db.session_manager import get_db_session
import logging

logger = logging.getLogger(__name__)


class MovimientoDAO:
    """Data Access Object para Movimiento (auditoría)"""
    
    @staticmethod
    def crear_movimiento(sucursal_id: int, insumo_id: int, lote_id: int, 
                        tipo_mov: int, motivo: int, cantidad: float,
                        pedido_id: int = None, det_recepcion_id: int = None,
                        compra_id: int = None, merma_id: int = None,
                        usuario_id: int = None, session=None) -> dict:
        """
        Crear registro de movimiento de inventario (auditoría).
        
        Args:
            sucursal_id: ID de la sucursal
            insumo_id: ID del insumo
            lote_id: ID del lote (puede ser None para salidas)
            tipo_mov: 1=Entrada, 2=Salida
            motivo: 1=Recepción, 2=Pedido, 3=Merma
            cantidad: Cantidad en unidad base (siempre positiva)
            pedido_id: ID del pedido (si motivo=2)
            det_recepcion_id: ID del detalle de recepción (si motivo=1)
            compra_id: ID de la compra (si motivo=1)
            merma_id: ID de la merma (si motivo=3)
            usuario_id: ID del usuario que registra
            session: Sesión de SQLAlchemy (opcional, si None crea una nueva)
            
        Returns:
            Dict con el movimiento creado
        """
        def _crear(sess):
            movimiento = Movimiento(
                sucursal_id=sucursal_id,
                insumo_id=insumo_id,
                lote_id=lote_id,
                tipo_mov=tipo_mov,
                motivo=motivo,
                cantidad=Decimal(str(cantidad)),
                pedido_id=pedido_id,
                det_recepcion_id=det_recepcion_id,
                compra_id=compra_id,
                merma_id=merma_id,
                usuario_id=usuario_id
            )
            sess.add(movimiento)
            sess.flush()  # Flush para obtener el ID sin commit
            
            logger.info(f"Movimiento creado: tipo={tipo_mov}, motivo={motivo}, cantidad={cantidad}, sucursal={sucursal_id}, insumo={insumo_id}")
            
            return {
                "id_movimiento": movimiento.id_movimiento,
                "sucursal_id": movimiento.sucursal_id,
                "insumo_id": movimiento.insumo_id,
                "lote_id": movimiento.lote_id,
                "tipo_mov": movimiento.tipo_mov,
                "motivo": movimiento.motivo,
                "cantidad": float(movimiento.cantidad),
                "created_at": movimiento.created_at.strftime('%Y-%m-%d %H:%M:%S') if movimiento.created_at else None
            }
        
        # Si se pasa una sesión, usarla. Si no, crear una nueva
        if session is not None:
            return _crear(session)
        else:
            with get_db_session() as sess:
                resultado = _crear(sess)
                sess.commit()
                return resultado
    
    
    @staticmethod
    def listar_movimientos_por_sucursal(sucursal_id: int, limit: int = 100) -> list:
        """
        Listar movimientos de una sucursal (más recientes primero).
        
        Args:
            sucursal_id: ID de la sucursal
            limit: Límite de registros
            
        Returns:
            Lista de movimientos
        """
        with get_db_session() as session:
            movimientos = session.query(Movimiento).filter(
                Movimiento.sucursal_id == sucursal_id
            ).order_by(Movimiento.created_at.desc()).limit(limit).all()
            
            resultado = []
            for mov in movimientos:
                resultado.append({
                    "id_movimiento": mov.id_movimiento,
                    "sucursal_id": mov.sucursal_id,
                    "insumo_id": mov.insumo_id,
                    "lote_id": mov.lote_id,
                    "tipo_mov": mov.tipo_mov,
                    "motivo": mov.motivo,
                    "cantidad": float(mov.cantidad),
                    "created_at": mov.created_at.strftime('%Y-%m-%d %H:%M:%S') if mov.created_at else None
                })
            
            return resultado
    
    
    @staticmethod
    def listar_movimientos_por_insumo(sucursal_id: int, insumo_id: int, limit: int = 50) -> list:
        """
        Listar movimientos de un insumo específico en una sucursal.
        
        Args:
            sucursal_id: ID de la sucursal
            insumo_id: ID del insumo
            limit: Límite de registros
            
        Returns:
            Lista de movimientos
        """
        with get_db_session() as session:
            movimientos = session.query(Movimiento).filter(
                Movimiento.sucursal_id == sucursal_id,
                Movimiento.insumo_id == insumo_id
            ).order_by(Movimiento.created_at.desc()).limit(limit).all()
            
            resultado = []
            for mov in movimientos:
                resultado.append({
                    "id_movimiento": mov.id_movimiento,
                    "tipo_mov": mov.tipo_mov,
                    "motivo": mov.motivo,
                    "cantidad": float(mov.cantidad),
                    "lote_id": mov.lote_id,
                    "created_at": mov.created_at.strftime('%Y-%m-%d %H:%M:%S') if mov.created_at else None
                })
            
            return resultado
