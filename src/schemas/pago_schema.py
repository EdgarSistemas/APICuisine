"""
Schemas para Pago - Validación con Marshmallow

Columnas disponibles en pagos.Pago:
  id_pago, pedido_id, sucursal_id, monto, propina, moneda, estatus, usuario_id, created_at, updated_at
"""

from marshmallow import Schema, fields, validates, ValidationError
from decimal import Decimal
from src.schemas.helpers import FormattedDateTime


class PagoCreateSchema(Schema):
    """Schema para crear/registrar pago"""
    pedido_id = fields.Int(required=True)
    sucursal_id = fields.Int(required=True)
    monto = fields.Decimal(required=True, as_string=False)
    propina = fields.Decimal(required=False, load_default=Decimal('0.00'), as_string=False)
    moneda = fields.Str(required=False, load_default='MXN')
    
    # Campos de cupón/descuento (opcionales)
    campania_usuario_id = fields.Int(required=False, allow_none=True, load_default=None)
    monto_descontado = fields.Decimal(required=False, allow_none=True, load_default=None, as_string=False)
    
    @validates('monto')
    def validate_monto(self, value):
        if value <= Decimal('0.00'):
            raise ValidationError("monto debe ser mayor a 0")
    
    @validates('propina')
    def validate_propina(self, value):
        if value is not None and value < Decimal('0.00'):
            raise ValidationError("propina no puede ser negativa")
    
    @validates('moneda')
    def validate_moneda(self, value):
        if value not in ['MXN', 'USD', 'EUR']:
            raise ValidationError("moneda debe ser MXN, USD o EUR")
    
    @validates('monto_descontado')
    def validate_monto_descontado(self, value):
        if value is not None and value < Decimal('0.00'):
            raise ValidationError("monto_descontado no puede ser negativo")


class PagoMarcarPagadoSchema(Schema):
    """Schema para marcar pago como pagado (vacío, no requiere datos extra)"""
    pass


class PagoResponseSchema(Schema):
    """Schema de respuesta para Pago"""
    id_pago = fields.Int()
    pedido_id = fields.Int()
    sucursal_id = fields.Int()
    monto = fields.Decimal(as_string=False)
    monto_descontado = fields.Decimal(as_string=False, allow_none=True)
    propina = fields.Decimal(as_string=False)
    moneda = fields.Str()
    estatus = fields.Int()
    usuario_id = fields.Int(allow_none=True)
    campania_usuario_id = fields.Int(allow_none=True)
    created_at = FormattedDateTime()
    updated_at = FormattedDateTime(allow_none=True)
    
    # Campos calculados
    monto_final = fields.Method("calcular_monto_final")
    total = fields.Method("calcular_monto_final")  # Alias para compatibilidad
    estatus_display = fields.Method("get_estatus_display")
    
    def calcular_monto_final(self, obj):
        """Calcula monto final (monto - descuento + propina)"""
        monto = Decimal(str(obj.get('monto', 0)))
        monto_descontado = Decimal(str(obj.get('monto_descontado', 0) or 0))
        propina = Decimal(str(obj.get('propina', 0)))
        return float(monto - monto_descontado + propina)
    
    def get_estatus_display(self, obj):
        """Retorna nombre legible del estatus"""
        estatus_map = {
            1: "Pendiente",
            2: "Pagado",
            3: "Anulado"
        }
        return estatus_map.get(obj.get('estatus'), "Desconocido")
