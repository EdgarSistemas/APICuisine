"""
Insumo Schema - Validación y serialización
"""

from marshmallow import Schema, fields, validate


class InsumoCreateSchema(Schema):
    """Schema para crear insumo"""
    nombre = fields.Str(required=True, validate=validate.Length(min=1, max=30))
    unidad_id = fields.Int(required=True, validate=validate.Range(min=1))
    minimo_stock = fields.Decimal(required=True, validate=validate.Range(min=0))

    class Meta:
        strict = True


class InsumoUpdateSchema(Schema):
    """Schema para actualizar insumo"""
    nombre = fields.Str(required=False, validate=validate.Length(min=1, max=30))
    minimo_stock = fields.Decimal(required=False, validate=validate.Range(min=0))

    class Meta:
        strict = True


class UnidadMedidaNestedSchema(Schema):
    """Schema anidado para unidad de medida"""
    id_unidad = fields.Int()
    clave = fields.Str()
    nombre = fields.Str()
    simbolo = fields.Str(allow_none=True)


class InsumoResponseSchema(Schema):
    """Schema para respuestas de insumo"""
    id_insumo = fields.Int()
    nombre = fields.Str()
    unidad_id = fields.Int()
    unidad_medida = fields.Nested(UnidadMedidaNestedSchema, allow_none=True)
    es_activo = fields.Bool()
    minimo_stock = fields.Decimal(places=2)
    created_at = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')
    updated_at = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')

    class Meta:
        strict = True
