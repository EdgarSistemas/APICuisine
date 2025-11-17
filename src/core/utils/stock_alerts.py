"""
stock_alerts.py - Utilidades para alertas de stock bajo

Funciones para:
1. Buscar insumos con stock por debajo del mínimo por sucursal
2. Consultar usuarios y extraer push tokens con filtros dinámicos
3. Enviar notificaciones vía Firebase Cloud Messaging (FCM)
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import and_, or_
from decimal import Decimal

from src.core.db.session_manager import get_db_session
from src.models import Insumo, UnidadMedida
from src.models.inventario import Existencia
from src.models.auth import Usuario, PushToken

logger = logging.getLogger(__name__)


class StockAlertDAO:
    """DAO para consultas de stock bajo y existencias"""
    
    @staticmethod
    def obtener_insumos_stock_bajo(sucursal_id: int, solo_activos: bool = True) -> List[Dict[str, Any]]:
        """
        Obtiene insumos donde la cantidad actual es MENOR que el mínimo stock.
        
        Ejemplo:
            - Insumo 1: minimo_stock=10, cantidad_actual=9 → INCLUYE
            - Insumo 2: minimo_stock=10, cantidad_actual=10 → NO incluye
            - Insumo 3: minimo_stock=10, cantidad_actual=11 → NO incluye
        
        Args:
            sucursal_id (int): ID de la sucursal
            solo_activos (bool): Si True, solo insumos activos
            
        Returns:
            List[Dict]: Lista de insumos con stock bajo:
            [
                {
                    "id_insumo": int,
                    "nombre": str,
                    "minimo_stock": float,
                    "cantidad_actual": float,
                    "diferencia": float,  # cantidad_actual - minimo_stock (negativo si está bajo)
                    "unidad_clave": str,
                    "unidad_nombre": str,
                    "es_activo": bool,
                    "costo_promedio": float,
                    "updated_at": str (ISO format)
                }
            ]
        """
        with get_db_session() as session:
            # Query que busca insumos donde cantidad < minimo_stock
            query = session.query(
                Insumo.id_insumo,
                Insumo.nombre,
                Insumo.minimo_stock,
                Existencia.cantidad,
                UnidadMedida.clave.label('unidad_clave'),
                UnidadMedida.nombre.label('unidad_nombre'),
                Insumo.es_activo,
                Existencia.costo_promedio,
                Existencia.updated_at
            ).join(
                UnidadMedida,
                Insumo.unidad_id == UnidadMedida.id_unidad
            ).join(
                Existencia,
                and_(
                    Existencia.insumo_id == Insumo.id_insumo,
                    Existencia.sucursal_id == sucursal_id
                )
            ).filter(
                # Condición clave: cantidad <= minimo_stock (igual o menor)
                Existencia.cantidad <= Insumo.minimo_stock
            )
            
            if solo_activos:
                query = query.filter(Insumo.es_activo == True)
            
            # Ordenar por diferencia (los más bajos primero)
            query = query.order_by(
                (Existencia.cantidad - Insumo.minimo_stock).asc()
            )
            
            resultados = query.all()
            
            insumos_bajo_stock = []
            for row in resultados:
                cantidad_actual = float(row.cantidad) if row.cantidad else 0.0
                minimo = float(row.minimo_stock) if row.minimo_stock else 0.0
                diferencia = cantidad_actual - minimo  # Será negativo
                
                insumos_bajo_stock.append({
                    "id_insumo": row.id_insumo,
                    "nombre": row.nombre,
                    "minimo_stock": minimo,
                    "cantidad_actual": cantidad_actual,
                    "diferencia": round(diferencia, 2),  # Negativo si está bajo
                    "unidad_clave": row.unidad_clave,
                    "unidad_nombre": row.unidad_nombre,
                    "es_activo": row.es_activo,
                    "costo_promedio": float(row.costo_promedio) if row.costo_promedio else 0.0,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None
                })
            
            logger.info(f"Se encontraron {len(insumos_bajo_stock)} insumos con stock bajo en sucursal {sucursal_id}")
            return insumos_bajo_stock


class PushTokenDAO:
    """DAO para consultas de usuarios y push tokens con filtros dinámicos"""
    
    @staticmethod
    def obtener_usuarios_con_push_tokens(
        filtros_usuario: Optional[Dict[str, Any]] = None,
        filtros_push_token: Optional[Dict[str, Any]] = None,
        solo_activos: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Consulta usuarios y extrae sus push tokens con filtros dinámicos.
        
        FILTROS USUARIO disponibles:
            - id_usuario (int): ID específico del usuario
            - email (str): Email exacto
            - nombre (str): Búsqueda parcial en nombre
            - es_cliente (bool): True para clientes, False para empleados
            - rol (str): Nombre del rol (ADMIN, GERENTE, EMPLEADO, etc.)
            - sucursal_id (int): ID de sucursal (busca en UsuarioSucursal)
            
        FILTROS PUSH_TOKEN disponibles:
            - plataforma (str): 'android' o 'web'
            - es_activo (bool): True para tokens activos
            
        Args:
            filtros_usuario (Dict): Filtros para Usuario (opcional)
            filtros_push_token (Dict): Filtros para PushToken (opcional)
            solo_activos (bool): Si True, solo usuarios activos (por defecto True)
            
        Returns:
            List[Dict]: Lista de usuarios con push tokens:
            [
                {
                    "usuario": {
                        "id_usuario": int,
                        "email": str,
                        "nombre": str,
                        "es_cliente": bool,
                        "es_activo": bool
                    },
                    "push_tokens": [
                        {
                            "id_push_token": int,
                            "plataforma": str,
                            "token": str,
                            "es_activo": bool
                        }
                    ]
                }
            ]
        """
        if not filtros_usuario:
            filtros_usuario = {}
        if not filtros_push_token:
            filtros_push_token = {}
        
        with get_db_session() as session:
            # Query base de usuarios
            query = session.query(Usuario).outerjoin(
                PushToken,
                Usuario.id_usuario == PushToken.usuario_id
            )
            
            # Aplicar filtros de usuario
            if 'id_usuario' in filtros_usuario:
                query = query.filter(Usuario.id_usuario == filtros_usuario['id_usuario'])
            
            if 'email' in filtros_usuario:
                query = query.filter(Usuario.email == filtros_usuario['email'])
            
            if 'nombre' in filtros_usuario:
                nombre_busqueda = f"%{filtros_usuario['nombre']}%"
                query = query.filter(Usuario.nombre.ilike(nombre_busqueda))
            
            if 'es_cliente' in filtros_usuario:
                query = query.filter(Usuario.es_cliente == filtros_usuario['es_cliente'])
            
            if 'rol' in filtros_usuario:
                from src.models.auth import Rol, UsuarioRol
                rol_nombre = filtros_usuario['rol']
                query = query.join(
                    UsuarioRol,
                    Usuario.id_usuario == UsuarioRol.usuario_id,
                    isouter=False
                ).join(
                    Rol,
                    UsuarioRol.rol_id == Rol.id_rol,
                    isouter=False
                ).filter(
                    Rol.nombre == rol_nombre
                )
            
            if 'sucursal_id' in filtros_usuario:
                from src.models.auth import UsuarioSucursal
                query = query.join(
                    UsuarioSucursal,
                    Usuario.id_usuario == UsuarioSucursal.usuario_id,
                    isouter=False
                ).filter(UsuarioSucursal.sucursal_id == filtros_usuario['sucursal_id'])
            
            # Aplicar filtro de usuarios activos
            if solo_activos:
                query = query.filter(Usuario.es_activo == True)
            
            # Aplicar filtros de push token
            if filtros_push_token:
                if 'plataforma' in filtros_push_token:
                    query = query.filter(PushToken.plataforma == filtros_push_token['plataforma'])
                
                if 'es_activo' in filtros_push_token:
                    query = query.filter(PushToken.es_activo == filtros_push_token['es_activo'])
            
            # Ordenar y ejecutar
            query = query.order_by(Usuario.nombre).distinct()
            usuarios = query.all()
            
            # Construir respuesta
            resultado = []
            for usuario in usuarios:
                # Filtrar push tokens por los filtros especificados
                push_tokens_validos = []
                
                for token in usuario.push_tokens:
                    # Verificar filtros de push token
                    if 'plataforma' in filtros_push_token:
                        if token.plataforma != filtros_push_token['plataforma']:
                            continue
                    
                    if 'es_activo' in filtros_push_token:
                        if token.es_activo != filtros_push_token['es_activo']:
                            continue
                    
                    push_tokens_validos.append({
                        "id_push_token": token.id_push_token,
                        "plataforma": token.plataforma,
                        "token": token.token,
                        "es_activo": token.es_activo
                    })
                
                # Solo incluir usuario si tiene push tokens válidos
                if push_tokens_validos:
                    resultado.append({
                        "usuario": {
                            "id_usuario": usuario.id_usuario,
                            "email": usuario.email,
                            "nombre": usuario.nombre,
                            "es_cliente": usuario.es_cliente,
                            "es_activo": usuario.es_activo
                        },
                        "push_tokens": push_tokens_validos
                    })
            
            logger.info(f"Se obtuvieron {len(resultado)} usuarios con push tokens usando filtros: usuario={filtros_usuario}, token={filtros_push_token}")
            return resultado
    
    
    @staticmethod
    def obtener_todos_push_tokens_por_usuario_id(usuario_id: int, solo_activos: bool = True) -> List[str]:
        """
        Obtiene todos los push tokens de un usuario específico.
        
        Args:
            usuario_id (int): ID del usuario
            solo_activos (bool): Si True, solo tokens activos
            
        Returns:
            List[str]: Lista de push tokens
        """
        with get_db_session() as session:
            query = session.query(PushToken.token).filter(
                PushToken.usuario_id == usuario_id
            )
            
            if solo_activos:
                query = query.filter(PushToken.es_activo == True)
            
            tokens = query.all()
            return [token[0] for token in tokens]
    
    
    @staticmethod
    def obtener_push_tokens_por_sucursal(
        sucursal_id: int,
        plataforma: Optional[str] = None,
        solo_activos: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Obtiene push tokens de todos los usuarios de una sucursal.
        
        Args:
            sucursal_id (int): ID de la sucursal
            plataforma (str): Filtrar por 'android' o 'web' (opcional)
            solo_activos (bool): Si True, solo tokens activos
            
        Returns:
            List[Dict]: Lista de {usuario_id, token, plataforma, es_activo}
        """
        from src.models.auth import UsuarioSucursal
        
        with get_db_session() as session:
            query = session.query(
                Usuario.id_usuario,
                Usuario.nombre,
                PushToken.id_push_token,
                PushToken.token,
                PushToken.plataforma,
                PushToken.es_activo
            ).join(
                UsuarioSucursal,
                Usuario.id_usuario == UsuarioSucursal.usuario_id
            ).join(
                PushToken,
                Usuario.id_usuario == PushToken.usuario_id
            ).filter(
                UsuarioSucursal.sucursal_id == sucursal_id,
                Usuario.es_activo == True
            )
            
            if plataforma:
                query = query.filter(PushToken.plataforma == plataforma)
            
            if solo_activos:
                query = query.filter(PushToken.es_activo == True)
            
            resultados = query.all()
            
            tokens_list = [
                {
                    "usuario_id": row.id_usuario,
                    "usuario_nombre": row.nombre,
                    "id_push_token": row.id_push_token,
                    "token": row.token,
                    "plataforma": row.plataforma,
                    "es_activo": row.es_activo
                }
                for row in resultados
            ]
            
            logger.info(f"Se obtuvieron {len(tokens_list)} push tokens para sucursal {sucursal_id}")
            return tokens_list

