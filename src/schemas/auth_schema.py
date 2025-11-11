from marshmallow import Schema, fields, validate, validates_schema, ValidationError

class LoginSchema(Schema):
    """Esquema para validación de login"""
    email = fields.Email(required=True, error_messages={'required': 'Email es requerido'})
    password = fields.Str(required=True, validate=validate.Length(min=6), 
                         error_messages={'required': 'Password es requerido'})
    push_token = fields.Str(required=False, validate=validate.Length(max=255),
                           error_messages={'invalid': 'Token FCM inválido'})
    plataforma = fields.Str(required=False, validate=validate.OneOf(['android', 'web']),
                           error_messages={'invalid': 'Plataforma debe ser android o web'})
    
    @validates_schema
    def validate_push_token_plataforma(self, data, **kwargs):
        """Validar que si se envía push_token, también se envíe plataforma"""
        push_token = data.get('push_token')
        plataforma = data.get('plataforma')
        
        if push_token and not plataforma:
            raise ValidationError('Plataforma es requerida cuando se envía push_token', 'plataforma')
        
        if plataforma and not push_token:
            raise ValidationError('Push token es requerido cuando se envía plataforma', 'push_token')

class TokenSchema(Schema):
    """Esquema para respuesta de token"""
    access_token = fields.Str(required=True)
    token_type = fields.Str(missing='Bearer')
    expires_in = fields.Int()
    user = fields.Dict()

class CambiarPasswordSchema(Schema):
    """Esquema para cambio de password"""
    password_actual = fields.Str(required=True, error_messages={'required': 'Password actual es requerido'})
    password_nuevo = fields.Str(required=True, validate=validate.Length(min=6),
                               error_messages={'required': 'Password nuevo es requerido'})

class ErrorSchema(Schema):
    """Esquema para respuestas de error"""
    error = fields.Str(required=True)
    message = fields.Str(required=True)
    details = fields.Raw()

class SuccessSchema(Schema):
    """Esquema para respuestas exitosas"""
    success = fields.Bool(required=True)
    message = fields.Str(required=True)
    data = fields.Raw()

# Esquemas para roles
class RolCreateSchema(Schema):
    """Esquema para creación de roles"""
    nombre = fields.Str(required=True, validate=validate.Length(min=2, max=100),
                       error_messages={'required': 'Nombre del rol es requerido'})
    descripcion = fields.Str(validate=validate.Length(max=255))
    activo = fields.Bool(missing=True)


class RolUpdateSchema(Schema):
    """
    Esquema para actualización de roles
    Campos:
        - nombre: str (opcional)
        - descripcion: str (opcional)
        - modulos: List[int] (opcional, IDs de módulos a asignar)
    """
    nombre = fields.Str(validate=validate.Length(min=2, max=100))
    descripcion = fields.Str(validate=validate.Length(max=500))
    modulos = fields.List(fields.Int())

class RolResponseSchema(Schema):
    """Esquema para respuesta de rol"""
    id_rol = fields.Int()
    nombre = fields.Str()
    descripcion = fields.Str()
    activo = fields.Bool()
    created_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')
    updated_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')

class UsuarioCreateSchema(Schema):
    """Esquema para creación de usuarios"""
    email = fields.Email(required=True, error_messages={'required': 'Email es requerido'})
    password = fields.Str(required=True, validate=validate.Length(min=6),
                         error_messages={'required': 'Password es requerido'})
    nombre = fields.Str(required=True, validate=validate.Length(min=2, max=100),
                       error_messages={'required': 'Nombre es requerido'})
    apellido = fields.Str(required=True, validate=validate.Length(min=2, max=100),
                         error_messages={'required': 'Apellido es requerido'})
    telefono = fields.Str(validate=validate.Length(max=20))
    es_cliente = fields.Bool(missing=False)
    acepta_marketing = fields.Bool(missing=False)
    tipo_acceso = fields.Str(validate=validate.OneOf(['amb', 'pwa', 'mov']), missing='amb')
    
    # Campos opcionales para usuarios del sistema
    sucursal_id = fields.Int()
    rol_id = fields.Int()
    
    @validates_schema
    def validate_usuario_sistema(self, data, **kwargs):
        """Validar campos requeridos para usuarios del sistema"""
        if not data.get('es_cliente', False):
            # Usuario del sistema requiere sucursal y rol
            if not data.get('sucursal_id'):
                raise ValidationError('Sucursal es requerida para usuarios del sistema', 'sucursal_id')
            if not data.get('rol_id'):
                raise ValidationError('Rol es requerido para usuarios del sistema', 'rol_id')

class UsuarioUpdateSchema(Schema):
    """Esquema para actualización de usuarios"""
    email = fields.Email()
    password = fields.Str(validate=validate.Length(min=6))
    nombre = fields.Str(validate=validate.Length(min=2, max=100))
    apellido = fields.Str(validate=validate.Length(min=2, max=100))
    telefono = fields.Str(validate=validate.Length(max=20))
    es_activo = fields.Bool()
    acepta_marketing = fields.Bool()
    tipo_acceso = fields.Str(validate=validate.OneOf(['amb', 'pwa', 'mov']))

class UsuarioResponseSchema(Schema):
    """Esquema para respuesta de usuario"""
    id_usuario = fields.Int()
    email = fields.Email()
    nombre = fields.Str()
    apellido = fields.Str()
    telefono = fields.Str()
    es_activo = fields.Bool()
    es_cliente = fields.Bool()
    acepta_marketing = fields.Bool()
    tipo_acceso = fields.Str()
    created_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')
    updated_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')
    roles = fields.List(fields.Dict())
    sucursales = fields.List(fields.Dict())
    modulos = fields.List(fields.Dict())

class RolCreateSchema(Schema):
    """Esquema para creación de roles"""
    nombre = fields.Str(required=True, validate=validate.Length(min=2, max=100),
                       error_messages={'required': 'Nombre es requerido'})
    descripcion = fields.Str(validate=validate.Length(max=500))
    modulos = fields.List(fields.Int(), required=True, error_messages={'required': 'Debes asignar al menos un módulo'})

class RolUpdateSchema(Schema):
    """Esquema para actualización de roles"""
    nombre = fields.Str(validate=validate.Length(min=2, max=100))
    descripcion = fields.Str(validate=validate.Length(max=500))
    modulos = fields.List(fields.Int())

class RolResponseSchema(Schema):
    """Esquema para respuesta de rol"""
    id_rol = fields.Int()
    nombre = fields.Str()
    descripcion = fields.Str()
    modulos = fields.List(fields.Dict())

class ModuloCreateSchema(Schema):
    """Esquema para creación de módulos"""
    nombre = fields.Str(required=True, validate=validate.Length(min=2, max=100),
                       error_messages={'required': 'Nombre es requerido'})
    clave = fields.Str(required=True, validate=validate.Length(min=2, max=50),
                      error_messages={'required': 'Clave es requerida'})
    descripcion = fields.Str(validate=validate.Length(max=500))
    icono = fields.Str(validate=validate.Length(max=100))
    url = fields.Str(validate=validate.Length(max=200))
    orden = fields.Int(missing=0)
    es_activo = fields.Bool(missing=True)
    requiere_permisos = fields.Bool(missing=True)

class ModuloUpdateSchema(Schema):
    """Esquema para actualización de módulos"""
    nombre = fields.Str(validate=validate.Length(min=2, max=100))
    clave = fields.Str(validate=validate.Length(min=2, max=50))
    descripcion = fields.Str(validate=validate.Length(max=500))
    icono = fields.Str(validate=validate.Length(max=100))
    url = fields.Str(validate=validate.Length(max=200))
    orden = fields.Int()
    es_activo = fields.Bool()
    requiere_permisos = fields.Bool()

class ModuloResponseSchema(Schema):
    """Esquema para respuesta de módulo"""
    id_modulo = fields.Int()
    nombre = fields.Str()
    clave = fields.Str()
    descripcion = fields.Str()
    icono = fields.Str()
    url = fields.Str()
    orden = fields.Int()
    es_activo = fields.Bool()
    requiere_permisos = fields.Bool()
    created_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')
    updated_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S')

class PermisoModuloSchema(Schema):
    """Esquema para permisos de módulo"""
    modulo_id = fields.Int(required=True)
    habilitado = fields.Bool(missing=True)
    lectura = fields.Bool(missing=False)
    escritura = fields.Bool(missing=False)
    eliminacion = fields.Bool(missing=False)
    aprobacion = fields.Bool(missing=False)

class ConfigurarPermisosSchema(Schema):
    """Esquema para configuración de permisos de rol"""
    modulos = fields.List(fields.Nested(PermisoModuloSchema), required=True)

class CambiarPasswordSchema(Schema):
    """Esquema para cambio de password"""
    password_actual = fields.Str(required=True, validate=validate.Length(min=6),
                                error_messages={'required': 'Password actual es requerido'})
    password_nuevo = fields.Str(required=True, validate=validate.Length(min=6),
                               error_messages={'required': 'Password nuevo es requerido'})
    
    @validates_schema
    def validate_passwords(self, data, **kwargs):
        """Validar que los passwords sean diferentes"""
        if data.get('password_actual') == data.get('password_nuevo'):
            raise ValidationError('El nuevo password debe ser diferente al actual', 'password_nuevo')

class ErrorSchema(Schema):
    """Esquema para respuestas de error"""
    error = fields.Str()
    message = fields.Str()
    details = fields.Dict()

class SuccessSchema(Schema):
    """Esquema para respuestas exitosas"""
    success = fields.Bool(missing=True)
    message = fields.Str()
    data = fields.Dict()

# === ESQUEMAS PARA PASSWORD RESET ===

class SolicitarResetSchema(Schema):
    """Esquema para solicitar reset de contraseña"""
    email = fields.Email(required=True, error_messages={'required': 'Email es requerido'})

class VerificarCodigoSchema(Schema):
    """Esquema para verificar código de reset"""
    email = fields.Email(required=True, error_messages={'required': 'Email es requerido'})
    codigo = fields.Str(required=True, validate=validate.Length(equal=6),
                       error_messages={'required': 'Código es requerido'})

class RestablecerPasswordSchema(Schema):
    """Esquema para restablecer contraseña"""
    email = fields.Email(required=True, error_messages={'required': 'Email es requerido'})
    codigo = fields.Str(required=True, validate=validate.Length(equal=6),
                       error_messages={'required': 'Código es requerido'})
    nueva_password = fields.Str(required=True, validate=validate.Length(min=6),
                               error_messages={'required': 'Nueva contraseña es requerida'})

class SolicitarResetAdminSchema(Schema):
    """Esquema para solicitar reset desde admin"""
    email_usuario = fields.Email(required=True, error_messages={'required': 'Email del usuario es requerido'})