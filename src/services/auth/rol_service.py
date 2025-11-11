"""
Servicio para gestión de roles y permisos
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.core.db.session_manager import get_db_session
from src.models.auth import Rol, Usuario, UsuarioRol, RolModulo, Modulo
from src.services.auditoria.log_service import log_action

logger = logging.getLogger(__name__)


class RolService:
    """Servicio para gestión de roles y permisos"""
    
    def crear_rol(self, datos_rol: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear un nuevo rol
        
        Args:
            datos_rol: Diccionario con datos del rol
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            with get_db_session() as session:
                # Verificar si ya existe un rol con ese nombre
                rol_existente = session.query(Rol).filter(
                    Rol.nombre == datos_rol['nombre']
                ).first()
                
                if rol_existente:
                    return {
                        'success': False,
                        'error': 'ROL_EXISTS',
                        'message': f'Ya existe un rol con el nombre "{datos_rol["nombre"]}"'
                    }
                
                # Crear nuevo rol
                nuevo_rol = Rol(
                    nombre=datos_rol['nombre'],
                    descripcion=datos_rol.get('descripcion', '')
                )
                session.add(nuevo_rol)
                session.flush()  # Para obtener el id_rol

                # Asignar módulos si vienen en la petición
                modulos_ids = datos_rol.get('modulos', [])
                for id_modulo in modulos_ids:
                    modulo = session.query(Modulo).filter(Modulo.id_modulo == id_modulo).first()
                    if modulo:
                        rol_modulo = RolModulo(rol_id=nuevo_rol.id_rol, modulo_id=id_modulo, plataforma=3)
                        session.add(rol_modulo)

                session.commit()

                # Log de creación de rol
                log_action('Rol', 'CREATE', 
                          entidad_id=str(nuevo_rol.id_rol),
                          detalle={
                              'nombre': nuevo_rol.nombre,
                              'descripcion': nuevo_rol.descripcion,
                              'modulos': modulos_ids
                          })

                logger.info(f"Rol creado exitosamente: {nuevo_rol.nombre}")

                return {
                    'success': True,
                    'message': 'Rol creado exitosamente',
                    'data': {
                        'id_rol': nuevo_rol.id_rol,
                        'nombre': nuevo_rol.nombre,
                        'descripcion': nuevo_rol.descripcion,
                        'modulos_asignados': modulos_ids
                    }
                }
                
        except Exception as e:
            logger.error(f"Error al crear rol: {str(e)}")
            return {
                'success': False,
                'error': 'CREATE_ROL_ERROR',
                'message': 'Error al crear rol',
                'details': str(e)
            }
    
    def listar_roles(self, search: str = '') -> Dict[str, Any]:
        """
        Listar roles con búsqueda opcional
        
        Args:
            search: Término de búsqueda
            
        Returns:
            Dict con lista de roles
        """
        try:
            with get_db_session() as session:
                query = session.query(Rol)
                
                # Aplicar filtro de búsqueda
                if search:
                    query = query.filter(
                        Rol.nombre.contains(search) |
                        Rol.descripcion.contains(search)
                    )
                
                # Obtener todos los roles
                roles = query.order_by(Rol.nombre).all()
                
                # Convertir a diccionarios
                roles_data = []
                for rol in roles:
                    rol_dict = {
                        'id_rol': rol.id_rol,
                        'nombre': rol.nombre,
                        'descripcion': rol.descripcion
                    }
                    roles_data.append(rol_dict)
                
                return {
                    'success': True,
                    'data': roles_data
                }
                
        except Exception as e:
            logger.error(f"Error al listar roles: {str(e)}")
            return {
                'success': False,
                'error': 'LIST_ROLES_ERROR',
                'message': 'Error al listar roles',
                'details': str(e)
            }
    
    def obtener_rol(self, id_rol: int) -> Dict[str, Any]:
        """
        Obtener un rol por ID
        
        Args:
            id_rol: ID del rol
            
        Returns:
            Dict con datos del rol
        """
        try:
            with get_db_session() as session:
                rol = session.query(Rol).filter(Rol.id_rol == id_rol).first()
                
                if not rol:
                    return {
                        'success': False,
                        'error': 'ROL_NOT_FOUND',
                        'message': f'Rol con ID {id_rol} no encontrado'
                    }
                
                # Obtener módulos asociados al rol
                modulos = session.query(Modulo).join(RolModulo).filter(
                    RolModulo.rol_id == id_rol
                ).all()
                
                modulos_data = []
                for modulo in modulos:
                    modulos_data.append({
                        'id_modulo': modulo.id_modulo,
                        'nombre': modulo.nombre,
                        'descripcion': modulo.descripcion
                    })
                
                rol_data = {
                    'id_rol': rol.id_rol,
                    'nombre': rol.nombre,
                    'descripcion': rol.descripcion,
                    'modulos': modulos_data
                }
                
                return {
                    'success': True,
                    'data': rol_data
                }
                
        except Exception as e:
            logger.error(f"Error al obtener rol: {str(e)}")
            return {
                'success': False,
                'error': 'GET_ROL_ERROR',
                'message': 'Error al obtener rol',
                'details': str(e)
            }
    
    def actualizar_rol(self, id_rol: int, datos_rol: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualizar un rol existente
        
        Args:
            id_rol: ID del rol a actualizar
            datos_rol: Diccionario con nuevos datos del rol
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            with get_db_session() as session:
                rol = session.query(Rol).filter(Rol.id_rol == id_rol).first()
                
                if not rol:
                    return {
                        'success': False,
                        'error': 'ROL_NOT_FOUND',
                        'message': f'Rol con ID {id_rol} no encontrado'
                    }
                
                # Verificar nombre único (si se está cambiando)
                if 'nombre' in datos_rol and datos_rol['nombre'] != rol.nombre:
                    rol_existente = session.query(Rol).filter(
                        Rol.nombre == datos_rol['nombre'],
                        Rol.id_rol != id_rol
                    ).first()
                    
                    if rol_existente:
                        return {
                            'success': False,
                            'error': 'ROL_NAME_EXISTS',
                            'message': f'Ya existe otro rol con el nombre "{datos_rol["nombre"]}"'
                        }
                
                # Actualizar campos
                if 'nombre' in datos_rol:
                    rol.nombre = datos_rol['nombre']
                if 'descripcion' in datos_rol:
                    rol.descripcion = datos_rol['descripcion']
                # Actualizar módulos si vienen en la petición
                if 'modulos' in datos_rol:
                    session.query(RolModulo).filter(RolModulo.rol_id == id_rol).delete()
                    for id_modulo in datos_rol['modulos']:
                        modulo = session.query(Modulo).filter(Modulo.id_modulo == id_modulo).first()
                        if modulo:
                            rol_modulo = RolModulo(rol_id=id_rol, modulo_id=id_modulo, plataforma=3)
                            session.add(rol_modulo)
                rol.updated_at = datetime.utcnow()
                session.commit()
                logger.info(f"Rol actualizado exitosamente: {rol.nombre}")
                return {
                    'success': True,
                    'message': 'Rol actualizado exitosamente',
                    'data': {
                        'id_rol': rol.id_rol,
                        'nombre': rol.nombre,
                        'descripcion': rol.descripcion
                    }
                }
                
        except Exception as e:
            logger.error(f"Error al actualizar rol: {str(e)}")
            return {
                'success': False,
                'error': 'UPDATE_ROL_ERROR',
                'message': 'Error al actualizar rol',
                'details': str(e)
            }
    
    def asignar_modulos(self, id_rol: int, modulos_ids: List[int]) -> Dict[str, Any]:
        """
        Asignar módulos a un rol
        
        Args:
            id_rol: ID del rol
            modulos_ids: Lista de IDs de módulos a asignar
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            with get_db_session() as session:
                rol = session.query(Rol).filter(Rol.id_rol == id_rol).first()
                
                if not rol:
                    return {
                        'success': False,
                        'error': 'ROL_NOT_FOUND',
                        'message': f'Rol con ID {id_rol} no encontrado'
                    }
                
                # Eliminar asignaciones existentes
                session.query(RolModulo).filter(RolModulo.rol_id == id_rol).delete()
                
                # Crear nuevas asignaciones
                for id_modulo in modulos_ids:
                    # Verificar que el módulo existe
                    modulo = session.query(Modulo).filter(Modulo.id_modulo == id_modulo).first()
                    if modulo:
                        rol_modulo = RolModulo(rol_id=id_rol, modulo_id=id_modulo, plataforma=3)
                        session.add(rol_modulo)
                
                session.commit()
                
                logger.info(f"Módulos asignados al rol {rol.nombre}: {modulos_ids}")
                
                return {
                    'success': True,
                    'message': f'Módulos asignados exitosamente al rol {rol.nombre}',
                    'data': {
                        'id_rol': id_rol,
                        'modulos_asignados': modulos_ids
                    }
                }
                
        except Exception as e:
            logger.error(f"Error al asignar módulos: {str(e)}")
            return {
                'success': False,
                'error': 'ASSIGN_MODULES_ERROR',
                'message': 'Error al asignar módulos',
                'details': str(e)
            }