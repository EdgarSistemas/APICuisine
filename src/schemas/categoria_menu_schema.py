"""
CategoriaMenu Schema - Validación y serialización
"""

from marshmallow import Schema, fields, validate


class CategoriaMenuCreateSchema(Schema):
    """Schema para crear categoría"""
    nombre = fields.Str(required=True, validate=validate.Length(min=1, max=30))
    descripcion = fields.Str(required=False, validate=validate.Length(max=100))

    class Meta:
        strict = True


class CategoriaMenuUpdateSchema(Schema):
    """Schema para actualizar categoría"""
    nombre = fields.Str(required=False, validate=validate.Length(min=1, max=30))
    descripcion = fields.Str(required=False, validate=validate.Length(max=100))

    class Meta:
        strict = True


class CategoriaMenuResponseSchema(Schema):
    """Schema para respuestas de categoría"""
    id_categoria = fields.Int()
    nombre = fields.Str()
    descripcion = fields.Str(allow_none=True)
    es_activa = fields.Bool()
    created_at = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')
    updated_at = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')

    class Meta:
        strict = True
