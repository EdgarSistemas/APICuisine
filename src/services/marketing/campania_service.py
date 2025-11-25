"""
CampaniaService - Lógica de negocio para Campañas y Cupones
Responsabilidades:
- Gestión de campañas promocionales
- Asignación de cupones a clientes
- Validación de cupones para pagos
"""

import logging
from datetime import datetime
from decimal import Decimal

from src.dao.marketing.campania_dao import CampaniaDAO

logger = logging.getLogger(__name__)


class CampaniaService:
    """
    Servicio para gestión de campañas de marketing y cupones de descuento.
    """
    
    # =========================================================================
    # GESTIÓN DE CAMPAÑAS
    # =========================================================================
    
    @staticmethod
    def crear_campania(
        usuario_id: int,
        nombre_campania: str,
        porcentaje_desc: float,
        codigo: str = None
    ) -> dict:
        """
        Crear nueva campaña de marketing.
        
        Args:
            usuario_id: ID del usuario que crea
            nombre_campania: Nombre de la campaña
            porcentaje_desc: Porcentaje de descuento (ej: 10 = 10%)
            codigo: Código de cupón único (opcional)
        
        Returns:
            dict: {success: bool, data: {campania}, error: str}
        """
        try:
            # Validaciones
            if not nombre_campania or len(nombre_campania.strip()) < 3:
                return {
                    'success': False,
                    'error': 'El nombre de la campaña debe tener al menos 3 caracteres'
                }
            
            if porcentaje_desc <= 0 or porcentaje_desc > 100:
                return {
                    'success': False,
                    'error': 'El porcentaje de descuento debe estar entre 0.01 y 100'
                }
            
            campania = CampaniaDAO.crear_campania(
                usuario_crea_id=usuario_id,
                nombre_campania=nombre_campania.strip(),
                porcentaje_desc=Decimal(str(porcentaje_desc)),
                codigo=codigo.strip().upper() if codigo else None,
                estatus=1
            )
            
            logger.info(f"Campaña creada: {campania['id_campania']} por usuario {usuario_id}")
            
            return {
                'success': True,
                'data': campania
            }
            
        except ValueError as e:
            logger.warning(f"Error de validación creando campaña: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Error creando campaña: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Error interno: {str(e)}'
            }
    
    
    @staticmethod
    def obtener_campania(campania_id: int) -> dict:
        """Obtener campaña por ID"""
        try:
            campania = CampaniaDAO.obtener_campania(campania_id)
            
            if not campania:
                return {
                    'success': False,
                    'error': f'Campaña {campania_id} no existe'
                }
            
            return {
                'success': True,
                'data': campania
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo campaña: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    
    @staticmethod
    def listar_campanias(estatus: int = None, limit: int = 50, offset: int = 0) -> dict:
        """Listar campañas con filtros"""
        try:
            resultado = CampaniaDAO.listar_campanias(
                estatus=estatus,
                limit=limit,
                offset=offset
            )
            
            return {
                'success': True,
                'data': resultado
            }
            
        except Exception as e:
            logger.error(f"Error listando campañas: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    
    @staticmethod
    def activar_campania(campania_id: int) -> dict:
        """Activar campaña (estatus = 1)"""
        try:
            campania = CampaniaDAO.cambiar_estatus_campania(campania_id, 1)
            logger.info(f"Campaña {campania_id} activada")
            return {
                'success': True,
                'data': campania
            }
        except ValueError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error activando campaña: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    
    @staticmethod
    def desactivar_campania(campania_id: int) -> dict:
        """Desactivar campaña (estatus = 0)"""
        try:
            campania = CampaniaDAO.cambiar_estatus_campania(campania_id, 0)
            logger.info(f"Campaña {campania_id} desactivada")
            return {
                'success': True,
                'data': campania
            }
        except ValueError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Error desactivando campaña: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    
    # =========================================================================
    # GESTIÓN DE CUPONES DE USUARIO
    # =========================================================================
    
    @staticmethod
    def asignar_cupon(
        cliente_id: int,
        campania_id: int,
        fecha_vigencia: datetime = None
    ) -> dict:
        """
        Asignar cupón de campaña a un cliente.
        
        Args:
            cliente_id: ID del cliente
            campania_id: ID de la campaña
            fecha_vigencia: Fecha límite de uso
        
        Returns:
            dict: {success: bool, data: {asignacion}, error: str}
        """
        try:
            asignacion = CampaniaDAO.asignar_cupon_usuario(
                cliente_id=cliente_id,
                campania_id=campania_id,
                fecha_vigencia=fecha_vigencia
            )
            
            logger.info(f"Cupón asignado: Cliente {cliente_id}, Campaña {campania_id}")
            
            return {
                'success': True,
                'data': asignacion
            }
            
        except ValueError as e:
            logger.warning(f"Error asignando cupón: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Error asignando cupón: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Error interno: {str(e)}'
            }
    
    
    @staticmethod
    def listar_cupones_cliente(cliente_id: int, solo_disponibles: bool = True) -> dict:
        """
        Listar cupones de un cliente.
        
        Args:
            cliente_id: ID del cliente
            solo_disponibles: Si True, solo cupones vigentes y no usados
        
        Returns:
            dict: {success: bool, data: [cupones], error: str}
        """
        try:
            cupones = CampaniaDAO.listar_cupones_usuario(
                cliente_id=cliente_id,
                solo_disponibles=solo_disponibles
            )
            
            return {
                'success': True,
                'data': cupones
            }
            
        except Exception as e:
            logger.error(f"Error listando cupones: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    
    # =========================================================================
    # VALIDACIÓN DE CUPÓN (Para uso en Pago)
    # =========================================================================
    
    @staticmethod
    def validar_cupon(codigo: str, cliente_id: int) -> dict:
        """
        Validar si un cupón es válido para un cliente.
        
        Validaciones:
            1. Campaña existe (por código)
            2. Campaña activa
            3. Cupón asignado al cliente
            4. Cupón no usado
            5. Cupón vigente (timezone México)
        
        Args:
            codigo: Código del cupón
            cliente_id: ID del cliente
        
        Returns:
            dict: {
                success: bool,
                valido: bool,
                data: {campania, porcentaje_desc, campania_usuario_id},
                error: str
            }
        """
        try:
            if not codigo or not codigo.strip():
                return {
                    'success': False,
                    'valido': False,
                    'error': 'Código de cupón requerido'
                }
            
            resultado = CampaniaDAO.validar_cupon(
                codigo=codigo.strip(),
                cliente_id=cliente_id
            )
            
            if resultado['valido']:
                logger.info(f"Cupón '{codigo}' validado para cliente {cliente_id}")
                return {
                    'success': True,
                    'valido': True,
                    'data': resultado
                }
            else:
                logger.warning(f"Cupón '{codigo}' inválido: {resultado.get('error')}")
                return {
                    'success': True,
                    'valido': False,
                    'error': resultado.get('error')
                }
                
        except Exception as e:
            logger.error(f"Error validando cupón: {str(e)}", exc_info=True)
            return {
                'success': False,
                'valido': False,
                'error': f'Error interno: {str(e)}'
            }
    
    
    @staticmethod
    def marcar_cupon_usado(campania_usuario_id: int) -> dict:
        """
        Marcar cupón como usado después de aplicar en pago.
        
        Args:
            campania_usuario_id: ID de la asignación
        
        Returns:
            dict: {success: bool, data: {asignacion}, error: str}
        """
        try:
            asignacion = CampaniaDAO.marcar_cupon_usado(campania_usuario_id)
            
            logger.info(f"Cupón {campania_usuario_id} marcado como usado")
            
            return {
                'success': True,
                'data': asignacion
            }
            
        except ValueError as e:
            logger.warning(f"Error marcando cupón usado: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Error marcando cupón usado: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    
    @staticmethod
    def calcular_descuento(monto: Decimal, porcentaje_desc: Decimal) -> Decimal:
        """
        Calcular monto de descuento.
        
        Args:
            monto: Monto original
            porcentaje_desc: Porcentaje de descuento (ej: 10 = 10%)
        
        Returns:
            Decimal: Monto a descontar
        """
        if not monto or monto <= 0:
            return Decimal('0.00')
        
        if not porcentaje_desc or porcentaje_desc <= 0:
            return Decimal('0.00')
        
        descuento = (Decimal(str(monto)) * Decimal(str(porcentaje_desc))) / Decimal('100')
        return descuento.quantize(Decimal('0.01'))
    
    
    # =========================================================================
    # MÉTRICAS CRM - Segmentación de Clientes
    # =========================================================================
    
    @staticmethod
    def obtener_clientes_vip(top_n: int = 20) -> dict:
        """
        Obtener TOP clientes por gasto total.
        
        Args:
            top_n: Número de clientes TOP a retornar
        
        Returns:
            dict: {success: bool, data: [clientes], error: str}
        """
        try:
            clientes = CampaniaDAO.obtener_clientes_vip(top_n=top_n)
            return {
                'success': True,
                'data': clientes,
                'metrica': 'clientes_vip',
                'descripcion': f'TOP {top_n} clientes por gasto total'
            }
        except Exception as e:
            logger.error(f"Error obteniendo clientes VIP: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    
    @staticmethod
    def obtener_clientes_frecuentes(top_n: int = 20) -> dict:
        """
        Obtener clientes con mayor frecuencia de visitas.
        
        Args:
            top_n: Número de clientes TOP a retornar
        
        Returns:
            dict: {success: bool, data: [clientes], error: str}
        """
        try:
            clientes = CampaniaDAO.obtener_clientes_frecuentes(top_n=top_n)
            return {
                'success': True,
                'data': clientes,
                'metrica': 'clientes_frecuentes',
                'descripcion': f'TOP {top_n} clientes por frecuencia de visitas'
            }
        except Exception as e:
            logger.error(f"Error obteniendo clientes frecuentes: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    
    @staticmethod
    def obtener_clientes_inactivos(dias_sin_comprar: int = 30) -> dict:
        """
        Obtener clientes que no han comprado en X días.
        
        Args:
            dias_sin_comprar: Número de días sin actividad
        
        Returns:
            dict: {success: bool, data: [clientes], error: str}
        """
        try:
            clientes = CampaniaDAO.obtener_clientes_inactivos(dias_sin_comprar=dias_sin_comprar)
            return {
                'success': True,
                'data': clientes,
                'metrica': 'clientes_inactivos',
                'descripcion': f'Clientes sin comprar en {dias_sin_comprar}+ dias'
            }
        except Exception as e:
            logger.error(f"Error obteniendo clientes inactivos: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    
    @staticmethod
    def obtener_clientes_nuevos(dias_registro: int = 30) -> dict:
        """
        Obtener clientes registrados recientemente.
        
        Args:
            dias_registro: Días desde el registro para considerar "nuevo"
        
        Returns:
            dict: {success: bool, data: [clientes], error: str}
        """
        try:
            clientes = CampaniaDAO.obtener_clientes_nuevos(dias_registro=dias_registro)
            return {
                'success': True,
                'data': clientes,
                'metrica': 'clientes_nuevos',
                'descripcion': f'Clientes nuevos (ultimos {dias_registro} dias o <= 2 pedidos)'
            }
        except Exception as e:
            logger.error(f"Error obteniendo clientes nuevos: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    
    @staticmethod
    def obtener_clientes_por_canal() -> dict:
        """
        Segmentar clientes por canal preferido.
        
        Returns:
            dict: {success: bool, data: [clientes], error: str}
        """
        try:
            clientes = CampaniaDAO.obtener_clientes_por_canal()
            return {
                'success': True,
                'data': clientes,
                'metrica': 'clientes_por_canal',
                'descripcion': 'Clientes segmentados por canal (Mesa/Takeaway/Delivery)'
            }
        except Exception as e:
            logger.error(f"Error obteniendo clientes por canal: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    
    @staticmethod
    def generar_campania_desde_metrica(
        usuario_id: int,
        nombre_campania: str,
        porcentaje_desc: float,
        codigo: str,
        cliente_ids: list,
        fecha_vigencia: datetime = None
    ) -> dict:
        """
        Crear campaña y asignar cupones a lista de clientes de una métrica.
        
        Args:
            usuario_id: ID del usuario que crea
            nombre_campania: Nombre de la campaña
            porcentaje_desc: Porcentaje de descuento
            codigo: Código del cupón
            cliente_ids: Lista de IDs de clientes
            fecha_vigencia: Fecha límite de uso
        
        Returns:
            dict: {success: bool, data: {campania, asignaciones}, error: str}
        """
        try:
            if not cliente_ids or len(cliente_ids) == 0:
                return {
                    'success': False,
                    'error': 'Debe seleccionar al menos un cliente'
                }
            
            # 1. Crear la campaña
            result_campania = CampaniaService.crear_campania(
                usuario_id=usuario_id,
                nombre_campania=nombre_campania,
                porcentaje_desc=porcentaje_desc,
                codigo=codigo
            )
            
            if not result_campania['success']:
                return result_campania
            
            campania = result_campania['data']
            campania_id = campania['id_campania']
            
            # 2. Asignar cupones masivamente
            resultado_asignacion = CampaniaDAO.asignar_cupones_masivo(
                cliente_ids=cliente_ids,
                campania_id=campania_id,
                fecha_vigencia=fecha_vigencia
            )
            
            logger.info(
                f"Campaña {campania_id} generada desde métrica: "
                f"{resultado_asignacion['asignados']} cupones asignados"
            )
            
            return {
                'success': True,
                'data': {
                    'campania': campania,
                    'asignaciones': resultado_asignacion
                }
            }
            
        except Exception as e:
            logger.error(f"Error generando campaña desde métrica: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Error interno: {str(e)}'
            }
