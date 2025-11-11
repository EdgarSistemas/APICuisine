"""
Recepcion y RecepcionDetalle Schemas - Validación y serialización
"""

from marshmallow import Schema, fields, validate


class RecepcionDetalleCreateSchema(Schema):
    """Schema para crear detalle de recepción"""
    insumo_id = fields.Int(required=True, validate=validate.Range(min=1))
    cant_presentacion = fields.Decimal(required=True, places=2, validate=validate.Range(min=0.01))
    unidades_por_present = fields.Decimal(required=True, places=2, validate=validate.Range(min=0.01))
    costo_unitario = fields.Decimal(required=True, places=2, validate=validate.Range(min=0))
    lote_proveedor = fields.Str(required=False, validate=validate.Length(max=100))
    fecha_caducidad = fields.DateTime(required=False, format='%Y-%m-%d')
    notas = fields.Str(required=False, validate=validate.Length(max=300))

    class Meta:
        strict = True


class RecepcionCreateSchema(Schema):
    """Schema para crear recepción con detalles"""
    compra_id = fields.Int(required=True, validate=validate.Range(min=1))
    recibido_por = fields.Int(required=True, validate=validate.Range(min=1))
    notas = fields.Str(required=False, validate=validate.Length(max=300))
    detalles = fields.List(
        fields.Nested(RecepcionDetalleCreateSchema),
        required=True,
        validate=validate.Length(min=1)
    )

    class Meta:
        strict = True


class RecepcionUpdateSchema(Schema):
    """Schema para actualizar recepción"""
    notas = fields.Str(required=False, validate=validate.Length(max=300))

    class Meta:
        strict = True


class RecepcionDetalleResponseSchema(Schema):
    """Schema para respuesta de detalle de recepción"""
    id_recepcion_det = fields.Int()
    recepcion_id = fields.Int()
    insumo_id = fields.Int()
    cant_presentacion = fields.Decimal(places=2)
    unidades_por_present = fields.Decimal(places=2)
    cantidad_base = fields.Decimal(places=4)
    costo_unitario = fields.Decimal(places=2)
    notas = fields.Str(allow_none=True)
    created_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S', allow_none=True)

    class Meta:
        strict = True


class RecepcionResponseSchema(Schema):
    """Schema para respuesta de recepción (listar)"""
    id_recepcion = fields.Int()
    compra_id = fields.Int(allow_none=True)
    recibido_por = fields.Int(allow_none=True)
    fecha_recepcion = fields.DateTime(format='%Y-%m-%d %H:%M:%S')
    notas = fields.Str(allow_none=True)
    estatus = fields.Int()
    created_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')

    class Meta:
        strict = True


class RecepcionDetailedSchema(Schema):
    """Schema para respuesta de recepción con detalles completos"""
    id_recepcion = fields.Int()
    compra_id = fields.Int(allow_none=True)
    recibido_por = fields.Int(allow_none=True)
    fecha_recepcion = fields.DateTime(format='%Y-%m-%d %H:%M:%S')
    notas = fields.Str(allow_none=True)
    estatus = fields.Int()
    created_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')
    detalles = fields.List(fields.Nested(RecepcionDetalleResponseSchema))

    class Meta:
        strict = True
