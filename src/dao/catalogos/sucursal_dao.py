"""
Data Access Object para la entidad Sucursal
Maneja todas las operaciones de base de datos para sucursales
"""
from typing import List, Optional, Dict, Any
from sqlalchemy import and_, or_, desc, asc, func
from sqlalchemy.exc import SQLAlchemyError
from src.models.catalogos.sucursal import Sucursal

from src.core.db.session_manager import get_db_session
from src.schemas.sucursal_schema import SucursalResponseSchema

class SucursalDAO:
    """
    Data Access Object para entidad Sucursal
    Proporciona métodos para interactuar con la tabla catalogos.Sucursal
    """
    
    def crear(self, datos_sucursal: dict) -> dict:
        """Crea una nueva sucursal y retorna un dict serializado"""
        schema = SucursalResponseSchema()
        with get_db_session() as session:
            sucursal = Sucursal(**datos_sucursal)
            session.add(sucursal)
            session.flush()
            session.refresh(sucursal)
            return schema.dump(sucursal)
    
    def obtener_por_id(self, id_sucursal: int) -> Optional[dict]:
        """Obtiene una sucursal por su ID y la serializa"""
        schema = SucursalResponseSchema()
        with get_db_session() as session:
            sucursal = session.query(Sucursal).filter(
                Sucursal.id_sucursal == id_sucursal
            ).first()
            return schema.dump(sucursal) if sucursal else None
    
    def obtener_por_codigo(self, codigo: str) -> Optional[dict]:
        """Obtiene una sucursal por su código único y la serializa"""
        schema = SucursalResponseSchema()
        with get_db_session() as session:
            sucursal = session.query(Sucursal).filter(
                Sucursal.codigo_sucursal == codigo.upper()
            ).first()
            return schema.dump(sucursal) if sucursal else None
    
    def actualizar(self, id_sucursal: int, datos: dict) -> Optional[dict]:
        """Actualiza una sucursal existente y la serializa"""
        schema = SucursalResponseSchema()
        with get_db_session() as session:
            sucursal = session.query(Sucursal).filter(
                Sucursal.id_sucursal == id_sucursal
            ).first()
            if not sucursal:
                return None
            # Solo actualizar campos válidos
            campos_validos = Sucursal.get_campos_actualizables()
            for key, value in datos.items():
                if key in campos_validos and hasattr(sucursal, key):
                    setattr(sucursal, key, value)
            session.flush()
            session.refresh(sucursal)
            return schema.dump(sucursal)
    
    def eliminar_logico(self, id_sucursal: int) -> bool:
        """Eliminación lógica de una sucursal (marcar como inactiva)"""
        with get_db_session() as session:
            sucursal = session.query(Sucursal).filter(
                Sucursal.id_sucursal == id_sucursal
            ).first()
            
            if not sucursal:
                return False
            
            sucursal.es_activa = False
            session.flush()
            return True
    
    def listar_todas(self) -> List[dict]:
        """Lista todas las sucursales activas (SIMPLE, serializado)"""
        schema = SucursalResponseSchema(many=True)
        with get_db_session() as session:
            sucursales = session.query(Sucursal).filter(
                Sucursal.es_activa == True
            ).order_by(asc(Sucursal.nombre)).all()
            return schema.dump(sucursales)
    
    def obtener_activas(self) -> List[dict]:
        """Obtiene solo las sucursales activas (serializado)"""
        schema = SucursalResponseSchema(many=True)
        with get_db_session() as session:
            sucursales = session.query(Sucursal).filter(
                Sucursal.es_activa == True
            ).order_by(asc(Sucursal.nombre)).all()
            return schema.dump(sucursales)
    
    def existe_codigo(self, codigo: str, excluir_id: int = None) -> bool:
        """Verifica si ya existe un código de sucursal"""
        with get_db_session() as session:
            query = session.query(Sucursal).filter(
                Sucursal.codigo_sucursal == codigo.upper()
            )
            
            if excluir_id:
                query = query.filter(Sucursal.id_sucursal != excluir_id)
            
            return query.first() is not None