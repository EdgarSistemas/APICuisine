"""
MesaEstatusDAO - Data Access Object para MesaEstatus
Gestión de estados de mesas (disponible, ocupada, en limpieza, etc)
"""

from datetime import datetime
from src.models.catalogos.mesa_estatus_model import MesaEstatus
from src.core.db.session_manager import get_db_session
import logging

logger = logging.getLogger(__name__)


class MesaEstatusDAO:
    """Data Access Object para MesaEstatus"""
    
    @staticmethod
    def obtener_estatus_mesa(mesa_id: int) -> dict:
        """
        Obtener estatus actual de una mesa.
        
        Args:
            mesa_id: ID de la mesa
            
        Returns:
            Dict con estatus de la mesa o None
        """
        with get_db_session() as session:
            estatus = session.query(MesaEstatus).filter(
                MesaEstatus.mesa_id == mesa_id
            ).first()
            
            if estatus:
                return {
                    "id_mesa_estatus": estatus.id_mesa_estatus,
                    "mesa_id": estatus.mesa_id,
                    "estatus": estatus.estatus,
                    "cambio_por": estatus.cambio_por,
                    "notas": estatus.notas,
                    "created_at": estatus.created_at,
                    "updated_at": estatus.updated_at
                }
            return None
    
    
    @staticmethod
    def actualizar_estatus_mesa(
        mesa_id: int,
        estatus: int,
        cambio_por: int = None,
        notas: str = None
    ) -> dict:
        """
        Actualizar estatus de una mesa.
        
        Estatus:
        - 1 = Disponible
        - 2 = Ocupada
        - 3 = En Limpieza
        - 4 = Fuera de Servicio
        
        Args:
            mesa_id: ID de la mesa
            estatus: Nuevo estatus (1, 2, 3, o 4)
            cambio_por: ID del usuario que realiza el cambio
            notas: Notas sobre el cambio
            
        Returns:
            Dict con estatus actualizado o None
        """
        estatus_map = {1: "Disponible", 2: "Ocupada", 3: "En Limpieza", 4: "Fuera de Servicio"}
        
        with get_db_session() as session:
            mesa_estatus = session.query(MesaEstatus).filter(
                MesaEstatus.mesa_id == mesa_id
            ).first()
            
            if not mesa_estatus:
                # Crear si no existe
                mesa_estatus = MesaEstatus(
                    mesa_id=mesa_id,
                    estatus=estatus,
                    cambio_por=cambio_por,
                    notas=notas
                )
                session.add(mesa_estatus)
            else:
                mesa_estatus.estatus = estatus
                mesa_estatus.cambio_por = cambio_por
                mesa_estatus.notas = notas
                mesa_estatus.updated_at = datetime.now()
            
            session.commit()
            logger.info(f"Mesa {mesa_id} actualizada a estatus {estatus_map.get(estatus, 'Desconocido')} por usuario {cambio_por}")
            
            return {
                "id_mesa_estatus": mesa_estatus.id_mesa_estatus,
                "mesa_id": mesa_estatus.mesa_id,
                "estatus": mesa_estatus.estatus,
                "cambio_por": mesa_estatus.cambio_por,
                "notas": mesa_estatus.notas,
                "created_at": mesa_estatus.created_at,
                "updated_at": mesa_estatus.updated_at
            }
    
    
    @staticmethod
    def obtener_mesas_en_limpieza(sucursal_id: int = None) -> list:
        """
        Obtener todas las mesas en estado de limpieza.
        
        Args:
            sucursal_id: Filtrar por sucursal (opcional)
            
        Returns:
            Lista de mesas en limpieza
        """
        from src.models.catalogos.mesa_model import Mesa
        from src.models.catalogos.area_model import Area
        
        with get_db_session() as session:
            query = session.query(MesaEstatus).join(
                Mesa, MesaEstatus.mesa_id == Mesa.id_mesa
            ).filter(
                MesaEstatus.estatus == 3  # En Limpieza
            )
            
            if sucursal_id:
                query = query.join(
                    Area, Mesa.area_id == Area.id_area
                ).filter(
                    Area.sucursal_id == sucursal_id
                )
            
            mesas = query.all()
            return [{
                "id_mesa_estatus": m.id_mesa_estatus,
                "mesa_id": m.mesa_id,
                "estatus": m.estatus,
                "cambio_por": m.cambio_por,
                "notas": m.notas,
                "created_at": m.created_at,
                "updated_at": m.updated_at
            } for m in mesas]
    
    
    @staticmethod
    def marcar_mesa_disponible(mesa_id: int, usuario_id: int = None) -> dict:
        """
        Marcar mesa como disponible (termina limpieza).
        
        Args:
            mesa_id: ID de la mesa
            usuario_id: ID del usuario que la marca disponible (personal de limpieza)
            
        Returns:
            Dict con estatus actualizado
        """
        return MesaEstatusDAO.actualizar_estatus_mesa(
            mesa_id,
            1,  # Disponible
            usuario_id,
            "Limpieza completada"
        )
