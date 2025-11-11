"""
Módulo rrhh - Modelos del esquema rrhh (Recursos Humanos)
"""

from .horario_model import Horario
from .horario_detalle_model import HorarioDetalle
from .usuario_horario_model import UsuarioHorario
from .turno_clave_model import TurnoClave
from .asistencia_model import Asistencia
from .solicitud_vacaciones_model import SolicitudVacaciones

__all__ = [
    'Horario',
    'HorarioDetalle',
    'UsuarioHorario',
    'TurnoClave',
    'Asistencia',
    'SolicitudVacaciones'
]
