"""
TurnoClaveDAO - Data Access Object para rrhh.TurnoClave
"""

from src.models.rrhh import TurnoClave
from src.core.db.session_manager import get_db_session
from src.schemas.rrhh_schema import TurnoClaveResponseSchema
from datetime import date, datetime, timedelta
import random
import string
import logging

logger = logging.getLogger(__name__)


class TurnoClaveDAO:
    """Data Access Object para TurnoClave"""
    
    @staticmethod
    def generar_codigo_6_digitos() -> str:
        """Genera código aleatorio de 6 dígitos numéricos"""
        return ''.join(random.choices(string.digits, k=6))
    
    
    @staticmethod
    def generar_turno_clave(sucursal_id: int, horario_id: int, fecha: date, 
                           expira_en_horas: int = 2, uso_maximo: int = 0, 
                           generado_por: int = None) -> dict:
        """
        Generar código de turno para una fecha específica.
        Este método es llamado por Azure Function.
        
        Args:
            sucursal_id: ID de la sucursal
            horario_id: ID del horario
            fecha: Fecha del turno (YYYY-MM-DD)
            expira_en_horas: Horas hasta expiración (default: 2)
            uso_maximo: Máximo de usos permitidos (0 = ilimitado)
            generado_por: ID del usuario que genera (NULL si es Azure Function)
            
        Returns:
            Dict con el turno clave generado
        """
        schema = TurnoClaveResponseSchema()
        
        with get_db_session() as session:
            # 1. Verificar si ya existe código activo para esta fecha/horario
            turno_existente = session.query(TurnoClave).filter(
                TurnoClave.sucursal_id == sucursal_id,
                TurnoClave.horario_id == horario_id,
                TurnoClave.fecha == fecha,
                TurnoClave.es_activo == True
            ).first()
            
            if turno_existente:
                logger.info(f"Ya existe código activo para horario {horario_id} en fecha {fecha}")
                return schema.dump(turno_existente)
            
            # 2. Generar código único
            codigo = TurnoClaveDAO.generar_codigo_6_digitos()
            
            # Asegurar unicidad
            while session.query(TurnoClave).filter(TurnoClave.codigo == codigo, TurnoClave.es_activo == True).first():
                codigo = TurnoClaveDAO.generar_codigo_6_digitos()
            
            # 3. Calcular expiración
            expira_en = datetime.now() + timedelta(hours=expira_en_horas)
            
            # 4. Crear TurnoClave
            turno = TurnoClave(
                horario_id=horario_id,
                horario_detalle_id=None,  # NULL porque es un solo turno por día
                sucursal_id=sucursal_id,
                fecha=fecha,
                turno_idx=1,  # Siempre 1
                codigo=codigo,
                hash_codigo=None,  # Opcional
                es_activo=True,
                generado_por=generado_por,
                generado_en=datetime.now(),
                expira_en=expira_en,
                uso_maximo=uso_maximo,
                usos_count=0,
                notas=None
            )
            session.add(turno)
            session.commit()
            
            logger.info(f"Código generado: {codigo} para horario {horario_id} en sucursal {sucursal_id}")
            return schema.dump(turno)
    
    
    @staticmethod
    def validar_codigo(codigo: str, usuario_id: int, horario_id: int) -> dict:
        """
        Validar código de turno.
        
        Returns:
            {
                "valido": bool,
                "turno": dict or None,
                "error": str or None
            }
        """
        schema = TurnoClaveResponseSchema()
        
        with get_db_session() as session:
            turno = session.query(TurnoClave).filter(
                TurnoClave.codigo == codigo,
                TurnoClave.es_activo == True
            ).first()
            
            if not turno:
                return {"valido": False, "turno": None, "error": "Código no existe o está inactivo"}
            
            # Validación 1: No expirado
            if turno.expira_en and datetime.now() > turno.expira_en:
                return {"valido": False, "turno": schema.dump(turno), "error": "Código expirado"}
            
            # Validación 2: Uso máximo
            if turno.uso_maximo > 0 and turno.usos_count >= turno.uso_maximo:
                return {"valido": False, "turno": schema.dump(turno), "error": "Código ha alcanzado uso máximo"}
            
            # Validación 3: Horario correcto
            if turno.horario_id != horario_id:
                return {"valido": False, "turno": schema.dump(turno), "error": "Código no corresponde a tu horario"}
            
            # Validación 4: Fecha correcta
            if turno.fecha != date.today():
                return {"valido": False, "turno": schema.dump(turno), "error": "Código no es para hoy"}
            
            # TODO: Incrementar uso
            turno.usos_count += 1
            session.commit()
            
            return {"valido": True, "turno": schema.dump(turno), "error": None}
    
    
    @staticmethod
    def obtener_codigo_activo(sucursal_id: int, horario_id: int, fecha: date) -> dict:
        """Obtener código activo para una sucursal/horario/fecha"""
        schema = TurnoClaveResponseSchema()
        with get_db_session() as session:
            turno = session.query(TurnoClave).filter(
                TurnoClave.sucursal_id == sucursal_id,
                TurnoClave.horario_id == horario_id,
                TurnoClave.fecha == fecha,
                TurnoClave.es_activo == True
            ).first()
            return schema.dump(turno) if turno else None
    
    
    @staticmethod
    def desactivar_codigos_expirados() -> int:
        """
        Desactivar todos los códigos expirados.
        Este método puede ser llamado por un job.
        """
        with get_db_session() as session:
            result = session.query(TurnoClave).filter(
                TurnoClave.es_activo == True,
                TurnoClave.expira_en <= datetime.now()
            ).update({"es_activo": False})
            session.commit()
            logger.info(f"Se desactivaron {result} códigos expirados")
            return result
