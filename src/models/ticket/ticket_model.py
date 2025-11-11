"""
Ticket - Modelo para incidencias/problemas reportados por empleados
Mapea tabla ticket.Ticket
"""

from sqlalchemy import Column, Integer, SmallInteger, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.base import BaseModel


class Ticket(BaseModel):
    """Modelo para Tickets de incidencias"""
    __tablename__ = 'Ticket'
    __table_args__ = {'schema': 'ticket'}
    
    id_ticket = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey('seguridad.Usuario.id_usuario'), nullable=False)
    notas = Column(String(500), nullable=True)
    imagen_url = Column(String(500), nullable=True)  # blob -> String para URL
    estatus = Column(SmallInteger, nullable=False, default=1)  # 1=Registrada, 2=EnProceso, 3=Completada, 4=Cancelada
    created_at = Column(DateTime, nullable=False, default=func.getdate())
    
    # Relaciones
    usuario = relationship("Usuario")
    
    def __repr__(self):
        return f"<Ticket id={self.id_ticket} usuario={self.usuario_id} estatus={self.estatus}>"
