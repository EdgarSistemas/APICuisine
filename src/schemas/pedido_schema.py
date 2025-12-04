"""
Schemas para Pedido y PedidoItem - Validación con Marshmallow

Estados Pedido (estado_pedido):
  1 = Abierto (creado, puede agregar items)
  2 = EnProceso (hay items en cocina)
  3 = Completo (todos los items listos)
  4 = Cancelado
  5 = Pagado

Estados PedidoItem (estatus_detalle):
  0 = Iniciado (recién agregado)
  1 = EnCocina (enviado a preparar)
  2 = Listo (preparado)
  3 = Completo (entregado)
  4 = Cancelado
  5 = Pagado
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
    estatus_detalle = fields.Int()
    estatus_display = fields.Str(dump_only=True)
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
    """
    Schema para crear pedido (Dine-in o Takeaway)
    
    NOTA: mesa_id NO se envía para Dine-in - se obtiene de la reserva automáticamente
    """
    sucursal_id = fields.Int(required=True)
    cliente_id = fields.Int(required=True)
    tipo_pedido = fields.Int(required=True)  # 1=Dine-in, 2=Takeaway
    canal = fields.Int(required=True)  # 1=PWA, 2=Móvil, 3=Presencial
    reserva_id = fields.Int(required=True)  # Requerido para Dine-in
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
        # Estados válidos: 2=EnProceso, 3=Completo, 4=Cancelado, 5=Pagado
        if value not in [2, 3, 4, 5]:
            raise ValidationError("estado_pedido debe ser: 2=EnProceso, 3=Completo, 4=Cancelado, 5=Pagado")


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
            1: "Abierto",
            2: "EnProceso",
            3: "Completo",
            4: "Cancelado",
            5: "Pagado"
        }
        estado = obj.get('estado_pedido') if isinstance(obj, dict) else getattr(obj, 'estado_pedido', None)
        return estado_map.get(estado, "Desconocido")
    
    def get_tipo_display(self, obj):
        """Retorna nombre legible del tipo"""
        tipo_map = {
            1: "Dine-in",
            2: "Takeaway"
        }
        tipo = obj.get('tipo_pedido') if isinstance(obj, dict) else getattr(obj, 'tipo_pedido', None)
        return tipo_map.get(tipo, "Desconocido")


class PedidoListSchema(Schema):
    """Schema para listar Pedidos (resumen)"""
    id_pedido = fields.Int()
    folio = fields.Str()
    sucursal_id = fields.Int(allow_none=True)
    sucursal_nombre = fields.Str(allow_none=True)  # Para clientes que ven pedidos de múltiples sucursales
    cliente_id = fields.Int()
    tipo_pedido = fields.Int()
    canal = fields.Int()
    mesa_id = fields.Int(allow_none=True)
    estado_pedido = fields.Int()
    created_at = FormattedDateTime()
    
    class Meta:
        ordered = True
