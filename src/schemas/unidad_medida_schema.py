"""
UnidadMedida Schema - Validación y serialización
"""

from marshmallow import Schema, fields, validate


class UnidadMedidaCreateSchema(Schema):
    """Schema para crear unidad de medida"""
    clave = fields.Str(required=True, validate=validate.Length(min=1, max=20))
    nombre = fields.Str(required=True, validate=validate.Length(min=1, max=30))

    class Meta:
        strict = True


class UnidadMedidaUpdateSchema(Schema):
    """Schema para actualizar unidad de medida"""
    clave = fields.Str(required=False, validate=validate.Length(min=1, max=20))
    nombre = fields.Str(required=False, validate=validate.Length(min=1, max=30))

    class Meta:
        strict = True


class UnidadMedidaResponseSchema(Schema):
    """Schema para respuestas de unidad de medida"""
    id_unidad = fields.Int()
    clave = fields.Str()
    nombre = fields.Str()
    created_at = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')
    updated_at = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')

    class Meta:
        strict = True
