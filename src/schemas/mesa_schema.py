"""
Mesa Schema - Validación y serialización de datos de Mesas
"""

from marshmallow import Schema, fields, validate


class MesaCreateSchema(Schema):
    """Schema para crear una mesa"""
    area_id = fields.Int(required=True, validate=validate.Range(min=1))
    codigo_mesa = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    capacidad = fields.Int(required=True, validate=validate.Range(min=1, max=100))

    class Meta:
        strict = True


class MesaUpdateSchema(Schema):
    """Schema para actualizar una mesa"""
    codigo_mesa = fields.Str(required=False, validate=validate.Length(min=1, max=50))
    capacidad = fields.Int(required=False, validate=validate.Range(min=1, max=100))
    es_activa = fields.Bool(required=False)

    class Meta:
        strict = True


class MesaResponseSchema(Schema):
    """Schema para respuestas de mesa"""
    id_mesa = fields.Int()
    area_id = fields.Int()
    codigo_mesa = fields.Str()
    capacidad = fields.Int()
    es_activa = fields.Bool()
    created_at = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')
    updated_at = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')

    class Meta:
        strict = True
