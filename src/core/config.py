import os
from dotenv import load_dotenv
from datetime import timedelta

# Cargar variables de entorno
load_dotenv()

class Config:
    """Configuración base"""
    
    # Configuración de SQL Server
    SQLSERVER_HOST = os.environ.get('SQLSERVER_HOST') or 'localhost'
    SQLSERVER_PORT = os.environ.get('SQLSERVER_PORT') or '1433'
    SQLSERVER_DATABASE = os.environ.get('SQLSERVER_DATABASE') or 'cuisine_db'
    SQLSERVER_USERNAME = os.environ.get('SQLSERVER_USERNAME') or 'sa'
    SQLSERVER_PASSWORD = os.environ.get('SQLSERVER_PASSWORD') or 'your_password'
    SQLSERVER_DRIVER = os.environ.get('SQLSERVER_DRIVER') or 'ODBC Driver 17 for SQL Server'
    
    # String de conexión para SQL Server
    if os.environ.get('AZURE_SQL_CONNECTION_STRING'):
        # Usar connection string de Azure directamente
        SQLALCHEMY_DATABASE_URI = os.environ.get('AZURE_SQL_CONNECTION_STRING')
    else:
        # Construcción manual para desarrollo local
        SQLALCHEMY_DATABASE_URI = (
            f"mssql+pyodbc://{SQLSERVER_USERNAME}:{SQLSERVER_PASSWORD}"
            f"@{SQLSERVER_HOST}:{SQLSERVER_PORT}/{SQLSERVER_DATABASE}"
            f"?driver={SQLSERVER_DRIVER.replace(' ', '+')}"
        )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.environ.get('SQLALCHEMY_ECHO', 'False').lower() == 'true'
    
    # Configuración JWT
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 3600)))
    JWT_EXPIRATION_HOURS = int(os.environ.get('JWT_EXPIRATION_HOURS', 24))  # Para compatibilidad
    
    # Configuración CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # Configuración del pool de conexiones
    POOL_SIZE = int(os.environ.get('POOL_SIZE', 5))
    POOL_MAX_OVERFLOW = int(os.environ.get('POOL_MAX_OVERFLOW', 10))
    POOL_TIMEOUT = int(os.environ.get('POOL_TIMEOUT', 30))
    POOL_RECYCLE = int(os.environ.get('POOL_RECYCLE', 3600))
    
    # COnfiguracion de Firebase
    FIREBASE_PROJECT_ID = os.environ.get('FIREBASE_PROJECT_ID')
    GOOGLE_APPLICATION_CREDENTIALS = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    
    # Configuración SMTP para emails
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
    SMTP_USE_TLS = os.environ.get('SMTP_USE_TLS', 'True').lower() == 'true'
    SMTP_FROM_EMAIL = os.environ.get('SMTP_FROM_EMAIL')
    SMTP_FROM_NAME = os.environ.get('SMTP_FROM_NAME', 'Sistema Cuisine')
    
    # Debug de emails (si es True, solo imprime logs)
    EMAIL_DEBUG = os.environ.get('EMAIL_DEBUG', 'False').lower() == 'true'

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    
class TestingConfig(Config):
    """Configuración para testing"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Diccionario de configuraciones
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Obtiene la configuración basada en la variable de entorno"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config_by_name.get(env, DevelopmentConfig)
