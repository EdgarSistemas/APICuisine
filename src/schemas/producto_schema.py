"""
Producto Schema - Validación y serialización
"""

from marshmallow import Schema, fields, validate


class ProductoCreateSchema(Schema):
    """Schema para crear producto con receta"""
    categoria_id = fields.Int(required=True, validate=validate.Range(min=1))
    codigo = fields.Str(required=False, validate=validate.Length(max=20))
    nombre = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    descripcion = fields.Str(required=False, validate=validate.Length(max=100))
    imagen_url = fields.Str(required=False)
    precio = fields.Decimal(required=True, places=2, validate=validate.Range(min=0))
    receta_items = fields.List(
        fields.Dict(
            keys=fields.Str(),
            values=fields.Field()
        ),
        required=False
    )  # Lista de {insumo_id, cantidad}

    class Meta:
        strict = True


class ProductoUpdateSchema(Schema):
    """Schema para actualizar producto"""
    nombre = fields.Str(required=False, validate=validate.Length(min=1, max=50))
    descripcion = fields.Str(required=False, validate=validate.Length(max=100))
    imagen_url = fields.Str(required=False)
    precio = fields.Decimal(required=False, places=2, validate=validate.Range(min=0))
    receta_items = fields.List(
        fields.Dict(
            keys=fields.Str(),
            values=fields.Field()
        ),
        required=False
    )  # Lista de {id_receta_item, cantidad} para actualizar cantidades

    class Meta:
        strict = True


class UnidadMedidaNestedSchema(Schema):
    """Schema anidado para UnidadMedida"""
    id_unidad_medida = fields.Int()
    clave = fields.Str()
    nombre = fields.Str()
    simbolo = fields.Str()
    
    class Meta:
        strict = True


class InsumoSimpleSchema(Schema):
    """Schema simple para Insumo (en receta items)"""
    id_insumo = fields.Int()
    nombre = fields.Str()
    unidad_medida = fields.Nested(UnidadMedidaNestedSchema)
    
    class Meta:
        strict = True


class ProductoRecetaItemSchema(Schema):
    """Schema para items de receta con insumo completo"""
    id_receta_item = fields.Int()
    insumo_id = fields.Int()
    cantidad = fields.Decimal(places=2)
    insumo = fields.Nested(InsumoSimpleSchema)
    
    class Meta:
        strict = True


class ProductoRecetaSchema(Schema):
    """Schema para receta de producto con items"""
    id_receta = fields.Int()
    nombre = fields.Str()
    items = fields.List(fields.Nested(ProductoRecetaItemSchema))
    
    class Meta:
        strict = True


class CategoriaMenuNestedSchema(Schema):
    """Schema anidado para CategoriaMenu"""
    id_categoria = fields.Int()
    nombre = fields.Str()
    descripcion = fields.Str(allow_none=True)
    
    class Meta:
        strict = True


class ProductoResponseSchema(Schema):
    """Schema para respuestas de producto (listar)"""
    id_producto = fields.Int()
    categoria_id = fields.Int()
    codigo = fields.Str(allow_none=True)
    nombre = fields.Str()
    descripcion = fields.Str(allow_none=True)
    imagen_url = fields.Str(allow_none=True)
    precio = fields.Decimal(places=2)
    es_activo = fields.Bool()
    created_at = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')
    updated_at = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')

    class Meta:
        strict = True


class ProductoDetailedSchema(Schema):
    """Schema para GET producto by ID con datos completos"""
    id_producto = fields.Int()
    codigo = fields.Str(allow_none=True)
    nombre = fields.Str()
    descripcion = fields.Str(allow_none=True)
    imagen_url = fields.Str(allow_none=True)
    precio = fields.Decimal(places=2)
    categoria = fields.Nested(CategoriaMenuNestedSchema)
    receta = fields.Nested(ProductoRecetaSchema, allow_none=True)
    es_activo = fields.Bool()
    created_at = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')
    updated_at = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')

    class Meta:
        strict = True
