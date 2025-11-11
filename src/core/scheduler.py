"""
Configuración de Jobs Automáticos con APScheduler
Expira holds y verifica NoShows periódicamente
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import logging
import atexit

logger = logging.getLogger(__name__)


def init_scheduler():
    """
    Inicializar scheduler de jobs automáticos.
    
    Jobs configurados:
    1. Expirar holds: Cada 2 minutos
    2. Verificar NoShows: Cada 5 minutos
    """
    from src.dao.operaciones.hold_mesa_dao import HoldMesaDAO
    from src.dao.operaciones.reserva_dao import ReservaDAO
    
    scheduler = BackgroundScheduler(
        daemon=True,
        timezone='America/Mexico_City'  # Ajustar según tu zona horaria
    )
    
    # JOB 1: Expirar holds vencidos
    def job_expirar_holds():
        try:
            count = HoldMesaDAO.expirar_holds_vencidos()
            if count > 0:
                logger.info(f"[SCHEDULER] Job expirar_holds: {count} holds expirados")
        except Exception as e:
            logger.error(f"[SCHEDULER] Error en job expirar_holds: {str(e)}")
    
    # JOB 2: Verificar reservas NoShow
    def job_verificar_noshows():
        try:
            count = ReservaDAO.verificar_no_shows()
            if count > 0:
                logger.info(f"[SCHEDULER] Job verificar_noshows: {count} reservas marcadas como NoShow")
        except Exception as e:
            logger.error(f"[SCHEDULER] Error en job verificar_noshows: {str(e)}")
    
    # Agregar jobs al scheduler
    scheduler.add_job(
        func=job_expirar_holds,
        trigger=IntervalTrigger(minutes=2),
        id='expirar_holds',
        name='Expirar Holds Vencidos',
        replace_existing=True,
        max_instances=1  # Solo una instancia a la vez
    )
    
    scheduler.add_job(
        func=job_verificar_noshows,
        trigger=IntervalTrigger(minutes=5),
        id='verificar_noshows',
        name='Verificar Reservas NoShow',
        replace_existing=True,
        max_instances=1
    )
    
    # Iniciar scheduler
    scheduler.start()
    logger.info("[SCHEDULER] Jobs automáticos iniciados:")
    logger.info("  - Expirar holds: cada 2 minutos")
    logger.info("  - Verificar NoShows: cada 5 minutos")
    
    # Shutdown graceful al cerrar app
    atexit.register(lambda: scheduler.shutdown(wait=False))
    
    return scheduler


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
