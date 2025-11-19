"""
Configuración de Jobs Automáticos con APScheduler
Expira holds incompletos y verifica NoShows periódicamente
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import logging
import atexit
import pytz

logger = logging.getLogger(__name__)

# Zona horaria de México
TZ_MEXICO = pytz.timezone('America/Mexico_City')

# Variable global para rastrear estado del scheduler
_scheduler_instance = None
_scheduler_status = {
    'initialized': False,
    'running': False,
    'error': None,
    'last_check': None
}


def init_scheduler():
    """
    Inicializar scheduler de jobs automáticos.
    
    ⚠️  SCHEDULER COMPLETAMENTE DESHABILITADO
    
    Los jobs NO se ejecutan en el scheduler.
    Azure Function ahora es responsable de ejecutar:
    - POST /api/jobs/expirar-holds (cada 30 segundos)
    - POST /api/jobs/verificar-no-shows (cada 5 minutos)
    
    El scheduler.py se mantiene por compatibilidad con el código existente.
    
    Returns:
        None (scheduler no se inicializa nunca)
    """
    global _scheduler_instance, _scheduler_status
    
    logger.warning("=" * 80)
    logger.warning("[SCHEDULER] ⚠️  SCHEDULER DESHABILITADO - Azure Function ejecutará los jobs")
    logger.warning("[SCHEDULER] Los jobs se ejecutan mediante:")
    logger.warning("  ├─ POST /api/jobs/expirar-holds (cada 30 segundos)")
    logger.warning("  └─ POST /api/jobs/verificar-no-shows (cada 5 minutos)")
    logger.warning("=" * 80)
    
    _scheduler_status['initialized'] = False
    _scheduler_status['running'] = False
    _scheduler_status['error'] = 'SCHEDULER_DISABLED_AZURE_FUNCTION'
    print("\n[SCHEDULER] ⚠️  SCHEDULER DESHABILITADO - Azure Function ejecutará los jobs\n")
    
    return None
    
    # ✅ CÓDIGO ORIGINAL REMOVIDO - scheduler no se inicializa
    
    # Los jobs ahora se ejecutan mediante Azure Function:
    # - POST /api/jobs/expirar-holds (cada 30 segundos)
    # - POST /api/jobs/verificar-no-shows (cada 5 minutos)


def get_scheduler_instance():
    """
    Obtener la instancia global del scheduler.
    
    Returns:
        None (scheduler siempre deshabilitado)
    """
    global _scheduler_instance
    return _scheduler_instance


def get_scheduler_status():
    """
    Obtener estado del scheduler.
    
    Returns:
        dict con estado del scheduler
    """
    return _scheduler_status.copy()


def is_scheduler_running():
    """
    Verificar si el scheduler está corriendo.
    
    Returns:
        False (scheduler siempre deshabilitado)
    """
    global _scheduler_instance
    if _scheduler_instance is None:
        return False
    return _scheduler_instance.running


# Para uso manual/testing
if __name__ == "__main__":
    # Configurar logging para pruebas
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Iniciando scheduler de prueba...")
    scheduler = init_scheduler()
    
    print("Scheduler activo. Jobs configurados:")
    for job in scheduler.get_jobs():
        print(f"  - {job.name} (ID: {job.id})")
        print(f"    Next run: {job.next_run_time}")
    
    print("\nPresiona Ctrl+C para detener...")
    
    try:
        # Mantener el script corriendo
        import time
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nDeteniendo scheduler...")
        scheduler.shutdown()
        print("Scheduler detenido.")

