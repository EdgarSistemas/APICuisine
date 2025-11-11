"""
Lote Schema - Validación y serialización
"""

from marshmallow import Schema, fields, validate


class LoteCreateSchema(Schema):
    """Schema para crear lote (generado automático desde RecepcionDetalle)"""
    det_recepcion_id = fields.Int(required=True, validate=validate.Range(min=1))
    lote = fields.Str(required=False, validate=validate.Length(max=20))
    lote_proveedor = fields.Str(required=False, validate=validate.Length(max=100))
    cantidad_inicial = fields.Decimal(required=True, places=2, validate=validate.Range(min=0))
    cantidad_disponible = fields.Decimal(required=True, places=2, validate=validate.Range(min=0))
    costo_unitario = fields.Decimal(required=True, places=2, validate=validate.Range(min=0))
    fecha_caducidad = fields.DateTime(required=False, format='%Y-%m-%d', allow_none=True)

    class Meta:
        strict = True


class LoteResponseSchema(Schema):
    """Schema para respuestas de lote"""
    id_lote = fields.Int()
    det_recepcion_id = fields.Int()
    lote = fields.Str(allow_none=True)
    lote_proveedor = fields.Str(allow_none=True)
    cantidad_inicial = fields.Decimal(places=2)
    cantidad_disponible = fields.Decimal(places=2)
    costo_unitario = fields.Decimal(places=2)
    fecha_caducidad = fields.DateTime(allow_none=True, format='%Y-%m-%d')
    estado = fields.Int()  # 1=Disponible, 2=Agotado
    created_at = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')

    class Meta:
        strict = True


class LoteDetailedSchema(Schema):
    """Schema detallado para lote con información de recepción"""
    id_lote = fields.Int()
    det_recepcion_id = fields.Int()
    lote = fields.Str(allow_none=True)
    lote_proveedor = fields.Str(allow_none=True)
    cantidad_inicial = fields.Decimal(places=2)
    cantidad_disponible = fields.Decimal(places=2)
    costo_unitario = fields.Decimal(places=2)
    fecha_caducidad = fields.DateTime(allow_none=True, format='%Y-%m-%d')
    estado = fields.Int()
    created_at = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')

    class Meta:
        strict = True
