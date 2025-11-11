"""
Esquemas de validación para Usuario usando Marshmallow
"""

from marshmallow import Schema, fields, validate, validates, ValidationError
import re


class UsuarioEmpleadoCreateSchema(Schema):
    """Esquema para crear usuario empleado"""
    
    email = fields.Email(
        required=True,
        validate=validate.Length(max=255),
        error_messages={'required': 'El email es requerido'}
    )
    
    password = fields.String(
        required=True,
        validate=validate.Length(min=6, max=255),
        error_messages={'required': 'El password es requerido'}
    )
    
    nombre = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100),
        error_messages={'required': 'El nombre es requerido'}
    )
    
    apellido = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100),
        error_messages={'required': 'El apellido es requerido'}
    )
    
    telefono = fields.String(
        validate=validate.Length(min=10, max=15),
        allow_none=True
    )
    
    rol_id = fields.Integer(
        required=True,
        error_messages={'required': 'El rol es requerido'}
    )
    
    sucursal_id = fields.Integer(
        required=True,
        error_messages={'required': 'La sucursal es requerida'}
    )
    
    @validates('password')
    def validate_password(self, value):
        """Validar fortaleza del password"""
        if len(value) < 6:
            raise ValidationError('El password debe tener al menos 6 caracteres')
        
        # Al menos una letra y un número
        if not re.search(r'[A-Za-z]', value) or not re.search(r'\d', value):
            raise ValidationError('El password debe contener al menos una letra y un número')


class UsuarioClienteCreateSchema(Schema):
    """Esquema para crear usuario cliente"""
    
    email = fields.Email(
        required=True,
        validate=validate.Length(max=255),
        error_messages={'required': 'El email es requerido'}
    )
    
    password = fields.String(
        required=True,
        validate=validate.Length(min=6, max=255),
        error_messages={'required': 'El password es requerido'}
    )
    
    nombre = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100),
        error_messages={'required': 'El nombre es requerido'}
    )
    
    apellido = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100),
        error_messages={'required': 'El apellido es requerido'}
    )
    
    telefono = fields.String(
        validate=validate.Length(min=10, max=15),
        allow_none=True
    )
    
    acepta_marketing = fields.Boolean(
        missing=False,
        default=False
    )
    
    @validates('password')
    def validate_password(self, value):
        """Validar fortaleza del password"""
        if len(value) < 6:
            raise ValidationError('El password debe tener al menos 6 caracteres')
        
        # Al menos una letra y un número
        if not re.search(r'[A-Za-z]', value) or not re.search(r'\d', value):
            raise ValidationError('El password debe contener al menos una letra y un número')


class UsuarioCreateSchema(Schema):
    """Esquema para crear usuario"""
    
    email = fields.Email(
        required=True,
        validate=validate.Length(max=255),
        error_messages={'required': 'El email es requerido'}
    )
    
    password = fields.String(
        required=True,
        validate=validate.Length(min=6, max=255),
        error_messages={'required': 'El password es requerido'}
    )
    
    nombre = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100),
        error_messages={'required': 'El nombre es requerido'}
    )
    
    apellido = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100),
        error_messages={'required': 'El apellido es requerido'}
    )
    
    activo = fields.Boolean(
        missing=True,
        default=True
    )
    
    @validates('password')
    def validate_password(self, value):
        """Validar fortaleza del password"""
        if len(value) < 6:
            raise ValidationError('El password debe tener al menos 6 caracteres')
        
        # Al menos una letra y un número
        if not re.search(r'[A-Za-z]', value) or not re.search(r'\d', value):
            raise ValidationError('El password debe contener al menos una letra y un número')


class UsuarioUpdateSchema(Schema):
    """Esquema para actualizar usuario"""
    
    email = fields.Email(
        validate=validate.Length(max=255),
        allow_none=True
    )
    
    nombre = fields.String(
        validate=validate.Length(min=2, max=100),
        allow_none=True
    )
    
    apellido = fields.String(
        validate=validate.Length(min=2, max=100),
        allow_none=True
    )
    
    telefono = fields.String(
        validate=validate.Length(min=10, max=15),
        allow_none=True
    )
    
    activo = fields.Boolean(
        allow_none=True
    )


class UsuarioResponseSchema(Schema):
    """Esquema para respuesta de usuario (sin password)"""
    
    id = fields.Integer(dump_only=True)
    email = fields.Email()
    nombre = fields.String()
    apellido = fields.String()
    activo = fields.Boolean()
    created_at = fields.DateTime(dump_only=True, format='%Y-%m-%d %H:%M:%S')
    updated_at = fields.DateTime(dump_only=True, format='%Y-%m-%d %H:%M:%S')


class ErrorSchema(Schema):
    """Esquema para respuestas de error"""
    
    error = fields.String(required=True)
    message = fields.String(required=True)
    details = fields.Raw(allow_none=True)


class SuccessSchema(Schema):
    """Esquema para respuestas exitosas"""
    
    success = fields.Boolean(required=True)
    message = fields.String(required=True)
    data = fields.Raw(allow_none=True)