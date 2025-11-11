"""
Esquemas para validación de reset de contraseñas
"""

from marshmallow import Schema, fields, validate, validates_schema, ValidationError

class SolicitarResetSchema(Schema):
    """Schema para solicitar reset de contraseña"""
    
    email = fields.Email(
        required=True,
        validate=validate.Length(max=255),
        error_messages={
            'required': 'El email es obligatorio',
            'invalid': 'Formato de email inválido',
            'validator_failed': 'Email demasiado largo'
        }
    )

class ResetPasswordConTokenSchema(Schema):
    """Schema para reset de contraseña con token JWT"""
    
    reset_token = fields.String(
        required=True,
        validate=validate.Length(min=20),
        error_messages={
            'required': 'El token de reset es obligatorio',
            'validator_failed': 'Token inválido'
        }
    )
    
    codigo = fields.String(
        required=True,
        validate=validate.Regexp(
            r'^\d{6}$',
            error='El código debe ser de 6 dígitos'
        ),
        error_messages={
            'required': 'El código es obligatorio'
        }
    )
    
    nueva_password = fields.String(
        required=True,
        validate=validate.Length(min=8, max=128),
        error_messages={
            'required': 'La nueva contraseña es obligatoria',
            'validator_failed': 'La contraseña debe tener entre 8 y 128 caracteres'
        }
    )
    
    @validates_schema
    def validate_password_strength(self, data, **kwargs):
        """Validar que la contraseña cumpla con criterios de seguridad"""
        password = data.get('nueva_password', '')
        
        if len(password) < 8:
            raise ValidationError('La contraseña debe tener al menos 8 caracteres', 'nueva_password')
        
        # Al menos una letra
        if not any(c.isalpha() for c in password):
            raise ValidationError('La contraseña debe contener al menos una letra', 'nueva_password')
        
        # Al menos un número
        if not any(c.isdigit() for c in password):
            raise ValidationError('La contraseña debe contener al menos un número', 'nueva_password')

class ResetPasswordConCodigoSchema(Schema):
    """Schema para reset de contraseña con código directo (alternativo)"""
    
    email = fields.Email(
        required=True,
        validate=validate.Length(max=255),
        error_messages={
            'required': 'El email es obligatorio',
            'invalid': 'Formato de email inválido'
        }
    )
    
    codigo = fields.String(
        required=True,
        validate=validate.Regexp(
            r'^\d{6}$',
            error='El código debe ser de 6 dígitos'
        ),
        error_messages={
            'required': 'El código es obligatorio'
        }
    )
    
    nueva_password = fields.String(
        required=True,
        validate=validate.Length(min=8, max=128),
        error_messages={
            'required': 'La nueva contraseña es obligatoria',
            'validator_failed': 'La contraseña debe tener entre 8 y 128 caracteres'
        }
    )
    
    @validates_schema
    def validate_password_strength(self, data, **kwargs):
        """Validar que la contraseña cumpla con criterios de seguridad"""
        password = data.get('nueva_password', '')
        
        if len(password) < 8:
            raise ValidationError('La contraseña debe tener al menos 8 caracteres', 'nueva_password')
        
        # Al menos una letra
        if not any(c.isalpha() for c in password):
            raise ValidationError('La contraseña debe contener al menos una letra', 'nueva_password')
        
        # Al menos un número
        if not any(c.isdigit() for c in password):
            raise ValidationError('La contraseña debe contener al menos un número', 'nueva_password')

class CambiarPasswordSchema(Schema):
    """Schema para cambiar contraseña autenticado (con contraseña actual)"""
    
    password_actual = fields.String(
        required=True,
        error_messages={
            'required': 'La contraseña actual es obligatoria'
        }
    )
    
    nueva_password = fields.String(
        required=True,
        validate=validate.Length(min=8, max=128),
        error_messages={
            'required': 'La nueva contraseña es obligatoria',
            'validator_failed': 'La contraseña debe tener entre 8 y 128 caracteres'
        }
    )
    
    confirmar_password = fields.String(
        required=True,
        error_messages={
            'required': 'La confirmación de contraseña es obligatoria'
        }
    )
    
    @validates_schema
    def validate_passwords_match(self, data, **kwargs):
        """Validar que las contraseñas coincidan"""
        if data.get('nueva_password') != data.get('confirmar_password'):
            raise ValidationError('Las contraseñas no coinciden', 'confirmar_password')
    
    @validates_schema
    def validate_password_strength(self, data, **kwargs):
        """Validar que la contraseña cumpla con criterios de seguridad"""
        password = data.get('nueva_password', '')
        
        if len(password) < 8:
            raise ValidationError('La contraseña debe tener al menos 8 caracteres', 'nueva_password')
        
        # Al menos una letra
        if not any(c.isalpha() for c in password):
            raise ValidationError('La contraseña debe contener al menos una letra', 'nueva_password')
        
        # Al menos un número
        if not any(c.isdigit() for c in password):
            raise ValidationError('La contraseña debe contener al menos un número', 'nueva_password')
    
    @validates_schema
    def validate_different_passwords(self, data, **kwargs):
        """Validar que la nueva contraseña sea diferente a la actual"""
        if data.get('password_actual') == data.get('nueva_password'):
            raise ValidationError('La nueva contraseña debe ser diferente a la actual', 'nueva_password')