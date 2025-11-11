import multiprocessing
import os

max_requests = 1000
max_requests_jitter = 50
log_file = "-"
bind = "0.0.0.0"
timeout = 230

num_cpus = multiprocessing.cpu_count()
workers = (num_cpus * 2) + 1
threads = 1 if num_cpus == 1 else 2
worker_class = "gthread"

preload_app = True
worker_connections = 1000
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info")