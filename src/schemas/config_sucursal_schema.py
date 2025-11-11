"""
ConfigSucursalSchema - Validación y serialización para ConfigSucursal
"""

from marshmallow import Schema, fields, validate, validates, ValidationError


class ConfigSucursalCreateSchema(Schema):
    """Schema para crear configuración"""
    sucursal_id = fields.Int(required=True, validate=validate.Range(min=1))
    clave = fields.Str(required=True, validate=validate.Length(min=1, max=30))
    valor_string = fields.Str(required=False, allow_none=True, validate=validate.Length(max=300))


class ConfigSucursalUpdateSchema(Schema):
    """Schema para actualizar configuración"""
    valor_string = fields.Str(required=False, allow_none=True, validate=validate.Length(max=300))


class ConfigSucursalResponseSchema(Schema):
    """Schema para respuesta de configuración"""
    id_config = fields.Int(dump_only=True)
    sucursal_id = fields.Int(dump_only=True)
    clave = fields.Str(dump_only=True)
    valor_string = fields.Str(dump_only=True, allow_none=True)
    updated_at = fields.DateTime(dump_only=True)
