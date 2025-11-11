"""
Log DAO - Acceso a datos de auditoría
"""

import logging
import json
from typing import Optional, List, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc, and_
from datetime import datetime, timedelta

from src.core.db.session_manager import get_db_session
from src.models.auditoria.log_accion import LogAccion

logger = logging.getLogger(__name__)

class LogDAO:
    """DAO para operaciones de logging y auditoría"""
    
    def crear_log(self, datos: Dict[str, Any]) -> bool:
        """
        Crear un nuevo log de auditoría
        
        Args:
            datos: Diccionario con datos del log
                - origen: str (obligatorio) - API, WEB, MOBILE, etc.
                - entidad: str (obligatorio) - Usuario, Producto, etc.
                - accion: str (obligatorio) - CREATE, UPDATE, DELETE, etc.
                - entidad_id: str (opcional) - ID del registro afectado
                - usuario_id: int (opcional) - ID del usuario que ejecuta la acción
                - detalle: dict (opcional) - Detalles adicionales
                
        Returns:
            bool: True si se creó correctamente
        """
        try:
            with get_db_session() as session:
                # Convertir detalle a JSON si existe
                detalle_json = None
                if 'detalle' in datos and datos['detalle']:
                    detalle_json = json.dumps(datos['detalle'], ensure_ascii=False)
                
                # Crear log
                log = LogAccion(
                    origen=datos['origen'],
                    entidad=datos['entidad'],
                    entidad_id=str(datos.get('entidad_id', '')),
                    accion=datos['accion'],
                    usuario_id=datos.get('usuario_id'),
                    detalle_json=detalle_json
                )
                
                session.add(log)
                session.commit()
                
                logger.debug(f"Log creado: {datos['entidad']}.{datos['accion']} por usuario {datos.get('usuario_id', 'SYSTEM')}")
                return True
                
        except Exception as e:
            logger.error(f"Error al crear log: {str(e)}")
            return False
    
    def obtener_logs(self, filtros: Dict[str, Any] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Obtener logs con filtros opcionales
        
        Args:
            filtros: Diccionario con filtros opcionales
                - entidad: str - Filtrar por entidad
                - accion: str - Filtrar por acción
                - usuario_id: int - Filtrar por usuario
                - fecha_desde: datetime - Logs desde esta fecha
                - fecha_hasta: datetime - Logs hasta esta fecha
                - origen: str - Filtrar por origen
            limit: Máximo número de registros (None = sin límite)
            offset: Número de registros a saltar
            
        Returns:
            Lista de logs como diccionarios
        """
        try:
            with get_db_session() as session:
                query = session.query(LogAccion)
                
                # Aplicar filtros si existen
                if filtros:
                    if 'entidad' in filtros:
                        query = query.filter(LogAccion.entidad == filtros['entidad'])
                    
                    if 'accion' in filtros:
                        query = query.filter(LogAccion.accion == filtros['accion'])
                    
                    if 'usuario_id' in filtros:
                        query = query.filter(LogAccion.usuario_id == filtros['usuario_id'])
                    
                    if 'origen' in filtros:
                        query = query.filter(LogAccion.origen == filtros['origen'])
                    
                    if 'fecha_desde' in filtros:
                        query = query.filter(LogAccion.created_at >= filtros['fecha_desde'])
                    
                    if 'fecha_hasta' in filtros:
                        query = query.filter(LogAccion.created_at <= filtros['fecha_hasta'])
                
                # Ordenar por fecha descendente
                query = query.order_by(desc(LogAccion.created_at))
                
                # Aplicar offset si se proporciona
                if offset:
                    query = query.offset(offset)
                
                # Aplicar límite solo si se proporciona
                if limit is not None:
                    query = query.limit(limit)
                
                logs = query.all()
                
                # Convertir a diccionarios
                return [self._log_to_dict(log) for log in logs]
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener logs: {str(e)}")
            return []
    
    def contar_logs(self, filtros: Dict[str, Any] = None) -> int:
        """
        Contar total de logs con filtros opcionales
        
        Args:
            filtros: Mismos filtros que obtener_logs
            
        Returns:
            Número total de logs
        """
        try:
            with get_db_session() as session:
                query = session.query(LogAccion)
                
                # Aplicar los mismos filtros
                if filtros:
                    if 'entidad' in filtros:
                        query = query.filter(LogAccion.entidad == filtros['entidad'])
                    
                    if 'accion' in filtros:
                        query = query.filter(LogAccion.accion == filtros['accion'])
                    
                    if 'usuario_id' in filtros:
                        query = query.filter(LogAccion.usuario_id == filtros['usuario_id'])
                    
                    if 'origen' in filtros:
                        query = query.filter(LogAccion.origen == filtros['origen'])
                    
                    if 'fecha_desde' in filtros:
                        query = query.filter(LogAccion.created_at >= filtros['fecha_desde'])
                    
                    if 'fecha_hasta' in filtros:
                        query = query.filter(LogAccion.created_at <= filtros['fecha_hasta'])
                
                return query.count()
                
        except SQLAlchemyError as e:
            logger.error(f"Error al contar logs: {str(e)}")
            return 0
    
    def obtener_estadisticas(self, dias: int = 30) -> Dict[str, Any]:
        """
        Obtener estadísticas de logs de los últimos N días
        
        Args:
            dias: Número de días hacia atrás
            
        Returns:
            Diccionario con estadísticas
        """
        try:
            with get_db_session() as session:
                fecha_desde = datetime.utcnow() - timedelta(days=dias)
                
                from sqlalchemy import func
                # Total de logs
                total = session.query(func.count(LogAccion.id_log_accion))\
                    .filter(LogAccion.created_at >= fecha_desde)\
                    .scalar()

                # Por entidad
                por_entidad = session.query(
                    LogAccion.entidad,
                    func.count(LogAccion.id_log_accion).label('count')
                ).filter(LogAccion.created_at >= fecha_desde)\
                .group_by(LogAccion.entidad)\
                .all()

                # Por acción
                por_accion = session.query(
                    LogAccion.accion,
                    func.count(LogAccion.id_log_accion).label('count')
                ).filter(LogAccion.created_at >= fecha_desde)\
                .group_by(LogAccion.accion)\
                .all()

                # Por usuario (top 10)
                por_usuario = session.query(
                    LogAccion.usuario_id,
                    func.count(LogAccion.id_log_accion).label('count')
                ).filter(
                    and_(
                        LogAccion.created_at >= fecha_desde,
                        LogAccion.usuario_id.isnot(None)
                    )
                ).group_by(LogAccion.usuario_id)\
                .order_by(desc('count'))\
                .limit(10)\
                .all()
                
                return {
                    'periodo_dias': dias,
                    'total_logs': total,
                    'por_entidad': [{'entidad': e, 'count': c} for e, c in por_entidad],
                    'por_accion': [{'accion': a, 'count': c} for a, c in por_accion],
                    'top_usuarios': [{'usuario_id': u, 'count': c} for u, c in por_usuario]
                }
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener estadísticas: {str(e)}")
            return {'error': str(e)}
    
    def limpiar_logs_antiguos(self, dias: int = 90) -> int:
        """
        Eliminar logs más antiguos que X días
        
        Args:
            dias: Días de antigüedad
            
        Returns:
            Número de logs eliminados
        """
        try:
            with get_db_session() as session:
                fecha_limite = datetime.utcnow() - timedelta(days=dias)
                
                resultado = session.query(LogAccion)\
                    .filter(LogAccion.created_at < fecha_limite)\
                    .delete()
                
                session.commit()
                logger.info(f"Eliminados {resultado} logs anteriores a {fecha_limite}")
                
                return resultado
                
        except SQLAlchemyError as e:
            logger.error(f"Error al limpiar logs antiguos: {str(e)}")
            return 0
    
    def _log_to_dict(self, log: LogAccion) -> Dict[str, Any]:
        """Convertir LogAccion a diccionario"""
        log_dict = log.to_dict()
        
        # Parsear JSON si existe
        if log_dict.get('detalle_json'):
            try:
                log_dict['detalle'] = json.loads(log_dict['detalle_json'])
            except json.JSONDecodeError:
                log_dict['detalle'] = None
            del log_dict['detalle_json']
        
        return log_dict