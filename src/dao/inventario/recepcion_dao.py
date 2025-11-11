"""
RecepcionDAO y RecepcionDetalleDAO - Data Access Objects
"""

from decimal import Decimal
from datetime import datetime
from src.models import Recepcion, RecepcionDetalle, Lote, Insumo, Compra, Movimiento, Existencia
from src.core.db.session_manager import get_db_session
from src.schemas.recepcion_schema import RecepcionResponseSchema, RecepcionDetalleResponseSchema, RecepcionDetailedSchema
import logging

logger = logging.getLogger(__name__)


class RecepcionDAO:
    """Data Access Object para Recepcion"""
    
    @staticmethod
    def crear_recepcion(compra_id: int, recibido_por: int, notas: str = None) -> dict:
        """
        Crear nueva recepción.
        
        Args:
            compra_id: ID de la compra
            recibido_por: ID del usuario que recibe
            notas: Notas opcionales
            
        Returns:
            Dict serializado de la recepción
        """
        schema = RecepcionResponseSchema()
        with get_db_session() as session:
            recepcion = Recepcion(
                compra_id=compra_id,
                recibido_por=recibido_por,
                notas=notas,
                estatus=1  # 1=Registrada
            )
            session.add(recepcion)
            session.commit()
            logger.info(f"Recepción creada: (ID: {recepcion.id_recepcion})")
            return schema.dump(recepcion)
    
    
    @staticmethod
    def obtener_recepcion_por_id(recepcion_id: int) -> dict:
        """Obtener recepción por ID"""
        schema = RecepcionResponseSchema()
        with get_db_session() as session:
            recepcion = session.query(Recepcion).filter(
                Recepcion.id_recepcion == recepcion_id
            ).first()
            return schema.dump(recepcion) if recepcion else None
    
    
    @staticmethod
    def obtener_recepcion_detallada(recepcion_id: int) -> dict:
        """Obtener recepción con detalles"""
        with get_db_session() as session:
            recepcion = session.query(Recepcion).filter(
                Recepcion.id_recepcion == recepcion_id
            ).first()
            
            if not recepcion:
                return None
            
            resultado = {
                "id_recepcion": recepcion.id_recepcion,
                "compra_id": recepcion.compra_id,
                "recibido_por": recepcion.recibido_por,
                "fecha_recepcion": recepcion.fecha_recepcion.strftime('%Y-%m-%d %H:%M:%S') if recepcion.fecha_recepcion else None,
                "notas": recepcion.notas,
                "estatus": recepcion.estatus,
                "created_at": recepcion.created_at.strftime('%Y-%m-%d %H:%M:%S') if recepcion.created_at else None,
                "detalles": []
            }
            
            # Obtener detalles
            detalles = session.query(RecepcionDetalle).filter(
                RecepcionDetalle.recepcion_id == recepcion_id
            ).all()
            
            for detalle in detalles:
                detalle_dict = {
                    "id_recepcion_det": detalle.id_recepcion_det,
                    "recepcion_id": detalle.recepcion_id,
                    "insumo_id": detalle.insumo_id,
                    "cant_presentacion": float(detalle.cant_presentacion),
                    "unidades_por_present": float(detalle.unidades_por_present),
                    "cantidad_base": float(detalle.cantidad_base),
                    "costo_unitario": float(detalle.costo_unitario),
                    "notas": detalle.notas,
                    "created_at": detalle.created_at.strftime('%Y-%m-%d %H:%M:%S') if detalle.created_at else None
                }
                resultado["detalles"].append(detalle_dict)
            
            return resultado
    
    
    @staticmethod
    def listar_recepciones(sucursal_id: int = None) -> list:
        """Listar recepciones"""
        schema = RecepcionResponseSchema(many=True)
        with get_db_session() as session:
            query = session.query(Recepcion)
            recepciones = query.all()
            return schema.dump(recepciones)
    
    
    @staticmethod
    def actualizar_recepcion(recepcion_id: int, notas: str = None) -> dict:
        """Actualizar recepción"""
        schema = RecepcionResponseSchema()
        with get_db_session() as session:
            recepcion = session.query(Recepcion).filter(
                Recepcion.id_recepcion == recepcion_id
            ).first()
            
            if not recepcion:
                return None
            
            if notas is not None:
                recepcion.notas = notas
            
            session.commit()
            return schema.dump(recepcion)
    
    
    @staticmethod
    def recepcion_existe(recepcion_id: int) -> bool:
        """Verificar si recepción existe"""
        with get_db_session() as session:
            existe = session.query(Recepcion).filter(
                Recepcion.id_recepcion == recepcion_id
            ).first()
            return existe is not None


class RecepcionDetalleDAO:
    """Data Access Object para RecepcionDetalle"""
    
    @staticmethod
    def crear_detalle(recepcion_id: int, insumo_id: int, cant_presentacion: float,
                     unidades_por_present: float, costo_unitario: float,
                     lote_proveedor: str = None, fecha_caducidad = None, notas: str = None,
                     sucursal_id: int = None, compra_id: int = None, usuario_id: int = None) -> dict:
        """
        Crear detalle de recepción y generar LOTE, MOVIMIENTO y actualizar EXISTENCIA automáticamente.
        El lote_numero se genera automáticamente con formato: LOT-YYYYMMDDHHMMSS
        
        Args:
            recepcion_id: ID de la recepción
            insumo_id: ID del insumo
            cant_presentacion: Cantidad de presentaciones
            unidades_por_present: Unidades por presentación
            costo_unitario: Costo por unidad base
            lote_proveedor: Número de lote del proveedor (opcional, se guarda en Lote)
            fecha_caducidad: Fecha de caducidad (opcional, se guarda en Lote)
            notas: Notas (opcional)
            sucursal_id: ID de la sucursal (para Movimiento y Existencia)
            compra_id: ID de la compra (para Movimiento)
            usuario_id: ID del usuario que registra (para Movimiento)
            
        Returns:
            Dict serializado del detalle
        """
        schema = RecepcionDetalleResponseSchema()
        with get_db_session() as session:
            # Generar lote_numero automáticamente
            lote_numero_generado = f"LOT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Calcular cantidad_base
            cantidad_base = Decimal(str(cant_presentacion)) * Decimal(str(unidades_por_present))
            
            # 1. Crear RecepcionDetalle
            detalle = RecepcionDetalle(
                recepcion_id=recepcion_id,
                insumo_id=insumo_id,
                cant_presentacion=cant_presentacion,
                unidades_por_present=unidades_por_present,
                cantidad_base=cantidad_base,
                costo_unitario=costo_unitario,
                notas=notas
            )
            session.add(detalle)
            session.flush()  # Para obtener el ID del detalle
            
            # 2. Crear LOTE automáticamente
            lote = Lote(
                det_recepcion_id=detalle.id_recepcion_det,
                lote=lote_numero_generado,
                lote_proveedor=lote_proveedor,
                cantidad_inicial=cantidad_base,
                cantidad_disponible=cantidad_base,
                costo_unitario=costo_unitario,
                fecha_caducidad=fecha_caducidad,
                estado=1  # 1=Disponible
            )
            session.add(lote)
            session.flush()  # Para obtener el ID del lote
            
            logger.info(f"RecepcionDetalle creado: {detalle.id_recepcion_det}, Lote generado: {lote_numero_generado} (ID: {lote.id_lote})")
            
            # 3. Crear MOVIMIENTO (ENTRADA) - EN LA MISMA SESIÓN
            if sucursal_id:
                movimiento = Movimiento(
                    sucursal_id=sucursal_id,
                    insumo_id=insumo_id,
                    lote_id=lote.id_lote,
                    tipo_mov=1,  # 1=Entrada
                    motivo=1,  # 1=Recepción
                    cantidad=cantidad_base,
                    det_recepcion_id=detalle.id_recepcion_det,
                    compra_id=compra_id,
                    usuario_id=usuario_id
                )
                session.add(movimiento)
                session.flush()
                logger.info(f"Movimiento ENTRADA creado (ID: {movimiento.id_movimiento}) para sucursal={sucursal_id}, insumo={insumo_id}, cantidad={float(cantidad_base)}")
                
                # 4. Actualizar/Crear EXISTENCIA - EN LA MISMA SESIÓN
                existencia = session.query(Existencia).filter(
                    Existencia.sucursal_id == sucursal_id,
                    Existencia.insumo_id == insumo_id
                ).first()
                
                cantidad_entrada_dec = cantidad_base
                costo_entrada_dec = Decimal(str(costo_unitario))
                
                if not existencia:
                    # NO EXISTE → Crear nueva existencia
                    existencia = Existencia(
                        sucursal_id=sucursal_id,
                        insumo_id=insumo_id,
                        cantidad=cantidad_entrada_dec,
                        costo_promedio=costo_entrada_dec
                    )
                    session.add(existencia)
                    logger.info(f"Existencia CREADA: sucursal={sucursal_id}, insumo={insumo_id}, cantidad={float(cantidad_entrada_dec)}, costo={float(costo_entrada_dec)}")
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
                    
                    logger.info(f"Existencia ACTUALIZADA: sucursal={sucursal_id}, insumo={insumo_id}, "
                               f"cantidad_anterior={float(cantidad_anterior)} → nueva={float(cantidad_nueva)}, "
                               f"costo_anterior={float(costo_anterior):.2f} → nuevo={float(costo_promedio_nuevo):.2f}")
            
            # COMMIT TODO junto (transacción atómica)
            session.commit()
            
            return schema.dump(detalle)
    
    
    @staticmethod
    def obtener_detalle_por_id(detalle_id: int) -> dict:
        """Obtener detalle por ID"""
        schema = RecepcionDetalleResponseSchema()
        with get_db_session() as session:
            detalle = session.query(RecepcionDetalle).filter(
                RecepcionDetalle.id_recepcion_det == detalle_id
            ).first()
            return schema.dump(detalle) if detalle else None
    
    
    @staticmethod
    def listar_detalles_por_recepcion(recepcion_id: int) -> list:
        """Listar detalles de una recepción"""
        schema = RecepcionDetalleResponseSchema(many=True)
        with get_db_session() as session:
            detalles = session.query(RecepcionDetalle).filter(
                RecepcionDetalle.recepcion_id == recepcion_id
            ).all()
            return schema.dump(detalles)
