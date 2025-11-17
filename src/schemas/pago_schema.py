"""
Schemas para Pago - Validación con Marshmallow
"""

from marshmallow import Schema, fields, validates, ValidationError
from decimal import Decimal


class PagoCreateSchema(Schema):
    """Schema para crear/registrar pago"""
    pedido_id = fields.Int(required=True)
    monto = fields.Decimal(required=True, as_string=False)
    propina = fields.Decimal(required=False, default=Decimal('0.00'), as_string=False)
    moneda = fields.Str(required=False, default='MXN')
    
    @validates('monto')
    def validate_monto(self, value):
        if value <= Decimal('0.00'):
            raise ValidationError("monto debe ser mayor a 0")
    
    @validates('propina')
    def validate_propina(self, value):
        if value < Decimal('0.00'):
            raise ValidationError("propina no puede ser negativa")
    
    @validates('moneda')
    def validate_moneda(self, value):
        if value not in ['MXN', 'USD', 'EUR']:
            raise ValidationError("moneda debe ser MXN, USD o EUR")


class PagoMarcarPagadoSchema(Schema):
    """Schema para marcar pedido como pagado"""
    pedido_id = fields.Int(required=True)
    monto_total = fields.Decimal(required=True, as_string=False)
    propina = fields.Decimal(required=False, default=Decimal('0.00'), as_string=False)
    metodo_pago = fields.Str(required=False, default='efectivo')  # efectivo, tarjeta, etc
    referencia = fields.Str(required=False, allow_none=True)  # Referencia de transacción
    
    @validates('monto_total')
    def validate_monto_total(self, value):
        if value <= Decimal('0.00'):
            raise ValidationError("monto_total debe ser mayor a 0")


class PagoResponseSchema(Schema):
    """Schema de respuesta para Pago"""
    id_pago = fields.Int()
    pedido_id = fields.Int()
    sucursal_id = fields.Int()
    monto = fields.Decimal(as_string=False)
    propina = fields.Decimal(as_string=False)
    moneda = fields.Str()
    estatus = fields.Int()
    usuario_id = fields.Int(allow_none=True)
    created_at = fields.DateTime()
    updated_at = fields.DateTime(allow_none=True)
    
    # Campos calculados
    total = fields.Method("calcular_total")
    estatus_display = fields.Method("get_estatus_display")
    
    def calcular_total(self, obj):
        """Calcula total (monto + propina)"""
        monto = Decimal(str(obj.get('monto', 0)))
        propina = Decimal(str(obj.get('propina', 0)))
        return float(monto + propina)
    
    def get_estatus_display(self, obj):
        """Retorna nombre legible del estatus"""
        estatus_map = {
            1: "Registrado",
            2: "Confirmado",
            3: "Revertido"
        }
        return estatus_map.get(obj.get('estatus'), "Desconocido")
