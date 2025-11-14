"""
Rol DAO - Acceso a datos de roles usando modelos declarativos
"""

import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_

from src.core.db.session_manager import get_db_session
from src.models.auth import Rol, RolModulo, UsuarioRol, Modulo

logger = logging.getLogger(__name__)

class RolDAO:
    """DAO para operaciones CRUD de roles usando modelos declarativos"""
    
    def crear_rol(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear nuevo rol
        
        Args:
            datos: Diccionario con datos del rol
            
        Returns:
            Dict con datos del rol creado
        """
        try:
            with get_db_session() as session:
                rol = Rol(**datos)
                session.add(rol)
                session.commit()
                
                return self._rol_to_dict(rol)
                
        except SQLAlchemyError as e:
            logger.error(f"Error al crear rol: {str(e)}")
            raise RuntimeError(f"Error en base de datos: {str(e)}")
    
    def obtener_por_id(self, rol_id: int) -> Optional[Dict[str, Any]]:
        """Obtener rol por ID"""
        try:
            with get_db_session() as session:
                rol = session.query(Rol).filter(
                    Rol.id_rol == rol_id
                ).first()
                
                if rol:
                    return self._rol_to_dict(rol)
                return None
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener rol {rol_id}: {str(e)}")
            raise RuntimeError(f"Error en base de datos: {str(e)}")
    
    def obtener_por_nombre(self, nombre: str) -> Optional[Dict[str, Any]]:
        """Obtener rol por nombre"""
        try:
            with get_db_session() as session:
                rol = session.query(Rol).filter(
                    Rol.nombre == nombre
                ).first()
                
                if rol:
                    return self._rol_to_dict(rol)
                return None
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener rol por nombre {nombre}: {str(e)}")
            raise RuntimeError(f"Error en base de datos: {str(e)}")
    
    def listar_roles(self, filtros: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Listar roles con filtros opcionales"""
        try:
            with get_db_session() as session:
                query = session.query(Rol)
                
                if filtros:
                    # Los roles no tienen campo es_activo, solo filtrar por nombre si es necesario
                    if 'nombre' in filtros:
                        query = query.filter(Rol.nombre.ilike(f"%{filtros['nombre']}%"))
                
                roles = query.all()
                return [self._rol_to_dict(rol) for rol in roles]
                
        except SQLAlchemyError as e:
            logger.error(f"Error al listar roles: {str(e)}")
            raise RuntimeError(f"Error en base de datos: {str(e)}")
    
    def actualizar_rol(self, rol_id: int, datos: Dict[str, Any]) -> Dict[str, Any]:
        """Actualizar rol existente"""
        try:
            with get_db_session() as session:
                rol = session.query(Rol).filter(
                    Rol.id_rol == rol_id
                ).first()
                
                if not rol:
                    raise ValueError(f"Rol {rol_id} no encontrado")
                
                # Actualizar campos del rol
                for key, value in datos.items():
                    if hasattr(rol, key):
                        setattr(rol, key, value)
                
                session.commit()
                return self._rol_to_dict(rol)
                
        except SQLAlchemyError as e:
            logger.error(f"Error al actualizar rol {rol_id}: {str(e)}")
            raise RuntimeError(f"Error en base de datos: {str(e)}")
    
    def asignar_modulo(self, rol_id: int, modulo_id: int, permisos: Dict[str, bool]) -> bool:
        """Asignar módulo a rol con permisos específicos"""
        try:
            with get_db_session() as session:
                # Verificar si ya existe la asignación
                existente = session.query(RolModulo).filter(
                    and_(
                        RolModulo.rol_id == rol_id,
                        RolModulo.modulo_id == modulo_id
                    )
                ).first()
                
                if existente:
                    # Actualizar permisos existentes
                    for permiso, valor in permisos.items():
                        if hasattr(existente, permiso):
                            setattr(existente, permiso, valor)
                else:
                    # Crear nueva asignación
                    rol_modulo = RolModulo(
                        rol_id=rol_id,
                        modulo_id=modulo_id,
                        **permisos
                    )
                    session.add(rol_modulo)
                
                session.commit()
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error al asignar módulo {modulo_id} a rol {rol_id}: {str(e)}")
            raise RuntimeError(f"Error en base de datos: {str(e)}")
    
    def obtener_modulos_rol(self, rol_id: int) -> List[Dict[str, Any]]:
        """Obtener módulos asignados a un rol con sus permisos"""
        try:
            with get_db_session() as session:
                rol_modulos = session.query(RolModulo, Modulo)\
                    .join(Modulo, RolModulo.modulo_id == Modulo.id_modulo)\
                    .filter(RolModulo.rol_id == rol_id)\
                    .all()
                
                resultado = []
                for rol_modulo, modulo in rol_modulos:
                    modulo_dict = {
                        'id_modulo': modulo.id_modulo,
                        'nombre': modulo.nombre,
                        'clave': modulo.clave,
                        'descripcion': modulo.descripcion,
                        'permisos': {
                            'habilitado': rol_modulo.habilitado,
                            'lectura': rol_modulo.lectura,
                            'escritura': rol_modulo.escritura,
                            'eliminacion': rol_modulo.eliminacion,
                            'aprobacion': rol_modulo.aprobacion
                        }
                    }
                    resultado.append(modulo_dict)
                
                return resultado
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener módulos del rol {rol_id}: {str(e)}")
            raise RuntimeError(f"Error en base de datos: {str(e)}")
    
    def listar_roles_con_modulos_y_usuarios(self, search: str = '') -> List[Dict[str, Any]]:
        """Listar roles con sus módulos y conteo de usuarios asignados"""
        try:
            with get_db_session() as session:
                query = session.query(Rol)
                
                # Aplicar filtro de búsqueda
                if search:
                    query = query.filter(
                        (Rol.nombre.contains(search)) |
                        (Rol.descripcion.contains(search))
                    )
                
                roles = query.order_by(Rol.nombre).all()
                
                roles_data = []
                for rol in roles:
                    # Obtener módulos del rol
                    modulos = session.query(Modulo)\
                        .join(RolModulo, Modulo.id_modulo == RolModulo.modulo_id)\
                        .filter(
                            RolModulo.rol_id == rol.id_rol,
                            RolModulo.habilitado == True
                        )\
                        .order_by(Modulo.nombre)\
                        .all()
                    
                    modulos_data = []
                    for modulo in modulos:
                        modulos_data.append({
                            'id_modulo': modulo.id_modulo,
                            'nombre': modulo.nombre,
                            'clave': modulo.clave,
                            'descripcion': modulo.descripcion
                        })
                    
                    # Contar usuarios asignados a este rol
                    count_usuarios = session.query(UsuarioRol)\
                        .filter(UsuarioRol.rol_id == rol.id_rol)\
                        .count()
                    
                    rol_dict = {
                        'id_rol': rol.id_rol,
                        'nombre': rol.nombre,
                        'descripcion': rol.descripcion,
                        'modulos': modulos_data,
                        'usuarios_asignados': count_usuarios
                    }
                    roles_data.append(rol_dict)
                
                return roles_data
                
        except SQLAlchemyError as e:
            logger.error(f"Error al listar roles con módulos: {str(e)}")
            raise RuntimeError(f"Error en base de datos: {str(e)}")
    
    def _rol_to_dict(self, rol) -> Dict[str, Any]:
        """Convertir rol a diccionario"""
        return {
            'id_rol': rol.id_rol,
            'nombre': rol.nombre,
            'descripcion': rol.descripcion
        }