"""
CompraDAO y CompraDetalleDAO - Data Access Objects para inventario.Compra y CompraDetalle
"""

from src.models import Compra, CompraDetalle, Insumo, UnidadMedida, Proveedor, Sucursal, Usuario
from src.core.db.session_manager import get_db_session
from src.schemas.compra_schema import CompraResponseSchema, CompraDetalleResponseSchema, CompraDetailedSchema
import logging

logger = logging.getLogger(__name__)


class CompraDAO:
    """Data Access Object para Compra"""
    
    @staticmethod
    def crear_compra(usuario_id: int, sucursal_id: int, proveedor_id: int, 
                    folio: str) -> dict:
        """
        Crear nueva compra.
        
        Args:
            usuario_id: ID del usuario que crea
            sucursal_id: ID de la sucursal
            proveedor_id: ID del proveedor
            folio: Folio de la compra
            
        Returns:
            Dict serializado de la compra
        """
        schema = CompraResponseSchema()
        with get_db_session() as session:
            compra = Compra(
                usuario_id=usuario_id,
                sucursal_id=sucursal_id,
                proveedor_id=proveedor_id,
                folio=folio,
                estatus=1  # 1=Registrada
            )
            session.add(compra)
            session.commit()
            logger.info(f"Compra creada: {folio} (ID: {compra.id_compra})")
            return schema.dump(compra)
    
    
    @staticmethod
    def obtener_compra_por_id(compra_id: int) -> dict:
        """
        Obtener compra por ID.
        
        Args:
            compra_id: ID de la compra
            
        Returns:
            Dict de la compra o None
        """
        schema = CompraResponseSchema()
        with get_db_session() as session:
            compra = session.query(Compra).filter(
                Compra.id_compra == compra_id
            ).first()
            return schema.dump(compra) if compra else None
    
    
    @staticmethod
    def obtener_compra_detallada(compra_id: int) -> dict:
        """
        Obtener compra con detalles.
        
        Args:
            compra_id: ID de la compra
            
        Returns:
            Dict con estructura: {id_compra, ..., detalles: [...]}
        """
        schema = CompraDetailedSchema()
        with get_db_session() as session:
            compra = session.query(Compra).filter(
                Compra.id_compra == compra_id
            ).first()
            
            if not compra:
                return None
            
            # Construir respuesta
            resultado = {
                "id_compra": compra.id_compra,
                "usuario_id": compra.usuario_id,
                "sucursal_id": compra.sucursal_id,
                "proveedor_id": compra.proveedor_id,
                "folio": compra.folio,
                "fecha_compra": compra.fecha_compra.strftime('%Y-%m-%d %H:%M:%S') if compra.fecha_compra else None,
                "estatus": compra.estatus,
                "created_at": compra.created_at.strftime('%Y-%m-%d %H:%M:%S') if compra.created_at else None,
                "updated_at": compra.updated_at.strftime('%Y-%m-%d %H:%M:%S') if compra.updated_at else None,
                "detalles": []
            }
            
            # Obtener detalles
            detalles = session.query(CompraDetalle).filter(
                CompraDetalle.compra_id == compra_id
            ).all()
            
            for detalle in detalles:
                det_dict = {
                    "id_compra_detalle": detalle.id_compra_detalle,
                    "compra_id": detalle.compra_id,
                    "insumo_id": detalle.insumo_id,
                    "cant_presentacion": float(detalle.cant_presentacion),
                    "costo_unit_present": float(detalle.costo_unit_present),
                    "created_at": detalle.created_at.strftime('%Y-%m-%d %H:%M:%S') if detalle.created_at else None,
                    "updated_at": detalle.updated_at.strftime('%Y-%m-%d %H:%M:%S') if detalle.updated_at else None
                }
                resultado["detalles"].append(det_dict)
            
            return resultado
    
    
    @staticmethod
    def obtener_compra_completa(compra_id: int) -> dict:
        """
        Obtener compra con datos completos: proveedor, sucursal, usuario,
        detalles con insumo y unidad de medida.
        
        Args:
            compra_id: ID de la compra
            
        Returns:
            {
                id_compra, folio, fecha_compra, estatus,
                proveedor: {id, nombre, telefono, email},
                sucursal: {id, nombre, codigo},
                usuario: {id, nombre, apellido, email},
                detalles: [{
                    id_compra_detalle, cant_presentacion, costo_unit_present, presentacion,
                    insumo: {
                        id_insumo, nombre,
                        unidad_medida: {id, clave, nombre, simbolo}
                    }
                }]
            }
        """
        with get_db_session() as session:
            compra = session.query(Compra).filter(
                Compra.id_compra == compra_id
            ).first()
            
            if not compra:
                return None
            
            # Construir respuesta completa
            resultado = {
                "id_compra": compra.id_compra,
                "folio": compra.folio,
                "fecha_compra": compra.fecha_compra.strftime('%Y-%m-%d %H:%M:%S') if compra.fecha_compra else None,
                "estatus": compra.estatus,
                "created_at": compra.created_at.strftime('%Y-%m-%d %H:%M:%S') if compra.created_at else None,
                "updated_at": compra.updated_at.strftime('%Y-%m-%d %H:%M:%S') if compra.updated_at else None
            }
            
            # Agregar proveedor
            if compra.proveedor:
                resultado["proveedor"] = {
                    "id_proveedor": compra.proveedor.id_proveedor,
                    "nombre": compra.proveedor.nombre,
                    "telefono": compra.proveedor.telefono,
                    "email": compra.proveedor.email
                }
            
            # Agregar sucursal
            if compra.sucursal:
                resultado["sucursal"] = {
                    "id_sucursal": compra.sucursal.id_sucursal,
                    "nombre": compra.sucursal.nombre,
                    "codigo_sucursal": compra.sucursal.codigo_sucursal
                }
            
            # Agregar usuario
            if compra.usuario:
                resultado["usuario"] = {
                    "id_usuario": compra.usuario.id_usuario,
                    "nombre": compra.usuario.nombre,
                    "apellido": compra.usuario.apellido,
                    "email": compra.usuario.email
                }
            
            # Agregar detalles con insumo y unidad de medida
            detalles = session.query(CompraDetalle).filter(
                CompraDetalle.compra_id == compra_id
            ).all()
            
            resultado["detalles"] = []
            total_compra = 0.0
            for detalle in detalles:
                # Obtener insumo con unidad de medida
                insumo = session.query(Insumo).filter(
                    Insumo.id_insumo == detalle.insumo_id
                ).first()
                
                det_dict = {
                    "id_compra_detalle": detalle.id_compra_detalle,
                    "cant_presentacion": float(detalle.cant_presentacion),
                    "presentacion": detalle.presentacion,
                    "costo_unit_present": float(detalle.costo_unit_present),
                    "subtotal": float(detalle.cant_presentacion) * float(detalle.costo_unit_present),
                    "insumo": {
                        "id_insumo": insumo.id_insumo,
                        "nombre": insumo.nombre,
                        "unidad_medida": {
                            "id_unidad_medida": insumo.unidad_medida.id_unidad,
                            "clave": insumo.unidad_medida.clave,
                            "nombre": insumo.unidad_medida.nombre
                        } if insumo.unidad_medida else None
                    }
                }
                resultado["detalles"].append(det_dict)
                
                total_compra += det_dict["subtotal"]
                
            
            resultado["total_compra"] = total_compra
            
            return resultado
    
    
    @staticmethod
    def listar_compras_por_sucursal(sucursal_id: int) -> list:
        """
        Listar compras por sucursal.
        
        Args:
            sucursal_id: ID de la sucursal
            
        Returns:
            Lista de dicts de compras
        """
        schema = CompraResponseSchema()
        with get_db_session() as session:
            compras = session.query(Compra).filter(
                Compra.sucursal_id == sucursal_id
            ).order_by(Compra.fecha_compra.desc()).all()
            
            return schema.dump(compras, many=True)
    
    
    @staticmethod
    def compra_existe(compra_id: int) -> bool:
        """
        Verificar si una compra existe.
        
        Args:
            compra_id: ID de la compra
            
        Returns:
            True si existe
        """
        with get_db_session() as session:
            existe = session.query(Compra).filter(
                Compra.id_compra == compra_id
            ).first()
            return existe is not None
    
    
    @staticmethod
    def actualizar_estatus_compra(compra_id: int, nuevo_estatus: int) -> bool:
        """
        Actualizar estatus de una compra.
        Estatus: 1=Pendiente, 2=En Inventario, 3=Cancelada
        
        Args:
            compra_id: ID de la compra
            nuevo_estatus: Nuevo estatus (1, 2 o 3)
            
        Returns:
            True si se actualizó correctamente
        """
        with get_db_session() as session:
            compra = session.query(Compra).filter(
                Compra.id_compra == compra_id
            ).first()
            
            if not compra:
                return False
            
            compra.estatus = nuevo_estatus
            session.commit()
            logger.info(f"Compra {compra_id} actualizada a estatus {nuevo_estatus}")
            return True


class CompraDetalleDAO:
    """Data Access Object para CompraDetalle"""
    
    @staticmethod
    def agregar_detalle(compra_id: int, insumo_id: int, 
                       cant_presentacion: float, costo_unit_present: float, presentacion: str) -> dict:
        """
        Agregar detalle a una compra.
        
        Args:
            compra_id: ID de la compra
            insumo_id: ID del insumo
            cant_presentacion: Cantidad en presentación del proveedor
            costo_unit_present: Costo unitario por presentación
            
        Returns:
            Dict serializado del detalle
        """
        schema = CompraDetalleResponseSchema()
        with get_db_session() as session:
            detalle = CompraDetalle(
                compra_id=compra_id,
                insumo_id=insumo_id,
                cant_presentacion=cant_presentacion,
                costo_unit_present=costo_unit_present,
                presentacion=presentacion
            )
            session.add(detalle)
            session.commit()
            logger.info(f"Detalle de compra agregado: Compra {compra_id}, Insumo {insumo_id}")
            return schema.dump(detalle)
    
    
    @staticmethod
    def obtener_detalles_por_compra(compra_id: int) -> list:
        """
        Obtener detalles de una compra.
        
        Args:
            compra_id: ID de la compra
            
        Returns:
            Lista de dicts de detalles
        """
        schema = CompraDetalleResponseSchema()
        with get_db_session() as session:
            detalles = session.query(CompraDetalle).filter(
                CompraDetalle.compra_id == compra_id
            ).all()
            
            return schema.dump(detalles, many=True)
