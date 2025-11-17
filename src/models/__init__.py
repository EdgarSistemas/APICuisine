"""
Models - Modelos declarativos de dominio
Sistema completamente declarativo sin automap para máximo performance
"""

# Base declarativa compartida
from .base import Base, BaseModel, TimestampMixin

# Modelos de autenticación y autorización
from .auth import (
    Usuario, 
    Rol, 
    Modulo,
    PushToken,
    CodigoReset,
    UsuarioRol,
    UsuarioSucursal, 
    RolModulo
)

# Modelos de catálogos
from .catalogos import (
    Sucursal,
    Area,
    Mesa,
    CategoriaMenu,
    Producto,
    Combo,
    ComboProducto,
    ProductoReceta,
    ProductoRecetaItem
)

# Modelos de operaciones
from .operaciones import (
    Pedido,
    PedidoItem,
    PedidoEstadoHist,
    AsignacionMesa
)

# Modelos de inventario
from .inventario import (
    UnidadMedida,
    Insumo,
    Compra,
    CompraDetalle,
    Proveedor,
    Recepcion,
    RecepcionDetalle,
    Lote,
    Movimiento,
    Existencia,
    Merma
)

# Modelos de pagos
from .pagos import (
    Pago
)

# Modelos de configuración
from .config import (
    ConfigSucursal
)

# Modelos de tickets
from .ticket import (
    Ticket
)

# Modelos de servicio
from .servicio import (
    Calificacion,
    Mejora
)

# Modelos de RRHH
from .rrhh import (
    Horario,
    HorarioDetalle,
    UsuarioHorario,
    TurnoClave,
    Asistencia,
    SolicitudVacaciones
)

__all__ = [
    # Base
    'Base',
    'BaseModel', 
    'TimestampMixin',
    
    # Modelos de seguridad
    'Usuario',
    'Rol',
    'Modulo',
    'PushToken',
    'CodigoReset',
    'UsuarioRol',
    'UsuarioSucursal',
    'RolModulo',
    
    # Modelos de catálogos
    'Sucursal',
    'Area',
    'Mesa',
    'CategoriaMenu',
    'Producto',
    'Combo',
    'ComboProducto',
    'ProductoReceta',
    'ProductoRecetaItem',
    
    # Modelos de operaciones
    'Pedido',
    'PedidoItem',
    'PedidoEstadoHist',
    'AsignacionMesa',
    
    # Modelos de inventario
    'UnidadMedida',
    'Insumo',
    'Compra',
    'CompraDetalle',
    'Proveedor',
    'Recepcion',
    'RecepcionDetalle',
    'Lote',
    'Movimiento',
    'Existencia',
    'Merma',
    
    # Modelos de pagos
    'Pago',
    
    # Modelos de configuración
    'ConfigSucursal',
    
    # Modelos de tickets
    'Ticket',
    
    # Modelos de servicio
    'Calificacion',
    'Mejora',
    
    # Modelos de RRHH
    'Horario',
    'HorarioDetalle',
    'UsuarioHorario',
    'TurnoClave',
    'Asistencia',
    'SolicitudVacaciones'
]