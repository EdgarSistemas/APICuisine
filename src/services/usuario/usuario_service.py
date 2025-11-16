"""
Servicio de gestión de usuarios
"""

import logging
from typing import Optional, List, Dict, Any
from werkzeug.security import generate_password_hash

from src.dao.auth import UsuarioDAO, RolDAO
from src.services.auth.auth_service import AuthService
from src.services.auditoria.log_service import log_action

logger = logging.getLogger(__name__)

class UsuarioService:
    """Servicio para gestión de usuarios"""
    
    def __init__(self):
        self.usuario_dao = UsuarioDAO()
        self.rol_dao = RolDAO()
    
    def crear_usuario_sistema(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear usuario del sistema (empleado) con validaciones específicas
        
        Args:
            datos: Datos del usuario, debe incluir sucursal_id y rol_id
            
        Returns:
            Dict con datos del usuario creado
        """
        try:
            # Validaciones específicas para usuarios del sistema
            if not datos.get('sucursal_id') and datos.get('rol_id') != 1:
                raise ValueError("Sucursal es requerida para usuarios del sistema")
            
            if not datos.get('rol_id'):
                raise ValueError("Rol es requerido para usuarios del sistema")
            
            # Verificar que el rol existe
            rol = self.rol_dao.obtener_por_id(datos['rol_id'])
            if not rol:
                raise ValueError(f"Rol {datos['rol_id']} no encontrado")
            
            # Validar email único
            if self.usuario_dao.obtener_por_email(datos['email']):
                raise ValueError("El email ya está registrado")
            
            # Configurar como usuario interno (no cliente)
            datos['es_cliente'] = False
            datos['es_activo'] = True
            datos['tipo_acceso'] = 'amb'  # amb = ambiente/sistema
            
            # Hashear password si se proporciona
            if 'password' in datos:
                datos['hash_password'] = generate_password_hash(datos['password'])
                del datos['password']
            
            # Crear usuario
            usuario = self.usuario_dao.crear_usuario(datos)
            
            # Log de creación de usuario del sistema
            log_action('Usuario', 'CREATE_SYSTEM_USER', 
                      entidad_id=str(usuario['id_usuario']),
                      detalle={
                          'email': usuario['email'],
                          'nombre': usuario['nombre'],
                          'tipo': 'empleado_sistema',
                          'sucursal_id': datos.get('sucursal_id'),
                          'rol_id': datos.get('rol_id')
                      })
            
            logger.info(f"Usuario del sistema {usuario['email']} creado exitosamente")
            
            # Obtener usuario completo para la respuesta
            usuario_completo = self.obtener_usuario_por_id(usuario['id_usuario'])
            return self.preparar_respuesta_usuario(usuario_completo)
            
        except Exception as e:
            logger.error(f"Error al crear usuario del sistema: {str(e)}")
            raise
    
    def crear_usuario_cliente(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear usuario cliente con configuración automática
        
        Args:
            datos: Datos básicos del cliente
            
        Returns:
            Dict con datos del usuario creado
        """
        try:
            # Validar email único
            if self.usuario_dao.obtener_por_email(datos['email']):
                raise ValueError("El email ya está registrado")
            
            # Configurar como cliente
            datos['es_cliente'] = True
            datos['es_activo'] = True
            datos['tipo_acceso'] = 'pwa'  # pwa = progressive web app/cliente
            
            # Asignar rol de cliente por defecto
            rol_cliente = self.rol_dao.obtener_por_nombre("Cliente")
            if rol_cliente:
                datos['rol_id'] = rol_cliente['id_rol']
            
            # Los clientes no requieren sucursal específica inicialmente
            # Se puede asignar dinámicamente según el pedido
            
            # Hashear password si se proporciona
            if 'password' in datos:
                datos['hash_password'] = generate_password_hash(datos['password'])
                del datos['password']
            
            # Crear usuario directamente
            try:
                from src.core.db.session_manager import get_db_session
                from src.models.auth.usuario import Usuario
                from src.models.auth import UsuarioRol
                
                with get_db_session() as session:
                    # Crear usuario
                    usuario_data = {k: v for k, v in datos.items() if k != 'rol_id'}
                    usuario = Usuario(**usuario_data)
                    session.add(usuario)
                    session.flush()  # Para obtener el ID
                    
                    # Asignar rol
                    if 'rol_id' in datos:
                        usuario_rol = UsuarioRol(
                            usuario_id=usuario.id_usuario,
                            rol_id=datos['rol_id']
                        )
                        session.add(usuario_rol)
                    
                    session.commit()
                    
                    # Convertir a diccionario para consistencia
                    usuario_dict = {
                        'id_usuario': usuario.id_usuario,
                        'email': usuario.email,
                        'nombre': usuario.nombre,
                        'apellido': usuario.apellido,
                        'telefono': usuario.telefono,
                        'es_activo': usuario.es_activo,
                        'es_cliente': usuario.es_cliente,
                        'acepta_marketing': usuario.acepta_marketing,
                        'tipo_acceso': usuario.tipo_acceso
                    }
                    
            except Exception as db_error:
                logger.error(f"Error en base de datos: {str(db_error)}")
                raise RuntimeError(f"Error en base de datos: {str(db_error)}")
            
            # Log de creación de usuario cliente
            log_action('Usuario', 'CREATE_CLIENT_USER', 
                      entidad_id=str(usuario_dict['id_usuario']),
                      detalle={
                          'email': usuario_dict['email'],
                          'nombre': usuario_dict['nombre'],
                          'tipo': 'cliente',
                          'acepta_marketing': datos.get('acepta_marketing', False)
                      })
            
            logger.info(f"Usuario cliente {usuario_dict['email']} creado exitosamente")
            
            # Generar respuesta directamente sin usar métodos problemáticos
            respuesta = {
                'id_usuario': usuario_dict['id_usuario'],
                'email': usuario_dict['email'],
                'nombre': usuario_dict['nombre'],
                'apellido': usuario_dict.get('apellido') or '',
                'telefono': usuario_dict.get('telefono') or '',
                'es_admin': False,  # Los clientes nunca son admin
                'es_cliente': True,
                'acepta_marketing': usuario_dict.get('acepta_marketing', False),
                'tipo_acceso': usuario_dict.get('tipo_acceso', 'pwa'),
                'roles': [{'id_rol': datos.get('rol_id'), 'nombre': 'Cliente'}],
                'modulos': [],  # Los clientes no tienen módulos específicos
                'sucursales': None  # Los clientes no tienen sucursales asignadas
            }
            
            return respuesta
            
        except Exception as e:
            logger.error(f"Error al crear usuario cliente: {str(e)}")
            raise
    
    def obtener_usuario_por_id(self, usuario_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtener usuario con toda su información relacionada y estructura completa
        
        Args:
            usuario_id: ID del usuario
            
        Returns:
            Dict con datos completos del usuario en formato de respuesta
        """
        try:
            usuario = self.usuario_dao.obtener_por_id(usuario_id)
            if not usuario:
                return None
            
            # Agregar módulos accesibles
            modulos = self.usuario_dao.obtener_modulos_usuario(usuario_id)
            usuario['modulos'] = modulos
            
            return self.preparar_respuesta_usuario(usuario)
            
        except Exception as e:
            logger.error(f"Error al obtener usuario completo {usuario_id}: {str(e)}")
            raise
    
    def listar_usuarios(self, filtros: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Listar usuarios con filtros opcionales y estructura completa
        
        Args:
            filtros: Diccionario con filtros a aplicar
            
        Returns:
            Lista de usuarios con estructura completa
        """
        try:
            usuarios = self.usuario_dao.listar_usuarios(filtros)
            usuarios_respuesta = []
            
            for usuario in usuarios:
                # Agregar módulos para cada usuario
                modulos = self.usuario_dao.obtener_modulos_usuario(usuario['id_usuario'])
                usuario['modulos'] = modulos
                
                # Preparar respuesta completa
                usuario_completo = self.preparar_respuesta_usuario(usuario)
                usuarios_respuesta.append(usuario_completo)
            
            return usuarios_respuesta
            
        except Exception as e:
            logger.error(f"Error al listar usuarios: {str(e)}")
            raise
    
    def listar_usuarios_con_filtro(self, usuario_id: int, roles: List[str]) -> Dict[str, Any]:
        """
        Listar usuarios con filtro según el rol del usuario autenticado
        
        Args:
            usuario_id: ID del usuario autenticado
            roles: Lista de nombres de roles del usuario
            
        Returns:
            Dict con success, usuarios y mensaje
        """
        try:
            # Verificar rol del usuario autenticado
            rol_normalizado = roles[0].upper() if roles else ''
            
            # ADMIN: Todos los usuarios activos
            if 'ADMIN' in rol_normalizado or 'ADMINISTRADOR' in rol_normalizado:
                logger.info(f"ADMIN {usuario_id} listando todos los usuarios")
                usuarios = self.usuario_dao.listar_usuarios({'es_activo': True})
                usuarios_respuesta = self._preparar_usuarios_respuesta(usuarios)
                return {
                    'success': True,
                    'usuarios': usuarios_respuesta,
                    'message': 'Todos los usuarios activos'
                }
            
            # GERENTE: Solo usuarios de su sucursal
            elif 'GERENTE' in rol_normalizado:
                logger.info(f"GERENTE {usuario_id} listando usuarios de su sucursal")
                # Obtener sucursal del gerente
                gerente = self.usuario_dao.obtener_por_id(usuario_id)
                if not gerente:
                    return {
                        'success': False,
                        'usuarios': [],
                        'message': 'Gerente no encontrado'
                    }
                
                # Obtener sucursales asignadas
                sucursales = gerente.get('sucursales', [])
                if not sucursales:
                    logger.warning(f"GERENTE {usuario_id} sin sucursales asignadas")
                    return {
                        'success': False,
                        'usuarios': [],
                        'message': 'Gerente sin sucursales asignadas'
                    }
                
                # Usar la primera sucursal asignada
                sucursal_id = sucursales[0]['id_sucursal']
                logger.info(f"GERENTE {usuario_id} listando usuarios de sucursal {sucursal_id}")
                
                # Listar usuarios de esa sucursal (empleados y clientes activos)
                filtros = {
                    'sucursal_id': sucursal_id,
                    'es_activo': True
                }
                usuarios = self.usuario_dao.listar_usuarios(filtros)
                usuarios_respuesta = self._preparar_usuarios_respuesta(usuarios)
                
                return {
                    'success': True,
                    'usuarios': usuarios_respuesta,
                    'message': f'Usuarios de sucursal {sucursal_id}'
                }
            
            # OTROS ROLES: Acceso denegado
            else:
                logger.warning(f"Usuario {usuario_id} con rol {rol_normalizado} intentó listar usuarios - ACCESO DENEGADO")
                return {
                    'success': False,
                    'usuarios': [],
                    'message': f'Acceso denegado. Solo ADMIN y GERENTE pueden listar usuarios. Rol actual: {rol_normalizado}'
                }
                
        except Exception as e:
            logger.error(f"Error al listar usuarios con filtro: {str(e)}")
            return {
                'success': False,
                'usuarios': [],
                'message': f'Error interno: {str(e)}'
            }
    
    def _preparar_usuarios_respuesta(self, usuarios: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Preparar usuarios para la respuesta (agregar módulos y datos completos)
        
        Args:
            usuarios: Lista de usuarios del DAO
            
        Returns:
            Lista de usuarios preparados para respuesta
        """
        usuarios_respuesta = []
        for usuario in usuarios:
            # Agregar módulos para cada usuario
            modulos = self.usuario_dao.obtener_modulos_usuario(usuario['id_usuario'])
            usuario['modulos'] = modulos
            
            # Preparar respuesta completa
            usuario_completo = self.preparar_respuesta_usuario(usuario)
            usuarios_respuesta.append(usuario_completo)
        
        return usuarios_respuesta
    
    def crear_empleado(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear usuario empleado con rol y sucursal específicos
        
        Args:
            datos: Datos del empleado incluyendo rol_id y sucursal_id
            
        Returns:
            Dict con datos del empleado creado
        """
        try:
            # Validaciones específicas para empleados
            if not datos.get('sucursal_id'):
                raise ValueError("Sucursal es requerida para empleados")
            
            if not datos.get('rol_id'):
                raise ValueError("Rol es requerido para empleados")
            
            # Verificar que el rol existe
            rol = self.rol_dao.obtener_por_id(datos['rol_id'])
            if not rol:
                raise ValueError(f"Rol {datos['rol_id']} no encontrado")
            
            # Si es rol de administrador, asignar todas las sucursales
            if datos['rol_id'] == 1:  # Admin
                # Para admin, ignorar sucursal_id específica ya que tendrá acceso a todas
                datos['sucursal_id'] = None
            
            # Configurar como empleado
            datos['es_cliente'] = False
            datos['es_activo'] = True
            datos['tipo_acceso'] = 'amb'  # amb = ambiente/sistema
            
            # Crear usuario empleado
            usuario = self.crear_usuario_sistema(datos)
            
            # Si es admin, asignar a todas las sucursales
            if datos.get('rol_id') == 1:
                self._asignar_todas_sucursales_admin(usuario['id_usuario'])
            
            # Generar respuesta directamente sin usar métodos problemáticos
            # Obtener nombre del rol
            rol_nombre = "Administrador" if datos.get('rol_id') == 1 else "Empleado"
            es_admin = datos.get('rol_id') == 1
            
            respuesta = {
                'id': usuario['id_usuario'],
                'email': usuario['email'],
                'nombre': usuario['nombre'],
                'apellido': usuario.get('apellido', ''),
                'telefono': usuario.get('telefono', ''),
                'es_admin': es_admin,
                'es_cliente': False,
                'acepta_marketing': usuario.get('acepta_marketing', False),
                'tipo_acceso': usuario.get('tipo_acceso', 'amb'),
                'roles': [{'id_rol': datos.get('rol_id'), 'nombre': rol_nombre}],
                'modulos': [],  # Se cargarían por separado si es necesario
                'sucursales': []  # Se cargarían por separado si es necesario
            }
            
            return respuesta
            
        except Exception as e:
            logger.error(f"Error al crear empleado: {str(e)}")
            raise
    
    def crear_cliente(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear usuario cliente
        
        Args:
            datos: Datos básicos del cliente (sin rol_id ni sucursal_id)
            
        Returns:
            Dict con datos del cliente creado
        """
        try:
            # Configurar como cliente
            datos['es_cliente'] = True
            datos['es_activo'] = True
            datos['tipo_acceso'] = 'pwa'
            
            # Asignar rol de cliente por defecto
            rol_cliente = self.rol_dao.obtener_por_nombre("Cliente")
            if rol_cliente:
                datos['rol_id'] = rol_cliente['id_rol']
            
            # Crear usuario cliente
            usuario = self.crear_usuario_cliente(datos)
            
            # Obtener usuario completo con relaciones
            usuario_completo = self.obtener_usuario_por_id(usuario['id_usuario'])
            
            return usuario_completo
            
        except Exception as e:
            logger.error(f"Error al crear cliente: {str(e)}")
            raise
    
    def _asignar_todas_sucursales_admin(self, usuario_id: int):
        """
        Asignar todas las sucursales activas a un usuario administrador
        
        Args:
            usuario_id: ID del usuario administrador
        """
        try:
            from src.dao.catalogos.sucursal_dao import SucursalDAO
            sucursal_dao = SucursalDAO()
            sucursales = sucursal_dao.obtener_activas()
            
            for sucursal in sucursales:
                self.usuario_dao.asignar_sucursal(usuario_id, sucursal['id_sucursal'])
                
        except Exception as e:
            logger.error(f"Error al asignar sucursales a admin {usuario_id}: {str(e)}")
            raise

    def crear_usuario(self, datos_usuario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear nuevo usuario (método genérico)
        
        Args:
            datos_usuario: Datos del usuario a crear
            
        Returns:
            Usuario creado
        """
        # Determinar tipo de usuario y usar método específico
        if datos_usuario.get('es_cliente', False):
            return self.crear_usuario_cliente(datos_usuario)
        else:
            return self.crear_usuario_sistema(datos_usuario)
    
    def actualizar_usuario(self, usuario_id: int, datos_usuario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualizar datos de usuario con validaciones
        
        Args:
            usuario_id: ID del usuario a actualizar
            datos_usuario: Datos a actualizar
            
        Returns:
            Dict con datos del usuario actualizado
        """
        try:
            # Verificar que el usuario existe
            usuario_actual = self.usuario_dao.obtener_por_id(usuario_id)
            if not usuario_actual:
                raise ValueError(f"Usuario {usuario_id} no encontrado")
            
            # Si se cambia email, verificar que sea único
            if 'email' in datos_usuario and datos_usuario['email'] != usuario_actual['email']:
                if self.usuario_dao.obtener_por_email(datos_usuario['email']):
                    raise ValueError("El email ya está registrado")
            
            # Hashear password si se proporciona
            if 'password' in datos_usuario:
                datos_usuario['hash_password'] = generate_password_hash(datos_usuario['password'])
                del datos_usuario['password']
            
            # Actualizar usuario
            usuario = self.usuario_dao.actualizar_usuario(usuario_id, datos_usuario)
            
            # Log de actualización de usuario
            log_action('Usuario', 'UPDATE', 
                      entidad_id=str(usuario_id),
                      detalle={
                          'email_anterior': usuario_actual['email'],
                          'email_nuevo': usuario.get('email', usuario_actual['email']),
                          'campos_modificados': list(datos_usuario.keys())
                      })
            
            logger.info(f"Usuario {usuario_id} actualizado exitosamente")
            return usuario
            
        except Exception as e:
            logger.error(f"Error al actualizar usuario {usuario_id}: {str(e)}")
            raise
    
    def eliminar_usuario(self, usuario_id: int) -> bool:
        """
        Desactivar usuario (eliminación lógica)
        
        Args:
            usuario_id: ID del usuario a eliminar
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            usuario = self.usuario_dao.actualizar_usuario(usuario_id, {'es_activo': False})
            logger.info(f"Usuario {usuario_id} desactivado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error al eliminar usuario {usuario_id}: {str(e)}")
            return False
    
    def listar_usuarios_sucursal(self, sucursal_id: int, incluir_clientes: bool = False) -> List[Dict[str, Any]]:
        """
        Listar usuarios de una sucursal específica
        
        Args:
            sucursal_id: ID de la sucursal
            incluir_clientes: Si incluir usuarios cliente
            
        Returns:
            Lista de usuarios
        """
        try:
            filtros = {
                'sucursal_id': sucursal_id,
                'es_activo': True
            }
            
            if not incluir_clientes:
                filtros['es_cliente'] = False
            
            usuarios = self.usuario_dao.listar_usuarios(filtros)
            return usuarios
            
        except Exception as e:
            logger.error(f"Error al listar usuarios de sucursal {sucursal_id}: {str(e)}")
            raise
    
    def activar_desactivar_usuario(self, usuario_id: int, es_activo: bool) -> Dict[str, Any]:
        """
        Activar o desactivar usuario
        
        Args:
            usuario_id: ID del usuario
            es_activo: Estado deseado
            
        Returns:
            Dict con datos del usuario actualizado
        """
        try:
            usuario = self.usuario_dao.actualizar_usuario(usuario_id, {'es_activo': es_activo})
            
            # Log de activación/desactivación
            accion = 'ACTIVATE' if es_activo else 'DEACTIVATE'
            log_action('Usuario', accion, 
                      entidad_id=str(usuario_id),
                      detalle={
                          'estado_anterior': not es_activo,
                          'estado_nuevo': es_activo,
                          'email': usuario.get('email', '')
                      })
            
            estado = "activado" if es_activo else "desactivado"
            logger.info(f"Usuario {usuario_id} {estado} exitosamente")
            return usuario
            
        except Exception as e:
            logger.error(f"Error al {'activar' if es_activo else 'desactivar'} usuario {usuario_id}: {str(e)}")
            raise
    
    def preparar_respuesta_usuario(self, usuario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preparar respuesta completa del usuario con la misma estructura que el login
        
        Args:
            usuario: Datos del usuario
            
        Returns:
            Dict con datos del usuario para la respuesta
        """
        es_admin = self._es_administrador(usuario)
        
        # Obtener sucursales según el tipo de usuario
        sucursales = None
        if es_admin:
            # Admin ve todas las sucursales activas
            from src.dao.catalogos.sucursal_dao import SucursalDAO
            sucursal_dao = SucursalDAO()
            sucursales = sucursal_dao.obtener_activas()
        elif not usuario.get('es_cliente', False):
            # Empleado ve solo su sucursal asignada
            sucursales_asignadas = usuario.get('sucursales', [])
            if sucursales_asignadas:
                from src.dao.catalogos.sucursal_dao import SucursalDAO
                sucursal_dao = SucursalDAO()
                sucursal_id = sucursales_asignadas[0].get('sucursal_id')
                if sucursal_id:
                    sucursal = sucursal_dao.obtener_por_id(sucursal_id)
                    sucursales = [sucursal] if sucursal else []
        # Cliente: sucursales = None (por defecto)
        
        return {
            'id_usuario': usuario['id_usuario'],
            'email': usuario['email'],
            'nombre': usuario['nombre'],
            'apellido': usuario.get('apellido', ''),
            'telefono': usuario.get('telefono', ''),
            'es_admin': es_admin,
            'es_cliente': usuario.get('es_cliente', False),
            'acepta_marketing': usuario.get('acepta_marketing', False),
            'tipo_acceso': usuario.get('tipo_acceso', ''),
            'mostrar_empresas': es_admin,
            'roles': usuario.get('roles', []),
            'created_at': usuario.get('created_at', None),
            'updated_at': usuario.get('updated_at', None),
            'modulos': usuario.get('modulos', []),
            'sucursales': sucursales
        }
    
    def _es_administrador(self, usuario: Dict[str, Any]) -> bool:
        """
        Determinar si un usuario es administrador basado en rol_id = 1
        
        Args:
            usuario: Datos del usuario con roles
            
        Returns:
            True si es administrador, False si no
        """
        roles = usuario.get('roles', [])
        return any(rol.get('id_rol') == 1 for rol in roles)

    def buscar_usuarios(self, termino: str, sucursal_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Buscar usuarios por nombre, apellido o email
        
        Args:
            termino: Término de búsqueda
            sucursal_id: Filtrar por sucursal específica
            
        Returns:
            Lista de usuarios que coinciden
        """
        try:
            filtros = {'es_activo': True}
            if sucursal_id:
                filtros['sucursal_id'] = sucursal_id
            
            usuarios = self.usuario_dao.listar_usuarios(filtros)
            
            # Filtrar por término de búsqueda
            termino_lower = termino.lower()
            usuarios_filtrados = []
            
            for usuario in usuarios:
                if (termino_lower in usuario.get('nombre', '').lower() or
                    termino_lower in usuario.get('apellido', '').lower() or
                    termino_lower in usuario.get('email', '').lower()):
                    usuarios_filtrados.append(usuario)
            
            return usuarios_filtrados
            
        except Exception as e:
            logger.error(f"Error al buscar usuarios con término '{termino}': {str(e)}")
            raise