"""
Combo Schema - Validación y serialización
"""

from marshmallow import Schema, fields, validate


class ComboCreateSchema(Schema):
    """Schema para crear combo con productos"""
    nombre = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    precio = fields.Decimal(required=True, places=2, validate=validate.Range(min=0))
    categoria_id = fields.Int(required=True, validate=validate.Range(min=1))
    descripcion = fields.Str(required=False, validate=validate.Length(max=100))
    imagen_url = fields.Str(required=False)
    productos = fields.List(
        fields.Dict(
            keys=fields.Str(),
            values=fields.Field()
        ),
        required=False
    )  # Lista de {producto_id, cantidad}

    class Meta:
        strict = True


class ComboUpdateSchema(Schema):
    """Schema para actualizar combo"""
    nombre = fields.Str(required=False, validate=validate.Length(min=1, max=50))
    descripcion = fields.Str(required=False, validate=validate.Length(max=100))
    imagen_url = fields.Str(required=False)
    precio = fields.Decimal(required=False, places=2, validate=validate.Range(min=0))

    class Meta:
        strict = True


class ProductoSimpleSchema(Schema):
    """Schema simple para Producto (en combo)"""
    id_producto = fields.Int()
    codigo = fields.Str(allow_none=True)
    nombre = fields.Str()
    descripcion = fields.Str(allow_none=True)
    imagen_url = fields.Str(allow_none=True)
    precio = fields.Decimal(places=2)
    
    class Meta:
        strict = True


class ComboProductoDetailSchema(Schema):
    """Schema para combo-producto con datos de producto"""
    id_combo_producto = fields.Int()
    producto_id = fields.Int()
    cantidad = fields.Int()
    producto = fields.Nested(ProductoSimpleSchema)
    
    class Meta:
        strict = True


class ComboResponseSchema(Schema):
    """Schema para respuestas de combo (listar)"""
    id_combo = fields.Int()
    nombre = fields.Str()
    descripcion = fields.Str(allow_none=True)
    imagen_url = fields.Str(allow_none=True)
    precio = fields.Decimal(places=2)
    es_activo = fields.Bool()
    created_at = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')
    updated_at = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')

    class Meta:
        strict = True


class ComboDetailedSchema(Schema):
    """Schema para GET combo by ID con productos completos"""
    id_combo = fields.Int()
    nombre = fields.Str()
    descripcion = fields.Str(allow_none=True)
    imagen_url = fields.Str(allow_none=True)
    precio = fields.Decimal(places=2)
    productos = fields.List(fields.Nested(ComboProductoDetailSchema))
    es_activo = fields.Bool()
    created_at = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')
    updated_at = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')

    class Meta:
        strict = True


class ComboCreateSchema(Schema):
    """Schema para crear combo con productos"""
    nombre = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    precio = fields.Decimal(required=True, places=2, validate=validate.Range(min=0))
    categoria_id = fields.Int(required=True, validate=validate.Range(min=1))
    descripcion = fields.Str(required=False, validate=validate.Length(max=100))
    imagen_url = fields.Str(required=False)
    productos = fields.List(
        fields.Dict(
            keys=fields.Str(),
            values=fields.Field()
        ),
        required=False
    )  # Lista de {producto_id, cantidad}

    class Meta:
        strict = True


class ComboUpdateSchema(Schema):
    """Schema para actualizar combo"""
    nombre = fields.Str(required=False, validate=validate.Length(min=1, max=50))
    descripcion = fields.Str(required=False, validate=validate.Length(max=100))
    imagen_url = fields.Str(required=False)
    precio = fields.Decimal(required=False, places=2, validate=validate.Range(min=0))

    class Meta:
        strict = True


class ComboProductoCreateSchema(Schema):
    """Schema para agregar producto a combo"""
    producto_id = fields.Int(required=True, validate=validate.Range(min=1))
    cantidad = fields.Int(required=False, validate=validate.Range(min=1), missing=1)

    class Meta:
        strict = True


class ComboProductoResponseSchema(Schema):
    """Schema para respuestas de combo-producto"""
    id_combo_producto = fields.Int()
    combo_id = fields.Int()
    producto_id = fields.Int()
    cantidad = fields.Int()
    created_at = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')
    updated_at = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')

    class Meta:
        strict = True
