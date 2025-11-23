"""
Pedido Model - Pedido, PedidoItem, PedidoEstadoHist
operaciones.Pedido - Centro de operaciones para pedidos
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Index, text, SMALLINT
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import Base, BaseModel


class Pedido(BaseModel):
    """Modelo para Pedido (Orden)"""
    __tablename__ = 'Pedido'
    __table_args__ = (
        Index('IX_Pedido_Sucursal', 'sucursal_id'),
        Index('IX_Pedido_SucursalFecha', 'sucursal_id', 'created_at'),
        Index('IX_Pedido_Estado', 'estado_pedido'),
        Index('IX_Pedido_MesaEstado', 'sucursal_id', 'mesa_id', 'estado_pedido'),
        {'schema': 'operaciones'}
    )
    
    id_pedido = Column(Integer, primary_key=True)
    sucursal_id = Column(Integer, ForeignKey('catalogos.Sucursal.id_sucursal'), nullable=False)
    folio = Column(String(20), nullable=False)
    cliente_id = Column(Integer, ForeignKey('seguridad.Usuario.id_usuario'), nullable=False)
    tipo_pedido = Column(SMALLINT, nullable=False)  # 1=Dine-in, 2=Takeaway
    canal = Column(SMALLINT, nullable=False)  # 1=PWA, 2=Móvil, 3=Presencial
    reserva_id = Column(Integer, ForeignKey('operaciones.Reserva.id_reserva'), nullable=False)
    mesa_id = Column(Integer, ForeignKey('catalogos.Mesa.id_mesa'), nullable=True)  # NULL para takeaway
    inicia_usuario_id = Column(Integer, ForeignKey('seguridad.Usuario.id_usuario'), nullable=False)
    estado_pedido = Column(SMALLINT, nullable=False, default=1)  # 1=Creado,2=Confirmado,3=EnPreparacion,4=Listo,5=Entregado,6=Cancelado
    notas = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=text('SYSUTCDATETIME()'), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relaciones
    sucursal = relationship("Sucursal", backref="pedidos")
    cliente = relationship("Usuario", foreign_keys=[cliente_id], backref="pedidos_como_cliente")
    usuario_inicia = relationship("Usuario", foreign_keys=[inicia_usuario_id], backref="pedidos_iniciados")
    mesa = relationship("Mesa", backref="pedidos")
    reserva = relationship("Reserva", backref="pedidos")
    items = relationship("PedidoItem", back_populates="pedido", cascade="all, delete-orphan")
    estado_hist = relationship("PedidoEstadoHist", back_populates="pedido", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Pedido {self.id_pedido}: {self.folio} (Estado={self.estado_pedido})>"


class PedidoItem(BaseModel):
    """Modelo para PedidoItem (Línea de Pedido)"""
    __tablename__ = 'PedidoItem'
    __table_args__ = (
        Index('IX_PedidoItem_Pedido', 'pedido_id'),
        {'schema': 'operaciones'}
    )
    
    id_pedido_item = Column(Integer, primary_key=True)
    pedido_id = Column(Integer, ForeignKey('operaciones.Pedido.id_pedido'), nullable=False)
    producto_id = Column(Integer, ForeignKey('catalogos.Producto.id_producto'), nullable=True)
    combo_id = Column(Integer, ForeignKey('catalogos.Combo.id_combo'), nullable=True)
    cantidad = Column(Integer, nullable=False, default=1)
    precio_unit = Column(Numeric(12, 2), nullable=False)
    notas = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=text('SYSUTCDATETIME()'), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relaciones
    pedido = relationship("Pedido", back_populates="items")
    
    def __repr__(self):
        return f"<PedidoItem pedido={self.pedido_id}, producto={self.producto_id}, combo={self.combo_id}, cant={self.cantidad}>"


class PedidoEstadoHist(BaseModel):
    """Modelo para PedidoEstadoHist (Historial de Estados)"""
    __tablename__ = 'PedidoEstadoHist'
    __table_args__ = ({'schema': 'operaciones'},)
    
    id_pedido_estado_hist = Column(Integer, primary_key=True)
    pedido_id = Column(Integer, ForeignKey('operaciones.Pedido.id_pedido'), nullable=False)
    estado_pedido = Column(SMALLINT, nullable=False)
    usuario_id = Column(Integer, ForeignKey('seguridad.Usuario.id_usuario'), nullable=True)
    created_at = Column(DateTime, server_default=text('SYSUTCDATETIME()'), nullable=False)
    comentario = Column(String(100), nullable=True)
    
    # Relaciones
    pedido = relationship("Pedido", back_populates="estado_hist")
    
    def __repr__(self):
        return f"<PedidoEstadoHist pedido={self.pedido_id}, estado={self.estado_pedido}>"
