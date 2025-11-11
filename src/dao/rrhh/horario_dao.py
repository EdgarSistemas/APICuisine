"""
HorarioDAO - Data Access Object para rrhh.Horario
"""

from src.models.rrhh import Horario, HorarioDetalle
from src.core.db.session_manager import get_db_session
from src.schemas.rrhh_schema import HorarioResponseSchema, HorarioDetalleResponseSchema
import logging

logger = logging.getLogger(__name__)


class HorarioDAO:
    """Data Access Object para Horario"""
    
    @staticmethod
    def crear_horario_con_detalles(sucursal_id: int, clave: str, nombre: str, descripcion: str, detalles: list) -> dict:
        """
        Crear horario con sus detalles en una sola transacción.
        
        Args:
            sucursal_id: ID de sucursal (NULL = global)
            clave: Clave única del horario
            nombre: Nombre descriptivo
            descripcion: Descripción (opcional)
            detalles: Lista de dicts con dia_semana, hora_inicio, hora_fin, tolerancia_min
            
        Returns:
            Dict con horario y detalles creados
        """
        schema_horario = HorarioResponseSchema()
        schema_detalle = HorarioDetalleResponseSchema()
        
        with get_db_session() as session:
            # 1. Crear Horario
            horario = Horario(
                sucursal_id=sucursal_id,
                clave=clave,
                nombre=nombre,
                descripcion=descripcion,
                es_activo=True
            )
            session.add(horario)
            session.flush()
            
            # 2. Crear HorarioDetalles
            detalles_creados = []
            for detalle_data in detalles:
                detalle = HorarioDetalle(
                    horario_id=horario.id_horario,
                    dia_semana=detalle_data['dia_semana'],
                    hora_inicio=detalle_data['hora_inicio'],
                    hora_fin=detalle_data['hora_fin'],
                    turno_idx=1,  # Siempre 1 (un solo turno por día)
                    tolerancia_min=detalle_data.get('tolerancia_min', 10),
                    es_activo=True
                )
                session.add(detalle)
                session.flush()
                detalles_creados.append(schema_detalle.dump(detalle))
            
            session.commit()
            
            logger.info(f"Horario creado: {clave} con {len(detalles_creados)} detalles")
            
            return {
                "horario": schema_horario.dump(horario),
                "detalles": detalles_creados
            }
    
    
    @staticmethod
    def obtener_horario_por_id(horario_id: int) -> dict:
        """Obtener horario por ID"""
        schema = HorarioResponseSchema()
        with get_db_session() as session:
            horario = session.query(Horario).filter(
                Horario.id_horario == horario_id
            ).first()
            return schema.dump(horario) if horario else None
    
    
    @staticmethod
    def obtener_detalles_horario(horario_id: int) -> list:
        """Obtener detalles de un horario"""
        schema = HorarioDetalleResponseSchema()
        with get_db_session() as session:
            detalles = session.query(HorarioDetalle).filter(
                HorarioDetalle.horario_id == horario_id,
                HorarioDetalle.es_activo == True
            ).order_by(HorarioDetalle.dia_semana).all()
            return [schema.dump(d) for d in detalles]
    
    
    @staticmethod
    def listar_horarios(sucursal_id: int = None, solo_activos: bool = True) -> list:
        """Listar horarios con filtros"""
        schema = HorarioResponseSchema()
        with get_db_session() as session:
            query = session.query(Horario)
            
            if sucursal_id:
                query = query.filter(Horario.sucursal_id == sucursal_id)
            
            if solo_activos:
                query = query.filter(Horario.es_activo == True)
            
            horarios = query.order_by(Horario.nombre).all()
            return [schema.dump(h) for h in horarios]
    
    
    @staticmethod
    def horario_existe(horario_id: int) -> bool:
        """Verificar si un horario existe"""
        with get_db_session() as session:
            existe = session.query(Horario).filter(
                Horario.id_horario == horario_id
            ).first()
            return existe is not None
    
    
    @staticmethod
    def clave_existe(clave: str) -> bool:
        """Verificar si una clave ya existe"""
        with get_db_session() as session:
            existe = session.query(Horario).filter(
                Horario.clave == clave
            ).first()
            return existe is not None
