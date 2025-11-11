"""
AsignacionMesa Schema - Validación y serialización de datos de Asignaciones de Mesas
"""

from marshmallow import Schema, fields, validate


class AsignacionMesaCreateSchema(Schema):
    """Schema para crear una asignación"""
    mesa_id = fields.Int(required=True, validate=validate.Range(min=1))
    usuario_id = fields.Int(required=True, validate=validate.Range(min=1))

    class Meta:
        strict = True


class AsignacionMesaResponseSchema(Schema):
    """Schema para respuestas de asignación"""
    id_asignacion_mesa = fields.Int()
    mesa_id = fields.Int()
    usuario_id = fields.Int()
    es_activa = fields.Bool()
    created_at = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')
    updated_at = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')

    class Meta:
        strict = True
