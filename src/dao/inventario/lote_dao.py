"""
LoteDAO - Data Access Object para inventario.Lote
"""

from datetime import datetime, timedelta
from src.models import Lote, RecepcionDetalle
from src.models.inventario.insumo_model import Insumo
from src.models.inventario.unidad_medida_model import UnidadMedida
from src.models.inventario.existencia_model import Existencia
from src.models.inventario.recepcion_model import Recepcion
from src.models.inventario.compra_model import Compra
from src.core.db.session_manager import get_db_session
from src.schemas.lote_schema import LoteResponseSchema
import logging
import pytz

logger = logging.getLogger(__name__)

# Zona horaria de México
TZ_MEXICO = pytz.timezone('America/Mexico_City')


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
    
    
    @staticmethod
    def obtener_lotes_proximos_a_vencer(sucursal_id: int, dias_proximidad: int = 30) -> list:
        """
        Obtener lotes más próximos a vencer por sucursal.
        
        Filtra lotes que vencen dentro de N días (default 30).
        Puede haber múltiples lotes del mismo insumo (diferente lote_proveedor, etc).
        
        Args:
            sucursal_id: ID de la sucursal
            dias_proximidad: Cantidad de días para considerar como "próximo a vencer" (default: 30)
            
        Returns:
            Lista de dicts con información de lotes próximos a vencer, 
            ordenados por fecha de caducidad (más próximos primero)
        """
        with get_db_session() as session:
            # Calcular fecha límite en timezone de México
            ahora_mexico = datetime.now(TZ_MEXICO).replace(tzinfo=None)
            fecha_limite = ahora_mexico + timedelta(days=dias_proximidad)
            
            # Query: Lote -> RecepcionDetalle -> Recepcion -> Compra
            # Luego JOIN Insumo + UnidadMedida para información adicional
            lotes = session.query(
                Lote.id_lote,
                Lote.lote,
                Lote.lote_proveedor,
                Lote.cantidad_inicial,
                Lote.cantidad_disponible,
                Lote.costo_unitario,
                Lote.fecha_caducidad,
                Lote.estado,
                Lote.created_at,
                Insumo.id_insumo,
                Insumo.nombre.label('insumo_nombre'),
                UnidadMedida.id_unidad,
                UnidadMedida.nombre.label('unidad_nombre'),
                UnidadMedida.clave.label('unidad_clave'),
                Compra.sucursal_id
            ).join(
                RecepcionDetalle, Lote.det_recepcion_id == RecepcionDetalle.id_recepcion_det
            ).join(
                Recepcion, RecepcionDetalle.recepcion_id == Recepcion.id_recepcion
            ).join(
                Compra, Recepcion.compra_id == Compra.id_compra
            ).join(
                Insumo, RecepcionDetalle.insumo_id == Insumo.id_insumo
            ).join(
                UnidadMedida, Insumo.unidad_id == UnidadMedida.id_unidad
            ).filter(
                Compra.sucursal_id == sucursal_id,
                Lote.estado == 1,  # Solo disponibles
                Lote.fecha_caducidad != None,  # Solo lotes con fecha de caducidad
                Lote.fecha_caducidad >= ahora_mexico,  # No vencidos
                Lote.fecha_caducidad <= fecha_limite  # Dentro del rango de días
            ).order_by(
                Lote.fecha_caducidad.asc()  # Los más próximos primero
            ).all()
            
            # Convertir a dicts
            resultado = []
            for lote in lotes:
                dias_para_vencer = (lote.fecha_caducidad - ahora_mexico).days
                
                resultado.append({
                    "id_lote": lote.id_lote,
                    "lote": lote.lote,
                    "lote_proveedor": lote.lote_proveedor,
                    "cantidad_inicial": float(lote.cantidad_inicial),
                    "cantidad_disponible": float(lote.cantidad_disponible),
                    "cantidad_utilizada": float(lote.cantidad_inicial - lote.cantidad_disponible),
                    "costo_unitario": float(lote.costo_unitario),
                    "costo_total": float(lote.cantidad_disponible * lote.costo_unitario),
                    "fecha_caducidad": lote.fecha_caducidad.strftime('%Y-%m-%d %H:%M:%S') if lote.fecha_caducidad else None,
                    "dias_para_vencer": dias_para_vencer,
                    "porcentaje_disponible": round((float(lote.cantidad_disponible) / float(lote.cantidad_inicial) * 100), 2) if lote.cantidad_inicial > 0 else 0,
                    "insumo_id": lote.id_insumo,
                    "insumo_nombre": lote.insumo_nombre,
                    "unidad_id": lote.id_unidad,
                    "unidad_nombre": lote.unidad_nombre,
                    "unidad_clave": lote.unidad_clave,
                    "sucursal_id": lote.sucursal_id,
                    "created_at": lote.created_at.strftime('%Y-%m-%d %H:%M:%S') if lote.created_at else None,
                    "urgencia": "Crítica" if dias_para_vencer <= 7 else ("Alta" if dias_para_vencer <= 14 else "Media")
                })
            
            logger.info(f"Lotes próximos a vencer en sucursal {sucursal_id}: {len(resultado)}")
            return resultado
    
    
    @staticmethod
    def obtener_lotes_vencidos(sucursal_id: int) -> list:
        """
        Obtener lotes vencidos por sucursal.
        
        Lista todos los lotes que ya pasaron su fecha de caducidad.
        Útil para auditoría e identificación de pérdidas.
        Puede haber múltiples lotes del mismo insumo.
        
        Args:
            sucursal_id: ID de la sucursal
            
        Returns:
            Lista de dicts con información de lotes vencidos, 
            ordenados por fecha de caducidad (más antiguos primero)
        """
        with get_db_session() as session:
            ahora_mexico = datetime.now(TZ_MEXICO).replace(tzinfo=None)
            
            # Query: Lote -> RecepcionDetalle -> Recepcion -> Compra
            lotes = session.query(
                Lote.id_lote,
                Lote.lote,
                Lote.lote_proveedor,
                Lote.cantidad_disponible,
                Lote.costo_unitario,
                Lote.fecha_caducidad,
                Insumo.id_insumo,
                Insumo.nombre.label('insumo_nombre'),
                UnidadMedida.clave.label('unidad_clave'),
                UnidadMedida.nombre.label('unidad_nombre'),
                Compra.sucursal_id
            ).join(
                RecepcionDetalle, Lote.det_recepcion_id == RecepcionDetalle.id_recepcion_det
            ).join(
                Recepcion, RecepcionDetalle.recepcion_id == Recepcion.id_recepcion
            ).join(
                Compra, Recepcion.compra_id == Compra.id_compra
            ).join(
                Insumo, RecepcionDetalle.insumo_id == Insumo.id_insumo
            ).join(
                UnidadMedida, Insumo.unidad_id == UnidadMedida.id_unidad
            ).filter(
                Compra.sucursal_id == sucursal_id,
                Lote.estado == 1,
                Lote.fecha_caducidad != None,
                Lote.fecha_caducidad < ahora_mexico  # Vencidos
            ).order_by(
                Lote.fecha_caducidad.asc()
            ).all()
            
            resultado = []
            for lote in lotes:
                dias_vencido = (ahora_mexico - lote.fecha_caducidad).days
                
                resultado.append({
                    "id_lote": lote.id_lote,
                    "lote": lote.lote,
                    "lote_proveedor": lote.lote_proveedor,
                    "cantidad_disponible": float(lote.cantidad_disponible),
                    "costo_unitario": float(lote.costo_unitario),
                    "costo_total_perdida": float(lote.cantidad_disponible * lote.costo_unitario),
                    "fecha_caducidad": lote.fecha_caducidad.strftime('%Y-%m-%d %H:%M:%S'),
                    "dias_vencido": dias_vencido,
                    "insumo_id": lote.id_insumo,
                    "insumo_nombre": lote.insumo_nombre,
                    "unidad_clave": lote.unidad_clave,
                    "unidad_nombre": lote.unidad_nombre,
                    "sucursal_id": lote.sucursal_id
                })
            
            logger.info(f"Lotes vencidos en sucursal {sucursal_id}: {len(resultado)}")
            return resultado
