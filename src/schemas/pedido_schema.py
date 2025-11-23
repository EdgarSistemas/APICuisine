"""
Schemas para Pedido y PedidoItem - Validación con Marshmallow
Estados Pedido: 1=Creado, 2=Confirmado, 3=EnPreparacion, 4=Listo, 5=Entregado, 6=Cancelado
"""

from marshmallow import Schema, fields, validates, ValidationError, validates_schema, pre_load
from decimal import Decimal
from src.schemas.helpers import FormattedDateTime


# ============================
# ITEM SCHEMAS
# ============================

class PedidoItemSchema(Schema):
    """Schema para cada item del pedido"""
    id_pedido_item = fields.Int(dump_only=True)
    pedido_id = fields.Int(dump_only=True)
    producto_id = fields.Int(allow_none=True)
    combo_id = fields.Int(allow_none=True)
    cantidad = fields.Int()
    precio_unit = fields.Decimal(as_string=True)
    notas = fields.Str(allow_none=True)
    created_at = FormattedDateTime()
    updated_at = FormattedDateTime(allow_none=True)


class PedidoCreateItemSchema(Schema):
    """Schema para agregar item a pedido"""
    producto_id = fields.Int(allow_none=True)
    combo_id = fields.Int(allow_none=True)
    cantidad = fields.Int(required=True)
    notas = fields.Str(allow_none=True)
    
    @validates('cantidad')
    def validate_cantidad(self, value):
        if value < 1:
            raise ValidationError("cantidad debe ser mayor a 0")
        if value > 100:
            raise ValidationError("cantidad no puede exceder 100 unidades")
    
    @validates_schema
    def validate_producto_o_combo(self, data, **kwargs):
        producto_id = data.get('producto_id')
        combo_id = data.get('combo_id')
        
        if not producto_id and not combo_id:
            raise ValidationError("Debe especificar producto_id O combo_id")
        
        if producto_id and combo_id:
            raise ValidationError("No puede especificar ambos producto_id y combo_id")


# ============================
# PEDIDO SCHEMAS
# ============================

class PedidoCreateSchema(Schema):
    """Schema para crear pedido (Dine-in o Takeaway)"""
    sucursal_id = fields.Int(required=True)
    cliente_id = fields.Int(required=True)
    tipo_pedido = fields.Int(required=True)  # 1=Dine-in, 2=Takeaway
    canal = fields.Int(required=True)  # 1=PWA, 2=Móvil, 3=Presencial
    reserva_id = fields.Int(required=True)
    mesa_id = fields.Int(allow_none=True)
    notas = fields.Str(allow_none=True)
    items = fields.List(fields.Nested(PedidoCreateItemSchema), required=True)
    
    @validates('tipo_pedido')
    def validate_tipo_pedido(self, value):
        if value not in [1, 2]:
            raise ValidationError("tipo_pedido debe ser: 1=Dine-in, 2=Takeaway")
    
    @validates('canal')
    def validate_canal(self, value):
        if value not in [1, 2, 3]:
            raise ValidationError("canal debe ser: 1=PWA, 2=Móvil, 3=Presencial")
    
    @validates('items')
    def validate_items(self, value):
        if not value:
            raise ValidationError("items no puede estar vacío")
        if len(value) > 50:
            raise ValidationError("No puedes agregar más de 50 items a la vez")
    
    @validates_schema
    def validate_mesa_por_tipo(self, data, **kwargs):
        tipo_pedido = data.get('tipo_pedido')
        mesa_id = data.get('mesa_id')
        
        if tipo_pedido == 1 and not mesa_id:
            raise ValidationError("mesa_id es requerido para pedidos Dine-in (tipo_pedido=1)")
        
        if tipo_pedido == 2 and mesa_id:
            raise ValidationError("mesa_id debe ser NULL para pedidos Takeaway (tipo_pedido=2)")
    
    @pre_load
    def strip_whitespace(self, data, **kwargs):
        if isinstance(data, dict) and data.get('notas'):
            data['notas'] = data['notas'].strip()
        return data


class PedidoCambiarEstadoSchema(Schema):
    """Schema para cambiar estado de pedido"""
    estado_pedido = fields.Int(required=True)
    comentario = fields.Str(allow_none=True)
    
    @validates('estado_pedido')
    def validate_estado(self, value):
        # Puedes transicionar a cualquier estado excepto 1 (Creado, que es inicial)
        if value not in [2, 3, 4, 5, 6]:
            raise ValidationError("estado_pedido debe ser: 2=Confirmado, 3=EnPreparacion, 4=Listo, 5=Entregado, 6=Cancelado")


class PedidoResponseSchema(Schema):
    """Schema de respuesta para Pedido"""
    id_pedido = fields.Int()
    sucursal_id = fields.Int()
    folio = fields.Str()
    cliente_id = fields.Int()
    tipo_pedido = fields.Int()
    canal = fields.Int()
    reserva_id = fields.Int()
    mesa_id = fields.Int(allow_none=True)
    inicia_usuario_id = fields.Int()
    estado_pedido = fields.Int()
    notas = fields.Str(allow_none=True)
    items = fields.List(fields.Nested(PedidoItemSchema))
    created_at = FormattedDateTime()
    updated_at = FormattedDateTime(allow_none=True)
    
    # Campos calculados
    estado_display = fields.Method("get_estado_display")
    tipo_display = fields.Method("get_tipo_display")
    
    def get_estado_display(self, obj):
        """Retorna nombre legible del estado"""
        estado_map = {
            1: "Creado",
            2: "Confirmado",
            3: "En Preparación",
            4: "Listo",
            5: "Entregado",
            6: "Cancelado"
        }
        return estado_map.get(obj.get('estado_pedido'), "Desconocido")
    
    def get_tipo_display(self, obj):
        """Retorna nombre legible del tipo"""
        tipo_map = {
            1: "Dine-in",
            2: "Takeaway"
        }
        return tipo_map.get(obj.get('tipo_pedido'), "Desconocido")


class PedidoListSchema(Schema):
    """Schema para listar Pedidos (resumen)"""
    id_pedido = fields.Int()
    folio = fields.Str()
    cliente_id = fields.Int()
    tipo_pedido = fields.Int()
    canal = fields.Int()
    mesa_id = fields.Int(allow_none=True)
    estado_pedido = fields.Int()
    created_at = FormattedDateTime()
    
    class Meta:
        ordered = True
