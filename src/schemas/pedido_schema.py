"""
Schemas para Pedido y PedidoItem - Validación con Marshmallow
"""

from marshmallow import Schema, fields, validates, ValidationError, validates_schema
from decimal import Decimal


# ============================
# PEDIDO SCHEMAS
# ============================

class PedidoCreateSchema(Schema):
    """Schema para crear pedido"""
    sucursal_id = fields.Int(required=True)
    reserva_id = fields.Int(required=True)
    inicia_usuario_id = fields.Int(required=True)
    mesa_id = fields.Int(required=True)
    cliente_id = fields.Int(required=False, allow_none=True)
    tipo_pedido = fields.Int(required=False, default=1)  # 1=Dine-in, 2=Pickup, 3=Delivery
    canal = fields.Int(required=False, default=2)  # 1=Mesero, 2=Sistema, 3=App
    notas = fields.Str(required=False, allow_none=True)
    
    @validates('tipo_pedido')
    def validate_tipo_pedido(self, value):
        if value not in [1, 2, 3]:
            raise ValidationError("tipo_pedido debe ser: 1=Dine-in, 2=Pickup, 3=Delivery")
    
    @validates('canal')
    def validate_canal(self, value):
        if value not in [1, 2, 3]:
            raise ValidationError("canal debe ser: 1=Mesero, 2=Sistema, 3=App")


class PedidoItemCreateSchema(Schema):
    """Schema para agregar item a pedido"""
    cantidad = fields.Int(required=True)
    precio_unit = fields.Decimal(required=True, as_string=False)
    producto_id = fields.Int(required=False, allow_none=True)
    combo_id = fields.Int(required=False, allow_none=True)
    notas = fields.Str(required=False, allow_none=True)
    
    @validates('cantidad')
    def validate_cantidad(self, value):
        if value < 1:
            raise ValidationError("cantidad debe ser mayor a 0")
        if value > 100:
            raise ValidationError("cantidad no puede exceder 100 unidades")
    
    @validates('precio_unit')
    def validate_precio(self, value):
        if value < Decimal('0.00'):
            raise ValidationError("precio_unit no puede ser negativo")
    
    @validates_schema
    def validate_producto_o_combo(self, data, **kwargs):
        producto_id = data.get('producto_id')
        combo_id = data.get('combo_id')
        
        if not producto_id and not combo_id:
            raise ValidationError("Debe especificar producto_id O combo_id")
        
        if producto_id and combo_id:
            raise ValidationError("No puede especificar ambos producto_id y combo_id")


class PedidoConfirmarItemsSchema(Schema):
    """Schema para confirmar items a cocina"""
    item_ids = fields.List(fields.Int(), required=True)
    
    @validates('item_ids')
    def validate_item_ids(self, value):
        if not value:
            raise ValidationError("item_ids no puede estar vacío")
        if len(value) > 50:
            raise ValidationError("No puedes confirmar más de 50 items a la vez")


class PedidoCambiarEstatusSchema(Schema):
    """Schema para cambiar estatus de pedido"""
    estatus = fields.Int(required=True)
    comentario = fields.Str(required=False, allow_none=True)
    
    @validates('estatus')
    def validate_estatus(self, value):
        # Estados posibles: 1=Abierto, 2=Enviado, 3=Entregado, 4=Cancelado, 5=Pagado
        if value not in [1, 2, 3, 4, 5]:
            raise ValidationError("estatus debe ser: 1=Abierto, 2=Enviado, 3=Entregado, 4=Cancelado, 5=Pagado")


class PedidoItemCambiarEstatusSchema(Schema):
    """Schema para cambiar estatus de item"""
    estatus = fields.Int(required=True)
    
    @validates('estatus')
    def validate_estatus(self, value):
        # Estados: 1=Agregado, 2=Confirmado, 3=EnCocina, 4=Listo, 5=Servido
        if value not in [1, 2, 3, 4, 5]:
            raise ValidationError("estatus debe ser: 1=Agregado, 2=Confirmado, 3=EnCocina, 4=Listo, 5=Servido")


class PedidoResponseSchema(Schema):
    """Schema de respuesta para Pedido"""
    id_pedido = fields.Int()
    sucursal_id = fields.Int()
    folio = fields.Str()
    cliente_id = fields.Int(allow_none=True)
    tipo_pedido = fields.Int()
    canal = fields.Int()
    reserva_id = fields.Int(allow_none=True)
    mesa_id = fields.Int(allow_none=True)
    inicia_usuario_id = fields.Int()
    estado_pedido = fields.Int()
    notas = fields.Str(allow_none=True)
    items = fields.List(fields.Dict())
    created_at = fields.DateTime()
    updated_at = fields.DateTime(allow_none=True)
    
    # Campos calculados
    estatus_display = fields.Method("get_estatus_display")
    tiene_items_sin_confirmar = fields.Method("verificar_items_sin_confirmar")
    
    def get_estatus_display(self, obj):
        """Retorna nombre legible del estatus"""
        estatus_map = {
            1: "Abierto",
            2: "Enviado",
            3: "Entregado",
            4: "Cancelado",
            5: "Pagado"
        }
        return estatus_map.get(obj.get('estado_pedido'), "Desconocido")
    
    def verificar_items_sin_confirmar(self, obj):
        """Verifica si hay items no confirmados"""
        items = obj.get('items', [])
        return any(item.get('estatus', 0) < 3 for item in items)


class PedidoItemResponseSchema(Schema):
    """Schema de respuesta para PedidoItem"""
    id_pedido_item = fields.Int()
    pedido_id = fields.Int()
    producto_id = fields.Int(allow_none=True)
    combo_id = fields.Int(allow_none=True)
    cantidad = fields.Int()
    precio_unit = fields.Decimal(as_string=False)
    estatus = fields.Int()
    notas = fields.Str(allow_none=True)
    created_at = fields.DateTime()
    updated_at = fields.DateTime(allow_none=True)
    
    # Campos calculados
    subtotal = fields.Method("calcular_subtotal")
    estatus_display = fields.Method("get_estatus_display")
    puede_ir_cocina = fields.Method("verificar_puede_ir_cocina")
    
    def calcular_subtotal(self, obj):
        """Calcula subtotal del item"""
        return float(obj.get('precio_unit', 0)) * obj.get('cantidad', 0)
    
    def get_estatus_display(self, obj):
        """Retorna nombre legible del estatus"""
        estatus_map = {
            1: "Agregado",
            2: "Confirmado",
            3: "En Cocina",
            4: "Listo",
            5: "Servido"
        }
        return estatus_map.get(obj.get('estatus'), "Desconocido")
    
    def verificar_puede_ir_cocina(self, obj):
        """Verifica si el item puede ir a cocina (estatus >= 2)"""
        return obj.get('estatus', 0) >= 2
