"""
Proveedor Schema - Validación y serialización
"""

from marshmallow import Schema, fields, validate


class ProveedorCreateSchema(Schema):
    """Schema para crear proveedor"""
    nombre = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    telefono = fields.Str(required=False, validate=validate.Length(max=20))
    email = fields.Str(required=False, validate=validate.Length(max=100))

    class Meta:
        strict = True


class ProveedorUpdateSchema(Schema):
    """Schema para actualizar proveedor"""
    nombre = fields.Str(required=False, validate=validate.Length(min=1, max=100))
    telefono = fields.Str(required=False, validate=validate.Length(max=20))
    email = fields.Str(required=False, validate=validate.Length(max=100))

    class Meta:
        strict = True


class ProveedorResponseSchema(Schema):
    """Schema para respuestas de proveedor"""
    id_proveedor = fields.Int()
    nombre = fields.Str()
    telefono = fields.Str(allow_none=True)
    email = fields.Str(allow_none=True)
    es_activo = fields.Bool()
    created_at = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')
    updated_at = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')

    class Meta:
        strict = True
