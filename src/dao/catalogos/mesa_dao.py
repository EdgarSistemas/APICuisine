"""
MesaDAO - Data Access Object para catalogos.Mesa
Queries específicas para CRUD de Mesas con indirection (Mesa→Area→Sucursal)
"""

from src.models import Mesa, Area, Sucursal
from src.core.db.session_manager import get_db_session
from src.schemas.mesa_schema import MesaResponseSchema
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MesaDAO:
    """Data Access Object para Mesa"""
    
    @staticmethod
    def generar_codigo_mesa() -> str:
        """
        Generar código automático para mesa.
        Formato: MES-YYYYMMDDHHMMSS
        Ejemplo: MES-20251106074844
        
        Returns:
            Código único generado
        """
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"MES-{timestamp}"
    
    @staticmethod
    def crear_mesa(area_id: int, capacidad: int) -> dict:
        """
        Crear nueva mesa en un área.
        El código se genera automáticamente con formato MES-YYYYMMDDHHMMSS.
        
        Args:
            area_id: ID del área
            capacidad: Capacidad de personas
            
        Returns:
            Dict serializado con datos de la mesa
        """
        schema = MesaResponseSchema()
        with get_db_session() as session:
            # Generar código automático
            codigo_mesa = MesaDAO.generar_codigo_mesa()
            
            mesa = Mesa(
                area_id=area_id,
                codigo_mesa=codigo_mesa,
                capacidad=capacidad,
                es_activa=True
            )
            session.add(mesa)
            session.flush()
            session.refresh(mesa)
            session.commit()
            logger.info(f"Mesa '{codigo_mesa}' creada en área {area_id}")
            return schema.dump(mesa)
    
    
    @staticmethod
    def obtener_mesa_por_id(mesa_id: int) -> dict:
        """
        Obtener mesa por ID.
        
        Args:
            mesa_id: ID de la mesa
            
        Returns:
            Dict serializado o None
        """
        schema = MesaResponseSchema()
        with get_db_session() as session:
            mesa = session.query(Mesa).filter(Mesa.id_mesa == mesa_id).first()
            return schema.dump(mesa) if mesa else None
    
    
    @staticmethod
    def obtener_mesas_por_area(area_id: int, solo_activas: bool = True) -> list:
        """
        Obtener todas las mesas de un área.
        
        Args:
            area_id: ID del área
            solo_activas: Si True, solo mesas activas
            
        Returns:
            Lista de dicts serializados
        """
        schema = MesaResponseSchema(many=True)
        with get_db_session() as session:
            query = session.query(Mesa).filter(Mesa.area_id == area_id)
            
            if solo_activas:
                query = query.filter(Mesa.es_activa == True)
            
            mesas = query.order_by(Mesa.codigo_mesa).all()
            return schema.dump(mesas)
    
    
    @staticmethod
    def obtener_mesas_por_sucursal(sucursal_id: int, solo_activas: bool = True) -> list:
        """
        Obtener todas las mesas de una sucursal (con indirection vía Area).
        
        Esto es lo CRITICAL: usamos la indirection Mesa→Area→Sucursal
        
        Args:
            sucursal_id: ID de la sucursal
            solo_activas: Si True, solo mesas activas
            
        Returns:
            Lista de dicts serializados
        """
        schema = MesaResponseSchema(many=True)
        with get_db_session() as session:
            # JOIN Mesa con Area, luego filtrar por sucursal_id
            query = session.query(Mesa).join(Area).filter(Area.sucursal_id == sucursal_id)
            
            if solo_activas:
                query = query.filter(Mesa.es_activa == True)
            
            mesas = query.order_by(Area.nombre, Mesa.codigo_mesa).all()
            return schema.dump(mesas)
    
    
    @staticmethod
    def obtener_todas_las_mesas(solo_activas: bool = True) -> list:
        """
        Obtener TODAS las mesas (solo para ADMIN).
        
        Args:
            solo_activas: Si True, solo mesas activas
            
        Returns:
            Lista de dicts serializados
        """
        schema = MesaResponseSchema(many=True)
        with get_db_session() as session:
            query = session.query(Mesa).join(Area)
            
            if solo_activas:
                query = query.filter(Mesa.es_activa == True)
            
            mesas = query.order_by(Area.sucursal_id, Area.nombre, Mesa.codigo_mesa).all()
            return schema.dump(mesas)
    
    
    @staticmethod
    def actualizar_mesa(mesa_id: int, capacidad: int = None, es_activa: bool = None) -> dict:
        """
        Actualizar campos de una mesa.
        El código de mesa NO se puede modificar.
        
        Args:
            mesa_id: ID de la mesa
            capacidad: Nueva capacidad (opcional)
            es_activa: Nuevo estado (opcional)
            
        Returns:
            Dict serializado o None
        """
        schema = MesaResponseSchema()
        with get_db_session() as session:
            mesa = session.query(Mesa).filter(Mesa.id_mesa == mesa_id).first()
            
            if not mesa:
                return None
            
            if capacidad is not None:
                mesa.capacidad = capacidad
            if es_activa is not None:
                mesa.es_activa = es_activa
            
            session.commit()
            logger.info(f"Mesa {mesa_id} actualizada")
            return schema.dump(mesa)
    
    
    @staticmethod
    def eliminar_mesa_soft(mesa_id: int) -> bool:
        """
        Eliminar mesa (soft delete: marcar como inactiva).
        
        Args:
            mesa_id: ID de la mesa
            
        Returns:
            True si se eliminó, False si no existe
        """
        with get_db_session() as session:
            mesa = session.query(Mesa).filter(Mesa.id_mesa == mesa_id).first()
            
            if not mesa:
                return False
            
            mesa.es_activa = False
            session.commit()
            logger.info(f"Mesa {mesa_id} marcada como inactiva")
            return True
    
    
    @staticmethod
    def area_existe(area_id: int) -> bool:
        """
        Verificar si un área existe.
        
        Args:
            area_id: ID del área
            
        Returns:
            True si existe
        """
        with get_db_session() as session:
            existe = session.query(Area).filter(Area.id_area == area_id).first()
            return existe is not None
    
    
    @staticmethod
    def obtener_sucursal_de_mesa(mesa_id: int) -> int:
        """
        Obtener sucursal_id de una mesa (via Area).
        
        Args:
            mesa_id: ID de la mesa
            
        Returns:
            sucursal_id o None
        """
        with get_db_session() as session:
            resultado = session.query(Area.sucursal_id).join(Mesa).filter(
                Mesa.id_mesa == mesa_id
            ).first()
            return resultado[0] if resultado else None
    
    
    @staticmethod
    def mesa_pertenece_a_sucursal(mesa_id: int, sucursal_id: int) -> bool:
        """
        Verificar que una mesa pertenece a una sucursal (via Area).
        
        Args:
            mesa_id: ID de la mesa
            sucursal_id: ID de la sucursal
            
        Returns:
            True si la mesa pertenece a esa sucursal
        """
        with get_db_session() as session:
            existe = session.query(Mesa).join(Area).filter(
                Mesa.id_mesa == mesa_id,
                Area.sucursal_id == sucursal_id
            ).first()
            return existe is not None
