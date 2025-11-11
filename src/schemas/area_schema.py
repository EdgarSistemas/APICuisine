"""
Esquemas de validación y serialización para la entidad Area
Usando Marshmallow para validación de entrada y serialización de salida
"""
from marshmallow import Schema, fields, validate, validates, ValidationError, post_load
from typing import Dict, Any

class AreaBaseSchema(Schema):
    """Schema base con campos comunes para Area"""
    
    sucursal_id = fields.Int(
        required=True,
        validate=validate.Range(
            min=1, 
            error="sucursal_id debe ser un número positivo"
        ),
        metadata={
            'description': 'ID de la sucursal a la que pertenece el área',
            'example': 1
        }
    )
    
    nombre = fields.Str(
        required=True,
        validate=validate.Length(
            min=2, max=50, 
            error="Nombre debe tener entre 2 y 50 caracteres"
        ),
        metadata={
            'description': 'Nombre del área',
            'example': 'Salón Principal'
        }
    )
    
    descripcion = fields.Str(
        allow_none=True,
        validate=validate.Length(
            max=100, 
            error="Descripción no puede exceder 100 caracteres"
        ),
        metadata={
            'description': 'Descripción opcional del área',
            'example': 'Área principal con vista al jardín'
        }
    )
    
    @validates('nombre')
    def validate_nombre(self, value):
        """Validación personalizada para nombre"""
        if value:
            # Verificar que no sea solo espacios
            if not value.strip():
                raise ValidationError("El nombre no puede estar vacío")
            
            # Verificar caracteres especiales excesivos
            if value.count('  ') > 0:  # No dobles espacios
                raise ValidationError("El nombre no puede contener espacios dobles")
    
    @validates('descripcion')
    def validate_descripcion(self, value):
        """Validación personalizada para descripción"""
        if value and not value.strip():
            raise ValidationError("La descripción no puede estar vacía si se proporciona")
    
    @post_load
    def transform_data(self, data, **kwargs):
        """Transformaciones post-validación"""
        # Normalizar nombre (capitalizar palabras y limpiar espacios)
        if 'nombre' in data:
            data['nombre'] = ' '.join(data['nombre'].strip().split()).title()
        
        # Limpiar descripción
        if 'descripcion' in data and data['descripcion']:
            data['descripcion'] = data['descripcion'].strip()
            # Si queda vacía después del strip, ponerla como None
            if not data['descripcion']:
                data['descripcion'] = None
        
        return data

class AreaCreateSchema(AreaBaseSchema):
    """Schema para creación de área"""
    
    class Meta:
        """Metadatos del schema"""
        description = "Esquema para crear una nueva área"

class AreaUpdateSchema(AreaBaseSchema):
    """Schema para actualización de área"""
    
    class Meta:
        """Metadatos del schema"""
        description = "Esquema para actualizar un área existente"
        
    # En actualización, ningún campo es obligatorio excepto validaciones básicas
    sucursal_id = fields.Int(
        required=False,
        validate=validate.Range(min=1),
        metadata={
            'description': 'ID de la sucursal (solo se permite si se desea cambiar de sucursal)',
            'example': 1
        }
    )
    
    nombre = fields.Str(
        required=False,
        validate=validate.Length(min=2, max=50),
        metadata={
            'description': 'Nombre del área',
            'example': 'Salón Principal'
        }
    )
    
    es_activa = fields.Bool(
        metadata={
            'description': 'Estado activo/inactivo del área',
            'example': True
        }
    )

class AreaResponseSchema(AreaBaseSchema):
    """Schema para respuestas (incluye campos de solo lectura)"""
    
    class Meta:
        """Metadatos del schema"""
        description = "Esquema de respuesta para área"
        
    id_area = fields.Int(
        dump_only=True,
        metadata={
            'description': 'ID único del área',
            'example': 1
        }
    )
    
    es_activa = fields.Bool(
        dump_only=True,
        metadata={
            'description': 'Estado activo/inactivo del área',
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

class AreaSimpleSchema(Schema):
    """Schema simplificado para listados o referencias"""
    
    id_area = fields.Int(
        metadata={
            'description': 'ID único del área',
            'example': 1
        }
    )
    sucursal_id = fields.Int(
        metadata={
            'description': 'ID de la sucursal',
            'example': 1
        }
    )
    nombre = fields.Str(
        metadata={
            'description': 'Nombre del área',
            'example': 'Salón Principal'
        }
    )
    es_activa = fields.Bool(
        metadata={
            'description': 'Estado activo/inactivo',
            'example': True
        }
    )

class AreaListResponseSchema(Schema):
    """Schema para respuestas de listados"""
    
    areas = fields.List(
        fields.Nested(AreaResponseSchema),
        metadata={'description': 'Lista de áreas'}
    )
    total = fields.Int(
        metadata={
            'description': 'Total de registros encontrados',
            'example': 15
        }
    )
    sucursal_id = fields.Int(
        allow_none=True,
        metadata={
            'description': 'ID de sucursal si se filtró por sucursal',
            'example': 1
        }
    )

class AreaFiltrosSchema(Schema):
    """Schema para filtros de búsqueda"""
    
    sucursal_id = fields.Int(
        allow_none=True,
        validate=validate.Range(min=1),
        metadata={
            'description': 'Filtrar por sucursal específica',
            'example': 1
        }
    )
    
    busqueda = fields.Str(
        allow_none=True,
        validate=validate.Length(min=1, max=100),
        metadata={
            'description': 'Búsqueda por nombre o descripción del área',
            'example': 'salón'
        }
    )
    
    es_activa = fields.Bool(
        allow_none=True,
        metadata={
            'description': 'Filtrar por estado activo/inactivo',
            'example': True
        }
    )
    
    orden_por = fields.Str(
        validate=validate.OneOf(['nombre', 'sucursal', 'fecha']),
        missing='nombre',
        metadata={
            'description': 'Campo por el cual ordenar los resultados',
            'example': 'nombre'
        }
    )

class AreaActivacionSchema(Schema):
    """Schema para activar/desactivar área"""
    
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
            'example': 'Remodelación en proceso'
        }
    )

class AreaEstadisticasSchema(Schema):
    """Schema para estadísticas de áreas por sucursal"""
    
    sucursal_id = fields.Int(
        metadata={
            'description': 'ID de la sucursal',
            'example': 1
        }
    )
    total = fields.Int(
        metadata={
            'description': 'Total de áreas en la sucursal',
            'example': 5
        }
    )
    activas = fields.Int(
        metadata={
            'description': 'Áreas activas',
            'example': 4
        }
    )
    inactivas = fields.Int(
        metadata={
            'description': 'Áreas inactivas',
            'example': 1
        }
    )

class AreaValidacionSucursalSchema(Schema):
    """Schema para validar existencia de sucursal"""
    
    sucursal_id = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        metadata={
            'description': 'ID de la sucursal a validar',
            'example': 1
        }
    )