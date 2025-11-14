"""
Configuración de documentación con Flasgger - Versión simplificada para evitar errores YAML
"""

from flasgger import Swagger
from flask import Flask

def init_swagger(app: Flask):
    """
    Inicializar Swagger con Flasgger - Configuración básica sin errores
    """
    
    # Configuración que incluye TODOS los endpoints
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec',
                "route": '/apispec.json',
                "rule_filter": lambda rule: True,  # TODOS los endpoints
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/docs"
    }
    
    # Template con configuración JWT Bearer
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "API Cuisine",
            "description": "API para gestión de restaurantes y usuarios",
            "version": "1.0.0"
        },
        "host": "localhost:5000",
        "basePath": "/",
        "consumes": ["application/json"],
        "produces": ["application/json"],
        
        # ⭐ CONFIGURACIÓN DE AUTENTICACIÓN JWT
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Authorization header using the Bearer scheme. Example: 'Authorization: Bearer {token}'"
            }
        },
        
        # Seguridad global (opcional - se puede aplicar por endpoint)
        "security": [
            {"Bearer": []}
        ],
        
        "paths": {
            "/health": {
                "get": {
                    "tags": ["Sistema"],
                    "summary": "Health check",
                    "responses": {
                        "200": {
                            "description": "Sistema OK"
                        }
                    }
                }
            }
        }
    }
    
    # Inicializar Swagger
    swagger = Swagger(app, config=swagger_config, template=swagger_template)
    
    return swagger