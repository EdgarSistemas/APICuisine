"""
Servicio de lógica de negocio para la entidad Sucursal
Contiene toda la lógica de negocio, validaciones y transacciones
"""
from typing import List, Optional, Dict, Any
from marshmallow import ValidationError
from src.dao.catalogos.sucursal_dao import SucursalDAO
from src.schemas.sucursal_schema import (
    SucursalCreateSchema, SucursalUpdateSchema, SucursalFiltrosSchema,
    SucursalResponseSchema, SucursalSimpleSchema
)
from src.services.auditoria.log_service import log_action
import re

class SucursalService:
    """
    Servicio para gestión de sucursales con lógica de negocio
    """
    
    def __init__(self):
        self.dao = SucursalDAO()
        self.create_schema = SucursalCreateSchema()
        self.update_schema = SucursalUpdateSchema()
        self.response_schema = SucursalResponseSchema()
        self.simple_schema = SucursalSimpleSchema()
        self.filtros_schema = SucursalFiltrosSchema()
    
    def crear_sucursal(self, datos: dict, usuario_id: int = None) -> dict:
        """
        Crea una nueva sucursal con validaciones de negocio.
        Args:
            datos: Datos de la sucursal
            usuario_id: ID del usuario que crea
        Returns:
            Diccionario con datos de la sucursal creada
        """
        # Validar datos de entrada
        datos_validados = self.create_schema.load(datos)
        # Validar que el código no exista
        if self.dao.existe_codigo(datos_validados['codigo_sucursal']):
            raise ValueError(f"Ya existe una sucursal con el código {datos_validados['codigo_sucursal']}")
        # Normalizar código
        datos_validados['codigo_sucursal'] = datos_validados['codigo_sucursal'].upper()
        # Crear sucursal
        sucursal = self.dao.crear(datos_validados)
        # Log de auditoría
        if usuario_id and 'id_sucursal' in sucursal:
            log_action('CREATE', 'Sucursal', sucursal['id_sucursal'], usuario_id)
        return sucursal
    
    def obtener_sucursal(self, id_sucursal: int) -> dict:
        """
        Obtiene una sucursal por ID.
        Args:
            id_sucursal: ID de la sucursal
        Returns:
            Diccionario serializado de la sucursal
        """
        sucursal = self.dao.obtener_por_id(id_sucursal)
        if not sucursal:
            raise ValueError(f"Sucursal con ID {id_sucursal} no encontrada")
        return sucursal
    
    def listar_sucursales(self, usuario_id: int = None, es_admin: bool = False) -> List[dict]:
        """
        Lista todas las sucursales. Si el usuario es admin, muestra todas. Si no, filtra por las permitidas (si aplica).
        Args:
            usuario_id: ID del usuario que consulta (opcional)
            es_admin: Si el usuario es admin
        Returns:
            Lista de sucursales en formato JSON
        """
        if es_admin:
            return self.dao.listar_todas()
        # Si no es admin, aquí podrías filtrar por sucursales permitidas
        # Por ahora, retorna todas (puedes personalizar la lógica si tienes multi-tenant)
        return self.dao.listar_todas()
    
    def obtener_sucursales_activas(self) -> List[dict]:
        """
        Obtiene lista simple de sucursales activas
        Returns:
            Lista simplificada de sucursales activas
        """
        sucursales = self.dao.obtener_activas()
        return sucursales
    
    def actualizar_sucursal(self, id_sucursal: int, datos: dict, usuario_id: int = None) -> dict:
        """
        Actualiza una sucursal existente
        Args:
            id_sucursal: ID de la sucursal
            datos: Datos a actualizar
            usuario_id: ID del usuario que actualiza
        Returns:
            Diccionario con datos actualizados
        """
        # Validar datos de entrada
        datos_validados = self.update_schema.load(datos)
        # Verificar que existe
        if not self.dao.obtener_por_id(id_sucursal):
            raise ValueError(f"Sucursal con ID {id_sucursal} no encontrada")
        # Actualizar
        sucursal = self.dao.actualizar(id_sucursal, datos_validados)
        # Log de auditoría
        if usuario_id and sucursal and 'id_sucursal' in sucursal:
            log_action('UPDATE', 'Sucursal', id_sucursal, usuario_id)
        return sucursal
    
    def eliminar_sucursal(self, id_sucursal: int, usuario_id: int = None) -> bool:
        """
        Elimina lógicamente una sucursal
        
        Args:
            id_sucursal: ID de la sucursal
            usuario_id: ID del usuario que elimina
            
        Returns:
            True si se eliminó correctamente
        """
        # Verificar que existe
        if not self.dao.obtener_por_id(id_sucursal):
            raise ValueError(f"Sucursal con ID {id_sucursal} no encontrada")
        
        # Eliminar lógicamente
        resultado = self.dao.eliminar_logico(id_sucursal)
        
        # Log de auditoría
        if usuario_id and resultado:
            log_action('DELETE', 'Sucursal', id_sucursal, usuario_id)
        
        return resultado
    
    def activar_desactivar_sucursal(self, id_sucursal: int, activar: bool, usuario_id: int = None) -> dict:
        """
        Activa o desactiva una sucursal
        Args:
            id_sucursal: ID de la sucursal
            activar: True para activar, False para desactivar
            usuario_id: ID del usuario que realiza la acción
        Returns:
            Diccionario con datos actualizados
        """
        # Verificar que existe
        if not self.dao.obtener_por_id(id_sucursal):
            raise ValueError(f"Sucursal con ID {id_sucursal} no encontrada")
        # Cambiar estado
        sucursal = self.dao.activar_desactivar(id_sucursal, activar)
        # Log de auditoría
        if usuario_id and sucursal and 'id_sucursal' in sucursal:
            accion = 'ACTIVATE' if activar else 'DEACTIVATE'
            log_action(accion, 'Sucursal', id_sucursal, usuario_id)
        return sucursal