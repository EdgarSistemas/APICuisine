"""
Servicio de logging y auditoría
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from flask import request, g

from src.dao.auditoria.log_dao import LogDAO

logger = logging.getLogger(__name__)

class LogService:
    """Servicio para gestión de logs y auditoría"""
    
    def __init__(self):
        self.log_dao = LogDAO()
    
    def log_accion(self, entidad: str, accion: str, entidad_id: str = None, 
                   usuario_id: int = None, detalle: Dict[str, Any] = None, 
                   origen: str = 'API') -> bool:
        """
        Registrar una acción en el log de auditoría
        
        Args:
            entidad: Nombre de la entidad (Usuario, Producto, etc.)
            accion: Acción realizada (CREATE, UPDATE, DELETE, LOGIN, etc.)
            entidad_id: ID del registro afectado (opcional)
            usuario_id: ID del usuario que ejecuta la acción (opcional)
            detalle: Información adicional (opcional)
            origen: Origen de la acción (API, WEB, MOBILE, etc.)
            
        Returns:
            bool: True si se registró correctamente
        """
        try:
            # Si no se proporciona usuario_id, intentar obtenerlo del contexto de Flask
            if usuario_id is None and hasattr(g, 'current_user'):
                usuario_id = g.current_user.get('user_id')
            
            # Preparar datos del log
            datos_log = {
                'origen': origen,
                'entidad': entidad,
                'accion': accion,
                'entidad_id': entidad_id,
                'usuario_id': usuario_id,
                'detalle': detalle or {}
            }
            
            # Agregar información de contexto si está disponible
            if request:
                datos_log['detalle'].update({
                    'ip': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', '')[:200],  # Limitar longitud
                    'endpoint': request.endpoint
                })
            
            return self.log_dao.crear_log(datos_log)
            
        except Exception as e:
            logger.error(f"Error al registrar log: {str(e)}")
            return False
    
    def obtener_logs(self, filtros: Dict[str, Any] = None, page: int = 1, 
                     per_page: int = 50) -> Dict[str, Any]:
        """
        Obtener logs con paginación
        
        Args:
            filtros: Filtros a aplicar
            page: Página actual (base 1)
            per_page: Registros por página
            
        Returns:
            Diccionario con logs y metadatos de paginación
        """
        try:
            offset = (page - 1) * per_page
            
            # Obtener logs y total
            logs = self.log_dao.obtener_logs(filtros, per_page, offset)
            total = self.log_dao.contar_logs(filtros)
            
            # Calcular metadatos de paginación
            total_pages = (total + per_page - 1) // per_page
            
            return {
                'logs': logs,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            }
            
        except Exception as e:
            logger.error(f"Error al obtener logs: {str(e)}")
            return {
                'logs': [],
                'pagination': {
                    'page': 1,
                    'per_page': per_page,
                    'total': 0,
                    'total_pages': 0,
                    'has_next': False,
                    'has_prev': False
                },
                'error': str(e)
            }
    
    def obtener_todos_los_logs(self, filtros: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Obtener todos los logs sin paginación
        
        Args:
            filtros: Filtros a aplicar
            
        Returns:
            Lista de logs
        """
        try:
            # Obtener todos los logs (sin límite)
            logs = self.log_dao.obtener_logs(filtros, limit=None, offset=None)
            return logs
            
        except Exception as e:
            logger.error(f"Error al obtener logs: {str(e)}")
            return []
    
    def obtener_estadisticas(self, dias: int = 30) -> Dict[str, Any]:
        """
        Obtener estadísticas de actividad
        
        Args:
            dias: Período en días
            
        Returns:
            Diccionario con estadísticas
        """
        try:
            return self.log_dao.obtener_estadisticas(dias)
        except Exception as e:
            logger.error(f"Error al obtener estadísticas: {str(e)}")
            return {'error': str(e)}
    
    def limpiar_logs_antiguos(self, dias: int = 90) -> Dict[str, Any]:
        """
        Limpiar logs antiguos (solo para administradores)
        
        Args:
            dias: Logs más antiguos que estos días serán eliminados
            
        Returns:
            Resultado de la operación
        """
        try:
            eliminados = self.log_dao.limpiar_logs_antiguos(dias)
            return {
                'success': True,
                'eliminados': eliminados,
                'message': f'Se eliminaron {eliminados} logs anteriores a {dias} días'
            }
        except Exception as e:
            logger.error(f"Error al limpiar logs: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

# === FUNCIÓN GLOBAL PARA USAR EN TODA LA APP ===

# Instancia global del servicio
_log_service = LogService()

def log_action(entidad: str, accion: str, entidad_id: str = None, 
               usuario_id: int = None, detalle: Dict[str, Any] = None, 
               origen: str = 'API') -> bool:
    """
    Función global para registrar acciones en el log desde cualquier parte de la app
    
    Ejemplos de uso:
        from src.services.auditoria.log_service import log_action
        
        # Log básico
        log_action('Usuario', 'CREATE', entidad_id='123')
        
        # Log con detalles
        log_action('Producto', 'UPDATE', entidad_id='456', 
                  detalle={'campos_modificados': ['nombre', 'precio']})
        
        # Log con usuario específico
        log_action('Pedido', 'DELETE', entidad_id='789', usuario_id=1)
    
    Args:
        entidad: Nombre de la entidad (Usuario, Producto, Pedido, etc.)
        accion: Acción realizada (CREATE, UPDATE, DELETE, LOGIN, LOGOUT, etc.)
        entidad_id: ID del registro afectado (opcional)
        usuario_id: ID del usuario que ejecuta la acción (opcional)
        detalle: Información adicional como dict (opcional)
        origen: Origen de la acción - API, WEB, MOBILE, SYSTEM (default: API)
        
    Returns:
        bool: True si se registró correctamente
    """
    return _log_service.log_accion(entidad, accion, entidad_id, usuario_id, detalle, origen)