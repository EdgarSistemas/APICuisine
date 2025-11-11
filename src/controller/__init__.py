"""
Controllers - Controladores con Flask Blueprints
Contiene los controladores que manejan las peticiones HTTP y respuestas de la API.
"""

from .AuthController import auth_bp
from .UsuarioController import usuario_bp
from .RolController import roles_bp
from .PedidoController import bp as pedidos_bp
from .CompraController import bp as compras_bp
from .MesaController import bp as mesas_bp
from .PagoController import bp as pagos_bp
from .UnidadMedidaController import bp as unidades_bp
from .InsumoController import bp as insumos_bp
from .CategoriaMenuController import bp as categorias_bp
from .ProductoController import bp as productos_bp
from .ComboController import bp as combos_bp
from .ProductoRecetaController import bp as recetas_bp

__all__ = [
    'auth_bp',
    'usuario_bp',
    'roles_bp',
    'pedidos_bp',
    'compras_bp',
    'mesas_bp',
    'pagos_bp',
    'unidades_bp',
    'insumos_bp',
    'categorias_bp',
    'productos_bp',
    'combos_bp',
    'recetas_bp'
]