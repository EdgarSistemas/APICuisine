"""
ProductoReceta Schemas - Validación y serialización con Marshmallow
"""

from marshmallow import Schema, fields, validate


class ProductoRecetaCreateSchema(Schema):
    """Schema para crear una receta"""
    producto_id = fields.Integer(required=True)
    nombre = fields.String(required=True, validate=validate.Length(min=1, max=120))
    es_activa = fields.Boolean(missing=True)


class ProductoRecetaUpdateSchema(Schema):
    """Schema para actualizar una receta"""
    nombre = fields.String(allow_none=True, validate=validate.Length(min=1, max=120))
    es_activa = fields.Boolean(allow_none=True)


class ProductoRecetaResponseSchema(Schema):
    """Schema para retornar una receta"""
    id_receta = fields.Integer()
    producto_id = fields.Integer()
    nombre = fields.String()
    es_activa = fields.Boolean()
    created_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')
    updated_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S', allow_none=True)


class ProductoRecetaItemCreateSchema(Schema):
    """Schema para agregar un insumo a una receta"""
    insumo_id = fields.Integer(required=True)
    cantidad = fields.Decimal(required=True, places=2)


class ProductoRecetaItemUpdateSchema(Schema):
    """Schema para actualizar cantidad de un insumo en receta"""
    cantidad = fields.Decimal(required=True, places=2)


class ProductoRecetaItemResponseSchema(Schema):
    """Schema para retornar un item de receta"""
    id_receta_item = fields.Integer()
    receta_id = fields.Integer()
    insumo_id = fields.Integer()
    cantidad = fields.Decimal(places=2)
    
    # Nested: datos del insumo
    insumo = fields.Nested(
        lambda: InsumoDetailSchema(),
        only=['id_insumo', 'nombre', 'unidad_id']
    )


class InsumoDetailSchema(Schema):
    """Detail schema para mostrar insumo dentro de item receta"""
    id_insumo = fields.Integer()
    nombre = fields.String()
    unidad_id = fields.Integer()


class ProductoRecetaDetailSchema(Schema):
    """Schema con detalles completos de receta + items"""
    id_receta = fields.Integer()
    producto_id = fields.Integer()
    nombre = fields.String()
    es_activa = fields.Boolean()
    created_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')
    updated_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S', allow_none=True)
    
    # Items de la receta
    items = fields.Nested(ProductoRecetaItemResponseSchema, many=True)
