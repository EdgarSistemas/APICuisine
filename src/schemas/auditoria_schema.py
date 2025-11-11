"""
Esquemas de validación para logs de auditoría
"""

from marshmallow import Schema, fields, validate

class LogFiltrosSchema(Schema):
    """Esquema para filtros de búsqueda de logs"""
    entidad = fields.Str(allow_none=True, validate=validate.Length(max=120))
    accion = fields.Str(allow_none=True, validate=validate.Length(max=40))
    usuario_id = fields.Int(allow_none=True, validate=validate.Range(min=1))
    origen = fields.Str(allow_none=True, validate=validate.OneOf(['API', 'WEB', 'MOBILE', 'SYSTEM']))
    fecha_desde = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')
    fecha_hasta = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')

class LogCrearSchema(Schema):
    """Esquema para crear logs manualmente (uso interno)"""
    entidad = fields.Str(required=True, validate=validate.Length(min=1, max=120))
    accion = fields.Str(required=True, validate=validate.Length(min=1, max=40))
    entidad_id = fields.Str(allow_none=True, validate=validate.Length(max=80))
    detalle = fields.Dict(allow_none=True)
    origen = fields.Str(missing='API', validate=validate.OneOf(['API', 'WEB', 'MOBILE', 'SYSTEM']))

class EstadisticasSchema(Schema):
    """Esquema para parámetros de estadísticas"""
    dias = fields.Int(missing=30, validate=validate.Range(min=1, max=365))

class LimpiarLogsSchema(Schema):
    """Esquema para limpieza de logs"""
    dias = fields.Int(required=True, validate=validate.Range(min=30, max=3650))  # Entre 30 días y 10 años