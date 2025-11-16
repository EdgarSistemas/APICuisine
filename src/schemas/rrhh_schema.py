"""
Schemas para RRHH (Horarios, Asistencia, Vacaciones) - Validación y serialización
"""

from marshmallow import Schema, fields, validate, validates, ValidationError
from datetime import time, date


# ============================================================================
# HORARIO SCHEMAS
# ============================================================================
class HorarioDetalleCreateSchema(Schema):
    """Schema para crear detalle de horario"""
    dia_semana = fields.Int(required=True, validate=validate.Range(min=1, max=7))  # 1=Lunes, 7=Domingo
    hora_inicio = fields.Time(required=True)
    hora_fin = fields.Time(required=True)
    tolerancia_min = fields.Int(required=False, validate=validate.Range(min=0, max=60), missing=10)
    turno_idx = fields.Int(required=False, validate=validate.Range(min=1), missing=1)


class HorarioCreateSchema(Schema):
    """Schema para crear horario"""
    sucursal_id = fields.Int(required=False, allow_none=True)  # NULL = global
    clave = fields.Str(required=True, validate=validate.Length(min=1, max=60))
    nombre = fields.Str(required=True, validate=validate.Length(min=1, max=120))
    descripcion = fields.Str(required=False, allow_none=True, validate=validate.Length(max=300))
    detalles = fields.List(fields.Nested(HorarioDetalleCreateSchema), required=True, validate=validate.Length(min=1))


class HorarioUpdateSchema(Schema):
    """Schema para actualizar horario"""
    nombre = fields.Str(required=False, validate=validate.Length(min=1, max=120))
    descripcion = fields.Str(required=False, allow_none=True, validate=validate.Length(max=300))
    clave = fields.Str(required=True, validate=validate.Length(min=1, max=60))


class HorarioResponseSchema(Schema):
    """Schema para respuesta de horario"""
    id_horario = fields.Int()
    sucursal_id = fields.Int(allow_none=True)
    clave = fields.Str()
    nombre = fields.Str()
    descripcion = fields.Str(allow_none=True)
    es_activo = fields.Bool()
    created_at = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')
    
    class Meta:
        ordered = True


class HorarioDetalleResponseSchema(Schema):
    """Schema para respuesta de detalle de horario"""
    id_detalle = fields.Int()
    horario_id = fields.Int()
    dia_semana = fields.Int()
    hora_inicio = fields.Time()
    hora_fin = fields.Time()
    turno_idx = fields.Int()
    tolerancia_min = fields.Int()
    es_activo = fields.Bool()
    
    class Meta:
        ordered = True


# ============================================================================
# USUARIO HORARIO SCHEMAS
# ============================================================================
class UsuarioHorarioCreateSchema(Schema):
    """Schema para asignar horario a usuario"""
    usuario_id = fields.Int(required=True)
    horario_id = fields.Int(required=True)
    fecha_inicio = fields.Date(required=True)
    fecha_fin = fields.Date(required=False, allow_none=True)


# Alias para compatibilidad con imports
AsignarHorarioSchema = UsuarioHorarioCreateSchema


class UsuarioHorarioResponseSchema(Schema):
    """Schema para respuesta de asignación"""
    id_usuario_horario = fields.Int()
    usuario_id = fields.Int()
    horario_id = fields.Int()
    fecha_inicio = fields.Date()
    fecha_fin = fields.Date(allow_none=True)
    es_recurring = fields.Bool()
    es_activo = fields.Bool()
    created_at = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')
    
    class Meta:
        ordered = True


# ============================================================================
# TURNO CLAVE SCHEMAS
# ============================================================================
class TurnoClaveGenerarSchema(Schema):
    """Schema para generar código de turno (Azure Function)"""
    sucursal_id = fields.Int(required=True)
    horario_id = fields.Int(required=True)
    fecha = fields.Date(required=True)
    expira_en_horas = fields.Int(required=False, validate=validate.Range(min=1, max=24), missing=2)
    uso_maximo = fields.Int(required=False, validate=validate.Range(min=0, max=1000), missing=0)  # 0 = ilimitado


class TurnoClaveResponseSchema(Schema):
    """Schema para respuesta de turno clave"""
    id_turno_clave = fields.Int()
    horario_id = fields.Int()
    sucursal_id = fields.Int()
    fecha = fields.Date()
    turno_idx = fields.Int()
    codigo = fields.Str()
    es_activo = fields.Bool()
    generado_por = fields.Int(allow_none=True)
    generado_en = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')
    expira_en = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')
    uso_maximo = fields.Int()
    usos_count = fields.Int()
    
    class Meta:
        ordered = True


# ============================================================================
# ASISTENCIA SCHEMAS
# ============================================================================
class AsistenciaCheckInSchema(Schema):
    """Schema para check-in de empleado"""
    codigo = fields.Str(required=True, validate=validate.Length(min=6, max=6))
    origen = fields.Str(required=False, validate=validate.OneOf(['movil', 'pwa', 'kiosk']), missing='movil')
    lat = fields.Decimal(required=False, allow_none=True, places=6)
    lng = fields.Decimal(required=False, allow_none=True, places=6)
    device_info = fields.Str(required=False, allow_none=True, validate=validate.Length(max=300))


class AsistenciaResponseSchema(Schema):
    """Schema para respuesta de asistencia"""
    id_asistencia = fields.Int()
    usuario_id = fields.Int()
    usuario_horario_id = fields.Int(allow_none=True)
    tipo_evento = fields.Int()  # 1=Entrada, 2=Salida
    evento_ts = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')
    origen = fields.Str(allow_none=True)
    lat = fields.Decimal(allow_none=True, places=6)
    lng = fields.Decimal(allow_none=True, places=6)
    turno_clave_id = fields.Int(allow_none=True)
    codigo_usuario = fields.Str(allow_none=True)
    codigo_validado = fields.Bool()
    observaciones = fields.Str(allow_none=True)
    created_at = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')
    
    class Meta:
        ordered = True


# ============================================================================
# SOLICITUD VACACIONES SCHEMAS
# ============================================================================
class SolicitudVacacionesCreateSchema(Schema):
    """Schema para solicitar vacaciones"""
    fecha_inicio = fields.Date(required=True)
    fecha_fin = fields.Date(required=True)
    motivo = fields.Str(required=False, allow_none=True, validate=validate.Length(min=1, max=300))
    
    @validates('fecha_fin')
    def validate_fecha_fin(self, value):
        # La validación de rango se hace en el DAO
        pass


class SolicitudVacacionesResponseSchema(Schema):
    """Schema para respuesta de solicitud"""
    id_solicitud = fields.Int()
    horario_usuario_id = fields.Int()
    fecha_inicio = fields.Date(allow_none=True)
    fecha_fin = fields.Date(allow_none=True)
    motivo = fields.Str(allow_none=True)
    estatus = fields.Int()  # 1=Registrada, 2=Aprobada, 3=Rechazada
    created_at = fields.DateTime(allow_none=True, format='%Y-%m-%d %H:%M:%S')
    
    class Meta:
        ordered = True


# ============================================================================
# SCHEMAS ADICIONALES (ALIASES Y COMPLEMENTOS)
# ============================================================================

# Alias para GenerarCodigoSchema
GenerarCodigoSchema = TurnoClaveGenerarSchema


# Schema para Check-In (alias)
CheckInSchema = AsistenciaCheckInSchema


# Schema para Check-Out (simple, sin validaciones adicionales)
class CheckOutSchema(Schema):
    """Schema para check-out de empleado"""
    origen = fields.Str(required=False, validate=validate.OneOf(['movil', 'pwa', 'kiosk']), missing='movil')
    lat = fields.Decimal(required=False, allow_none=True, places=6)
    lng = fields.Decimal(required=False, allow_none=True, places=6)
    device_info = fields.Str(required=False, allow_none=True, validate=validate.Length(max=300))


# Schema para aprobar/rechazar vacaciones
class AprobarVacacionesSchema(Schema):
    """Schema para aprobar o rechazar solicitud de vacaciones"""
    notas_gerente = fields.Str(required=False, allow_none=True, validate=validate.Length(max=300))

