"""
Models Catalogos - Entidades del esquema catalogos
"""
from .sucursal import Sucursal
from .area_model import Area
from .mesa_model import Mesa
from .categoria_menu_model import CategoriaMenu
from .producto_model import Producto
from .combo_model import Combo
from .combo_producto_model import ComboProducto
from .producto_receta_model import ProductoReceta
from .producto_receta_item_model import ProductoRecetaItem

__all__ = [
    'Sucursal',
    'Area',
    'Mesa',
    'CategoriaMenu',
    'Producto',
    'Combo',
    'ComboProducto',
    'ProductoReceta',
    'ProductoRecetaItem'
]
