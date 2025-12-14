import multiprocessing

workers = (2 * multiprocessing.cpu_count()) + 1
worker_class = "uvicorn.workers.UvicornWorker"

bind = "0.0.0.0:8000"

accesslog = "-"
errorlog = "-"
loglevel = "info"
