"""
DAO para operaciones CRUD de Push Tokens
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, func
from src.models.auth.push_token_model import PushToken
from src.core.db import get_db_session
import logging

logger = logging.getLogger(__name__)

class PushTokenDAO:
    """
    Data Access Object para la tabla movil.PushToken
    """
    
    @staticmethod
    def crear_o_actualizar_token(usuario_id: int, token: str, plataforma: str) -> Optional[PushToken]:
        """
        Crea un nuevo token o reasigna uno existente al nuevo usuario
        El token representa un dispositivo específico y se reasigna al usuario que hace login
        
        Args:
            usuario_id: ID del usuario
            token: Token FCM del dispositivo
            plataforma: Plataforma ('android', 'web')
            
        Returns:
            PushToken creado o actualizado, None en caso de error
        """
        try:
            with get_db_session() as session:
                # Buscar token existente por el token mismo (representa el dispositivo)
                token_existente = session.query(PushToken).filter(
                    PushToken.token == token
                ).first()
                
                if token_existente:
                    # Reasignar token existente al nuevo usuario
                    token_existente.usuario_id = usuario_id
                    token_existente.plataforma = plataforma  # Actualizar plataforma por si cambió
                    token_existente.es_activo = True  # Asegurar que esté activo
                    token_existente.actualizado_en = func.sysutcdatetime()
                    session.commit()
                    session.refresh(token_existente)
                    logger.info(f"Token reasignado de dispositivo a usuario {usuario_id}, plataforma {plataforma}")
                    return token_existente
                else:
                    # Crear nuevo token para dispositivo nuevo
                    nuevo_token = PushToken(
                        usuario_id=usuario_id,
                        token=token,
                        plataforma=plataforma,
                        es_activo=True
                    )
                    session.add(nuevo_token)
                    session.commit()
                    session.refresh(nuevo_token)
                    logger.info(f"Nuevo token de dispositivo creado para usuario {usuario_id}, plataforma {plataforma}")
                    return nuevo_token
                    
        except SQLAlchemyError as e:
            logger.error(f"Error al crear/actualizar token: {str(e)}")
            return None
    
    @staticmethod
    def obtener_token_por_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de un token específico
        
        Args:
            token: Token FCM a buscar
            
        Returns:
            Dict con datos del token si existe, None si no
        """
        try:
            with get_db_session() as session:
                push_token = session.query(PushToken).filter(
                    PushToken.token == token
                ).first()
                
                if push_token:
                    return push_token.to_dict()
                return None
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener token: {str(e)}")
            return None
    
    @staticmethod
    def desactivar_token(token: str) -> bool:
        """
        Desactiva un token específico
        
        Args:
            token: Token FCM a desactivar
            
        Returns:
            True si se desactivó correctamente, False si no
        """
        try:
            with get_db_session() as session:
                push_token = session.query(PushToken).filter(
                    PushToken.token == token
                ).first()
                
                if push_token:
                    push_token.es_activo = False
                    push_token.actualizado_en = func.sysutcdatetime()
                    session.commit()
                    logger.info(f"Token desactivado: {token[:20]}...")
                    return True
                else:
                    logger.warning(f"Token no encontrado para desactivar: {token[:20]}...")
                    return False
                    
        except SQLAlchemyError as e:
            logger.error(f"Error al desactivar token: {str(e)}")
            return False
    
    @staticmethod
    def obtener_tokens_usuario(usuario_id: int, solo_activos: bool = True) -> List[PushToken]:
        """
        Obtiene todos los tokens de un usuario
        
        Args:
            usuario_id: ID del usuario
            solo_activos: Si True, solo retorna tokens activos
            
        Returns:
            Lista de tokens del usuario
        """
        try:
            with get_db_session() as session:
                query = session.query(PushToken).filter(
                    PushToken.usuario_id == usuario_id
                )
                
                if solo_activos:
                    query = query.filter(PushToken.es_activo == True)
                
                tokens = query.all()
                logger.info(f"Obtenidos {len(tokens)} tokens para usuario {usuario_id}")
                return tokens
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener tokens del usuario {usuario_id}: {str(e)}")
            return []
    
    @staticmethod
    def desactivar_tokens_usuario(usuario_id: int, plataforma: Optional[str] = None) -> bool:
        """
        Desactiva todos los tokens de un usuario
        
        Args:
            usuario_id: ID del usuario
            plataforma: Plataforma específica (opcional)
            
        Returns:
            True si se desactivaron correctamente, False si no
        """
        try:
            with get_db_session() as session:
                query = session.query(PushToken).filter(
                    and_(
                        PushToken.usuario_id == usuario_id,
                        PushToken.es_activo == True
                    )
                )
                
                if plataforma:
                    query = query.filter(PushToken.plataforma == plataforma)
                
                tokens = query.all()
                for token in tokens:
                    token.es_activo = False
                    token.actualizado_en = func.sysutcdatetime()
                
                session.commit()
                logger.info(f"Desactivados {len(tokens)} tokens para usuario {usuario_id}")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error al desactivar tokens del usuario {usuario_id}: {str(e)}")
            return False
    
    @staticmethod
    def validar_token_existe(token: str) -> bool:
        """
        Valida si un token existe y está activo
        
        Args:
            token: Token FCM a validar
            
        Returns:
            True si el token existe y está activo, False si no
        """
        try:
            with get_db_session() as session:
                push_token = session.query(PushToken).filter(
                    and_(
                        PushToken.token == token,
                        PushToken.es_activo == True
                    )
                ).first()
                
                return push_token is not None
                
        except SQLAlchemyError as e:
            logger.error(f"Error al validar token: {str(e)}")
            return False