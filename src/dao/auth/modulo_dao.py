"""
Modulo DAO - Acceso a datos de módulos usando modelos declarativos
"""

import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_

from src.core.db.session_manager import get_db_session
from src.models.auth import Modulo, RolModulo, Rol, UsuarioRol

logger = logging.getLogger(__name__)

class ModuloDAO:
    """DAO para operaciones CRUD de módulos usando modelos declarativos"""
    
    def crear_modulo(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear nuevo módulo
        
        Args:
            datos: Diccionario con datos del módulo
            
        Returns:
            Dict con datos del módulo creado
        """
        try:
            with get_db_session() as session:
                modulo = Modulo(**datos)
                session.add(modulo)
                session.commit()
                
                return self._modulo_to_dict(modulo)
                
        except SQLAlchemyError as e:
            logger.error(f"Error al crear módulo: {str(e)}")
            raise RuntimeError(f"Error en base de datos: {str(e)}")
    
    def obtener_por_id(self, modulo_id: int) -> Optional[Dict[str, Any]]:
        """Obtener módulo por ID"""
        try:
            with get_db_session() as session:
                modulo = session.query(Modulo).filter(
                    Modulo.id_modulo == modulo_id
                ).first()
                
                if modulo:
                    return self._modulo_to_dict(modulo)
                return None
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener módulo {modulo_id}: {str(e)}")
            raise RuntimeError(f"Error en base de datos: {str(e)}")
    
    def obtener_por_clave(self, clave: str) -> Optional[Dict[str, Any]]:
        """Obtener módulo por clave"""
        try:
            with get_db_session() as session:
                modulo = session.query(Modulo).filter(
                    Modulo.clave == clave
                ).first()
                
                if modulo:
                    return self._modulo_to_dict(modulo)
                return None
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener módulo por clave {clave}: {str(e)}")
            raise RuntimeError(f"Error en base de datos: {str(e)}")
    
    def listar_modulos(self, filtros: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Listar módulos con filtros opcionales"""
        try:
            with get_db_session() as session:
                query = session.query(Modulo)
                
                if filtros:
                    if 'es_activo' in filtros:
                        query = query.filter(Modulo.es_activo == filtros['es_activo'])
                    if 'requiere_permisos' in filtros:
                        query = query.filter(Modulo.requiere_permisos == filtros['requiere_permisos'])
                
                query = query.order_by(Modulo.orden, Modulo.nombre)
                modulos = query.all()
                return [self._modulo_to_dict(modulo) for modulo in modulos]
                
        except SQLAlchemyError as e:
            logger.error(f"Error al listar módulos: {str(e)}")
            raise RuntimeError(f"Error en base de datos: {str(e)}")
    
    def actualizar_modulo(self, modulo_id: int, datos: Dict[str, Any]) -> Dict[str, Any]:
        """Actualizar módulo existente"""
        try:
            with get_db_session() as session:
                modulo = session.query(Modulo).filter(
                    Modulo.id_modulo == modulo_id
                ).first()
                
                if not modulo:
                    raise ValueError(f"Módulo {modulo_id} no encontrado")
                
                # Actualizar campos del módulo
                for key, value in datos.items():
                    if hasattr(modulo, key):
                        setattr(modulo, key, value)
                
                session.commit()
                return self._modulo_to_dict(modulo)
                
        except SQLAlchemyError as e:
            logger.error(f"Error al actualizar módulo {modulo_id}: {str(e)}")
            raise RuntimeError(f"Error en base de datos: {str(e)}")
    
    def obtener_roles_modulo(self, modulo_id: int) -> List[Dict[str, Any]]:
        """Obtener roles que tienen acceso a un módulo"""
        try:
            with get_db_session() as session:
                rol_modulos = session.query(RolModulo, Rol)\
                    .join(Rol, RolModulo.rol_id == Rol.id_rol)\
                    .filter(
                        and_(
                            RolModulo.modulo_id == modulo_id,
                            RolModulo.habilitado == True
                        )
                    ).all()
                
                resultado = []
                for rol_modulo, rol in rol_modulos:
                    rol_dict = {
                        'id_rol': rol.id_rol,
                        'nombre': rol.nombre,
                        'descripcion': rol.descripcion,
                        'permisos': {
                            'lectura': rol_modulo.lectura,
                            'escritura': rol_modulo.escritura,
                            'eliminacion': rol_modulo.eliminacion,
                            'aprobacion': rol_modulo.aprobacion
                        }
                    }
                    resultado.append(rol_dict)
                
                return resultado
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener roles del módulo {modulo_id}: {str(e)}")
            raise RuntimeError(f"Error en base de datos: {str(e)}")
    
    def eliminar_modulo(self, modulo_id: int) -> bool:
        """Eliminar módulo (soft delete)"""
        try:
            with get_db_session() as session:
                modulo = session.query(Modulo).filter(
                    Modulo.id_modulo == modulo_id
                ).first()
                
                if not modulo:
                    raise ValueError(f"Módulo {modulo_id} no encontrado")
                
                # Soft delete
                modulo.es_activo = False
                session.commit()
                
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error al eliminar módulo {modulo_id}: {str(e)}")
            raise RuntimeError(f"Error en base de datos: {str(e)}")
    
    def obtener_menu_usuario(self, usuario_id: int) -> List[Dict[str, Any]]:
        """Obtener módulos de menú para un usuario específico"""
        try:
            with get_db_session() as session:
                # Query complejo para obtener módulos del usuario a través de sus roles
                modulos = session.query(Modulo)\
                    .join(RolModulo, Modulo.id_modulo == RolModulo.modulo_id)\
                    .join(Rol, RolModulo.rol_id == Rol.id_rol)\
                    .join(UsuarioRol, Rol.id_rol == UsuarioRol.rol_id)\
                    .filter(
                        and_(
                            UsuarioRol.usuario_id == usuario_id,
                            RolModulo.habilitado == True,
                            RolModulo.lectura == True,  # Al menos debe tener lectura
                            Modulo.es_activo == True
                        )
                    )\
                    .distinct()\
                    .order_by(Modulo.orden, Modulo.nombre)\
                    .all()
                
                return [self._modulo_to_dict(modulo) for modulo in modulos]
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener menú del usuario {usuario_id}: {str(e)}")
            raise RuntimeError(f"Error en base de datos: {str(e)}")
    
    def buscar_modulos(self, termino: str, filtros: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Buscar módulos por nombre, descripción o clave"""
        try:
            with get_db_session() as session:
                query = session.query(Modulo).filter(
                    or_(
                        Modulo.nombre.ilike(f'%{termino}%'),
                        Modulo.descripcion.ilike(f'%{termino}%'),
                        Modulo.clave.ilike(f'%{termino}%')
                    )
                )
                
                if filtros:
                    if 'es_activo' in filtros:
                        query = query.filter(Modulo.es_activo == filtros['es_activo'])
                
                modulos = query.order_by(Modulo.orden, Modulo.nombre).all()
                return [self._modulo_to_dict(modulo) for modulo in modulos]
                
        except SQLAlchemyError as e:
            logger.error(f"Error al buscar módulos con término '{termino}': {str(e)}")
            raise RuntimeError(f"Error en base de datos: {str(e)}")
    
    def _modulo_to_dict(self, modulo) -> Dict[str, Any]:
        """Convertir módulo a diccionario"""
        return {
            'id_modulo': modulo.id_modulo,
            'nombre': modulo.nombre,
            'clave': modulo.clave,
            'descripcion': modulo.descripcion,
            'icono': modulo.icono,
            'url': modulo.url,
            'orden': modulo.orden,
            'es_activo': modulo.es_activo,
            'requiere_permisos': modulo.requiere_permisos,
            'created_at': modulo.created_at.isoformat() if modulo.created_at else None,
            'updated_at': modulo.updated_at.isoformat() if modulo.updated_at else None
        }