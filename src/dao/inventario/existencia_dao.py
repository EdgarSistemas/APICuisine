"""
ExistenciaDAO - Data Access Object para existencias de inventario
"""

from decimal import Decimal
from src.models import Existencia
from src.core.db.session_manager import get_db_session
import logging

logger = logging.getLogger(__name__)


class ExistenciaDAO:
    """Data Access Object para Existencia (snapshot en tiempo real)"""
    
    @staticmethod
    def obtener_existencia(sucursal_id: int, insumo_id: int) -> dict:
        """
        Obtener existencia de un insumo en una sucursal.
        
        Args:
            sucursal_id: ID de la sucursal
            insumo_id: ID del insumo
            
        Returns:
            Dict con existencia o None si no existe
        """
        with get_db_session() as session:
            existencia = session.query(Existencia).filter(
                Existencia.sucursal_id == sucursal_id,
                Existencia.insumo_id == insumo_id
            ).first()
            
            if not existencia:
                return None
            
            return {
                "id_existencia": existencia.id_existencia,
                "sucursal_id": existencia.sucursal_id,
                "insumo_id": existencia.insumo_id,
                "cantidad": float(existencia.cantidad),
                "costo_promedio": float(existencia.costo_promedio),
                "updated_at": existencia.updated_at.strftime('%Y-%m-%d %H:%M:%S') if existencia.updated_at else None
            }
    
    
    @staticmethod
    def actualizar_existencia_entrada(sucursal_id: int, insumo_id: int, 
                                      cantidad_entrada: float, costo_unitario_entrada: float) -> dict:
        """
        Actualizar existencia con ENTRADA de inventario (recepción).
        Calcula costo promedio ponderado.
        
        Args:
            sucursal_id: ID de la sucursal
            insumo_id: ID del insumo
            cantidad_entrada: Cantidad que entra (en unidad base)
            costo_unitario_entrada: Costo por unidad base del lote que entra
            
        Returns:
            Dict con existencia actualizada
        """
        with get_db_session() as session:
            existencia = session.query(Existencia).filter(
                Existencia.sucursal_id == sucursal_id,
                Existencia.insumo_id == insumo_id
            ).first()
            
            cantidad_entrada_dec = Decimal(str(cantidad_entrada))
            costo_entrada_dec = Decimal(str(costo_unitario_entrada))
            
            if not existencia:
                # NO EXISTE → Crear nueva existencia
                existencia = Existencia(
                    sucursal_id=sucursal_id,
                    insumo_id=insumo_id,
                    cantidad=cantidad_entrada_dec,
                    costo_promedio=costo_entrada_dec
                )
                session.add(existencia)
                session.commit()
                
                logger.info(f"Existencia CREADA: sucursal={sucursal_id}, insumo={insumo_id}, cantidad={cantidad_entrada}, costo={costo_unitario_entrada}")
            else:
                # YA EXISTE → Calcular costo promedio ponderado
                cantidad_anterior = existencia.cantidad
                costo_anterior = existencia.costo_promedio
                
                # Costo total anterior
                costo_total_anterior = cantidad_anterior * costo_anterior
                
                # Costo del lote que entra
                costo_total_entrada = cantidad_entrada_dec * costo_entrada_dec
                
                # Nueva cantidad total
                cantidad_nueva = cantidad_anterior + cantidad_entrada_dec
                
                # Nuevo costo promedio ponderado
                if cantidad_nueva > 0:
                    costo_promedio_nuevo = (costo_total_anterior + costo_total_entrada) / cantidad_nueva
                else:
                    costo_promedio_nuevo = costo_anterior
                
                existencia.cantidad = cantidad_nueva
                existencia.costo_promedio = costo_promedio_nuevo
                session.commit()
                
                logger.info(f"Existencia ACTUALIZADA: sucursal={sucursal_id}, insumo={insumo_id}, "
                           f"cantidad_anterior={float(cantidad_anterior)} → nueva={float(cantidad_nueva)}, "
                           f"costo_anterior={float(costo_anterior):.2f} → nuevo={float(costo_promedio_nuevo):.2f}")
            
            return {
                "id_existencia": existencia.id_existencia,
                "sucursal_id": existencia.sucursal_id,
                "insumo_id": existencia.insumo_id,
                "cantidad": float(existencia.cantidad),
                "costo_promedio": float(existencia.costo_promedio),
                "updated_at": existencia.updated_at.strftime('%Y-%m-%d %H:%M:%S') if existencia.updated_at else None
            }
    
    
    @staticmethod
    def actualizar_existencia_salida(sucursal_id: int, insumo_id: int, cantidad_salida: float, session=None) -> dict:
        """
        Actualizar existencia con SALIDA de inventario (pedido/merma).
        Solo resta cantidad, NO cambia costo promedio.
        
        Args:
            sucursal_id: ID de la sucursal
            insumo_id: ID del insumo
            cantidad_salida: Cantidad que sale (siempre positiva)
            session: Sesión de SQLAlchemy (opcional, si None crea una nueva)
            
        Returns:
            Dict con existencia actualizada o None si no existe
        """
        def _actualizar(sess):
            existencia = sess.query(Existencia).filter(
                Existencia.sucursal_id == sucursal_id,
                Existencia.insumo_id == insumo_id
            ).first()
            
            if not existencia:
                logger.warning(f"No existe existencia para sucursal={sucursal_id}, insumo={insumo_id}")
                return None
            
            cantidad_salida_dec = Decimal(str(cantidad_salida))
            
            # Restar cantidad
            existencia.cantidad = existencia.cantidad - cantidad_salida_dec
            
            # Validar que no quede negativa (advertencia, pero se permite)
            if existencia.cantidad < 0:
                logger.warning(f"⚠️ Existencia NEGATIVA: sucursal={sucursal_id}, insumo={insumo_id}, cantidad={float(existencia.cantidad)}")
            
            sess.flush()
            
            logger.info(f"Existencia SALIDA: sucursal={sucursal_id}, insumo={insumo_id}, cantidad_restada={cantidad_salida}, nueva_cantidad={float(existencia.cantidad)}")
            
            return {
                "id_existencia": existencia.id_existencia,
                "sucursal_id": existencia.sucursal_id,
                "insumo_id": existencia.insumo_id,
                "cantidad": float(existencia.cantidad),
                "costo_promedio": float(existencia.costo_promedio),
                "updated_at": existencia.updated_at.strftime('%Y-%m-%d %H:%M:%S') if existencia.updated_at else None
            }
        
        # Si se pasa una sesión, usarla. Si no, crear una nueva
        if session is not None:
            return _actualizar(session)
        else:
            with get_db_session() as sess:
                resultado = _actualizar(sess)
                sess.commit()
                return resultado
    
    
    @staticmethod
    def actualizar_existencia_cancelacion_recepcion(sucursal_id: int, insumo_id: int, 
                                                    cantidad_cancelada: float, 
                                                    costo_unitario_cancelado: float,
                                                    session=None) -> dict:
        """
        Actualizar existencia al CANCELAR una recepción.
        Resta cantidad Y recalcula costo_promedio ponderado.
        
        Fórmula:
        - valor_antes = (cantidad_actual * costo_promedio_actual) - (cantidad_cancelada * costo_cancelado)
        - cantidad_antes = cantidad_actual - cantidad_cancelada
        - nuevo_costo_promedio = valor_antes / cantidad_antes
        
        Args:
            sucursal_id: ID de la sucursal
            insumo_id: ID del insumo
            cantidad_cancelada: Cantidad que se cancela (siempre positiva)
            costo_unitario_cancelado: Costo unitario de la recepción cancelada
            session: Sesión de SQLAlchemy (opcional, si None crea una nueva)
            
        Returns:
            Dict con existencia actualizada o None si no existe
        """
        def _actualizar(sess):
            existencia = sess.query(Existencia).filter(
                Existencia.sucursal_id == sucursal_id,
                Existencia.insumo_id == insumo_id
            ).first()
            
            if not existencia:
                logger.warning(f"No existe existencia para sucursal={sucursal_id}, insumo={insumo_id}")
                return None
            
            cantidad_cancelada_dec = Decimal(str(cantidad_cancelada))
            costo_unitario_cancelado_dec = Decimal(str(costo_unitario_cancelado))
            
            # Calcular valores actuales
            cantidad_actual = existencia.cantidad
            costo_promedio_actual = existencia.costo_promedio
            valor_total_actual = cantidad_actual * costo_promedio_actual
            
            # Calcular valores de la recepción cancelada
            valor_recepcion_cancelada = cantidad_cancelada_dec * costo_unitario_cancelado_dec
            
            # Calcular valores ANTES de la recepción (revertir)
            valor_antes_recepcion = valor_total_actual - valor_recepcion_cancelada
            cantidad_antes_recepcion = cantidad_actual - cantidad_cancelada_dec
            
            # Validar que no quede cantidad negativa
            if cantidad_antes_recepcion < 0:
                logger.error(f"⚠️ Cancelación causaría cantidad NEGATIVA: sucursal={sucursal_id}, insumo={insumo_id}, cantidad_antes={float(cantidad_antes_recepcion)}")
                return None
            
            # Recalcular costo promedio (solo si queda cantidad > 0)
            if cantidad_antes_recepcion > 0:
                nuevo_costo_promedio = valor_antes_recepcion / cantidad_antes_recepcion
            else:
                # Si queda en 0, mantener el costo promedio anterior
                nuevo_costo_promedio = costo_promedio_actual
            
            # Actualizar existencia
            existencia.cantidad = cantidad_antes_recepcion
            existencia.costo_promedio = nuevo_costo_promedio
            
            sess.flush()
            
            logger.info(f"Existencia CANCELACIÓN RECEPCIÓN: sucursal={sucursal_id}, insumo={insumo_id}")
            logger.info(f"  ├─ Cantidad: {float(cantidad_actual)} → {float(cantidad_antes_recepcion)} (restó {cantidad_cancelada})")
            logger.info(f"  ├─ Costo promedio: {float(costo_promedio_actual):.2f} → {float(nuevo_costo_promedio):.2f}")
            logger.info(f"  └─ Valor total: {float(valor_total_actual):.2f} → {float(valor_antes_recepcion):.2f}")
            
            return {
                "id_existencia": existencia.id_existencia,
                "sucursal_id": existencia.sucursal_id,
                "insumo_id": existencia.insumo_id,
                "cantidad": float(existencia.cantidad),
                "costo_promedio": float(existencia.costo_promedio),
                "updated_at": existencia.updated_at.strftime('%Y-%m-%d %H:%M:%S') if existencia.updated_at else None
            }
        
        # Si se pasa una sesión, usarla. Si no, crear una nueva
        if session is not None:
            return _actualizar(session)
        else:
            with get_db_session() as sess:
                resultado = _actualizar(sess)
                sess.commit()
                return resultado
    
    
    @staticmethod
    def listar_existencias_por_sucursal(sucursal_id: int) -> list:
        """
        Listar todas las existencias de una sucursal.
        
        Args:
            sucursal_id: ID de la sucursal
            
        Returns:
            Lista de existencias
        """
        with get_db_session() as session:
            existencias = session.query(Existencia).filter(
                Existencia.sucursal_id == sucursal_id
            ).all()
            
            resultado = []
            for ex in existencias:
                resultado.append({
                    "id_existencia": ex.id_existencia,
                    "sucursal_id": ex.sucursal_id,
                    "insumo_id": ex.insumo_id,
                    "cantidad": float(ex.cantidad),
                    "costo_promedio": float(ex.costo_promedio),
                    "updated_at": ex.updated_at.strftime('%Y-%m-%d %H:%M:%S') if ex.updated_at else None
                })
            
            return resultado
