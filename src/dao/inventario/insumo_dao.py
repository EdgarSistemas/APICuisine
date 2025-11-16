"""
InsumoDAO - Data Access Object para inventario.Insumo
"""

from src.models import Insumo, UnidadMedida
from src.models.inventario import Existencia
from src.core.db.session_manager import get_db_session
from src.schemas.insumo_schema import InsumoResponseSchema
from sqlalchemy import func, and_
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class InsumoDAO:
    """Data Access Object para Insumo"""
    
    @staticmethod
    def crear_insumo(nombre: str, minimo_stock: float, unidad_id: int) -> dict:
        """
        Crear nuevo insumo.
        
        Args:
            nombre: Nombre del insumo
            minimo_stock: Mínimo stock del insumo
            unidad_id: ID de la unidad de medida
            
        Returns:
            Dict serializado del insumo
        """
        schema = InsumoResponseSchema()
        with get_db_session() as session:
            insumo = Insumo(
                nombre=nombre,
                unidad_id=unidad_id,
                minimo_stock=minimo_stock,
                es_activo=True
            )
            session.add(insumo)
            session.commit()
            logger.info(f"Insumo creado: {nombre} (ID: {insumo.id_insumo})")
            return schema.dump(insumo)
    
    
    @staticmethod
    def obtener_insumo_por_id(insumo_id: int) -> dict:
        """
        Obtener insumo por ID.
        
        Args:
            insumo_id: ID del insumo
            
        Returns:
            Dict del insumo o None
        """
        schema = InsumoResponseSchema()
        with get_db_session() as session:
            insumo = session.query(Insumo).filter(
                Insumo.id_insumo == insumo_id
            ).first()
            return schema.dump(insumo) if insumo else None
    
    
    @staticmethod
    def obtener_insumos_por_unidad(unidad_id: int, solo_activos: bool = True) -> list:
        """
        Obtener insumos por unidad de medida.
        
        Args:
            unidad_id: ID de la unidad de medida
            solo_activos: Si True, solo insumos activos
            
        Returns:
            Lista de dicts de insumos
        """
        schema = InsumoResponseSchema()
        with get_db_session() as session:
            query = session.query(Insumo).filter(Insumo.unidad_id == unidad_id)
            
            if solo_activos:
                query = query.filter(Insumo.es_activo == True)
            
            insumos = query.order_by(Insumo.nombre).all()
            return [schema.dump(i) for i in insumos]
    
    
    @staticmethod
    def obtener_todos_los_insumos(solo_activos: bool = True) -> list:
        """
        Obtener todos los insumos.
        
        Args:
            solo_activos: Si True, solo insumos activos
            
        Returns:
            Lista de dicts de insumos
        """
        schema = InsumoResponseSchema()
        with get_db_session() as session:
            query = session.query(Insumo)
            
            if solo_activos:
                query = query.filter(Insumo.es_activo == True)
            
            insumos = query.order_by(Insumo.nombre).all()
            return [schema.dump(i) for i in insumos]
    
    
    @staticmethod
    def listar_insumos_con_existencias(sucursal_id: int, solo_activos: bool = True) -> list:
        """
        Obtener todos los insumos con sus existencias para una sucursal específica.
        Utiliza LEFT JOIN para incluir insumos sin existencias (cantidad=0, costo_promedio=0).
        
        Args:
            sucursal_id: ID de la sucursal
            solo_activos: Si True, solo insumos activos
            
        Returns:
            Lista de dicts con estructura:
            [
                {
                    "id_insumo": int,
                    "nombre": str,
                    "unidad_id": int,
                    "unidad_clave": str,
                    "unidad_nombre": str,
                    "es_activo": bool,
                    "cantidad": Decimal,
                    "costo_promedio": Decimal,
                    "updated_at": datetime (o None si no hay existencias)
                }
            ]
        """
        with get_db_session() as session:
            # Query con LEFT JOIN para incluir todos los insumos
            query = session.query(
                Insumo.id_insumo,
                Insumo.nombre,
                Insumo.unidad_id,
                UnidadMedida.clave.label('unidad_clave'),
                UnidadMedida.nombre.label('unidad_nombre'),
                Insumo.es_activo,
                func.coalesce(Existencia.cantidad, 0).label('cantidad'),
                func.coalesce(Existencia.costo_promedio, 0).label('costo_promedio'),
                Existencia.updated_at
            ).join(
                UnidadMedida, 
                Insumo.unidad_id == UnidadMedida.id_unidad
            ).outerjoin(
                Existencia,
                and_(
                    Existencia.insumo_id == Insumo.id_insumo,
                    Existencia.sucursal_id == sucursal_id
                )
            )
            
            # Filtro de insumos activos
            if solo_activos:
                query = query.filter(Insumo.es_activo == True)
            
            # Ordenar por nombre
            query = query.order_by(Insumo.nombre)
            
            # Ejecutar query
            resultados = query.all()
            
            # Convertir a lista de dicts
            insumos_con_existencias = []
            for row in resultados:
                insumos_con_existencias.append({
                    "id_insumo": row.id_insumo,
                    "nombre": row.nombre,
                    "unidad_id": row.unidad_id,
                    "unidad_clave": row.unidad_clave,
                    "unidad_nombre": row.unidad_nombre,
                    "es_activo": row.es_activo,
                    "cantidad": float(row.cantidad) if row.cantidad else 0.0,
                    "costo_promedio": float(row.costo_promedio) if row.costo_promedio else 0.0,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None
                })
            
            logger.info(f"Se obtuvieron {len(insumos_con_existencias)} insumos con existencias para sucursal {sucursal_id}")
            return insumos_con_existencias
    
    
    @staticmethod
    def actualizar_insumo(insumo_id: int, nombre: str = None, minimo_stock: float = None) -> dict:
        """
        Actualizar insumo.
        
        Args:
            insumo_id: ID del insumo
            nombre: Nuevo nombre (opcional)
            
        Returns:
            Dict actualizado o None
        """
        schema = InsumoResponseSchema()
        with get_db_session() as session:
            insumo = session.query(Insumo).filter(
                Insumo.id_insumo == insumo_id
            ).first()
            
            if not insumo:
                return None
            
            if nombre is not None:
                insumo.nombre = nombre
            if minimo_stock is not None:
                insumo.minimo_stock = Decimal(minimo_stock)
            
            session.commit()
            logger.info(f"Insumo actualizado: {insumo_id}")
            return schema.dump(insumo)
    
    
    @staticmethod
    def insumo_existe(insumo_id: int) -> bool:
        """
        Verificar si un insumo existe.
        
        Args:
            insumo_id: ID del insumo
            
        Returns:
            True si existe
        """
        with get_db_session() as session:
            existe = session.query(Insumo).filter(
                Insumo.id_insumo == insumo_id
            ).first()
            return existe is not None
    
    
    @staticmethod
    def unidad_existe(unidad_id: int) -> bool:
        """
        Verificar si una unidad de medida existe.
        
        Args:
            unidad_id: ID de la unidad
            
        Returns:
            True si existe
        """
        with get_db_session() as session:
            existe = session.query(UnidadMedida).filter(
                UnidadMedida.id_unidad == unidad_id
            ).first()
            return existe is not None
