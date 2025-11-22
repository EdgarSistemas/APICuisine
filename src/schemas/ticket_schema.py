"""
Schemas para Ticket - Validación y serialización
"""

from marshmallow import Schema, fields, validate, validates, ValidationError


class TicketCreateSchema(Schema):
    """Schema para crear ticket"""
    notas = fields.Str(required=True, validate=validate.Length(min=1, max=500))
    imagen_url = fields.Str(required=False, allow_none=True)


class TicketUpdateEstatusSchema(Schema):
    """Schema para actualizar estatus de ticket"""
    estatus = fields.Int(required=True, validate=validate.OneOf([1, 2, 3, 4]))  # 1=Registrada, 2=EnProceso, 3=Completada, 4=Cancelada
    
    @validates('estatus')
    def validate_estatus(self, value):
        if value not in [1, 2, 3, 4]:
            raise ValidationError("Estatus debe ser 1 (Registrada), 2 (En Proceso), 3 (Completada) o 4 (Cancelada)")


class TicketResponseSchema(Schema):
    """Schema para respuesta de ticket"""
    id_ticket = fields.Int()
    usuario_id = fields.Int()
    notas = fields.Str()
    imagen_url = fields.Str(allow_none=True)
    estatus = fields.Int()
    created_at = fields.DateTime(format='iso')
    
    class Meta:
        ordered = True
