
### Supervisor
  is a process control system that lets you monitor and control processes (especially background services) on UNIX-like systems.

- Installation: sudo apt install supervisor
- Configuration Directory: /etc/supervisor/conf.d/
- uses of Supervisor:
  - Keep long-running processes alive (auto-restart on crash).
  - Manage background tasks (e.g., Celery workers, Gunicorn, etc.).
  - Start/stop/restart processes easily.
  - Log stdout/stderr to files.
  - Run processes as different users

- Control Commands:
  - sudo supervisorctl reread	        // Detect new .conf files
  - sudo supervisorctl update	        // Apply changes
  - sudo supervisorctl start celery	  // Start the celery program
  - sudo supervisorctl stop celery	  // Stop the celery program
  - sudo supervisorctl restart celery	// Restart the celery program
  - sudo supervisorctl status	        // See all program statuses
    
- Example of Supervisor Command:
  ```
    # setup.conf
    [fcgi-program:data_collector_asgi]
    socket=tcp://localhost:8000
    command=/opt/DataCollector-Backend/venv/bin/daphne -u /run/daphne/daphne%(process_num)d.sock --fd 0 --access-log - --proxy-headers config.asgi:application
    process_name=asgi_%(process_num)d
    numprocs=1
    directory=/opt/DataCollector-Backend
    priority=999
    autostart=true
    autorestart=true
    user=www-data
    redirect_stderr=true
    stdout_logfile=/var/log/DataCollector-Backend/asgi.log
    environment=DJANGO_SETTINGS_MODULE=config.settings.production
    
    [program:data_collector_celery_worker]
    command=/opt/DataCollector-Backend/venv/bin/celery -A config.celery worker --loglevel=INFO --concurrency=1
    process_name=celery_worker_%(process_num)d
    numprocs=1
    directory=/opt/DataCollector-Backend
    priority=997
    autostart=true
    autorestart=true
    redirect_stderr=true
    stdout_logfile=/var/log/DataCollector-Backend/celery_worker.log
    environment=DJANGO_SETTINGS_MODULE=config.settings.production
    
    [program:data_collector_celery_beat]
    command=/opt/DataCollector-Backend/venv/bin/celery -A config.celery beat --loglevel=INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler
    process_name=celery_beat_%(process_num)d
    numprocs=1
    directory=/opt/DataCollector-Backend
    priority=998
    autostart=true
    autorestart=true
    redirect_stderr=true
    stdout_logfile=/var/log/DataCollector-Backend/celery_beat.log
    environment=DJANGO_SETTINGS_MODULE=config.settings.production
    
    [group:data_collector_celery]
    programs=data_collector_celery_worker,data_collector_celery_beat

  ```

- FastCGI is a binary protocol used to communicate between a web server (like Nginx or Apache) and a backend application (like PHP, Python, etc.).
