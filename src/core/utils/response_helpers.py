"""
Response Helpers - Funciones para crear respuestas HTTP estandarizadas
"""

import time
import threading
from typing import Dict, Any, Optional, Union, List


def get_thread_info() -> Dict[str, Any]:
    """
    Obtener información del hilo actual
    
    Returns:
        Dict con información del hilo
    """
    return {
        "thread_id": threading.current_thread().ident,
        "thread_name": threading.current_thread().name
    }


def create_success_response(
    data: Optional[Dict[str, Any]] = None, 
    message: Optional[str] = None,
    status_code: int = 200,
    include_timestamp: bool = True
) -> tuple[Dict[str, Any], int]:
    """
    Crear respuesta de éxito estandarizada
    
    Args:
        data: Datos a incluir en la respuesta
        message: Mensaje descriptivo opcional
        status_code: Código de estado HTTP
        include_timestamp: Si incluir timestamp en la respuesta
        
    Returns:
        Tupla con diccionario de respuesta y código de estado
    """
    response = {
        "success": True
    }
    
    if message:
        response["message"] = message
        
    if data:
        response.update(data)
        
    if include_timestamp:
        response["timestamp"] = time.time()
        
    return response, status_code


def create_error_response(
    error: Union[str, Exception],
    status_code: int = 500,
    include_timestamp: bool = True,
    additional_data: Optional[Dict[str, Any]] = None
) -> tuple[Dict[str, Any], int]:
    """
    Crear respuesta de error estandarizada
    
    Args:
        error: Error a reportar (string o excepción)
        status_code: Código de estado HTTP
        include_timestamp: Si incluir timestamp en la respuesta
        additional_data: Datos adicionales a incluir
        
    Returns:
        Tupla con diccionario de respuesta y código de estado
    """
    response = {
        "success": False,
        "error": str(error)
    }
    
    if additional_data:
        response.update(additional_data)
        
    if include_timestamp:
        response["timestamp"] = time.time()
        
    return response, status_code


def create_not_found_response(
    resource: str,
    available_options: Optional[List[str]] = None
) -> tuple[Dict[str, Any], int]:
    """
    Crear respuesta de recurso no encontrado
    
    Args:
        resource: Descripción del recurso no encontrado
        available_options: Lista de opciones disponibles
        
    Returns:
        Tupla con diccionario de respuesta y código 404
    """
    additional_data = {}
    if available_options:
        additional_data["available_options"] = available_options
        
    return create_error_response(
        error=f"{resource} no encontrado",
        status_code=404,
        additional_data=additional_data
    )


def create_validation_error_response(
    validation_errors: Union[str, List[str], Dict[str, Any]]
) -> tuple[Dict[str, Any], int]:
    """
    Crear respuesta de error de validación
    
    Args:
        validation_errors: Errores de validación
        
    Returns:
        Tupla con diccionario de respuesta y código 400
    """
    additional_data = {"validation_errors": validation_errors}
    
    return create_error_response(
        error="Error de validación",
        status_code=400,
        additional_data=additional_data
    )