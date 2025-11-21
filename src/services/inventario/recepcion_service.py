"""
RecepcionService - Lógica de negocio para recepciones
"""

from datetime import datetime
import logging
from src.dao.inventario.recepcion_dao import RecepcionDAO, RecepcionDetalleDAO
from src.dao.inventario.compra_dao import CompraDAO
from src.dao.inventario.insumo_dao import InsumoDAO
from src.core.utils.multitenant import es_admin

logger = logging.getLogger(__name__)


class RecepcionService:
    """Service de Recepcion"""
    
    @staticmethod
    def crear_lote() -> str:
        return f"LOT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
    
    @staticmethod
    def crear_recepcion(usuario_id: int, sucursal_id: int, compra_id: int, 
                       recibido_por: int, detalles: list, notas: str = None) -> dict:
        """
        Crear recepción con detalles.
        Genera Lotes automáticamente para cada detalle.
        Solo ADMIN o usuarios con acceso a sucursal.
        
        Args:
            usuario_id: ID del usuario autenticado
            sucursal_id: ID de la sucursal (del payload)
            compra_id: ID de la compra
            recibido_por: ID del usuario que recibe
            detalles: Lista de {insumo_id, cant_presentacion, unidades_por_present, costo_unitario, ...}
            notas: Notas opcionales
            
        Returns:
            {success: bool, data?: dict, error?: str, message?: str}
        """
        try:
            # VALIDACIÓN 1: Solo ADMIN
            if not es_admin(usuario_id):
                logger.warning(f"Usuario {usuario_id} intentó crear recepción sin permisos")
                return {"success": False, "error": "Solo administradores pueden crear recepciones"}
            
            # VALIDACIÓN 2: Compra existe
            compra = CompraDAO.obtener_compra_por_id(compra_id)
            if not compra:
                return {"success": False, "error": f"Compra {compra_id} no existe"}
            
            # Obtener sucursal_id de la compra (para consistencia)
            sucursal_id_compra = compra.get('sucursal_id') if isinstance(compra, dict) else compra.sucursal_id
            
            # VALIDACIÓN 3: Detalles no vacíos
            if not detalles or len(detalles) == 0:
                return {"success": False, "error": "Debe incluir al menos un detalle"}
            
            # VALIDACIÓN 4: Validar insumos
            for item in detalles:
                insumo_id = item.get('insumo_id')
                if not InsumoDAO.insumo_existe(insumo_id):
                    return {"success": False, "error": f"Insumo {insumo_id} no existe"}
            
            # CREAR RECEPCIÓN
            recepcion = RecepcionDAO.crear_recepcion(
                compra_id=compra_id,
                recibido_por=recibido_por,
                notas=notas
            )
            
            # AGREGAR DETALLES (Esto genera Lotes, Movimientos y actualiza Existencias automáticamente)
            detalles_creados = []
            for item in detalles:
                detalle = RecepcionDetalleDAO.crear_detalle(
                    recepcion_id=recepcion['id_recepcion'],
                    insumo_id=item['insumo_id'],
                    cant_presentacion=item['cant_presentacion'],
                    unidades_por_present=item['unidades_por_present'],
                    costo_unitario=item['costo_unitario'],
                    lote_proveedor=item.get('lote_proveedor'),
                    fecha_caducidad=item.get('fecha_caducidad'),
                    notas=item.get('notas'),
                    sucursal_id=sucursal_id_compra,  # Usar sucursal de la Compra (consistencia)
                    compra_id=compra_id,  # Para Movimiento
                    usuario_id=usuario_id  # Para Movimiento
                )
                detalles_creados.append(detalle)
            
            # Obtener recepción completa con detalles
            recepcion_completa = RecepcionDAO.obtener_recepcion_detallada(recepcion['id_recepcion'])
            
            # ACTUALIZAR ESTATUS DE LA COMPRA A "EN INVENTARIO" (estatus=2)
            CompraDAO.actualizar_estatus_compra(compra_id, 2)
            
            logger.info(f"Admin {usuario_id} creó recepción: {recepcion['id_recepcion']} con {len(detalles_creados)} detalles. "
                       f"Compra {compra_id} actualizada a 'En Inventario'. Movimientos y Existencias actualizadas.")
            return {
                "success": True,
                "data": recepcion_completa,
                "message": f"Recepción creada exitosamente con {len(detalles_creados)} detalles. Lotes generados, Movimientos registrados y Existencias actualizadas. Compra actualizada a 'En Inventario'"
            }
            
        except Exception as e:
            logger.error(f"Error en RecepcionService.crear_recepcion: {str(e)}")
            return {"success": False, "error": f"Error al crear recepción: {str(e)}"}
    
    
    @staticmethod
    def obtener_recepcion(recepcion_id: int) -> dict:
        """
        Obtener recepción completa con detalles.
        
        Args:
            recepcion_id: ID de la recepción
            
        Returns:
            {success: bool, data?: dict, error?: str}
        """
        try:
            recepcion = RecepcionDAO.obtener_recepcion_detallada(recepcion_id)
            
            if not recepcion:
                return {"success": False, "error": f"Recepción {recepcion_id} no encontrada"}
            
            return {"success": True, "data": recepcion}
            
        except Exception as e:
            logger.error(f"Error en RecepcionService.obtener_recepcion: {str(e)}")
            return {"success": False, "error": f"Error al obtener recepción: {str(e)}"}
    
    
    @staticmethod
    def listar_recepciones(usuario_id: int, sucursal_id: int) -> dict:
        """
        Listar recepciones de la sucursal.
        
        Args:
            usuario_id: ID del usuario autenticado
            sucursal_id: ID de la sucursal (del payload)
            
        Returns:
            {success: bool, data?: list, error?: str}
        """
        try:
            recepciones = RecepcionDAO.listar_recepciones(sucursal_id)
            return {"success": True, "data": recepciones}
        except Exception as e:
            logger.error(f"Error en RecepcionService.listar_recepciones: {str(e)}")
            return {"success": False, "error": f"Error al listar recepciones: {str(e)}"}
    
    
    @staticmethod
    def cancelar_recepcion(usuario_id: int, recepcion_id: int, revertir_compra: bool = True) -> dict:
        """
        Cancelar una recepción.
        - Solo ADMIN o COMPRAS
        - Marca Lotes como cancelados (estado=3)
        - Crea Movimientos de salida (tipo_mov=2, motivo=1=Recepción reversada) para revertir
        - Resta cantidades de Existencias usando actualizar_existencia_salida
        - Marca Recepcion con estatus=3 (Cancelada)
        - Opcionalmente revierte Compra a estatus=1 (Pendiente)
        
        IMPORTANTE: El costo_promedio NO se recalcula al cancelar. Solo se resta la cantidad.
        
        Args:
            usuario_id: ID del usuario autenticado
            recepcion_id: ID de la recepción a cancelar
            revertir_compra: Si True, regresa Compra a estatus=1
            
        Returns:
            {success: bool, message?: str, error?: str}
        """
        try:
            from src.core.utils.multitenant import tiene_rol
            from src.dao.inventario.movimiento_dao import MovimientoDAO
            from src.dao.inventario.existencia_dao import ExistenciaDAO
            from src.models import Lote, RecepcionDetalle, Recepcion
            from src.core.db.session_manager import get_db_session
            
            # VALIDACIÓN 1: Solo ADMIN o COMPRAS
            if not (es_admin(usuario_id) or tiene_rol(usuario_id, 8)):
                logger.warning(f"Usuario {usuario_id} intentó cancelar recepción sin permisos")
                return {"success": False, "error": "Solo administradores o usuarios de compras pueden cancelar recepciones"}
            
            with get_db_session() as session:
                # VALIDACIÓN 2: Recepción existe
                recepcion = session.query(Recepcion).filter(
                    Recepcion.id_recepcion == recepcion_id
                ).first()
                
                if not recepcion:
                    return {"success": False, "error": f"Recepción {recepcion_id} no existe"}
                
                # VALIDACIÓN 3: No está ya cancelada
                if recepcion.estatus == 3:
                    return {"success": False, "error": "La recepción ya está cancelada"}
                
                # Obtener compra_id para revertir al final
                compra_id = recepcion.compra_id
                
                # Obtener todos los detalles de la recepción
                detalles = session.query(RecepcionDetalle).filter(
                    RecepcionDetalle.recepcion_id == recepcion_id
                ).all()
                
                if not detalles or len(detalles) == 0:
                    return {"success": False, "error": "La recepción no tiene detalles para cancelar"}
                
                # REVERSAR CADA DETALLE
                for detalle in detalles:
                    # 1. Obtener el Lote asociado
                    lote = session.query(Lote).filter(
                        Lote.det_recepcion_id == detalle.id_recepcion_det
                    ).first()
                    
                    if not lote:
                        logger.warning(f"Detalle {detalle.id_recepcion_det} no tiene lote asociado")
                        continue
                    
                    # 2. Marcar Lote como cancelado (estado=3)
                    lote.estado = 3
                    logger.info(f"Lote {lote.id_lote} marcado como cancelado")
                    
                    # 3. Obtener datos para reversar
                    cantidad_base = float(detalle.cantidad_base)
                    costo_unitario = float(detalle.costo_unitario)  # ← AGREGAR ESTO
                    insumo_id = detalle.insumo_id
                    sucursal_id = recepcion.compra.sucursal_id if recepcion.compra else None
                    
                    if not sucursal_id:
                        logger.error(f"No se puede obtener sucursal_id de la recepción {recepcion_id}")
                        continue
                    
                    # 4. Crear Movimiento de SALIDA para cancelación
                    # tipo_mov=2 (Salida), motivo=1 (Recepción - reversión)
                    movimiento_cancelacion = MovimientoDAO.crear_movimiento(
                        sucursal_id=sucursal_id,
                        insumo_id=insumo_id,
                        lote_id=lote.id_lote,
                        tipo_mov=2,  # Salida (reversión)
                        motivo=1,    # Recepción (origen de la reversión)
                        cantidad=cantidad_base,
                        det_recepcion_id=detalle.id_recepcion_det,
                        compra_id=compra_id,
                        usuario_id=usuario_id,
                        session=session  # PASAR LA SESIÓN EXISTENTE
                    )
                    logger.info(f"Movimiento de cancelación creado: {movimiento_cancelacion.get('id_movimiento')}")
                    
                    # 5. Restar cantidad Y recalcular costo_promedio de Existencia
                    existencia_actualizada = ExistenciaDAO.actualizar_existencia_cancelacion_recepcion(
                        sucursal_id=sucursal_id,
                        insumo_id=insumo_id,
                        cantidad_cancelada=cantidad_base,
                        costo_unitario_cancelado=costo_unitario,
                        session=session  # PASAR LA SESIÓN EXISTENTE
                    )
                    
                    if existencia_actualizada:
                        logger.info(f"Existencia actualizada: insumo={insumo_id}, nueva cantidad={existencia_actualizada.get('cantidad')}")
                    else:
                        logger.warning(f"No se pudo actualizar existencia para insumo {insumo_id} en sucursal {sucursal_id}")
                
                # 6. Marcar Recepción como cancelada (estatus=3)
                recepcion.estatus = 3
                logger.info(f"Recepción {recepcion_id} marcada como cancelada")
                
                # 7. Actualizar estatus de la Compra
                if compra_id:
                    if revertir_compra:
                        # Si se cancela todo, marcar Compra como Cancelada (estatus=3)
                        CompraDAO.actualizar_estatus_compra(compra_id, 3)
                        logger.info(f"Compra {compra_id} marcada como Cancelada (estatus=3)")
                    else:
                        # Si solo se cancela la recepción, regresar Compra a Pendiente (estatus=1)
                        # para permitir re-recibir la mercancía
                        CompraDAO.actualizar_estatus_compra(compra_id, 1)
                        logger.info(f"Compra {compra_id} revertida a Pendiente (estatus=1) - puede re-recibirse")
                
                session.commit()
                
                logger.info(f"Usuario {usuario_id} canceló recepción {recepcion_id} con {len(detalles)} detalles")
                return {
                    "success": True,
                    "message": f"Recepción {recepcion_id} cancelada exitosamente. {len(detalles)} lotes cancelados, movimientos revertidos y existencias actualizadas"
                }
                
        except Exception as e:
            logger.error(f"Error en RecepcionService.cancelar_recepcion: {str(e)}")
            return {"success": False, "error": f"Error al cancelar recepción: {str(e)}"}

