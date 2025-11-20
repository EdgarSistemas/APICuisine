"""
Compra Schema - Validación y serialización
"""

from marshmallow import Schema, fields, validate
from src.schemas.helpers import FormattedDateTime


class CompraDetalleItemSchema(Schema):
    """Schema para items de detalle al crear compra"""
    insumo_id = fields.Int(required=True, validate=validate.Range(min=1))
    cant_presentacion = fields.Decimal(required=True, places=2, validate=validate.Range(min=0))
    costo_unit_present = fields.Decimal(required=True, places=2, validate=validate.Range(min=0))
    presentacion = fields.Str(required=True, validate=validate.Length(min=1, max=100))

    class Meta:
        strict = True


class CompraCreateSchema(Schema):
    """Schema para crear compra con detalles"""
    sucursal_id = fields.Int(required=True, validate=validate.Range(min=1))
    proveedor_id = fields.Int(required=True, validate=validate.Range(min=1))
    detalles = fields.List(
        fields.Nested(CompraDetalleItemSchema),
        required=True,
        validate=validate.Length(min=1)
    )

    class Meta:
        strict = True


class CompraUpdateSchema(Schema):
    """Schema para actualizar compra"""
    folio = fields.Str(required=False, validate=validate.Length(min=1, max=20))
    estatus = fields.Int(required=False, validate=validate.Range(min=1, max=3))

    class Meta:
        strict = True


class CompraDetalleResponseSchema(Schema):
    """Schema para respuesta de detalle de compra"""
    id_compra_detalle = fields.Int()
    compra_id = fields.Int()
    insumo_id = fields.Int()
    cant_presentacion = fields.Decimal(places=2)
    presentacion = fields.Str()
    costo_unit_present = fields.Decimal(places=2)
    created_at = FormattedDateTime(allow_none=True)
    updated_at = FormattedDateTime(allow_none=True)

    class Meta:
        strict = True


class CompraResponseSchema(Schema):
    """Schema para respuestas de compra (listar)"""
    id_compra = fields.Int()
    usuario_id = fields.Int()
    sucursal_id = fields.Int()
    proveedor_id = fields.Int()
    folio = fields.Str()
    fecha_compra = FormattedDateTime()
    estatus = fields.Int()
    created_at = FormattedDateTime(allow_none=True)
    updated_at = FormattedDateTime(allow_none=True)

    class Meta:
        strict = True


class CompraDetailedSchema(Schema):
    """Schema para GET compra by ID con detalles completos"""
    id_compra = fields.Int()
    usuario_id = fields.Int()
    sucursal_id = fields.Int()
    proveedor_id = fields.Int()
    folio = fields.Str()
    fecha_compra = FormattedDateTime()
    estatus = fields.Int()
    detalles = fields.List(fields.Nested(CompraDetalleResponseSchema))
    created_at = FormattedDateTime(allow_none=True)
    updated_at = FormattedDateTime(allow_none=True)

    class Meta:
        strict = True
