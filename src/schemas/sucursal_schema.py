"""
Esquemas de validación y serialización para la entidad Sucursal
Usando Marshmallow para validación de entrada y serialización de salida
"""
from marshmallow import Schema, fields, validate, validates, ValidationError, post_load
from typing import Dict, Any

class SucursalBaseSchema(Schema):
    """Schema base con campos comunes para Sucursal"""
    
    codigo_sucursal = fields.Str(
        required=False,  # Cambiar a opcional para permitir generación automática
        validate=[
            validate.Length(min=2, max=20, error="Código debe tener entre 2 y 20 caracteres"),
            validate.Regexp(
                r'^[A-Z0-9_-]+$', 
                error="Código solo puede contener mayúsculas, números, guiones y guiones bajos"
            )
        ],
        metadata={
            'description': 'Código único identificador de la sucursal',
            'example': 'SUC-001'
        }
    )
    
    nombre = fields.Str(
        required=True,
        validate=validate.Length(
            min=3, max=100, 
            error="Nombre debe tener entre 3 y 100 caracteres"
        ),
        metadata={
            'description': 'Nombre comercial de la sucursal',
            'example': 'Sucursal Centro'
        }
    )
    
    telefono = fields.Str(
        allow_none=True,
        validate=validate.Length(
            min=10, max=15, 
            error="Teléfono debe tener entre 10 y 15 caracteres"
        ),
        metadata={
            'description': 'Teléfono de contacto de la sucursal',
            'example': '555-123-4567'
        }
    )
    
    direccion = fields.Str(
        allow_none=True,
        validate=validate.Length(
            max=100, 
            error="Dirección no puede exceder 100 caracteres"
        ),
        metadata={
            'description': 'Dirección física de la sucursal',
            'example': 'Av. Principal #123, Col. Centro'
        }
    )
    
    @validates('telefono')
    def validate_telefono(self, value):
        """Validación personalizada para teléfono"""
        if value:
            # Remover espacios, guiones y paréntesis para validar
            telefono_limpio = value.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            if not telefono_limpio.isdigit():
                raise ValidationError("El teléfono solo puede contener números, espacios, guiones y paréntesis")
    
    @validates('codigo_sucursal')
    def validate_codigo_format(self, value):
        """Validación adicional para el código"""
        if value:
            # Verificar que no sea solo números o solo guiones
            if value.replace('-', '').replace('_', '') == '':
                raise ValidationError("El código debe contener al menos un carácter alfanumérico")
    
    @post_load
    def transform_data(self, data, **kwargs):
        """Transformaciones post-validación"""
        # Normalizar código a mayúsculas
        if 'codigo_sucursal' in data:
            data['codigo_sucursal'] = data['codigo_sucursal'].upper().strip()
        
        # Normalizar nombre (capitalizar palabras)
        if 'nombre' in data:
            data['nombre'] = data['nombre'].strip().title()
        
        # Limpiar teléfono
        if 'telefono' in data and data['telefono']:
            data['telefono'] = data['telefono'].strip()
        
        # Limpiar dirección
        if 'direccion' in data and data['direccion']:
            data['direccion'] = data['direccion'].strip()
        
        return data

    @post_load
    def generate_codigo_sucursal(self, data, **kwargs):
        """Generar código único si no se proporciona."""
        from datetime import datetime
        if 'codigo_sucursal' not in data or not data['codigo_sucursal']:
            data['codigo_sucursal'] = f"SUC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        return data

class SucursalCreateSchema(SucursalBaseSchema):
    """Schema para creación de sucursal"""
    
    class Meta:
        """Metadatos del schema"""
        description = "Esquema para crear una nueva sucursal"
        

class SucursalUpdateSchema(SucursalBaseSchema):
    """Schema para actualización de sucursal"""
    
    class Meta:
        """Metadatos del schema"""
        description = "Esquema para actualizar una sucursal existente"
        
    # En actualización, ningún campo es obligatorio
    codigo_sucursal = fields.Str(
        required=False,
        validate=[
            validate.Length(min=2, max=20),
            validate.Regexp(r'^[A-Z0-9_-]+$')
        ],
        metadata={
            'description': 'Código único identificador de la sucursal',
            'example': 'SUC-001'
        }
    )
    
    nombre = fields.Str(
        required=False,
        validate=validate.Length(min=3, max=100),
        metadata={
            'description': 'Nombre comercial de la sucursal',
            'example': 'Sucursal Centro'
        }
    )
    
    es_activa = fields.Bool(
        metadata={
            'description': 'Estado activo/inactivo de la sucursal',
            'example': True
        }
    )

class SucursalResponseSchema(SucursalBaseSchema):
    """Schema para respuestas (incluye campos de solo lectura)"""
    
    class Meta:
        """Metadatos del schema"""
        description = "Esquema de respuesta para sucursal"
        
    id_sucursal = fields.Int(
        dump_only=True,
        metadata={
            'description': 'ID único de la sucursal',
            'example': 1
        }
    )
    
    es_activa = fields.Bool(
        dump_only=True,
        metadata={
            'description': 'Estado activo/inactivo de la sucursal',
            'example': True
        }
    )
    
    created_at = fields.DateTime(
        dump_only=True,
        format='%Y-%m-%d %H:%M:%S',
        metadata={
            'description': 'Fecha de creación',
            'example': '2024-01-15 10:30:00'
        }
    )
    
    updated_at = fields.DateTime(
        dump_only=True,
        format='%Y-%m-%d %H:%M:%S',
        metadata={
            'description': 'Fecha de actualización',
            'example': '2024-01-15 10:30:00'
        }
    )
    
    updated_at = fields.DateTime(
        dump_only=True,
        format='iso',
        allow_none=True,
        metadata={
            'description': 'Fecha de última actualización',
            'example': '2024-01-20T15:45:00Z'
        }
    )

class SucursalSimpleSchema(Schema):
    """Schema simplificado para listados o referencias"""
    
    id_sucursal = fields.Int(
        metadata={
            'description': 'ID único de la sucursal',
            'example': 1
        }
    )
    codigo_sucursal = fields.Str(
        metadata={
            'description': 'Código de la sucursal',
            'example': 'SUC-001'
        }
    )
    nombre = fields.Str(
        metadata={
            'description': 'Nombre de la sucursal',
            'example': 'Sucursal Centro'
        }
    )
    es_activa = fields.Bool(
        metadata={
            'description': 'Estado activo/inactivo',
            'example': True
        }
    )

class SucursalListResponseSchema(Schema):
    """Schema para respuestas de listados paginados"""
    
    sucursales = fields.List(
        fields.Nested(SucursalResponseSchema),
        metadata={'description': 'Lista de sucursales'}
    )
    total = fields.Int(
        metadata={
            'description': 'Total de registros encontrados',
            'example': 25
        }
    )
    pagina = fields.Int(
        metadata={
            'description': 'Página actual',
            'example': 1
        }
    )
    por_pagina = fields.Int(
        metadata={
            'description': 'Registros por página',
            'example': 10
        }
    )
    total_paginas = fields.Int(
        metadata={
            'description': 'Total de páginas disponibles',
            'example': 3
        }
    )

class SucursalFiltrosSchema(Schema):
    """Schema para filtros de búsqueda"""
    
    busqueda = fields.Str(
        allow_none=True,
        validate=validate.Length(min=1, max=100),
        metadata={
            'description': 'Búsqueda por nombre o código de sucursal',
            'example': 'centro'
        }
    )
    
    es_activa = fields.Bool(
        allow_none=True,
        metadata={
            'description': 'Filtrar por estado activo/inactivo',
            'example': True
        }
    )
    
    ciudad = fields.Str(
        allow_none=True,
        validate=validate.Length(min=2, max=50),
        metadata={
            'description': 'Filtrar por ciudad en la dirección',
            'example': 'México'
        }
    )
    
    orden_por = fields.Str(
        validate=validate.OneOf(['nombre', 'codigo', 'fecha']),
        missing='nombre',
        metadata={
            'description': 'Campo por el cual ordenar los resultados',
            'example': 'nombre'
        }
    )
    
    pagina = fields.Int(
        validate=validate.Range(min=1),
        missing=1,
        metadata={
            'description': 'Número de página',
            'example': 1
        }
    )
    
    por_pagina = fields.Int(
        validate=validate.Range(min=1, max=100),
        missing=10,
        metadata={
            'description': 'Registros por página (máximo 100)',
            'example': 10
        }
    )

class SucursalActivacionSchema(Schema):
    """Schema para activar/desactivar sucursal"""
    
    activar = fields.Bool(
        required=True,
        metadata={
            'description': 'True para activar, False para desactivar',
            'example': True
        }
    )
    
    motivo = fields.Str(
        allow_none=True,
        validate=validate.Length(max=200),
        metadata={
            'description': 'Motivo de la activación/desactivación',
            'example': 'Mantenimiento programado'
        }
    )

class SucursalEstadisticasSchema(Schema):
    """Schema para estadísticas de sucursales"""
    
    total = fields.Int(
        metadata={
            'description': 'Total de sucursales',
            'example': 25
        }
    )
    activas = fields.Int(
        metadata={
            'description': 'Sucursales activas',
            'example': 22
        }
    )
    inactivas = fields.Int(
        metadata={
            'description': 'Sucursales inactivas',
            'example': 3
        }
    )
    porcentaje_activas = fields.Float(
        metadata={
            'description': 'Porcentaje de sucursales activas',
            'example': 88.0
        }
    )
    ultima_creada = fields.Nested(
        SucursalSimpleSchema,
        allow_none=True,
        metadata={'description': 'Última sucursal creada'}
    )