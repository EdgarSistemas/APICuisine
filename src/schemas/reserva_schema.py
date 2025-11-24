"""
Schemas para HoldMesa y Reserva - Validación con Marshmallow
"""

from marshmallow import Schema, fields, validates, ValidationError, validates_schema
from datetime import datetime, timedelta
import pytz
from src.schemas.helpers import FormattedDateTime

# Zona horaria de México
TZ_MEXICO = pytz.timezone('America/Mexico_City')


# ============================
# HOLD MESA SCHEMAS
# ============================

class HoldMesaCreateSchema(Schema):
    """Schema para crear hold de mesa"""
    mesa_id = fields.Int(required=True)
    actor_tipo = fields.Int(required=True)  # 1=Cliente, 2=Recepcionista
    actor_usuario_id = fields.Int(required=False, allow_none=True)
    inicio = fields.DateTime(required=True)
    ttl_minutes = fields.Int(required=False, default=3)  # Minutos antes de expirar (default 5)
    notas = fields.Str(required=False, allow_none=True)
    horas = fields.Integer(required=True)  # Numero de horas a apartar la mesa
    
    @validates('actor_tipo')
    def validate_actor_tipo(self, value):
        if value not in [1, 2]:
            raise ValidationError("actor_tipo debe ser 1 (Cliente) o 2 (Recepcionista)")
    
    @validates('ttl_minutes')
    def validate_ttl(self, value):
        if value < 1 or value > 30:
            raise ValidationError("ttl_minutes debe estar entre 1 y 30 minutos")
    
    @validates_schema
    def validate_fechas(self, data, **kwargs):
        inicio = data.get('inicio')
        fin_estimado = data.get('fin_estimado')
        
        if inicio and fin_estimado:
            if fin_estimado <= inicio:
                raise ValidationError("fin_estimado debe ser posterior a inicio")
            
            # Validar que inicio sea futuro (con margen de 5 minutos) - usar zona de México
            ahora = datetime.now(TZ_MEXICO).replace(tzinfo=None)
            if inicio < ahora - timedelta(minutes=5):
                raise ValidationError("La fecha de inicio debe ser futura o actual")


class HoldMesaCancelarSchema(Schema):
    """Schema para cancelar hold"""
    motivo = fields.Str(required=False, allow_none=True)


class HoldMesaResponseSchema(Schema):
    """Schema de respuesta para HoldMesa"""
    id_hold_mesa = fields.Int()
    mesa_id = fields.Int()
    actor_tipo = fields.Int()
    actor_usuario_id = fields.Int(allow_none=True)
    inicio = FormattedDateTime()
    horas = fields.Int()
    fin_estimado = FormattedDateTime()
    expires_at = FormattedDateTime()
    estatus = fields.Int()
    notas = fields.Str(allow_none=True)
    created_at = FormattedDateTime()
    updated_at = FormattedDateTime(allow_none=True)
    
    # Campos calculados
    tiempo_restante_segundos = fields.Method("calcular_tiempo_restante")
    esta_expirado = fields.Method("verificar_expirado")
    
    def calcular_tiempo_restante(self, obj):
        """Calcula segundos restantes hasta expiración"""
        if obj.estatus != 1:  # Solo si está activo
            return 0
        ahora = datetime.now(TZ_MEXICO).replace(tzinfo=None)
        delta = obj.expires_at - ahora
        return max(0, int(delta.total_seconds()))
    
    def verificar_expirado(self, obj):
        """Verifica si ya expiró por tiempo (usando zona de México)"""
        ahora = datetime.now(TZ_MEXICO).replace(tzinfo=None)
        return ahora > obj.expires_at


# ============================
# RESERVA SCHEMAS
# ============================

class ReservaCreateSchema(Schema):
    """Schema para crear reserva"""
    cliente_id = fields.Int(required=False, allow_none=True)
    recepcionista_id = fields.Int(required=False, allow_none=True)
    inicio = fields.DateTime(required=True, format='%Y-%m-%d %H:%M:%S')
    fin_estimado = fields.DateTime(required=True, format='%Y-%m-%d %H:%M:%S')
    tolerancia_min = fields.Int(required=False, allow_none=True)
    notas = fields.Str(required=False, allow_none=True)
    hold_id = fields.Int(required=False, allow_none=True)  # Si viene de un hold
    
    @validates('tolerancia_min')
    def validate_tolerancia(self, value):
        if value is not None and (value < 0 or value > 120):
            raise ValidationError("tolerancia_min debe estar entre 0 y 120 minutos")
    
    @validates_schema
    def validate_fechas(self, data, **kwargs):
        inicio = data.get('inicio')
        fin_estimado = data.get('fin_estimado')
        
        if inicio and fin_estimado:
            if fin_estimado <= inicio:
                raise ValidationError("fin_estimado debe ser posterior a inicio")
            
            # Reserva debe ser futura (con margen de 5 min) - usar zona horaria de México
            ahora = datetime.now(TZ_MEXICO).replace(tzinfo=None)
            if inicio < ahora - timedelta(minutes=5):
                raise ValidationError("La fecha de inicio debe ser futura o actual")


class ReservaActualizarEstatusSchema(Schema):
    """Schema para actualizar estatus de reserva"""
    estatus = fields.Int(required=True)
    notas = fields.Str(required=False, allow_none=True)
    
    @validates('estatus')
    def validate_estatus(self, value):
        if value not in [1, 2, 3, 4, 5]:
            raise ValidationError("estatus debe ser: 1=Programada, 2=EnCurso, 3=Completada, 4=NoShow, 5=Cancelada")


class ReservaCancelarSchema(Schema):
    """Schema para cancelar reserva"""
    motivo = fields.Str(required=False, allow_none=True)


class ReservaResponseSchema(Schema):
    """Schema de respuesta para Reserva"""
    id_reserva = fields.Int()
    cliente_id = fields.Int(allow_none=True)
    recepcionista_id = fields.Int(allow_none=True)
    inicio = FormattedDateTime()
    fin_estimado = FormattedDateTime()
    estatus = fields.Int()
    tolerancia_min = fields.Int(allow_none=True)
    notas = fields.Str(allow_none=True)
    hold_id = fields.Int(allow_none=True)
    created_at = FormattedDateTime()
    updated_at = FormattedDateTime(allow_none=True)
    
    # Campos calculados
    estatus_display = fields.Method("get_estatus_display")
    puede_iniciar = fields.Method("verificar_puede_iniciar")
    
    def get_estatus_display(self, obj):
        """Retorna nombre legible del estatus"""
        estatus_map = {
            1: "Programada",
            2: "En Curso",
            3: "Completada",
            4: "No Show",
            5: "Cancelada"
        }
        return estatus_map.get(obj.estatus, "Desconocido")
    
    def verificar_puede_iniciar(self, obj):
        """Verifica si puede iniciar la reserva (está cerca de la hora) - usa zona de México"""
        if obj.estatus != 1:  # Solo si está programada
            return False
        ahora = datetime.now(TZ_MEXICO).replace(tzinfo=None)
        tolerancia = timedelta(minutes=obj.tolerancia_min or 15)
        return ahora >= (obj.inicio - tolerancia)


class ReservaListarQuerySchema(Schema):
    """Schema para query params al listar reservas"""
    sucursal_id = fields.Int(required=False, allow_none=True, missing=None)
    cliente_id = fields.Int(required=False, allow_none=True, missing=None)
    estatus = fields.Int(required=False, allow_none=True, missing=None)
    fecha_desde = fields.DateTime(required=False, allow_none=True, format='iso', missing=None)
    fecha_hasta = fields.DateTime(required=False, allow_none=True, format='iso', missing=None)
