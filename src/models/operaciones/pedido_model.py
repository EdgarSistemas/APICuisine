"""
Pedido Model - Pedido, PedidoEstadoHist
operaciones.Pedido - Centro de operaciones para pedidos

Sistema de Estados de Pedido (estado_pedido):
    0 = Iniciado (pedido recién creado, items se agregan en EnCocina directamente)
    1 = (reservado para items EnCocina)
    2 = (reservado para items Listo)
    3 = Completo (usuario cierra el pedido)
    4 = Cancelado
    5 = Pagado

Flujo Pedido: 0 (crear) → 3 (cerrar) → 5 (pagar)
Flujo Items:  1 (crear+inventario) → 2 (cocina listo) → 3 (cerrar) → 5 (pagar)

NOTA: PedidoItem está en pedido_item_model.py para evitar duplicados
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Index, text, SMALLINT
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import Base, BaseModel

# Constantes de estado de Pedido
ESTADO_INICIADO = 0     # Pedido recién creado
ESTADO_COMPLETO = 3     # Pedido cerrado por usuario
ESTADO_CANCELADO = 4    # Pedido cancelado
ESTADO_PAGADO = 5       # Pedido pagado

# Mapas de estados para display
ESTADO_PEDIDO_MAP = {
    0: 'Iniciado',
    3: 'Completo',
    4: 'Cancelado',
    5: 'Pagado'
}

# Re-exportar constantes de PedidoItem para compatibilidad
from src.models.operaciones.pedido_item_model import (
    ESTATUS_ITEM_EN_COCINA,
    ESTATUS_ITEM_LISTO,
    ESTATUS_ITEM_COMPLETO,
    ESTATUS_ITEM_CANCELADO,
    ESTATUS_ITEM_PAGADO,
    ESTATUS_ITEM_MAP,
    PedidoItem
)


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
    estado_pedido = Column(SMALLINT, nullable=False, default=ESTADO_INICIADO)  # 0=Iniciado,3=Completo,4=Cancelado,5=Pagado
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
        estado_str = ESTADO_PEDIDO_MAP.get(self.estado_pedido, 'Desconocido')
        return f"<Pedido {self.id_pedido}: {self.folio} ({estado_str})>"


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
