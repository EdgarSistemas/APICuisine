from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import declarative_base
from sqlalchemy import text, inspect
from .pool_manager import pool_manager
from .session_manager import get_db_connection
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

DeclarativeBase = declarative_base()
AutomapBase = automap_base()

class DatabaseReflection:
    _reflected = False
    
    @classmethod
    def get_available_schemas(cls) -> List[str]:
        try:
            query = text("""
                SELECT DISTINCT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name NOT IN ('information_schema', 'sys', 'db_owner', 'db_accessadmin', 'db_securityadmin', 'db_ddladmin', 'db_backupoperator', 'db_datawriter', 'db_datareader', 'db_denydatawriter', 'db_denydatareader')
                ORDER BY schema_name
            """)
            
            with get_db_connection() as conn:
                result = conn.execute(query)
                return [row[0] for row in result]
                
        except Exception as e:
            logger.error(f"Error obteniendo schemas: {e}")
            return ['dbo', 'catalogos', 'operaciones', 'seguridad', 'inventario', 
                   'pagos', 'config', 'auditoria', 'movil', 'rrhh', 
                   'ticket', 'servicio', 'marketing']
    
    @classmethod
    def get_tables_in_schema(cls, schema: str) -> List[str]:
        try:
            query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = :schema 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            
            with get_db_connection() as conn:
                result = conn.execute(query, {"schema": schema})
                return [row[0] for row in result]
                
        except Exception as e:
            logger.error(f"Error obteniendo tablas del schema {schema}: {e}")
            return []
    
    @classmethod
    def reflect_database(cls):
        if cls._reflected:
            return AutomapBase
            
        try:
            engine = pool_manager.get_engine()
            inspector = inspect(engine)
            available_schemas = cls.get_available_schemas()
            
            for schema in available_schemas:
                try:
                    tables_in_schema = inspector.get_table_names(schema=schema)
                    
                    if tables_in_schema:
                        for table_name in tables_in_schema:
                            try:
                                AutomapBase.metadata.reflect(
                                    bind=engine,
                                    schema=schema,
                                    only=[table_name],
                                    extend_existing=True
                                )
                            except Exception as e:
                                logger.warning(f"Error reflejando {schema}.{table_name}: {e}")
                except Exception as e:
                    logger.error(f"Error procesando schema {schema}: {e}")
                    continue
            
            AutomapBase.prepare(engine, reflect=False)
            cls._reflected = True
            return AutomapBase
            
        except Exception as e:
            logger.error(f"Error en reflexión: {e}")
            raise e
    
    @classmethod
    def get_table_names(cls) -> List[str]:
        try:
            if not cls._reflected:
                cls.reflect_database()
            return list(AutomapBase.classes.keys())
        except Exception as e:
            logger.error(f"Error al obtener nombres de tablas: {e}")
            return []
    
    @classmethod
    def get_tables_by_schema(cls) -> Dict[str, List[str]]:
        try:
            schemas = cls.get_available_schemas()
            tables_by_schema = {}
            
            for schema in schemas:
                tables = cls.get_tables_in_schema(schema)
                if tables:
                    tables_by_schema[schema] = tables
            
            return tables_by_schema
        except Exception as e:
            logger.error(f"Error al obtener tablas por schema: {e}")
            return {}
    
    @classmethod
    def get_table_class(cls, table_name: str, schema: str = None):
        try:
            if not cls._reflected:
                cls.reflect_database()
            
            possible_names = []
            
            if schema:
                possible_names.extend([
                    f"{schema}_{table_name}",
                    f"{schema}.{table_name}",
                    f"{schema.title()}{table_name}",
                    f"{schema.title()}{table_name.title()}",
                ])
            
            possible_names.extend([
                table_name,
                table_name.title(),
                table_name.lower(),
                table_name.upper()
            ])
            
            for name in possible_names:
                if name in AutomapBase.classes:
                    return AutomapBase.classes[name]
            
            for class_name, cls_obj in AutomapBase.classes.items():
                try:
                    table_obj = cls_obj.__table__
                    if (table_obj.name == table_name and 
                        (not schema or table_obj.schema == schema)):
                        return cls_obj
                except Exception:
                    continue
            
            return None
        except Exception as e:
            logger.error(f"Error al obtener clase de tabla {table_name}: {e}")
            return None
    
    @classmethod
    def get_table_info(cls, table_name: str, schema: str = None) -> Optional[Dict[str, Any]]:
        try:
            table_class = cls.get_table_class(table_name, schema)
            if not table_class:
                return None
            
            table_obj = table_class.__table__
            
            columns = []
            for col in table_obj.columns:
                col_info = {
                    'name': col.name,
                    'type': str(col.type),
                    'nullable': col.nullable,
                    'primary_key': col.primary_key,
                    'foreign_keys': [str(fk) for fk in col.foreign_keys] if col.foreign_keys else []
                }
                columns.append(col_info)
            
            return {
                'schema': table_obj.schema or 'dbo',
                'table_name': table_obj.name,
                'full_name': f"{table_obj.schema}.{table_obj.name}" if table_obj.schema else table_obj.name,
                'columns': columns,
                'primary_keys': [col.name for col in table_obj.primary_key],
                'foreign_keys': list(table_obj.foreign_keys)
            }
            
        except Exception as e:
            logger.error(f"Error al obtener info de tabla {table_name}: {e}")
            return None

def get_automap_base():
    if not DatabaseReflection._reflected:
        DatabaseReflection.reflect_database()
    return AutomapBase

def get_model_class(table_name: str, schema: str = None):
    return DatabaseReflection.get_table_class(table_name, schema)

def list_available_tables() -> List[str]:
    return DatabaseReflection.get_table_names()

def get_tables_by_schema() -> Dict[str, List[str]]:
    return DatabaseReflection.get_tables_by_schema()

def get_table_info(table_name: str, schema: str = None) -> Optional[Dict[str, Any]]:
    return DatabaseReflection.get_table_info(table_name, schema)