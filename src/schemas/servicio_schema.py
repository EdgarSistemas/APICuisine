"""
Schemas para Calificación y Mejoras - Validación y serialización
"""

from marshmallow import Schema, fields, validate, validates, ValidationError


# ============================================================================
# CALIFICACION SCHEMAS
# ============================================================================
class CalificacionCreateSchema(Schema):
    """Schema para crear calificación"""
    pedido_id = fields.Int(required=True)
    empleado_id = fields.Int(required=True)
    calificacion = fields.Int(required=True, validate=validate.Range(min=1, max=10))
    notas = fields.Str(required=False, allow_none=True, validate=validate.Length(max=300))


class CalificacionResponseSchema(Schema):
    """Schema para respuesta de calificación"""
    id_calificacion = fields.Int()
    pedido_id = fields.Int()
    cliente_id = fields.Int()
    empleado_id = fields.Int()
    calificacion = fields.Int()
    notas = fields.Str(allow_none=True)
    created_at = fields.DateTime(format='iso')
    es_activo = fields.Int()
    
    class Meta:
        ordered = True


# ============================================================================
# MEJORAS SCHEMAS
# ============================================================================
class MejoraCreateSchema(Schema):
    """Schema para crear mejora/sugerencia"""
    notas = fields.Str(required=True, validate=validate.Length(min=1, max=300))


class MejoraResponseSchema(Schema):
    """Schema para respuesta de mejora"""
    id_mejora = fields.Int()
    cliente_id = fields.Int()
    notas = fields.Str()
    created_at = fields.DateTime(format='iso')
    estatus = fields.Int()
    
    class Meta:
        ordered = True
