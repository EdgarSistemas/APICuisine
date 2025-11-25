"""
Pago Model
pagos.Pago - Gestión de pagos

Columnas en BD:
  id_pago, pedido_id, sucursal_id, monto, propina, moneda, estatus, usuario_id, created_at, updated_at
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, Numeric, String, SmallInteger, Index, text
from sqlalchemy.orm import relationship
from src.models.base import BaseModel


class Pago(BaseModel):
    """
    Modelo de Pago.
    
    Estatus:
        1 = Pendiente (registrado, sin confirmar)
        2 = Pagado (confirmado)
        3 = Anulado/Cancelado
    """
    __tablename__ = 'Pago'
    __table_args__ = (
        Index('IX_Pago_Pedido', 'pedido_id'),
        Index('IX_Pago_PedidoEstatus', 'pedido_id', 'estatus'),
        Index('IX_Pago_SucursalFecha', 'sucursal_id', 'created_at'),
        {'schema': 'pagos'}
    )
    
    id_pago = Column(Integer, primary_key=True)
    pedido_id = Column(Integer, ForeignKey('operaciones.Pedido.id_pedido'), nullable=False)
    sucursal_id = Column(Integer, ForeignKey('catalogos.Sucursal.id_sucursal'), nullable=False)
    monto = Column(Numeric(10, 2), nullable=False)
    propina = Column(Numeric(10, 2), default=0, nullable=False)
    moneda = Column(String(5), default='MXN', nullable=False)
    estatus = Column(SmallInteger, nullable=False, default=1)  # 1=Pendiente, 2=Pagado, 3=Anulado
    usuario_id = Column(Integer, ForeignKey('seguridad.Usuario.id_usuario'))
    created_at = Column(DateTime, server_default=text('SYSUTCDATETIME()'), nullable=False)
    updated_at = Column(DateTime)
    
    # Relaciones
    pedido = relationship("Pedido", backref="pagos")
    sucursal = relationship("Sucursal", backref="pagos")
    usuario = relationship("Usuario", backref="pagos")
    
    def __repr__(self):
        return f"<Pago {self.id_pago}: ${self.monto} (Pedido {self.pedido_id})>"
    
    def to_dict(self):
        """Serializa el modelo a diccionario"""
        monto_float = float(self.monto) if self.monto else 0
        propina_float = float(self.propina) if self.propina else 0
        
        return {
            'id_pago': self.id_pago,
            'pedido_id': self.pedido_id,
            'sucursal_id': self.sucursal_id,
            'monto': monto_float,
            'propina': propina_float,
            'total': monto_float + propina_float,
            'moneda': self.moneda,
            'estatus': self.estatus,
            'estatus_display': self._get_estatus_display(),
            'usuario_id': self.usuario_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def _get_estatus_display(self):
        """Retorna nombre legible del estatus"""
        estatus_map = {
            1: "Pendiente",
            2: "Pagado",
            3: "Anulado"
        }
        return estatus_map.get(self.estatus, "Desconocido")
