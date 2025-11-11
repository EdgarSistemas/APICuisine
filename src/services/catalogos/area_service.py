"""
Servicio de lógica de negocio para la entidad Area
Contiene toda la lógica de negocio, validaciones y transacciones
"""
from typing import List, Optional, Dict, Any
from marshmallow import ValidationError
from src.dao.catalogos.area_dao import AreaDAO
from src.schemas.area_schema import (
    AreaCreateSchema, AreaUpdateSchema, AreaFiltrosSchema,
    AreaResponseSchema, AreaSimpleSchema
)
from src.services.auditoria.log_service import log_action

class AreaService:
    """
    Servicio para gestión de áreas con lógica de negocio
    """
    
    def __init__(self):
        self.dao = AreaDAO()
        self.create_schema = AreaCreateSchema()
        self.update_schema = AreaUpdateSchema()
        self.response_schema = AreaResponseSchema()
        self.simple_schema = AreaSimpleSchema()
        self.filtros_schema = AreaFiltrosSchema()
    
    def crear_area(self, datos: dict, usuario_id: int = None) -> dict:
        """
        Crea una nueva área con validaciones de negocio.
        Args:
            datos: Datos del área
            usuario_id: ID del usuario que crea
        Returns:
            Diccionario con datos del área creada
        """
        # Validar datos de entrada
        datos_validados = self.create_schema.load(datos)
        
        # Validar que la sucursal exista y esté activa
        if not self.dao.validar_sucursal_existe(datos_validados['sucursal_id']):
            raise ValueError(f"La sucursal con ID {datos_validados['sucursal_id']} no existe o no está activa")
        
        # Validar que no exista otra área con el mismo nombre en la misma sucursal
        if self.dao.existe_nombre_en_sucursal(
            datos_validados['sucursal_id'], 
            datos_validados['nombre']
        ):
            raise ValueError(f"Ya existe un área con el nombre '{datos_validados['nombre']}' en esta sucursal")
        
        # Crear área
        area = self.dao.crear(datos_validados)
        
        # Log de auditoría
        if usuario_id and 'id_area' in area:
            log_action('CREATE', 'Area', area['id_area'], usuario_id)
        
        return area
    
    def obtener_area(self, id_area: int) -> dict:
        """
        Obtiene un área por ID.
        Args:
            id_area: ID del área
        Returns:
            Diccionario serializado del área
        """
        area = self.dao.obtener_por_id(id_area)
        if not area:
            raise ValueError(f"Área con ID {id_area} no encontrada")
        return area
    
    def listar_areas(self, sucursal_id: int = None, solo_activas: bool = True) -> List[dict]:
        """
        Lista áreas, opcionalmente filtradas por sucursal
        Args:
            sucursal_id: ID de sucursal para filtrar (opcional)
            solo_activas: Si solo mostrar áreas activas
        Returns:
            Lista de áreas en formato JSON
        """
        if sucursal_id:
            return self.dao.obtener_por_sucursal(sucursal_id, solo_activas)
        else:
            return self.dao.listar_todas(solo_activas)
    
    def obtener_areas_por_sucursal(self, sucursal_id: int, solo_activas: bool = True) -> List[dict]:
        """
        Obtiene todas las áreas de una sucursal específica
        Args:
            sucursal_id: ID de la sucursal
            solo_activas: Si solo mostrar áreas activas
        Returns:
            Lista de áreas de la sucursal
        """
        # Validar que la sucursal exista
        if not self.dao.validar_sucursal_existe(sucursal_id):
            raise ValueError(f"La sucursal con ID {sucursal_id} no existe o no está activa")
        
        return self.dao.obtener_por_sucursal(sucursal_id, solo_activas)
    
    def obtener_areas_activas(self) -> List[dict]:
        """
        Obtiene lista simple de áreas activas
        Returns:
            Lista simplificada de áreas activas
        """
        return self.dao.obtener_activas()
    
    def actualizar_area(self, id_area: int, datos: dict, usuario_id: int = None) -> dict:
        """
        Actualiza un área existente
        Args:
            id_area: ID del área
            datos: Datos a actualizar
            usuario_id: ID del usuario que actualiza
        Returns:
            Diccionario con datos actualizados
        """
        # Validar datos de entrada
        datos_validados = self.update_schema.load(datos)
        
        # Verificar que el área existe
        area_actual = self.dao.obtener_por_id(id_area)
        if not area_actual:
            raise ValueError(f"Área con ID {id_area} no encontrada")
        
        # Si se está cambiando la sucursal, validar que la nueva sucursal exista
        if 'sucursal_id' in datos_validados and datos_validados['sucursal_id'] != area_actual['sucursal_id']:
            if not self.dao.validar_sucursal_existe(datos_validados['sucursal_id']):
                raise ValueError(f"La sucursal con ID {datos_validados['sucursal_id']} no existe o no está activa")
        
        # Si se está cambiando el nombre, validar que no exista otro con el mismo nombre en la misma sucursal
        if 'nombre' in datos_validados:
            sucursal_id_final = datos_validados.get('sucursal_id', area_actual['sucursal_id'])
            if self.dao.existe_nombre_en_sucursal(
                sucursal_id_final, 
                datos_validados['nombre'], 
                excluir_id=id_area
            ):
                raise ValueError(f"Ya existe un área con el nombre '{datos_validados['nombre']}' en esta sucursal")
        
        # Actualizar
        area = self.dao.actualizar(id_area, datos_validados)
        
        # Log de auditoría
        if usuario_id and area and 'id_area' in area:
            log_action('UPDATE', 'Area', id_area, usuario_id)
        
        return area
    
    def eliminar_area(self, id_area: int, usuario_id: int = None) -> bool:
        """
        Elimina lógicamente un área
        Args:
            id_area: ID del área
            usuario_id: ID del usuario que elimina
        Returns:
            True si se eliminó correctamente
        """
        # Verificar que existe
        if not self.dao.obtener_por_id(id_area):
            raise ValueError(f"Área con ID {id_area} no encontrada")
        
        # TODO: Validar que no tenga mesas activas asociadas cuando se implemente Mesa
        # if self.dao.tiene_mesas_activas(id_area):
        #     raise ValueError("No se puede eliminar un área que tiene mesas activas")
        
        # Eliminar lógicamente
        resultado = self.dao.eliminar_logico(id_area)
        
        # Log de auditoría
        if usuario_id and resultado:
            log_action('DELETE', 'Area', id_area, usuario_id)
        
        return resultado
    
    def activar_desactivar_area(self, id_area: int, activar: bool, usuario_id: int = None) -> dict:
        """
        Activa o desactiva un área
        Args:
            id_area: ID del área
            activar: True para activar, False para desactivar
            usuario_id: ID del usuario que realiza la acción
        Returns:
            Diccionario con datos actualizados
        """
        # Verificar que existe
        if not self.dao.obtener_por_id(id_area):
            raise ValueError(f"Área con ID {id_area} no encontrada")
        
        # Cambiar estado
        area = self.dao.actualizar(id_area, {'es_activa': activar})
        
        # Log de auditoría
        if usuario_id and area and 'id_area' in area:
            accion = 'ACTIVATE' if activar else 'DEACTIVATE'
            log_action(accion, 'Area', id_area, usuario_id)
        
        return area
    
    def buscar_areas(self, termino_busqueda: str, sucursal_id: int = None) -> List[dict]:
        """
        Busca áreas por nombre o descripción
        Args:
            termino_busqueda: Término a buscar
            sucursal_id: ID de sucursal para filtrar (opcional)
        Returns:
            Lista de áreas que coinciden con la búsqueda
        """
        if not termino_busqueda or len(termino_busqueda.strip()) < 2:
            raise ValueError("El término de búsqueda debe tener al menos 2 caracteres")
        
        return self.dao.buscar_por_nombre(termino_busqueda.strip(), sucursal_id)
    
    def obtener_estadisticas_por_sucursal(self, sucursal_id: int) -> dict:
        """
        Obtiene estadísticas de áreas por sucursal
        Args:
            sucursal_id: ID de la sucursal
        Returns:
            Diccionario con estadísticas
        """
        # Validar que la sucursal exista
        if not self.dao.validar_sucursal_existe(sucursal_id):
            raise ValueError(f"La sucursal con ID {sucursal_id} no existe o no está activa")
        
        estadisticas = self.dao.contar_por_sucursal(sucursal_id)
        estadisticas['sucursal_id'] = sucursal_id
        
        return estadisticas