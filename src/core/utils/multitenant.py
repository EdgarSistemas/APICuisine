"""
Utilidades Multi-Tenant reutilizables
Usadas en todos los controllers para validación y filtrado
"""

from src.models import Usuario, UsuarioRol, UsuarioSucursal, Sucursal
from src.core.db.session_manager import get_db_session


# ============================================================================
# VALIDACIONES
# ============================================================================

def es_admin(usuario_id: int) -> bool:
    """
    ¿El usuario es admin (rol_id=1)?
    """
    with get_db_session() as session:
        usuario_rol = session.query(UsuarioRol).filter(
            UsuarioRol.usuario_id == usuario_id
        ).first()
        return usuario_rol and usuario_rol.rol_id == 1
    
def es_cliente(usuario_id: int) -> bool:
    """
    ¿El usuario es empleado (rol_id=2)?
    """
    with get_db_session() as session:
        usuario_rol = session.query(UsuarioRol).filter(
            UsuarioRol.usuario_id == usuario_id
        ).first()
        return usuario_rol and usuario_rol.rol_id == 10


def tiene_rol(usuario_id: int, rol_id: int) -> bool:
    """
    ¿El usuario tiene un rol específico?
    
    Args:
        usuario_id: ID del usuario
        rol_id: ID del rol a verificar
        
    Returns:
        True si el usuario tiene ese rol, False si no
    """
    with get_db_session() as session:
        usuario_rol = session.query(UsuarioRol).filter(
            UsuarioRol.usuario_id == usuario_id,
            UsuarioRol.rol_id == rol_id
        ).first()
        return usuario_rol is not None


def obtener_rol_usuario(usuario_id: int) -> int:
    """
    Obtener rol_id del usuario. Retorna None si no existe.
    """
    with get_db_session() as session:
        usuario_rol = session.query(UsuarioRol).filter(
            UsuarioRol.usuario_id == usuario_id
        ).first()
        return usuario_rol.rol_id if usuario_rol else None


def validar_acceso_sucursal(usuario_id: int, sucursal_id: int) -> bool:
    """
    ¿El usuario tiene acceso a esta sucursal?
    - Admin: SÍ (acceso a todas)
    - Cliente: SÍ (pueden ver cualquier sucursal para reservar)
    - Empleado: SÍ si está en UsuarioSucursal
    
    Retorna: True/False
    """
    # Admin siempre tiene acceso
    if es_admin(usuario_id):
        return True
    
    # Cliente siempre tiene acceso (necesita ver sucursales/áreas/mesas para reservar)
    if es_cliente(usuario_id):
        return True
    
    # Empleado: verificar en UsuarioSucursal
    with get_db_session() as session:
        existe = session.query(UsuarioSucursal).filter(
            UsuarioSucursal.usuario_id == usuario_id,
            UsuarioSucursal.sucursal_id == sucursal_id
        ).first()
        return existe is not None


def obtener_sucursales_usuario(usuario_id: int) -> list:
    """
    Obtener lista de IDs de sucursales a las que el usuario tiene acceso.
    - Admin: retorna lista vacía (significa "todas")
    - Empleado: retorna sus sucursales de UsuarioSucursal
    
    Retorna: [sucursal_id1, sucursal_id2, ...]
    """
    # Admin: retorna lista vacía (interpretamos como "todas")
    if es_admin(usuario_id):
        return []
    
    sucursales = []
    # Empleado: obtener sus sucursales
    with get_db_session() as session:
        if es_cliente(usuario_id):
            # listar todas las sucursales para clientes, pero sin que sucursal_id se repita, id's unicos
            sucursales = session.query(UsuarioSucursal.sucursal_id).distinct().all()
        else:
            sucursales = session.query(UsuarioSucursal.sucursal_id).filter(
                UsuarioSucursal.usuario_id == usuario_id
            ).all()
        return [s[0] for s in sucursales]


def validar_sucursal_existe(sucursal_id: int) -> bool:
    """
    ¿La sucursal existe?
    """
    with get_db_session() as session:
        existe = session.query(Sucursal).filter(
            Sucursal.id_sucursal == sucursal_id
        ).first()
        return existe is not None


# ============================================================================
# FILTRADO PARA QUERIES
# ============================================================================

def agregar_filtro_sucursal(query, tabla_model, usuario_id: int):
    """
    Agregar filtro de sucursal a un query.
    
    Si admin: sin filtro (ve todo)
    Si empleado: filtrar por sucursales en UsuarioSucursal
    
    Uso:
        query = session.query(Pedido)
        query = agregar_filtro_sucursal(query, Pedido, usuario_id)
        resultados = query.all()
    """
    # Admin: sin filtro
    if es_admin(usuario_id):
        return query
    
    # Empleado: obtener sucursales y filtrar
    sucursales = obtener_sucursales_usuario(usuario_id)
    if not sucursales:
        # Empleado sin sucursales asignadas = no ve nada
        return query.filter(False)
    
    # Filtrar por sucursal_id
    return query.filter(tabla_model.sucursal_id.in_(sucursales))


# ============================================================================
# VALIDACIONES DE PERMISOS
# ============================================================================

def solo_admin(usuario_id: int) -> bool:
    """
    ¿Es válido que el usuario sea ADMIN?
    Retorna True si es admin, False si no.
    
    Uso en controller:
        if not solo_admin(usuario_id):
            return {"error": "FORBIDDEN"}, 403
    """
    return es_admin(usuario_id)


def validar_pertenencia_sucursal(usuario_id: int, registro_con_sucursal_id) -> bool:
    """
    ¿El usuario tiene acceso al registro?
    
    - Admin: SÍ
    - Empleado: SÍ si registro.sucursal_id en sus sucursales
    
    Uso en controller:
        if not validar_pertenencia_sucursal(usuario_id, pedido):
            return {"error": "FORBIDDEN"}, 403
    """
    # Admin: acceso a todo
    if es_admin(usuario_id):
        return True
    
    # Empleado: verificar que registro pertenece a su sucursal
    return validar_acceso_sucursal(usuario_id, registro_con_sucursal_id.sucursal_id)
