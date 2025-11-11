"""
Helpers para Flask-JWT-Extended
"""

from functools import wraps
from flask import g, jsonify
from flask_jwt_extended import get_jwt_identity, get_jwt

def get_current_user():
    """
    Función helper para obtener el usuario actual desde JWT
    
    Returns:
        dict: Datos del usuario actual construidos desde JWT claims
    """
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return None
            
        claims = get_jwt()
        
        current_user = {
            'user_id': int(user_id),  # Convertir de string a int
            'email': claims.get('email', ''),
            'nombre': claims.get('nombre', ''),
            'apellido': claims.get('apellido', ''),
            'roles': claims.get('roles', []),
            'modulos': claims.get('modulos', []),
            'es_admin': claims.get('es_admin', False),
            'exp': claims.get('exp'),
            'iat': claims.get('iat')
        }
        
        return current_user
        
    except Exception:
        return None

def get_current_user_id():
    """
    Función helper para obtener el ID del usuario actual
    
    Returns:
        int: ID del usuario actual o None si no está autenticado
    """
    try:
        user_id = get_jwt_identity()
        return int(user_id) if user_id else None
    except Exception:
        return None

def get_current_user_roles():
    """
    Función helper para obtener los roles del usuario actual
    
    Returns:
        list: Lista de roles del usuario actual
    """
    try:
        claims = get_jwt()
        return claims.get('roles', [])
    except Exception:
        return []

def get_current_user_email():
    """
    Función helper para obtener el email del usuario actual
    
    Returns:
        str: Email del usuario actual
    """
    try:
        claims = get_jwt()
        return claims.get('email', '')
    except Exception:
        return ''

def admin_required(f):
    """
    Decorador para verificar que el usuario actual es administrador
    
    Returns:
        function: Función decorada que verifica permisos de admin
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            user = get_current_user()
            if not user:
                return jsonify({
                    'success': False,
                    'error': 'AUTHENTICATION_REQUIRED',
                    'message': 'Token de autenticación requerido'
                }), 401
            
            if not user.get('es_admin', False):
                return jsonify({
                    'success': False,
                    'error': 'ADMIN_REQUIRED',
                    'message': 'Se requieren permisos de administrador'
                }), 403
            
            return f(*args, **kwargs)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': 'AUTHORIZATION_ERROR',
                'message': 'Error al verificar permisos'
            }), 500
    
    return decorated